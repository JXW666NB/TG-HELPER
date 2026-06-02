"""
TG桌面机器人 - PC端通信客户端
通过WebSocket与ESP32S3机器人通信
支持UDP自动发现
"""
import websocket
import json
import threading
import time
import socket
from typing import Callable, Optional


class RobotDiscovery:
    """UDP自动发现机器人"""

    DISCOVERY_PORT = 8888
    BROADCAST_ADDR = "255.255.255.255"
    DISCOVERY_MSG = "DISCOVER_TG_ROBOT"

    def __init__(self):
        self.discovered_robots = []
        self._stop_event = threading.Event()
        self._thread = None
        self.on_discovered = None

    def start_discovery(self, timeout: int = 5):
        """
        开始发现机器人
        :param timeout: 发现超时时间（秒）
        :return: 发现的机器人列表
        """
        self.discovered_robots = []
        self._stop_event.clear()

        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)

        # 发送发现广播
        sock.sendto(
            self.DISCOVERY_MSG.encode('utf-8'),
            (self.BROADCAST_ADDR, self.DISCOVERY_PORT)
        )

        print(f"[Discovery] 发送发现广播到 {self.BROADCAST_ADDR}:{self.DISCOVERY_PORT}")

        # 等待响应
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                response = json.loads(data.decode('utf-8'))

                if response.get("type") == "robot_discovered":
                    robot_info = {
                        "name": response.get("name", "Unknown"),
                        "ip": response.get("ip", addr[0]),
                        "mac": response.get("mac", ""),
                        "version": response.get("version", ""),
                        "status": response.get("status", ""),
                        "port": 81  # WebSocket端口
                    }

                    # 去重
                    if not any(r["ip"] == robot_info["ip"] for r in self.discovered_robots):
                        self.discovered_robots.append(robot_info)
                        print(f"[Discovery] 发现机器人: {robot_info['name']} @ {robot_info['ip']}")

                        if self.on_discovered:
                            self.on_discovered(robot_info)

            except socket.timeout:
                break
            except Exception as e:
                print(f"[Discovery] 错误: {e}")

        sock.close()
        return self.discovered_robots


