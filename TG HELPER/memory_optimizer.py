# -*- coding: utf-8 -*-
"""
内存优化器 - 进程管理、系统内存清理、显存清理
"""
import os
import sys
import gc
import ctypes
import subprocess
import threading
from typing import List, Dict, Optional

# 受保护进程白名单（绝对不能被关闭）
_SYSTEM_WHITELIST = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "winlogon.exe", "services.exe", "lsass.exe", "svchost.exe",
    "spoolsv.exe", "dwm.exe", "explorer.exe", "taskhostw.exe", "sihost.exe",
    "ctfmon.exe", "fontdrvhost.exe", "audiodg.exe", "wlms.exe",
}

# 属于 AI 自身的进程（不能关闭自己）
_SELF_PIDS = {os.getpid()}

def _get_parent_pids() -> set:
    pids = set()
    try:
        pid = os.getpid()
        while pid > 0:
            try:
                import psutil
                proc = psutil.Process(pid)
                parent = proc.ppid()
                if parent > 0 and parent != pid:
                    pids.add(parent)
                    pid = parent
                else:
                    break
            except (ImportError, Exception):
                break
    except Exception:
        pass
    return pids

_SELF_PIDS |= _get_parent_pids()


def _is_safe_to_kill(proc_name: str, pid: int) -> bool:
    """检查进程是否可以安全关闭"""
    name_lower = proc_name.lower().replace('.exe', '')
    if any(wl in name_lower for wl in _SYSTEM_WHITELIST):
        return False
    if pid in _SELF_PIDS:
        return False
    if pid == 0 or pid == 4:
        return False
    return True


def list_processes(top_n: int = 30) -> str:
    """列出当前正在运行的进程（按内存占用排序）"""
    try:
        import psutil
    except ImportError:
        return "ERROR: 缺少 psutil 模块，请使用 install_python_package 安装 psutil"

    lines = ["PID    内存(MB)  进程名"]
    lines.append("-" * 50)
    try:
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                info = proc.info
                mem_mb = info['memory_info'].rss / 1024 / 1024 if info['memory_info'] else 0
                procs.append((info['pid'], info['name'], mem_mb))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x[2], reverse=True)
        for i, (pid, name, mem_mb) in enumerate(procs[:top_n]):
            mark = ""
            if not _is_safe_to_kill(name, pid):
                mark = " 🛡️(受保护)"
            lines.append(f"{pid:<7} {mem_mb:<10.1f} {name}{mark}")
        lines.append(f"\n共 {len(procs)} 个进程，显示前 {min(top_n, len(procs))} 个（按内存排序）")
        lines.append("🛡️ 标记的进程受系统保护，不可关闭")
    except Exception as e:
        return f"ERROR: 获取进程列表失败: {e}"
    return "\n".join(lines)


def kill_process_by_name(name: str) -> str:
    """按进程名结束进程（受白名单保护）"""
    try:
        import psutil
    except ImportError:
        return "ERROR: 缺少 psutil 模块"

    killed = []
    blocked = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == name.lower():
                pid = proc.info['pid']
                if _is_safe_to_kill(proc.info['name'], pid):
                    proc.terminate()
                    killed.append(f"{proc.info['name']}(PID:{pid})")
                else:
                    blocked.append(f"{proc.info['name']}(PID:{pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    result = []
    if killed:
        result.append(f"已结束 {len(killed)} 个进程: {', '.join(killed)}")
    if blocked:
        result.append(f"拒绝结束 {len(blocked)} 个受保护进程: {', '.join(blocked)}")
    if not killed and not blocked:
        result.append(f"未找到进程: {name}")
    return "\n".join(result)


def kill_process_by_pid(pid: int) -> str:
    """按 PID 结束进程（受白名单保护）"""
    try:
        import psutil
    except ImportError:
        return "ERROR: 缺少 psutil 模块"

    try:
        proc = psutil.Process(pid)
        name = proc.name()
        if _is_safe_to_kill(name, pid):
            proc.terminate()
            return f"已结束进程: {name}(PID:{pid})"
        else:
            return f"拒绝结束受保护进程: {name}(PID:{pid})"
    except psutil.NoSuchProcess:
        return f"进程 PID:{pid} 不存在或已退出"
    except psutil.AccessDenied:
        return f"权限不足，无法结束 PID:{pid}"


def optimize_memory() -> str:
    """执行系统内存清理（非破坏性）"""
    lines = []

    # 1. Python GC
    gc.collect()
    gc.collect()
    lines.append("✅ Python 垃圾回收已执行")

    # 2. ctypes 释放工作集
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, -1, -1)
        lines.append("✅ 当前进程工作集已释放")
    except Exception as e:
        lines.append(f"⚠️ 工作集释放失败: {e}")

    # 3. 调用 Windows EmptyWorkingSet
    try:
        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
        lines.append("✅ Windows EmptyWorkingSet 已执行")
    except Exception:
        pass

    # 4. 各磁盘的临时文件统计（不自动删除）
    temp_paths = [
        os.environ.get('TEMP', ''),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
    ]
    total_temp_size = 0
    for tp in temp_paths:
        if os.path.exists(tp):
            try:
                for root, dirs, files in os.walk(tp):
                    for f in files:
                        try:
                            total_temp_size += os.path.getsize(os.path.join(root, f))
                        except OSError:
                            pass
            except Exception:
                pass
    if total_temp_size > 0:
        lines.append(f"💡 临时文件夹约占用 {total_temp_size / 1024 / 1024:.1f} MB（未自动清理）")

    return "\n".join(lines)


def optimize_vram() -> str:
    """尝试清理显存（仅对 PyTorch / CUDA 生效）"""
    lines = []

    # CUDA
    try:
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024 / 1024
            cached = torch.cuda.memory_reserved() / 1024 / 1024
            torch.cuda.empty_cache()
            lines.append(f"✅ CUDA 显存已清理（释放前: 已分配 {allocated:.1f}MB, 缓存 {cached:.1f}MB）")
        else:
            lines.append("ℹ️ CUDA 不可用，跳过")
    except ImportError:
        lines.append("ℹ️ 未安装 PyTorch，跳过 CUDA 显存清理")

    # ONNX Runtime
    try:
        import onnxruntime
        if hasattr(onnxruntime, 'OrtSession'):
            gc.collect()
            lines.append("✅ ONNX Runtime 显存垃圾回收已触发")
    except ImportError:
        pass

    # Ollama（通知重新加载而非清理）
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            lines.append("ℹ️ 检测到 Ollama 正在运行（显存由其管理，不可外部清理）")
    except Exception:
        pass

    # llama.cpp / GGUF 通用提示
    lines.append("💡 GGUF/llama.cpp 模型的显存由推理引擎管理，退出时会自动释放")

    return "\n".join(lines)


def full_optimize() -> str:
    """执行完整优化：内存 + 显存"""
    lines = ["📊 ====== 内存优化报告 ======="]
    lines.append(optimize_memory())
    lines.append("\n🎮 ====== 显存优化报告 =======")
    lines.append(optimize_vram())
    return "\n".join(lines)
