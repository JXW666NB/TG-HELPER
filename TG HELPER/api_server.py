#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TG Home API Server - 独立运行，提供物联网设备控制和工具接口
默认地址: http://127.0.0.1:5000
使用前请确保 TG Helper 的主程序未同时占用 IOT_manager 单例（可单独运行，不冲突）
"""

import json
import os
import sys
import threading
import time
from functools import wraps

# 添加当前目录到路径，以便导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入所需模块
from IOT_manager import iot_manager
from tools import Tools
from memory import Memory
from config import config

# 尝试导入 Flask，若失败则自动安装
try:
    from flask import Flask, request, jsonify
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    from flask import Flask, request, jsonify

# ==================== 初始化 ====================
app = Flask(__name__)

# 初始化 Tools（需要 memory 和 config）
memory = Memory(config.memory_dir)
tools = Tools(memory, confirm_callback=lambda msg: True, output_callback=print, task_scheduler=None, gui=None)

# 可选：API 密钥认证（从环境变量或配置文件读取）
API_KEY = os.environ.get("TG_API_KEY", "")  # 设置 TG_API_KEY 环境变量可启用认证
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if API_KEY:
            provided = request.headers.get("X-API-Key") or request.args.get("api_key")
            if provided != API_KEY:
                return jsonify({"error": "Unauthorized", "message": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated

# ==================== 通用响应格式 ====================
def make_response(success, data=None, error=None):
    return jsonify({
        "success": success,
        "data": data,
        "error": error
    })

# ==================== 设备管理 API ====================
@app.route("/api/devices", methods=["GET"])
@require_api_key
def list_devices():
    """获取所有设备列表"""
    devices = iot_manager.list_devices()
    return make_response(True, devices)

@app.route("/api/devices/<device_name>/control", methods=["POST"])
@require_api_key
def control_device(device_name):
    """控制设备
    请求体 JSON: {"command": "on"} 或 {"command": "off"} (布尔类)
                或 {"command": "预设指令名称"} (复杂类)
    """
    data = request.get_json()
    if not data or "command" not in data:
        return make_response(False, error="Missing 'command' field")
    command = data["command"]
    dev = iot_manager.get_device(device_name)
    if not dev:
        return make_response(False, error=f"Device '{device_name}' not found")
    if dev.device_type == "bool":
        result = iot_manager.send_to_device(device_name, command)
    else:
        result = iot_manager.send_to_device(device_name, command)
    return make_response(True, {"result": result})

@app.route("/api/devices/<device_name>/bool", methods=["POST"])
@require_api_key
def control_bool_device(device_name):
    """控制布尔设备（专用）"""
    data = request.get_json()
    if not data or "state" not in data:
        return make_response(False, error="Missing 'state' field (on/off)")
    state = data["state"].lower()
    if state not in ("on", "off"):
        return make_response(False, error="State must be 'on' or 'off'")
    dev = iot_manager.get_device(device_name)
    if not dev:
        return make_response(False, error=f"Device '{device_name}' not found")
    if dev.device_type != "bool":
        return make_response(False, error=f"Device '{device_name}' is not a bool device")
    result = iot_manager.send_to_device(device_name, state)
    return make_response(True, {"result": result})

@app.route("/api/devices/<device_name>/complex", methods=["POST"])
@require_api_key
def control_complex_device(device_name):
    """控制复杂设备"""
    data = request.get_json()
    if not data or "command" not in data:
        return make_response(False, error="Missing 'command' field")
    command = data["command"]
    dev = iot_manager.get_device(device_name)
    if not dev:
        return make_response(False, error=f"Device '{device_name}' not found")
    if dev.device_type != "complex":
        return make_response(False, error=f"Device '{device_name}' is not a complex device")
    result = iot_manager.send_to_device(device_name, command)
    return make_response(True, {"result": result})

# ==================== 传感器管理 API ====================
@app.route("/api/sensors", methods=["GET"])
@require_api_key
def list_sensors():
    """获取所有传感器列表"""
    sensors = [s.to_dict() for s in iot_manager.sensors.values()]
    return make_response(True, sensors)

# ==================== 触发器管理 API ====================
@app.route("/api/triggers", methods=["GET"])
@require_api_key
def list_triggers():
    """获取所有触发器"""
    triggers = iot_manager.get_triggers()
    return make_response(True, triggers)

@app.route("/api/triggers", methods=["POST"])
@require_api_key
def add_trigger():
    """添加触发器
    请求体 JSON: {"name": "xxx", "sensor_name": "xxx", "match_pattern": "", "tasks": [...]}
    """
    data = request.get_json()
    if not data or "name" not in data or "sensor_name" not in data:
        return make_response(False, error="Missing 'name' or 'sensor_name'")
    # 复用 tools.ai_add_trigger 的逻辑
    from tools import Tools
    # 注意：需要临时创建 Tools 实例或直接调用 iot_manager.add_trigger
    trigger_data = {
        "name": data["name"],
        "sensor_name": data["sensor_name"],
        "match_pattern": data.get("match_pattern", ""),
        "tasks": data.get("tasks", []),
        "enabled": data.get("enabled", True)
    }
    if iot_manager.add_trigger(trigger_data):
        return make_response(True, {"message": f"Trigger '{data['name']}' added"})
    else:
        return make_response(False, error=f"Trigger '{data['name']}' already exists")

@app.route("/api/triggers/<trigger_name>", methods=["DELETE"])
@require_api_key
def delete_trigger(trigger_name):
    """删除触发器"""
    if iot_manager.remove_trigger(trigger_name):
        return make_response(True, {"message": f"Trigger '{trigger_name}' deleted"})
    else:
        return make_response(False, error=f"Trigger '{trigger_name}' not found")

# ==================== 日志 API ====================
@app.route("/api/logs", methods=["GET"])
@require_api_key
def get_logs():
    """获取设备日志，参数 ?limit=100"""
    limit = request.args.get("limit", 100, type=int)
    from iot_logger import iot_logger
    logs = iot_logger.get_logs(limit)
    return make_response(True, logs)

# ==================== 工具 API ====================
@app.route("/api/tools/screenshot", methods=["POST"])
@require_api_key
def api_screenshot():
    """截取屏幕截图"""
    result = tools.screenshot()
    return make_response(True, {"result": result})

@app.route("/api/tools/execute_command", methods=["POST"])
@require_api_key
def api_execute_command():
    """执行系统命令（危险操作，请谨慎使用）"""
    data = request.get_json()
    if not data or "command" not in data:
        return make_response(False, error="Missing 'command' field")
    command = data["command"]
    cwd = data.get("cwd", None)
    result = tools.execute_command(command, cwd)
    return make_response(True, result)

@app.route("/api/tools/read_file", methods=["POST"])
@require_api_key
def api_read_file():
    """读取文件内容"""
    data = request.get_json()
    if not data or "filepath" not in data:
        return make_response(False, error="Missing 'filepath' field")
    filepath = data["filepath"]
    max_chars = data.get("max_chars", 8000000)
    result = tools.read_file(filepath, max_chars)
    return make_response(True, {"result": result})

@app.route("/api/tools/write_file", methods=["POST"])
@require_api_key
def api_write_file():
    """写入文件"""
    data = request.get_json()
    if not data or "filepath" not in data or "content" not in data:
        return make_response(False, error="Missing 'filepath' or 'content'")
    result = tools.write_file(data["filepath"], data["content"])
    return make_response(True, {"result": result})

@app.route("/api/tools/list_directory", methods=["POST"])
@require_api_key
def api_list_directory():
    """列出目录内容"""
    data = request.get_json()
    path = data.get("path", ".") if data else "."
    result = tools.list_directory(path)
    return make_response(True, {"result": result})

@app.route("/api/tools/open_browser", methods=["POST"])
@require_api_key
def api_open_browser():
    """打开浏览器"""
    data = request.get_json()
    if not data or "url" not in data:
        return make_response(False, error="Missing 'url'")
    result = tools.open_browser(data["url"])
    return make_response(True, {"result": result})

# ==================== 健康检查 ====================
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "timestamp": time.time()})

# ==================== 启动服务器 ====================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="TG Home API Server")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址 (默认 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5001, help="监听端口 (默认 5000)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()
    
    print(f"Starting TG Home API Server on http://{args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /api/devices")
    print("  POST /api/devices/<name>/control")
    print("  POST /api/devices/<name>/bool")
    print("  POST /api/devices/<name>/complex")
    print("  GET  /api/sensors")
    print("  GET  /api/triggers")
    print("  POST /api/triggers")
    print("  DELETE /api/triggers/<name>")
    print("  GET  /api/logs")
    print("  POST /api/tools/screenshot")
    print("  POST /api/tools/execute_command")
    print("  POST /api/tools/read_file")
    print("  POST /api/tools/write_file")
    print("  POST /api/tools/list_directory")
    print("  POST /api/tools/open_browser")
    print("  GET  /api/health")
    if API_KEY:
        print("API Key authentication enabled. Set 'X-API-Key' header or 'api_key' param.")
    else:
        print("No API key set. To enable authentication, set environment variable TG_API_KEY.")
    
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

if __name__ == "__main__":
    main()
