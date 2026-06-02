"""
科大讯飞语音识别模块
使用讯飞WebAPI流式接口进行语音转文字
"""
import websocket
import hashlib
import base64
import hmac
import json
import time
import threading
import ssl
from urllib.parse import urlencode
from datetime import datetime, timezone
from typing import Callable, Optional, List


class XunfeiSTT:
    """科大讯飞语音听写（流式版）"""

    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"

        self.ws: Optional[websocket.WebSocketApp] = None
        self.is_recording = False
        self.audio_buffer: List[bytes] = []
        self.result_text = ""

        # 回调
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_partial: Optional[Callable[[str], None]] = None

        self._thread: Optional[threading.Thread] = None

    def _generate_auth_url(self) -> str:
        """生成带鉴权参数的WebSocket URL"""
        date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

        # 构建签名
        signature_origin = f"host: iat-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')

        # 构建authorization
        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

        # 构建URL
        params = {
            "authorization": authorization,
            "date": date,
            "host": "iat-api.xfyun.cn"
        }
        return f"{self.ws_url}?{urlencode(params)}"

    def start_recognition(self):
        """开始语音识别"""
        if self.is_recording:
            return

        self.is_recording = True
        self.audio_buffer = []
        self.result_text = ""

        auth_url = self._generate_auth_url()

        self.ws = websocket.WebSocketApp(
            auth_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self._thread = threading.Thread(target=self.ws.run_forever, kwargs={
            "sslopt": {"cert_reqs": ssl.CERT_NONE}
        }, daemon=True)
        self._thread.start()

    def stop_recognition(self):
        """停止语音识别"""
        self.is_recording = False
        if self.ws:
            # 发送结束帧
            end_frame = {
                "data": {
                    "status": 2,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": ""
                }
            }
            self.ws.send(json.dumps(end_frame))
            time.sleep(0.5)
            self.ws.close()

    def feed_audio(self, audio_data: bytes):
        """喂入音频数据"""
        if not self.is_recording or not self.ws:
            return

        # 音频数据base64编码
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        frame = {
            "data": {
                "status": 1,  # 中间帧
                "format": "audio/L16;rate=16000",
                "encoding": "raw",
                "audio": audio_base64
            }
        }
        self.ws.send(json.dumps(frame))

    def _on_open(self, ws):
        """连接成功"""
        # 发送首帧
        first_frame = {
            "common": {"app_id": self.app_id},
            "business": {
                "language": "zh_cn",
                "domain": "iat",
                "accent": "mandarin",
                "dwa": "wpgs",  # 开启动态修正
                "ptt": 1        # 添加标点
            },
            "data": {
                "status": 0,  # 首帧
                "format": "audio/L16;rate=16000",
                "encoding": "raw",
                "audio": ""
            }
        }
        ws.send(json.dumps(first_frame))

    def _on_message(self, ws, message):
        """收到消息"""
        try:
            result = json.loads(message)
            code = result.get("code", -1)

            if code != 0:
                error_msg = result.get("message", "未知错误")
                if self.on_error:
                    self.on_error(f"讯飞错误 [{code}]: {error_msg}")
                return

            # 解析识别结果
            if "data" in result and "result" in result["data"]:
                data = result["data"]
                result_data = data["result"]
                ws_list = result_data.get("ws", [])

                text = ""
                for ws_item in ws_list:
                    cw_list = ws_item.get("cw", [])
                    for cw in cw_list:
                        text += cw.get("w", "")

                # 检查是否是动态修正
                pgs = result_data.get("pgs", "")
                if pgs == "rpl":
                    # 替换模式，替换之前的部分结果
                    rg = result_data.get("rg", [])
                    self.result_text = text
                else:
                    # 追加模式
                    self.result_text += text

                # 回调
                if self.on_partial:
                    self.on_partial(self.result_text)

                # 检查是否结束
                if data.get("status") == 2:
                    if self.on_result:
                        self.on_result(self.result_text)
                    self.is_recording = False

        except Exception as e:
            if self.on_error:
                self.on_error(f"解析错误: {str(e)}")

    def _on_error(self, ws, error):
        """错误回调"""
        if self.on_error:
            self.on_error(f"WebSocket错误: {str(error)}")

    def _on_close(self, ws, close_status_code, close_msg):
        """关闭回调"""
        self.is_recording = False


class XunfeiSTTSimple:
    """简化的讯飞语音识别 - 一次性识别"""

    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.stt = XunfeiSTT(app_id, api_key, api_secret)
        self._result = ""
        self._done = threading.Event()

    def recognize(self, audio_data: bytes, timeout: int = 10) -> str:
        """
        识别音频数据
        :param audio_data: PCM音频数据 (16kHz, 16bit, 单声道)
        :param timeout: 超时时间（秒）
        :return: 识别结果文本
        """
        self._result = ""
        self._done.clear()

        def on_result(text):
            self._result = text
            self._done.set()

        self.stt.on_result = on_result
        self.stt.start_recognition()

        # 等待连接建立
        time.sleep(0.5)

        # 发送音频数据（分块发送，每块1280字节）
        chunk_size = 1280
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            self.stt.feed_audio(chunk)
            time.sleep(0.04)  # 40ms间隔

        # 停止录音
        self.stt.stop_recognition()

        # 等待结果
        self._done.wait(timeout=timeout)
        return self._result