class TGRobotClient:
    """TG桌面机器人WebSocket客户端"""

    def __init__(self, robot_ip: str = "192.168.4.1", port: int = 81):
        self.robot_ip = robot_ip
        self.port = port
        self.ws_url = f"ws://{robot_ip}:{port}"
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.reconnect_interval = 3
        self.max_reconnect = 5
        self.reconnect_count = 0

        # 回调函数
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        self.on_audio_data: Optional[Callable] = None  # 音频数据回调
        self.on_status_update: Optional[Callable] = None
        self.on_wifi_scanned: Optional[Callable] = None  # WiFi扫描结果回调
        self.on_wifi_saved: Optional[Callable] = None  # WiFi配置保存回调
        self.on_voice_wake: Optional[Callable] = None  # 语音唤醒回调
        self.on_voice_data: Optional[Callable] = None   # 实时语音数据回调

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 语音唤醒缓冲区
        self._voice_wake_buffer = bytearray()
        self._voice_wake_samples = 0
        self._voice_wake_rate = 16000
        self._collecting_voice = False

    @staticmethod
    def discover_robots(timeout: int = 5) -> list:
        """静态方法：发现局域网内的机器人"""
        discovery = RobotDiscovery()
        return discovery.start_discovery(timeout)

    def connect(self, timeout: int = 8) -> bool:
        """连接到机器人，返回是否成功"""
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._stop_event.clear()
            self._thread.start()

            # 等待连接成功或超时
            waited = 0
            while not self.connected and waited < timeout:
                time.sleep(0.5)
                waited += 0.5

            if self.connected:
                print(f"[RobotClient] 连接成功: {self.ws_url}")
                return True
            else:
                print(f"[RobotClient] 连接超时 ({timeout}s)")
                self.disconnect()
                return False

        except Exception as e:
            print(f"[RobotClient] 连接失败: {e}")
            return False

    def _run(self):
        """WebSocket运行循环"""
        while not self._stop_event.is_set():
            try:
                # 添加心跳机制防止断连
                # ping_interval: 发送心跳间隔(秒)
                # ping_timeout: 心跳超时(秒)
                self.ws.run_forever(
                    ping_interval=10,
                    ping_timeout=30,
                    ping_payload="heartbeat"
                )
            except Exception as e:
                print(f"[RobotClient] WebSocket错误: {e}")

            if self._stop_event.is_set():
                break

            # 自动重连
            self.reconnect_count += 1
            if self.reconnect_count <= self.max_reconnect:
                print(f"[RobotClient] {self.reconnect_interval}秒后重连... ({self.reconnect_count}/{self.max_reconnect})")
                time.sleep(self.reconnect_interval)
            else:
                print("[RobotClient] 重连次数超限，停止重连")
                break

    def disconnect(self):
        """断开连接"""
        self._stop_event.set()
        self.connected = False
        if self.ws:
            self.ws.close()

    def _on_open(self, ws):
        """连接成功回调"""
        print("[RobotClient] 已连接到机器人")
        self.connected = True
        self.reconnect_count = 0
        if self.on_connected:
            self.on_connected()

    def _on_message(self, ws, message):
        """收到消息回调"""
        if isinstance(message, bytes):
            # 检查是否在收集语音唤醒数据
            if self._collecting_voice:
                self._voice_wake_buffer.extend(message)
                expected_bytes = self._voice_wake_samples * 2
                if len(self._voice_wake_buffer) >= expected_bytes - 100:
                    self._collecting_voice = False
                    pcm_data = bytes(self._voice_wake_buffer)
                    if self.on_voice_wake:
                        self.on_voice_wake(pcm_data, self._voice_wake_rate)
            elif self.on_audio_data:
                # 普通音频数据（TTS）
                self.on_audio_data(message)
            return

        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "connected":
                print(f"[RobotClient] 机器人就绪: {data.get('name', 'Unknown')}")

            elif msg_type == "status":
                if self.on_status_update:
                    self.on_status_update(data)

            elif msg_type == "servo_moved":
                print(f"[RobotClient] 舵机移动: {data.get('servo')} -> {data.get('angle')}°")

            elif msg_type == "self_test_complete":
                print("[RobotClient] 设备自检完成")

            elif msg_type == "wifi_saved":
                print(f"[RobotClient] WiFi配置: {data.get('message')}")
                if self.on_wifi_saved:
                    self.on_wifi_saved(data)

            elif msg_type == "wifi_scanned":
                networks = data.get("networks", [])
                print(f"[RobotClient] WiFi扫描: 发现 {len(networks)} 个网络")
                if self.on_wifi_scanned:
                    self.on_wifi_scanned(networks)

            elif msg_type == "recording_started":
                print("[RobotClient] 机器人开始录音")

            elif msg_type == "voice_wake":
                # 机器人检测到语音，开始接收唤醒音频
                self._voice_wake_samples = data.get("samples", 0)
                self._voice_wake_rate = data.get("rate", 16000)
                self._voice_wake_buffer = bytearray()
                self._collecting_voice = True
                print(f"[RobotClient] 收到唤醒音频 ({self._voice_wake_samples} 样本, {self._voice_wake_rate}Hz)")

            elif msg_type == "voice_data":
                if self.on_voice_data:
                    self.on_voice_data(data)

            elif msg_type == "speech_end":
                print("[RobotClient] 用户说话结束")

            # 通用消息回调
            if self.on_message:
                self.on_message(data)

        except json.JSONDecodeError:
            print(f"[RobotClient] 收到非JSON消息: {message}")
        except Exception as e:
            print(f"[RobotClient] 消息处理错误: {e}")

    def _on_error(self, ws, error):
        """错误回调"""
        print(f"[RobotClient] WebSocket错误: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭回调"""
        print("[RobotClient] 连接已关闭")
        self.connected = False
        if self.on_disconnected:
            self.on_disconnected()

    def send_command(self, command: dict) -> bool:
        """发送命令到机器人"""
        if not self.connected or not self.ws:
            print("[RobotClient] 未连接，无法发送命令")
            return False
        try:
            self.ws.send(json.dumps(command))
            return True
        except Exception as e:
            print(f"[RobotClient] 发送失败: {e}")
            return False

    def send_audio(self, audio_data: bytes) -> bool:
        """发送音频数据到机器人（播放）"""
        if not self.connected or not self.ws:
            print("[RobotClient] 未连接，无法发送音频")
            return False
        try:
            self.ws.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)
            return True
        except Exception as e:
            print(f"[RobotClient] 发送音频失败: {e}")
            return False

    def speak(self, text: str):
        """
        让机器人说话
        通过Edge TTS合成语音后发送PCM音频到机器人
        """
        try:
            from ai_hardware.edge_tts import EdgeTTS
            tts = EdgeTTS()
            pcm_data = tts.synthesize_to_pcm(text)
            return self.send_audio(pcm_data)
        except Exception as e:
            print(f"[RobotClient] TTS合成失败: {e}")
            return False

    # ========== 便捷命令方法 ==========

    def set_servo(self, servo_name: str, angle: int, speed: int = 10):
        """控制舵机"""
        return self.send_command({
            "type": "servo_control",
            "servo": servo_name,
            "angle": angle,
            "speed": speed
        })

    def set_expression(self, expression: str):
        """设置表情"""
        return self.send_command({
            "type": "set_expression",
            "expression": expression
        })

    def start_recording(self):
        """开始录音"""
        return self.send_command({"type": "start_recording"})

    def stop_recording(self):
        """停止录音"""
        return self.send_command({"type": "stop_recording"})

    def perform_action(self, action: str):
        """执行预设动作"""
        return self.send_command({
            "type": "perform_action",
            "action": action
        })

    def self_test(self):
        """设备自检"""
        return self.send_command({"type": "self_test"})

    def set_volume(self, volume: int):
        """设置音量"""
        return self.send_command({
            "type": "set_volume",
            "volume": volume
        })

    def get_status(self):
        """获取状态"""
        return self.send_command({"type": "get_status"})

    def set_wifi(self, ssid: str, password: str):
        """设置WiFi"""
        return self.send_command({
            "type": "set_wifi",
            "ssid": ssid,
            "password": password
        })

    def scan_wifi(self):
        """扫描WiFi网络"""
        return self.send_command({"type": "scan_wifi"})
