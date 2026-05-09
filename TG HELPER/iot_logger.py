import json
import os
import threading
from datetime import datetime
from typing import List, Dict

class IOTLogger:
    """物联网日志记录器（单例）"""
    _instance = None

    def __new__(cls, log_dir="./iot_logs"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_dir="./iot_logs"):
        if self._initialized:
            return
        self._initialized = True
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "device_log.json")
        self.lock = threading.Lock()
        self._load_logs()

    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
            except:
                self.logs = []
        else:
            self.logs = []

    def _save_logs(self):
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)

    def log_device_command(self, device_name: str, command: str, result: str, protocol: str):
        """记录向设备发送的指令"""
        with self.lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "command",
                "device_name": device_name,
                "command": command,
                "result": result,
                "protocol": protocol
            }
            self.logs.append(entry)
            self._save_logs()

    def log_sensor_message(self, sensor_name: str, message: str, protocol: str, topic: str = ""):
        """记录传感器收到的消息"""
        with self.lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "sensor",
                "device_name": sensor_name,
                "message": message,
                "protocol": protocol,
                "topic": topic
            }
            self.logs.append(entry)
            self._save_logs()

    def get_logs(self, limit: int = 1000) -> List[Dict]:
        """获取最近的日志（最多 limit 条）"""
        with self.lock:
            return self.logs[-limit:]

    def get_logs_since(self, since: datetime) -> List[Dict]:
        """获取指定时间之后的日志"""
        with self.lock:
            result = []
            for entry in self.logs:
                try:
                    ts = datetime.fromisoformat(entry["timestamp"])
                    if ts >= since:
                        result.append(entry)
                except:
                    pass
            return result

    def clear_logs(self):
        """清空日志（调试用）"""
        with self.lock:
            self.logs = []
            self._save_logs()
            
    def log_trigger_triggered(self, trigger_name: str, sensor_name: str, message: str):
        """记录触发器被触发"""
        with self.lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "trigger",
                "trigger_name": trigger_name,
                "sensor_name": sensor_name,
                "message": message
            }
            self.logs.append(entry)
            self._save_logs()
iot_logger = IOTLogger()
