"""
Edge TTS 模块
使用微软Edge浏览器的在线TTS服务，无需API Key
"""
import asyncio
import edge_tts
import tempfile
import os
from typing import Optional, Callable


class EdgeTTS:
    """Edge TTS 语音合成"""

    # 中文语音列表
    VOICES = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 晓晓 - 女声
        "xiaoyi": "zh-CN-XiaoyiNeural",          # 晓伊 - 女声
        "yunjian": "zh-CN-YunjianNeural",        # 云健 - 男声
        "yunxi": "zh-CN-YunxiNeural",            # 云希 - 男声
        "xiaochen": "zh-CN-XiaochenNeural",      # 晓晨 - 女声
        "xiaohan": "zh-CN-XiaohanNeural",        # 晓涵 - 女声
    }

    def __init__(self, voice: str = "xiaoxiao", rate: str = "+0%", volume: str = "+0%"):
        self.voice = self.VOICES.get(voice, self.VOICES["xiaoxiao"])
        self.rate = rate
        self.volume = volume
        self._temp_dir = tempfile.gettempdir()

    async def synthesize_async(self, text: str, output_path: Optional[str] = None) -> str:
        """
        异步合成语音
        :param text: 要合成的文本
        :param output_path: 输出文件路径，None则使用临时文件
        :return: 音频文件路径
        """
        if output_path is None:
            output_path = os.path.join(self._temp_dir, f"edge_tts_{hash(text)}.mp3")

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume
        )
        await communicate.save(output_path)
        return output_path

    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """同步合成语音（阻塞调用）"""
        return asyncio.run(self.synthesize_async(text, output_path))

    def synthesize_to_pcm(self, text: str) -> bytes:
        """
        合成语音并返回PCM数据（用于直接播放）
        :return: PCM音频数据
        """
        import subprocess

        mp3_path = self.synthesize(text)

        # 使用ffmpeg转换为PCM 16kHz 16bit 单声道
        pcm_path = mp3_path.replace(".mp3", ".pcm")

        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_path,
            "-ar", "16000", "-ac", "1", "-f", "s16le",
            pcm_path
        ], capture_output=True)

        with open(pcm_path, "rb") as f:
            pcm_data = f.read()

        # 清理临时文件
        try:
            os.remove(mp3_path)
            os.remove(pcm_path)
        except:
            pass

        return pcm_data

    def set_voice(self, voice_name: str):
        """设置语音"""
        self.voice = self.VOICES.get(voice_name, self.VOICES["xiaoxiao"])

    def list_voices(self) -> dict:
        """返回可用语音列表"""
        return self.VOICES.copy()


# 便捷函数
def speak(text: str, voice: str = "xiaoxiao") -> str:
    """快速合成语音"""
    tts = EdgeTTS(voice=voice)
    return tts.synthesize(text)
