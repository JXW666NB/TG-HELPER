"""
AI硬件管理器
统一管理TG桌面机器人、TG智能眼镜等AI硬件设备
"""
import threading
import time
from typing import Optional, Callable
from .robot_client import TGRobotClient
from .smart_glasses import TGSmartGlasses


class AIHardwareManager:
    """AI硬件设备管理器"""

    def __init__(self):
        # TG桌面机器人
        self.robot_client: Optional[TGRobotClient] = None
        self.is_robot_connected = False
        self.robot_ip = "192.168.4.1"
        self.robot_port = 81

        # TG智能眼镜
        self.glasses_client: Optional[TGSmartGlasses] = None
        self.is_glasses_connected = False

        # 语音相关配置（简化配置，使用Edge TTS无需API Key）
        self.stt_app_id = ""      # 科大讯飞 AppID
        self.stt_api_key = ""     # 科大讯飞 API Key
        self.stt_api_secret = ""  # 科大讯飞 API Secret
        self.robot_volume = 80

        # 回调
        self.on_robot_connected: Optional[Callable] = None
        self.on_robot_disconnected: Optional[Callable] = None
        self.on_glasses_connected: Optional[Callable] = None
        self.on_glasses_disconnected: Optional[Callable] = None
        self.on_voice_input: Optional[Callable] = None  # 语音输入回调(text)
        self.on_status_change: Optional[Callable] = None

        # 语音唤醒
        self.wake_word = "TGAI"
        self.is_listening = False
        self._listen_thread: Optional[threading.Thread] = None

    # ========== TG桌面机器人 ==========

    def connect_robot(self, ip: str = None, port: int = 81) -> bool:
        """连接TG桌面机器人"""
        if ip:
            self.robot_ip = ip
        if port:
            self.robot_port = port

        self.robot_client = TGRobotClient(self.robot_ip, self.robot_port)

        # 设置回调
        self.robot_client.on_connected = self._on_robot_connected
        self.robot_client.on_disconnected = self._on_robot_disconnected
        self.robot_client.on_status_update = self._on_status_update

        return self.robot_client.connect()

    def disconnect_robot(self):
        """断开机器人连接"""
        if self.robot_client:
            self.robot_client.disconnect()
            self.robot_client = None
        self.is_robot_connected = False

    def _on_robot_connected(self):
        """机器人连接成功"""
        self.is_robot_connected = True
        print("[HardwareManager] 机器人已连接")
        if self.on_robot_connected:
            self.on_robot_connected()
        if self.on_status_change:
            self.on_status_change("robot_connected")

    def _on_robot_disconnected(self):
        """机器人断开连接"""
        self.is_robot_connected = False
        print("[HardwareManager] 机器人已断开")
        if self.on_robot_disconnected:
            self.on_robot_disconnected()
        if self.on_status_change:
            self.on_status_change("robot_disconnected")

    def _on_status_update(self, status: dict):
        """状态更新"""
        print(f"[HardwareManager] 状态更新: {status}")

    def send_text_to_robot(self, text: str):
        """发送文本让机器人播报（通过Edge TTS生成音频后发送）"""
        if self.robot_client and self.is_robot_connected:
            self.robot_client.speak(text)

    def control_servo(self, servo_name: str, angle: int, speed: int = 10):
        """控制舵机"""
        if self.robot_client and self.is_robot_connected:
            self.robot_client.set_servo(servo_name, angle, speed)

    def set_robot_expression(self, expression: str):
        """设置机器人表情"""
        if self.robot_client and self.is_robot_connected:
            self.robot_client.set_expression(expression)

    def perform_action(self, action: str):
        """执行预设动作"""
        if self.robot_client and self.is_robot_connected:
            self.robot_client.perform_action(action)

    def self_test(self):
        """设备自检"""
        if self.robot_client and self.is_robot_connected:
            self.robot_client.self_test()

    def set_volume(self, volume: int):
        """设置音量"""
        self.robot_volume = volume
        if self.robot_client and self.is_robot_connected:
            self.robot_client.set_volume(volume)

    def get_robot_status(self):
        """获取机器人状态"""
        if self.robot_client and self.is_robot_connected:
            self.robot_client.get_status()

    def set_robot_wifi(self, ssid: str, password: str):
        """设置机器人WiFi"""
        if self.robot_client and self.is_robot_connected:
            self.robot_client.set_wifi(ssid, password)

    def scan_robot_wifi(self):
        """扫描机器人周围的WiFi，返回扫描结果"""
        if self.robot_client and self.is_robot_connected:
            return self.robot_client.scan_wifi()
        return None

    # ========== TG智能眼镜 ==========

    def connect_glasses(self, ip: str = None) -> bool:
        """连接TG智能眼镜"""
        self.glasses_client = TGSmartGlasses()

        # 设置回调
        self.glasses_client.on_connected = self._on_glasses_connected
        self.glasses_client.on_disconnected = self._on_glasses_disconnected

        result = self.glasses_client.connect(ip)
        if result:
            self.is_glasses_connected = True
        return result

    def disconnect_glasses(self):
        """断开智能眼镜连接"""
        if self.glasses_client:
            self.glasses_client.disconnect()
            self.glasses_client = None
        self.is_glasses_connected = False

    def _on_glasses_connected(self):
        """智能眼镜连接成功"""
        self.is_glasses_connected = True
        print("[HardwareManager] 智能眼镜已连接")
        if self.on_glasses_connected:
            self.on_glasses_connected()
        if self.on_status_change:
            self.on_status_change("glasses_connected")

    def _on_glasses_disconnected(self):
        """智能眼镜断开连接"""
        self.is_glasses_connected = False
        print("[HardwareManager] 智能眼镜已断开")
        if self.on_glasses_disconnected:
            self.on_glasses_disconnected()
        if self.on_status_change:
            self.on_status_change("glasses_disconnected")

    def send_to_glasses(self, text: str):
        """发送文本到智能眼镜显示"""
        if self.glasses_client and self.is_glasses_connected:
            self.glasses_client.send_text(text)

    def send_notification_to_glasses(self, title: str, message: str):
        """发送通知到智能眼镜"""
        if self.glasses_client and self.is_glasses_connected:
            self.glasses_client.send_notification(title, message)

    def get_glasses_status(self) -> dict:
        """获取智能眼镜状态"""
        if self.glasses_client:
            return self.glasses_client.get_status()
        return {"connected": False}

    # ========== 通用功能 ==========

    def send_to_ai(self, text: str):
        """将语音识别的文本发送给TGAI处理"""
        if self.on_voice_input:
            self.on_voice_input(text)

    def is_robot_connected(self) -> bool:
        """检查机器人是否已连接"""
        return self.is_robot_connected and self.robot_client is not None

    def is_glasses_connected(self) -> bool:
        """检查智能眼镜是否已连接"""
        return self.is_glasses_connected and self.glasses_client is not None

    def get_connected_devices(self) -> dict:
        """获取所有已连接设备"""
        return {
            "robot": self.is_robot_connected and self.robot_client is not None,
            "glasses": self.is_glasses_connected and self.glasses_client is not None,
        }

    def disconnect_all(self):
        """断开所有设备"""
        self.disconnect_robot()
        self.disconnect_glasses()


# 全局单例
_hardware_manager: Optional[AIHardwareManager] = None


def get_hardware_manager() -> AIHardwareManager:
    """获取硬件管理器单例"""
    global _hardware_manager
    if _hardware_manager is None:
        _hardware_manager = AIHardwareManager()
    return _hardware_manager
