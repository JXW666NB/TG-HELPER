# -*- coding: utf-8 -*-
"""
Node.js 子进程桥接模块
"""
import os
import sys
import json
import subprocess
import threading
import queue
from typing import Optional, Callable, Dict, Any


class NodeBridge:
    """管理 Node.js 子进程，提供双向 JSON-RPC 通信和实时输出捕获"""

    def __init__(self, plugin_path: str, entry_script: str = "bridge.js"):
        self.plugin_path = plugin_path
        self.entry_script = os.path.join(plugin_path, entry_script)
        self.process: Optional[subprocess.Popen] = None
        self._running = False
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._message_handlers: Dict[str, Callable] = {}
        self._pending_requests: Dict[str, queue.Queue] = {}
        self._request_counter = 0
        self._lock = threading.Lock()

        self._stdout_callback: Optional[Callable[[str], None]] = None
        self._stderr_callback: Optional[Callable[[str], None]] = None

        self._node_executable = self._find_node()

    def _find_node(self) -> Optional[str]:
        paths = ["node", "nodejs", "/usr/bin/node", "/usr/local/bin/node"]
        for p in paths:
            try:
                result = subprocess.run([p, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return p
            except:
                continue
        return None

    def is_available(self) -> bool:
        return self._node_executable is not None

    def set_stdout_callback(self, callback: Callable[[str], None]):
        self._stdout_callback = callback

    def set_stderr_callback(self, callback: Callable[[str], None]):
        self._stderr_callback = callback

    def register_handler(self, method: str, handler: Callable):
        self._message_handlers[method] = handler

    def start(self, config: Dict[str, Any] = None) -> bool:
        if not self.is_available():
            print("[NodeBridge] Node.js 不可用，无法启动桥接进程")
            return False

        if self._running:
            return True

        env = os.environ.copy()
        if config:
            env["OPENCLAW_CONFIG"] = json.dumps(config)
        env["OPENCLAW_PLUGIN_PATH"] = self.plugin_path

        try:
            self.process = subprocess.Popen(
                [self._node_executable, self.entry_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env,
                bufsize=1
            )
            self._running = True

            self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self._stdout_thread.start()
            self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
            self._stderr_thread.start()

            print(f"[NodeBridge] 子进程已启动，PID: {self.process.pid}")
            return True
        except Exception as e:
            print(f"[NodeBridge] 启动子进程失败: {e}")
            return False

    def stop(self):
        self._running = False
        # 释放所有挂起的 call() 请求，防止线程永久阻塞
        with self._lock:
            for req_id, q in list(self._pending_requests.items()):
                q.put({"error": {"message": "NodeBridge 已停止"}})
            self._pending_requests.clear()
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            self.process = None
        print("[NodeBridge] 子进程已停止")

    def send_stdin(self, text: str):
        if not self.process or not self.process.stdin:
            return
        try:
            self.process.stdin.write(text + "\n")
            self.process.stdin.flush()
        except Exception as e:
            print(f"[NodeBridge] 发送 stdin 失败: {e}")

    def _read_stdout(self):
        while self._running and self.process and self.process.stdout:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                line = line.rstrip('\n')
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                    if "jsonrpc" in msg or "method" in msg or "id" in msg:
                        self._handle_message(msg)
                        continue
                except:
                    pass

                if self._stdout_callback:
                    self._stdout_callback(line)
                else:
                    print(f"[NodeBridge/stdout] {line}")

            except Exception as e:
                print(f"[NodeBridge] 读取 stdout 错误: {e}")

    def _read_stderr(self):
        while self._running and self.process and self.process.stderr:
            try:
                line = self.process.stderr.readline()
                if not line:
                    break
                line = line.rstrip('\n')
                if not line:
                    continue

                if self._stderr_callback:
                    self._stderr_callback(line)
                else:
                    print(f"[NodeBridge/stderr] {line}")
            except:
                pass

    def _handle_message(self, msg: Dict[str, Any]):
        if "id" in msg:
            req_id = msg["id"]
            with self._lock:
                if req_id in self._pending_requests:
                    self._pending_requests[req_id].put(msg)
            return

        method = msg.get("method")
        if not method:
            return

        handler = self._message_handlers.get(method)
        if handler:
            try:
                result = handler(msg.get("params", {}))
                if "id" in msg:
                    response = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
                    self._send_message(response)
            except Exception as e:
                if "id" in msg:
                    error_response = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32000, "message": str(e)}}
                    self._send_message(error_response)

    def _send_message(self, msg: Dict[str, Any]):
        if not self.process or not self.process.stdin:
            return
        try:
            line = json.dumps(msg, ensure_ascii=False)
            self.process.stdin.write(line + "\n")
            self.process.stdin.flush()
        except Exception as e:
            print(f"[NodeBridge] 发送消息失败: {e}")

    def call(self, method: str, params: Dict[str, Any] = None, timeout: float = 30.0) -> Any:
        if not self._running:
            raise RuntimeError("NodeBridge 未运行")

        with self._lock:
            self._request_counter += 1
            req_id = str(self._request_counter)
            q = queue.Queue()
            self._pending_requests[req_id] = q

        request = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
        self._send_message(request)

        try:
            response = q.get(timeout=timeout)
            if "error" in response:
                raise RuntimeError(response["error"].get("message", "RPC error"))
            return response.get("result")
        except queue.Empty:
            raise TimeoutError(f"RPC 调用超时: {method}")
        finally:
            with self._lock:
                del self._pending_requests[req_id]

    def notify(self, method: str, params: Dict[str, Any] = None):
        msg = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        self._send_message(msg)
