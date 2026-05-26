import os
import sys
import subprocess
import threading
import time
import socket
import json
import tempfile
import zipfile
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

import subprocess
import ctypes
# MQTT 客户端（用于内部订阅）
try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

class MosquittoManager:
    """管理 mosquitto MQTT broker 进程"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.process = None
        self.running = False
        self.mosquitto_dir = os.path.abspath("./mosquitto")
        self.config_file = os.path.join(self.mosquitto_dir, "mosquitto.conf")
        self.pid_file = os.path.join(self.mosquitto_dir, "mosquitto.pid")
        self.log_callback = None
        
        # 新增：后台安装控制
        self._installing = False
        self._install_thread = None
        self._pending_start_args = None  # 存储待启动的参数

    def set_log_callback(self, callback):
        self.log_callback = callback

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(msg)

    def _safe_log(self, msg):
        """线程安全地记录日志"""
        self._log(msg)

    def _safe_after(self, delay_ms, callback):
        """线程安全地延迟执行"""
        def wrapper():
            try:
                callback()
            except Exception as e:
                print(f"延迟执行出错: {e}")
        threading.Timer(delay_ms / 1000.0, wrapper).start()
        return True

    def ensure_installed(self):
        """
        检查并安装 mosquitto
        返回: True-已安装, False-安装失败, None-正在后台安装中
        """
        exe_path = os.path.join(self.mosquitto_dir, "mosquitto.exe")
        if os.path.exists(exe_path):
            return True
        local_installer = os.path.join(self.mosquitto_dir, "mosquitto-installer.exe")
        if os.path.exists(local_installer):
            self._log("发现本地安装包，直接安装...")
            return self._run_installer(local_installer)        
        # 防止重复点击
        if self._installing:
            self._safe_log("安装已在进行中，请稍候...")
            return None
        
        self._installing = True
        self._safe_log("准备下载 mosquitto...")
        
        # 在后台线程执行下载安装
        self._install_thread = threading.Thread(target=self._download_and_install, daemon=True)
        self._install_thread.start()
        return None

    def _download_and_install(self):
        """后台线程：下载并安装（不阻塞 GUI）"""
        urls = [
            "https://mosquitto.org/files/binary/win64/mosquitto-2.0.22-install-windows-x64.exe",
            "https://mosquitto.org/files/binary/win64/mosquitto-2.0.20-install-windows-x64.exe",
            "https://mosquitto.org/files/binary/win64/mosquitto-2.0.18a-install-windows-x64.exe",
            "https://github.com/eclipse-mosquitto/mosquitto/releases/download/v2.0.22/mosquitto-2.0.22-install-windows-x64.exe",
            "https://github.com/eclipse-mosquitto/mosquitto/releases/download/v2.0.20/mosquitto-2.0.20-install-windows-x64.exe",
        ]
        
        installer_path = os.path.join(self.mosquitto_dir, "mosquitto-installer.exe")
        os.makedirs(self.mosquitto_dir, exist_ok=True)
        
        download_success = False
        last_error = None
        
        for url in urls:
            try:
                self._safe_log(f"尝试下载: {url.split('/')[-1]}")
                try:
                    import requests
                    self._download_with_requests(url, installer_path)
                except ImportError:
                    self._download_with_urllib(url, installer_path)
                download_success = True
                break
            except Exception as e:
                last_error = e
                self._safe_log(f"该源失败: {str(e)[:50]}")
                continue
        
        if not download_success:
            self._safe_log(f"❌ 所有下载源都失败")
            self._installing = False
            self._safe_after(100, lambda: self._show_install_error(f"下载失败: {last_error}"))
            return
        
        # 已下载完毕，直接调用统一的安装方法
        self._safe_log("下载完成，正在安装...")
        if self._run_installer(installer_path):
            self._safe_log("✅ Mosquitto 安装完成！")
            self._installing = False
            if self._pending_start_args:
                self._safe_after(500, self._do_pending_start)
        else:
            self._safe_log("❌ 安装失败")
            self._installing = False
            self._safe_after(100, lambda: self._show_install_error("安装程序执行失败"))

    def _download_with_requests(self, url, save_path):
        """使用 requests 流式下载，带进度"""
        import requests
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            last_log_time = time.time()
            
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 每 2 秒更新一次进度，避免界面刷屏
                        current_time = time.time()
                        if current_time - last_log_time > 2.0:
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                mb = downloaded / 1024 / 1024
                                total_mb = total_size / 1024 / 1024
                                self._safe_log(f"下载中... {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)")
                            else:
                                self._safe_log(f"已下载 {downloaded/1024/1024:.1f} MB")
                            last_log_time = current_time

    def _download_with_urllib(self, url, save_path):
        """使用 urllib 下载（备用方案）"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            last_log_time = time.time()
            
            with open(save_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    current_time = time.time()
                    if current_time - last_log_time > 2.0:
                        self._safe_log(f"已下载 {downloaded/1024/1024:.1f} MB...")
                        last_log_time = current_time

    def _show_install_error(self, error_msg):
        """显示安装错误信息"""
        print(f"\n❌ 安装失败: {error_msg}")
        print(f"可能原因：")
        print(f"1. 网络连接超时（官网在国外，建议翻墙或等待）")
        print(f"2. 没有管理员权限（安装需要写入系统）")
        print(f"3. 安装路径包含空格")
        print(f"\n建议手动下载并安装到：{os.path.abspath(self.mosquitto_dir)}")
        print(f"下载地址：https://mosquitto.org/download/")
        try:
            answer = input("是否重试？(y/n): ").strip().lower()
            if answer in ('y', 'yes', '是'):
                self.ensure_installed()
        except:
            pass

    def start(self, port=1883, username="", password=""):
        """
        启动 mosquitto
        如果正在安装，会等待安装完成后自动启动
        """
        result = self.ensure_installed()
        
        if result is None:
            # 正在安装中，保存参数等待安装完成后自动启动
            self._pending_start_args = (port, username, password)
            self._safe_log("等待安装完成，将自动启动...")
            return False
        
        if result is False:
            return False
        
        # 已经安装，直接启动
        return self._do_start(port, username, password)

    def _do_pending_start(self):
        """安装完成后执行待启动的任务"""
        if self._pending_start_args:
            port, username, password = self._pending_start_args
            self._pending_start_args = None
            self._safe_log("安装完成，正在启动 MQTT 服务器...")
            self._do_start(port, username, password)

    def _do_start(self, port=1883, username="", password=""):
        """实际启动 mosquitto（必须在 ensure_installed 返回 True 后调用）"""
        if self.running:
            self.stop()
        
        # 生成配置文件
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(f"listener {port} 0.0.0.0\n")
                f.write("allow_anonymous true\n")
                if username and password:
                    # 简化：暂不支持密码认证，需要 mosquitto_passwd 工具
                    pass
                f.write("log_type all\n")
                f.write(f"pid_file {self.pid_file}\n")
        except Exception as e:
            self._log(f"写入配置文件失败: {e}")
            return False
        
        exe = os.path.join(self.mosquitto_dir, "mosquitto.exe")
        if not os.path.exists(exe):
            self._log(f"错误: 找不到 {exe}")
            return False
        
        try:
            # 使用绝对路径，不设置 cwd，避免工作目录错误
            self.process = subprocess.Popen(
                [exe, "-c", self.config_file, "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self.running = True
            
            # 启动日志读取线程
            def read_log():
                while self.running and self.process:
                    try:
                        line = self.process.stdout.readline()
                        if not line:
                            break
                        self._safe_log(f"[MQTT] {line.strip()}")
                    except Exception as e:
                        break
                if self.running:
                    self._safe_log("MQTT 进程意外退出")
                    self.running = False
            
            threading.Thread(target=read_log, daemon=True).start()
            self._log(f"✅ MQTT 服务器已启动，端口 {port}")
            return True
            
        except Exception as e:
            self._log(f"启动 MQTT 失败: {e}")
            return False

    def stop(self):
        """停止 mosquitto"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
        self.running = False
        self._log("MQTT 服务器已停止")
    def _run_installer(self, installer_path):
        """运行 mosquitto 安装程序并等待完成"""
        self._log("正在运行安装程序...")
        install_dir = os.path.abspath(self.mosquitto_dir).replace("/", "\\")
        cmd_params = "/S"
        if " " not in install_dir:
            cmd_params += f" /D={install_dir}"
        try:
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", installer_path, cmd_params, None, 1
            )
            if ret <= 32:
                self._log(f"安装启动失败，错误码: {ret}")
                return False
        except Exception as e:
            self._log(f"调用安装程序异常: {e}")
            return False

        # 等待 mosquitto.exe 出现，最多等 60 秒
        exe_path = os.path.join(self.mosquitto_dir, "mosquitto.exe")
        for i in range(60):
            time.sleep(1)
            if os.path.exists(exe_path):
                # 清理安装文件
                try:
                    os.remove(installer_path)
                except:
                    pass
                self._log("✅ Mosquitto 安装成功")
                return True
        self._log("⚠️ 安装可能失败，未找到 mosquitto.exe")
        return False
    
class TCPServerManager:
    """简单 TCP 服务器管理"""
    def __init__(self):
        self.server_socket = None
        self.running = False
        self.thread = None
        self.clients = []  # 存储 (conn, addr)
        self.log_callback = None
        self.port = 8888
        self.message_callback = None  # 收到消息时回调，用于记录

    def set_log_callback(self, callback):
        self.log_callback = callback

    def set_message_callback(self, callback):
        self.message_callback = callback

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def start(self, port=8888):
        if self.running:
            self.stop()
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)
            self.running = True
            self.thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.thread.start()
            self._log(f"TCP 服务器已启动，端口 {port}")
            return True
        except Exception as e:
            self._log(f"TCP 启动失败: {e}")
            return False

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                self.clients.append((conn, addr))
                self._log(f"TCP 客户端连接: {addr}")
                threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
            except:
                break

    def _handle_client(self, conn, addr):
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                msg = data.decode('utf-8')
                self._log(f"TCP 收到 {addr}: {msg}")
                if self.message_callback:
                    self.message_callback(addr, msg)
            except:
                break
        if (conn, addr) in self.clients:
            self.clients.remove((conn, addr))
        conn.close()
        self._log(f"TCP 客户端断开: {addr}")

    def send_to_client(self, addr, msg):
        for conn, client_addr in self.clients:
            if client_addr == addr:
                try:
                    conn.sendall(msg.encode('utf-8'))
                    self._log(f"TCP 发送到 {addr}: {msg}")
                    return True
                except:
                    pass
        return False

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for conn, _ in self.clients:
            try:
                conn.close()
            except:
                pass
        self.clients.clear()
        self._log("TCP 服务器已停止")

# 全局实例
mqtt_manager = MosquittoManager()
tcp_manager = TCPServerManager()
