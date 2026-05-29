# -*- coding: utf-8 -*-
"""
AI 视频生成模块 V4 - Hyperframes 对标版
架构：主Agent给prompt → 子Agent设计HTML+CSS(@keyframes动画) → Playwright逐帧捕获 → MoviePy合成视频
核心技术：Web Animations API (document.getAnimations()) 逐帧seek CSS动画，实现与GSAP等效的动画能力
"""
import os
import sys
import time
import json
import base64
import shutil
import re
import asyncio
import requests
import tempfile
import concurrent.futures
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from config import config

MOVIEPY_AVAILABLE = False
ImageSequenceClip = None
try:
    from moviepy import (
        ImageClip, AudioFileClip, CompositeAudioClip, VideoFileClip,
        concatenate_videoclips, ColorClip, concatenate_audioclips
    )
    try:
        from moviepy import ImageSequenceClip
    except ImportError:
        pass
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import (
            ImageClip, AudioFileClip, CompositeAudioClip, VideoFileClip,
            concatenate_videoclips, ColorClip, concatenate_audioclips
        )
        try:
            from moviepy.editor import ImageSequenceClip
        except ImportError:
            pass
        MOVIEPY_AVAILABLE = True
    except ImportError:
        pass

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


# ==================== 子Agent 系统提示词 ====================

VIDEO_DESIGNER_SYSTEM_PROMPT = """你是一个世界级的视频动效设计师和HTML/CSS动画专家。根据用户提示设计带有精美CSS动画的视频。

## 输出格式
只输出一个JSON对象，不要有任何其他文字：

{
    "scenes": [
        {
            "html": "HTML代码（必须使用单引号）",
            "duration": 5,
            "narration": "该场景对应的旁白文本"
        }
    ],
    "resolution": {"width": 1920, "height": 1080},
    "music_style": "大气/轻松/科技/温暖"
}

## 致命规则
1. **HTML标签属性必须用单引号**：JSON用双引号，HTML标签的属性值用单引号
   正确: <div class='title' style='color:red;'>
   错误: <div class="title" style="color:red;">
   ⚠️ **注意**：CSS代码里的值（如animation、@keyframes）**不需要引号**！
2. **HTML控制在2500字符内**：包含CSS动画代码和装饰元素

## CSS 动画规范（核心！动画被逐帧渲染成视频，你可以尽情发挥创意！）

**核心原则：入场要快（0.5-1.2s），持续要活（infinite微妙循环），大胆组合多种动画！**

1. **动画声明格式**（必须包含 **paused** 和 **both**）:
   ```css
   .title { animation: bounceIn 0.8s cubic-bezier(0.34,1.56,0.64,1) both paused; }
   .glow { animation: gentlePulse 3s ease-in-out infinite both paused; }
   ```

2. **两层动画体系（每个场景都要有！）**:
   **A. 入场动画**（每个文字元素1个，0.5-1.2s，快而有力，可以用cubic-bezier弹性缓动）
   **B. 持续微动**（至少1个装饰/背景元素，2-5s loop infinite，画面全程不死板）

3. **动画类型库（任选组合，鼓励混搭）**:

   🎯 **入场冲击类**（0.5-1.2s，弹性缓动）:
   
   | 动画名 | 效果 | @keyframes关键帧 |
   |--------|------|-----------------|
   | **bounceIn** | 弹性放大 | `0%{scale(0.3) opacity:0} 50%{scale(1.1) opacity:1} 70%{scale(0.95)} 100%{scale(1)}` |
   | **slideUp** | 下方飘入 | `from{opacity:0;translateY(60px)} to{opacity:1;translateY(0)}` |
   | **slideDown** | 上方坠入 | `from{opacity:0;translateY(-60px)} to{opacity:1;translateY(0)}` |
   | **slideInLeft** | 左侧飞入 | `from{opacity:0;translateX(-80px)} to{opacity:1;translateX(0)}` |
   | **slideInRight** | 右侧飞入 | `from{opacity:0;translateX(80px)} to{opacity:1;translateX(0)}` |
   | **zoomOut** | 从大到小 | `from{opacity:0;scale(1.5)} to{opacity:1;scale(1)}` |
   | **flipIn** | 3D翻转进入 | `from{opacity:0;rotateY(90deg); perspective(800px)} to{opacity:1;rotateY(0)}` |
   | **rotateIn** | 旋转淡入 | `from{opacity:0;rotate(-15deg);scale(0.6)} to{opacity:1;rotate(0);scale(1)}` |

   🌊 **持续动感类**（infinite，2-5s循环）:
   
   | 动画名 | 效果 | @keyframes关键帧 |
   |--------|------|-----------------|
   | **gentlePulse** | 柔和呼吸 | `0%,100%{opacity:1} 50%{opacity:0.5}` |
   | **floatUpDown** | 上下浮动 | `0%,100%{translateY(0)} 50%{translateY(-15px)}` |
   | **floatLeftRight** | 左右摇摆 | `0%,100%{translateX(0)} 50%{translateX(15px)}` |
   | **rotateSlow** | 缓慢旋转 | `from{rotate(0deg)} to{rotate(360deg)}` |
   | **scaleBreath** | 缩放呼吸 | `0%,100%{scale(1)} 50%{scale(1.05)}` |
   | **shimmer** | 光泽扫过 | `0%{translateX(-100%)} 100%{translateX(200%)}` |
   | **waveHue** | 色相波动（装饰） | `0%{filter:hue-rotate(0deg)} 100%{filter:hue-rotate(30deg)}` |

   ✨ **特殊效果类**（可组合使用）:
   
   | 动画名 | 效果 | @keyframes关键帧 |
   |--------|------|-----------------|
   | **revealWidth** | 横线展开 | `from{width:0;opacity:0} to{width:200px;opacity:1}` |
   | **revealHeight** | 竖线展开 | `from{height:0;opacity:0} to{height:200px;opacity:1}` |
   | **borderGlow** | 边框发光扫描 | `0%,100%{border-color:rgba(255,255,255,0.1)} 50%{border-color:rgba(100,150,255,0.6)}` |
   | **textGlow** | 文字发光脉冲 | `0%,80%,100%{text-shadow:0 0 10px currentColor} 40%{text-shadow:0 0 40px currentColor,0 0 80px currentColor}` |
   | **typewriter** | 打字机光标 | `0%,100%{border-color:transparent} 50%{border-color:currentColor}` （配合overflow:hidden）|

4. **缓动曲线库**:
   - `ease-out` — 通用减速（默认推荐）
   - `cubic-bezier(0.34,1.56,0.64,1)` — 弹性弹跳（bounceIn专用）
   - `cubic-bezier(0.22,0.61,0.36,1)` — 流畅慢入快出
   - `cubic-bezier(0.68,-0.55,0.27,1.55)` — 强烈弹性回弹
   - `ease-in-out` — 对称缓动（循环动画用）

5. **Stagger编排（密集有力）**:
   - 3个元素: delay=0s, 0.12s, 0.24s
   - 5个元素: delay=0s, 0.1s, 0.2s, 0.3s, 0.4s

6. **创意自由**:
   - ✅ 大胆混搭不同类型（标题bounceIn + 副标题slideInLeft + 装饰rotateSlow）
   - ✅ 组合多种持续微动（floatUpDown大圆 + gentlePulse光晕 + rotateSlow小圆）
   - ✅ 用伪元素::before/::after创建额外动画层
   - ✅ 在keyframes中组合多种属性（opacity+translate+scale同帧变化）
   - ✅ 同一个元素可以用`,`分隔绑定多个动画 `.box{animation:slideUp 0.8s both paused, floatUpDown 3s 1s infinite both paused;}`
   - ⚠️ 只需确保使用了**paused**和**both**，动画类型尽情发挥！

## HTML 视觉设计（要炫！要科技感！）
1. **画面尺寸**: 1920x1080，`body{margin:0;overflow:hidden}`
2. **字体**: 'Microsoft YaHei', sans-serif
3. **背景（必须有层次）**:
   - 深色科技风背景: `linear-gradient(135deg, #0a0a1a 0%, #1a1040 40%, #0d1b3e 100%)`
   - 或暗紫渐变: `linear-gradient(160deg, #0f0c29, #302b63, #24243e)`
   - 叠加径向光晕: 用伪元素+radial-gradient模拟点光源
4. **装饰元素（必须有！增加视觉丰富度）**:
   - 背景圆圈: 半透明大圆 `border:1px solid rgba(255,255,255,0.1); border-radius:50%` + floatUpDown动画
   - 装饰线条: 细横线 `height:1px; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent)` + revealWidth动画
   - 光晕: 用box-shadow+blur制造发光效果
   - 毛玻璃卡片: `background:rgba(255,255,255,0.05); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.1)`
5. **文字效果**:
   - 标题发光: `text-shadow: 0 0 40px rgba(100,120,255,0.6), 0 0 80px rgba(80,100,255,0.3)`
   - 渐变色文字: `background:linear-gradient(90deg,#7b61ff,#42e8ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent`
   - 大标题 80-120px, 副标题 40-56px, 正文 26-34px
6. **配色**: 根据主题自由选择配色，适配不同风格（科技/温暖/商务/自然）
7. **图片**: 用户图片用 <img src='[IMG:name]'>；如需AI生成新图片用 <img src='[GEN_IMG:描述]'>（程序会自动替换为图片数据）
8. **禁止**: 外部资源、滚动条、纯白色文字（无质感）

## 场景设计原则
- 场景1（3-4秒）: 爆发式开场！Logo/title bounceIn 弹入+背景光晕pulse
- 中间场景（4-6秒）: 信息展开，文字slideUp依次入场，装饰元素float+rotate
- 结尾场景（3-4秒）: 升华收尾，所有元素聚合+最后pulse一次

## narration 旁白
- 每个场景的 narration 是TTS配音的文本
- 旁白文本根据场景内容写，语速约每秒3-4个汉字

## 带动画的炫酷示例（5s场景）
{
    "html": "<!DOCTYPE html><html><head><style>body{margin:0;overflow:hidden;width:1920px;height:1080px;background:linear-gradient(135deg,#0a0a1a,#1a1040,#0d1b3e);display:flex;align-items:center;justify-content:center;flex-direction:column;font-family:'Microsoft YaHei',sans-serif;position:relative;}body::before{content:'';position:absolute;top:-200px;right:-200px;width:600px;height:600px;background:radial-gradient(circle,rgba(100,120,255,0.15),transparent 70%);border-radius:50%;animation:gentlePulse 4s ease-in-out infinite both paused;}.decor{position:absolute;border:1.5px solid rgba(255,255,255,0.08);border-radius:50%;animation:floatUpDown 5s ease-in-out infinite both paused;}.line{width:0;height:2px;background:linear-gradient(90deg,transparent,rgba(100,150,255,0.5),transparent);animation:revealWidth 0.9s 0.5s cubic-bezier(0.22,0.61,0.36,1) both paused;}@keyframes bounceIn{0%{opacity:0;transform:scale(0.3)}50%{opacity:1;transform:scale(1.08)}70%{transform:scale(0.95)}100%{opacity:1;transform:scale(1)}}@keyframes slideUp{from{opacity:0;transform:translateY(60px)}to{opacity:1;transform:translateY(0)}}@keyframes gentlePulse{0%,100%{opacity:1}50%{opacity:0.55}}@keyframes floatUpDown{0%,100%{transform:translateY(0)}50%{transform:translateY(-18px)}}@keyframes revealWidth{to{width:280px}}h1{font-size:100px;background:linear-gradient(90deg,#7b61ff,#42e8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:none;margin:0;animation:bounceIn 0.8s cubic-bezier(0.34,1.56,0.64,1) both paused;}p{font-size:34px;color:#a0b0ff;margin-top:25px;animation:slideUp 0.7s 0.15s cubic-bezier(0.22,0.61,0.36,1) both paused;}</style></head><body><h1>TG HELPER</h1><div class='line'></div><p>你的智能AI伙伴</p><div class='decor' style='width:400px;height:400px;top:-100px;left:-100px;animation-delay:0s;'></div><div class='decor' style='width:250px;height:250px;bottom:-80px;right:-60px;animation-delay:1.5s;'></div></body></html>",
    "duration": 5,
    "narration": "TG HELPER，你的智能AI伙伴，开启无限可能"
}"""


# ==================== MoviePy v1/v2 兼容工具 ====================

def _subclip(clip, start, end):
    """兼容 MoviePy v1 (subclip) 和 v2 (subclipped)"""
    if hasattr(clip, 'subclipped'):
        return clip.subclipped(start, end)
    return clip.subclip(start, end)


# ==================== TTS 配置 ====================
TTS_PROVIDER_CONFIGS = {
    "openai": {
        "name": "OpenAI TTS", "base_url": "https://api.openai.com/v1",
        "endpoint": "/audio/speech", "default_model": "tts-1",
        "default_voice": "alloy", "auth_header": "Authorization",
        "auth_prefix": "Bearer ", "format": "openai_tts",
    },
    "volcengine": {
        "name": "字节跳动豆包 TTS", "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "endpoint": "/audio/speech", "default_model": "doubao-tts",
        "default_voice": "zh_female_qingxin", "auth_header": "Authorization",
        "auth_prefix": "Bearer ", "format": "openai_tts",
    },
    "minimax": {
        "name": "MiniMax TTS", "base_url": "https://api.minimaxi.com/v1",
        "endpoint": "/text_to_speech", "default_model": "speech-01",
        "default_voice": "male-qn-qingse", "auth_header": "Authorization",
        "auth_prefix": "Bearer ", "format": "minimax_tts",
    },
    "edge_tts": {
        "name": "Edge TTS (免费)", "base_url": "", "endpoint": "",
        "default_model": "edge", "default_voice": "zh-CN-XiaoxiaoNeural",
        "auth_header": "", "auth_prefix": "", "format": "edge_tts",
    },
    "custom": {
        "name": "自定义 TTS 端点", "base_url": "", "endpoint": "/audio/speech",
        "default_model": "", "default_voice": "", "auth_header": "Authorization",
        "auth_prefix": "Bearer ", "format": "openai_tts",
    },
}


def _get_tts_config():
    provider = getattr(config, 'video_tts_provider', 'edge_tts')
    return provider, TTS_PROVIDER_CONFIGS.get(provider, TTS_PROVIDER_CONFIGS["edge_tts"])


def _generate_tts(text: str, output_path: str, voice: str = None, speed: float = 1.0) -> str:
    provider_key, cfg = _get_tts_config()
    api_key = getattr(config, 'video_tts_api_key', '') or config.ai_api_key
    base_url = getattr(config, 'video_tts_base_url', '') or cfg["base_url"]
    model = getattr(config, 'video_tts_model', '') or cfg["default_model"]
    voice = voice or getattr(config, 'video_tts_voice', '') or cfg["default_voice"] or cfg["default_voice"]

    fmt = cfg["format"]
    print(f"[VideoGen] TTS请求: provider={provider_key}, voice={voice}, text_len={len(text)}, speed={speed}")

    try:
        if fmt == "edge_tts":
            result = _tts_edge(text, output_path, voice, speed)
            if not result.startswith("ERROR"):
                print(f"[VideoGen] Edge TTS成功: {output_path}")
            return result
        if not api_key:
            return f"ERROR: 未配置 TTS API Key。"
        if not base_url:
            return f"ERROR: 未配置 TTS Base URL。"

        if fmt == "openai_tts":
            url = base_url.rstrip("/") + cfg["endpoint"]
            headers = {cfg["auth_header"]: f"{cfg['auth_prefix']}{api_key}", "Content-Type": "application/json"}
            payload = {"model": model, "input": text, "voice": voice, "speed": speed, "response_format": "mp3"}
            print(f"[VideoGen] TTS API请求: {url}, model={model}")
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                print(f"[VideoGen] TTS API失败: {resp.status_code}, {resp.text[:200]}")
                return f"ERROR: TTS API ({resp.status_code}): {resp.text[:200]}"
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(f"[VideoGen] TTS API成功: {output_path} ({os.path.getsize(output_path)} bytes)")
            return output_path

        elif fmt == "minimax_tts":
            url = base_url.rstrip("/") + cfg["endpoint"]
            headers = {cfg["auth_header"]: f"{cfg['auth_prefix']}{api_key}", "Content-Type": "application/json"}
            payload = {"model": model, "text": text, "voice_setting": {"voice_id": voice, "speed": speed},
                       "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"}}
            print(f"[VideoGen] MiniMax TTS请求: {url}")
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                print(f"[VideoGen] MiniMax TTS失败: {resp.status_code}, {resp.text[:200]}")
                return f"ERROR: MiniMax TTS ({resp.status_code}): {resp.text[:200]}"
            data = resp.json()
            audio_hex = data.get("data", {}).get("audio")
            if not audio_hex:
                return "ERROR: MiniMax TTS 返回空数据。"
            with open(output_path, "wb") as f:
                f.write(bytes.fromhex(audio_hex))
            print(f"[VideoGen] MiniMax TTS成功: {output_path}")
            return output_path

        return f"ERROR: 未知 TTS 格式: {fmt}"
    except Exception as e:
        print(f"[VideoGen] TTS异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return f"ERROR: TTS 失败: {str(e)}"


def _tts_edge(text: str, output_path: str, voice: str, speed: float = 1.0) -> str:
    try:
        import edge_tts, asyncio
        print(f"[VideoGen] Edge TTS: voice={voice}, speed={speed}")
        async def _run():
            communicate = edge_tts.Communicate(text, voice, rate=f"{int((speed-1)*100):+d}%")
            await communicate.save(output_path)
        asyncio.run(_run())
        print(f"[VideoGen] Edge TTS完成: {output_path}")
        return output_path
    except ImportError:
        return "ERROR: 未安装 edge-tts。运行: pip install edge-tts"
    except Exception as e:
        print(f"[VideoGen] Edge TTS异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return f"ERROR: Edge TTS 失败: {str(e)}"


# ==================== Playwright CSS动画逐帧渲染引擎 ====================

def _is_inside_asyncio_loop() -> bool:
    """检测当前是否在 asyncio 事件循环中运行"""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def _run_playwright_safe(func, *args, **kwargs):
    """
    安全运行 Playwright 同步代码：如果检测到 asyncio 事件循环，
    则在独立线程中执行以避免 "Sync API inside the asyncio loop" 错误。
    """
    if _is_inside_asyncio_loop():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            return future.result()
    return func(*args, **kwargs)


FRAME_CAPTURE_JS = """
(function() {
    var initDone = false;
    var initStart = Date.now();

    function initAnimControl() {
        if (initDone) return;

        // 步骤1: 找到所有有CSS动画的元素，将animation-play-state从paused改为running
        // 这样浏览器会把它们注册进document.getAnimations()
        var animatedElements = [];
        var all = document.getElementsByTagName('*');
        for (var i = 0; i < all.length; i++) {
            var el = all[i];
            var comp = getComputedStyle(el);
            if (comp.animationName && comp.animationName !== 'none') {
                // 关键：inline style设为running（覆盖CSS的paused），保留原始delay
                 el.style.animationPlayState = 'running';
                 animatedElements.push(el);
            }
        }

        // 步骤2: 等待浏览器注册动画到WAAPI
        document.body.offsetHeight; // 强制reflow

        function waitForAnimations() {
            var anims = document.getAnimations();
            if (anims.length > 0 || Date.now() - initStart > 3000) {
                // 步骤3: 用WAAPI暂停所有动画，设currentTime=0
                // WAAPI的pause()独立于CSS animation-play-state，之后currentTime可自由控制
                for (var a = 0; a < anims.length; a++) {
                    try {
                        anims[a].pause();
                        anims[a].currentTime = 0;
                    } catch(e) {}
                }

                // 检测带animation元素但无WAAPI注册的fallback
                if (anims.length === 0 && animatedElements.length > 0) {
                    window.__animCount = animatedElements.length;
                } else {
                    window.__animCount = anims.length;
                }
                window.__animReady = true;
                initDone = true;
                return;
            }
            requestAnimationFrame(waitForAnimations);
        }
        requestAnimationFrame(waitForAnimations);
    }

    window.__seekTo = function(timeSec) {
         var wallMs = timeSec * 1000;
         var anims = document.getAnimations();
         for (var i = 0; i < anims.length; i++) {
             try {
                 var delay = 0;
                 var dur = 5000;
                 var iterations = 1;
                 if (anims[i].effect && anims[i].effect.getTiming) {
                     var timing = anims[i].effect.getTiming();
                     delay = timing.delay || 0;
                     dur = timing.duration || 5000;
                     iterations = timing.iterations || 1;
                 }
                 var animTime = wallMs - delay;
                 if (animTime < 0) animTime = 0;
                 // infinite动画用取模实现无缝循环，非infinite动画clamp到duration
                 if (iterations === Infinity && dur > 0) {
                     animTime = animTime % dur;
                 } else {
                     if (animTime > dur) animTime = dur;
                 }
                 anims[i].currentTime = animTime;
             } catch(e) {}
         }
         document.body.offsetHeight;
     };

    window.__destroy = function() {
        var anims = document.getAnimations();
        for (var i = 0; i < anims.length; i++) {
            try { anims[i].cancel(); } catch(e) {}
        }
    };

    initAnimControl();
})();
"""


def _has_css_animation(html: str) -> bool:
    """检测HTML是否包含CSS动画（支持 @keyframes / animation / transition）"""
    return bool(re.search(r'@keyframes\s|animation\s*:|transition\s*:', html))


def _render_html_to_frames_impl(
    html: str, width: int, height: int, duration: float, fps: int,
    output_dir: str, scene_idx: int, scale: float = 1.0
) -> List[str]:
    """
    Playwright 逐帧捕获 CSS 动画（内部实现，在独立线程中运行）
    """
    if not PLAYWRIGHT_AVAILABLE:
        return []

    frames = []
    total_frames = max(1, int(duration * fps))
    capture_width = max(1, int(width * scale))
    capture_height = max(1, int(height * scale))

    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox', '--disable-setuid-sandbox',
            '--disable-gpu', '--disable-dev-shm-usage'
        ]
    )
    context = browser.new_context(
        viewport={"width": capture_width, "height": capture_height},
        device_scale_factor=1
    )
    page = context.new_page()

    try:
        page.set_content(html, wait_until="networkidle", timeout=20000)

        # 检查HTML中是否声明了CSS动画
        html_has_anim = _has_css_animation(html)
        print(f"[VideoGen] 场景{scene_idx}: HTML中声明动画={html_has_anim}")

        page.evaluate(FRAME_CAPTURE_JS)
        page.wait_for_function("window.__animReady === true", timeout=10000)

        anim_count = page.evaluate("window.__animCount || 0")
        print(f"[VideoGen] 场景{scene_idx}: 浏览器检测到 {anim_count} 个CSS动画")

        if anim_count == 0:
            # 无动画：只截1帧，避免浪费
            frame_path = os.path.join(
                output_dir, f"scene_{scene_idx:03d}_f_000000.png"
            )
            page.screenshot(path=frame_path, full_page=False)
            frames.append(frame_path)
            print(f"[VideoGen] 场景{scene_idx} 无动画，单帧截图")
            return frames

        for frame_num in range(total_frames):
            t = frame_num / fps
            page.evaluate(f"window.__seekTo({t});")
            page.wait_for_timeout(2)

            frame_path = os.path.join(
                output_dir, f"scene_{scene_idx:03d}_f_{frame_num:06d}.png"
            )
            page.screenshot(path=frame_path, full_page=False)
            frames.append(frame_path)

        page.evaluate("window.__destroy();")

        print(f"[VideoGen] 场景{scene_idx} 逐帧渲染: {len(frames)}帧/{duration:.1f}s@{fps}fps")
        return frames

    except Exception as e:
        print(f"[VideoGen] 逐帧渲染场景{scene_idx} 失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        try: page.close()
        except: pass
        try: context.close()
        except: pass
        try: browser.close()
        except: pass
        try: playwright.stop()
        except: pass


def _render_html_to_frames(
    html: str, width: int, height: int, duration: float, fps: int,
    output_dir: str, scene_idx: int, scale: float = 1.0
) -> List[str]:
    """
    使用 Playwright + Web Animations API 逐帧捕获 CSS 动画
    自动处理 asyncio 事件循环冲突
    """
    return _run_playwright_safe(
        _render_html_to_frames_impl,
        html, width, height, duration, fps, output_dir, scene_idx, scale
    )


def _render_html_to_image_fallback_impl(
    html: str, width: int, height: int, output_dir: str, scene_index: int
) -> Optional[str]:
    """静态截图内部实现（在独立线程中运行）"""
    if not PLAYWRIGHT_AVAILABLE:
        return None

    img_path = os.path.join(output_dir, f"scene_{scene_index:03d}.png")

    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    page = browser.new_page(viewport={"width": width, "height": height})

    try:
        page.set_content(html, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(500)
        page.screenshot(path=img_path, full_page=False)
        print(f"[VideoGen] 静态截图成功: {img_path}")
        return img_path
    except Exception as e:
        print(f"[VideoGen] Playwright 渲染场景 {scene_index} 失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        try: page.close()
        except: pass
        try: browser.close()
        except: pass
        try: playwright.stop()
        except: pass


def _render_html_to_image_fallback(
    html: str, width: int, height: int, output_dir: str, scene_index: int
) -> Optional[str]:
    """静态截图（自动处理 asyncio 冲突）"""
    return _run_playwright_safe(
        _render_html_to_image_fallback_impl,
        html, width, height, output_dir, scene_index
    )


# ==================== 图片加载 ====================

def _load_images_as_base64(images: dict) -> Tuple[dict, dict]:
    """返回 (placeholder_map, full_data_map)，用于避免base64撑爆AI上下文"""
    placeholder_map = {}  # name -> 简短描述
    full_data_map = {}    # name -> 完整data URI（后处理替换用）
    if not images:
        return placeholder_map, full_data_map
    try:
        from PIL import Image as PILImage
    except ImportError:
        PILImage = None
    for name, path in images.items():
        if not os.path.isfile(path):
            print(f"[VideoGen] 图片未找到: {path}")
            continue
        try:
            img_data = None
            img_w, img_h, fmt = 0, 0, "PNG"
            img_mime = "image/png"
            if PILImage:
                img = PILImage.open(path)
                img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
                max_side = 200
                w, h = img.size
                if max(w, h) > max_side:
                    scale = max_side / max(w, h)
                    w, h = int(w * scale), int(h * scale)
                    img = img.resize((w, h), PILImage.LANCZOS)
                img_w, img_h = w, h
                buf = BytesIO()
                fmt = "PNG" if img.mode == "RGBA" else "JPEG"
                img.save(buf, format=fmt, optimize=True, quality=75)
                img_data = buf.getvalue()
                img_mime = "image/png" if fmt == "PNG" else "image/jpeg"
            else:
                with open(path, "rb") as f:
                    img_data = f.read()
                ext = os.path.splitext(path)[1].lower()
                mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
                img_mime = mime_map.get(ext, "image/png")
                fmt = "PNG" if "png" in img_mime else "JPEG"
            b64 = base64.b64encode(img_data).decode("utf-8")
            full_uri = f"data:{img_mime};base64,{b64}"
            full_data_map[name] = full_uri
            placeholder_map[name] = f"[IMG:{name}] (可用图片, {fmt}, {img_w}x{img_h}px)"
            print(f"[VideoGen] 图片已加载: {name} ({len(b64)} chars base64, {img_w}x{img_h}px)")
        except Exception as e:
            print(f"[VideoGen] 图片加载失败 {name}: {e}")
    return placeholder_map, full_data_map


def _replace_image_placeholders(html: str, full_data_map: dict) -> str:
    """将HTML中的 [IMG:name] 占位符替换为完整base64 data URI"""
    for name, uri in full_data_map.items():
        placeholder = f"[IMG:{name}]"
        html = html.replace(placeholder, uri)
    return html


def _handle_generated_images(html: str, work_dir: str) -> str:
    """检测HTML中的[GEN_IMG:描述]占位符，调用AI生成图片并替换为base64 data URI"""
    import re
    pattern = re.compile(r'\[GEN_IMG:([^\]]+)\]')

    if not pattern.search(html):
        return html

    try:
        from image_generator import generate_image as gen_img
    except ImportError:
        print("[VideoGen] image_generator模块不可用，跳过AI图片生成")
        return html

    def _replace_match(match):
        prompt = match.group(1).strip()
        if not prompt:
            return match.group(0)
        print(f"[VideoGen] AI图片生成请求: {prompt[:120]}...")
        try:
            img_dir = os.path.join(work_dir, "gen_images")
            os.makedirs(img_dir, exist_ok=True)
            result = gen_img(prompt=prompt, size="16:9", n=1, output_dir=img_dir)

            # generate_image 返回的是字符串（如 "SUCCESS: 已生成 1 张图片:\n  - /path/to/img.png\n"）
            # 需要从字符串中解析出文件路径
            img_path = None
            if isinstance(result, str):
                print(f"[VideoGen] AI图片生成结果: {result[:200]}")
                if result.startswith("SUCCESS:"):
                    for line in result.split('\n'):
                        line = line.strip()
                        if line.startswith('- '):
                            candidate = line[2:].strip()
                            if os.path.isfile(candidate):
                                img_path = candidate
                                break
                if not img_path:
                    print(f"[VideoGen] AI图片生成返回字符串但无法提取文件路径")
            elif isinstance(result, list) and len(result) > 0:
                img_path = result[0] if os.path.isfile(result[0]) else None

            if img_path and os.path.isfile(img_path):
                with open(img_path, "rb") as f:
                    img_data = f.read()
                b64 = base64.b64encode(img_data).decode("utf-8")
                uri = f"data:image/png;base64,{b64}"
                print(f"[VideoGen] AI图片生成成功: {os.path.basename(img_path)} ({len(b64)} chars base64)")
                return uri
            else:
                print(f"[VideoGen] AI图片生成失败: 未获取到有效文件路径")
        except Exception as e:
            print(f"[VideoGen] AI图片生成失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        return match.group(0)

    return pattern.sub(_replace_match, html)


def _is_image_gen_available() -> bool:
    """检查AI图片生成是否配置并可用"""
    return bool(
        config.image_gen_provider
        and (config.image_gen_api_key or config.ai_api_key)
    )


# ==================== AI调用工具 ====================

def _call_ai(system_prompt: str, user_prompt: str, max_tokens: int = 4000, retries: int = 3) -> Optional[str]:
    """通用AI调用，返回响应文本。自动重试空响应和网络错误。"""
    from openai import OpenAI
    api_key = config.ai_api_key
    if not api_key:
        print(f"[VideoGen] AI调用失败: 未配置API密钥")
        return None

    client = OpenAI(api_key=api_key, base_url=config.ai_base_url)

    for attempt in range(retries):
        try:
            kwargs = dict(
                model=config.ai_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.7, max_tokens=max_tokens)
            # DeepSeek 深度思考模式
            if 'deepseek' in config.ai_model.lower() and getattr(config, 'deepseek_thinking_enabled', False):
                kwargs['reasoning_effort'] = getattr(config, 'deepseek_reasoning_effort', 'high')
                kwargs['extra_body'] = {"thinking": {"type": "enabled"}}
                ctx = getattr(config, 'deepseek_context_window', 0)
                if ctx:
                    kwargs['max_tokens'] = ctx
            resp = client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or ""
            print(f"[VideoGen] AI响应长度: {len(content)} chars, 模型: {config.ai_model}")

            if content.strip():
                return content

            if attempt < retries - 1:
                wait = (attempt + 1) * 3
                print(f"[VideoGen] AI返回空响应，{wait}s后重试 ({attempt+1}/{retries})...")
                time.sleep(wait)
            else:
                print(f"[VideoGen] AI返回空响应，已重试{retries}次仍失败")
                return None
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 3
                print(f"[VideoGen] AI调用失败 ({attempt+1}/{retries}): {type(e).__name__}: {e}，{wait}s后重试...")
                time.sleep(wait)
            else:
                print(f"[VideoGen] AI调用失败，已重试{retries}次: {type(e).__name__}: {e}")
                return None

    return None


def _extract_json_brace_count(content: str) -> Optional[str]:
    """用括号计数精确提取最外层JSON对象，避免贪婪正则误匹配CSS中的{}"""
    start = content.find('{')
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(content)):
        ch = content[i]
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return content[start:i + 1]
    return None


def _extract_json(content: str) -> Optional[Dict]:
    """从AI响应中提取并解析JSON，自动修复HTML双引号问题"""
    if not content:
        print("[VideoGen] JSON解析: 输入为空")
        return None

    # 先尝试直接解析（模型可能输出干净的JSON）
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[VideoGen] JSON直接解析失败: {str(e)[:100]}")

    # 用括号计数提取最外层JSON（避免贪婪正则在CSS括号处误匹配）
    json_str = _extract_json_brace_count(content)
    if not json_str:
        # 调试：显示内容头部和尾部
        head = content[:200].replace('\n', '\\n')
        tail = content[-200:].replace('\n', '\\n') if len(content) > 200 else ''
        print(f"[VideoGen] JSON括号提取失败: 内容={len(content)}chars, 头部=[{head}], 尾部=[{tail}]")
        # 回退：尝试用正则提取
        import re
        m = re.search(r'\{[\s\S]*\}', content)
        if m:
            json_str = m.group()
            print(f"[VideoGen] 正则回退提取到JSON块: {len(json_str)} chars")
        else:
            return None

    # 保存原始字符串用于调试
    original_json = json_str

    # 第一步：精准匹配 "html": "..." 字段，用非贪婪匹配直到下一个JSON键
    # 使用更安全的匹配：匹配 "html": 后的字符串，直到遇到 ", " 或 "} 或 "]
    def _fix_html_field(match):
        key = match.group(1)
        html_val = match.group(2)
        # 只替换HTML标签属性中的双引号，保留其他内容
        fixed = html_val.replace('"', "'")
        return f'"{key}":"{fixed}"'

    # 更安全的正则：匹配 "html": "..." 其中 ... 不能包含未转义的 " 后跟 , } ]
    # 使用逐字符扫描替代正则，更可靠
    json_str = _fix_json_string_fields(json_str)

    # 第二步：修复剩余 HTML 属性双引号
    for attr in ('class', 'style', 'id', 'src', 'alt', 'width', 'height', 'href'):
        json_str = re.sub(
            rf'\s{attr}=("[^"]*")',
            lambda m: m.group(0).replace('"', "'"),
            json_str
        )

    # 第三步：补全括号
    brace_count = json_str.count('{') - json_str.count('}')
    if brace_count > 0:
        json_str += '}' * brace_count
    bracket_count = json_str.count('[') - json_str.count(']')
    if bracket_count > 0:
        json_str += ']' * bracket_count

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[VideoGen] JSON解析失败 (首次): {str(e)[:120]}")
        print(f"[VideoGen] JSON解析失败位置附近: ...{json_str[max(0,e.pos-50):e.pos+50]}...")

        # 尝试修复：找到错误位置，截断并补全
        err_col = getattr(e, 'colno', None) or getattr(e, 'pos', None)
        if err_col and err_col > 0:
            truncated = json_str[:err_col]
            # 如果截断在字符串中间，先补全引号
            quote_count = truncated.count('"') - truncated.count('\\"')
            if quote_count % 2 == 1:
                truncated += '"'
            brace_count = truncated.count('{') - truncated.count('}')
            if brace_count > 0:
                truncated += '}' * brace_count
            bracket_count = truncated.count('[') - truncated.count(']')
            if bracket_count > 0:
                truncated += ']' * bracket_count
            try:
                result = json.loads(truncated)
                print(f"[VideoGen] JSON截断修复成功")
                return result
            except Exception as e_fix:
                print(f"[VideoGen] JSON截断修复失败: {e_fix}")

        # 暴力修复：全局替换所有HTML属性双引号
        try:
            raw = original_json
            # 替换所有 style="..." class="..." 等
            raw = re.sub(r'\s([a-zA-Z-]+)="([^"]*)"', r" \1='\2'", raw)
            # 替换所有 "..." 中的HTML标签属性（在JSON字符串值内部）
            brace_count = raw.count('{') - raw.count('}')
            if brace_count > 0:
                raw += '}' * brace_count
            bracket_count = raw.count('[') - raw.count(']')
            if bracket_count > 0:
                raw += ']' * bracket_count
            return json.loads(raw)
        except json.JSONDecodeError as e2:
            print(f"[VideoGen] JSON解析彻底失败: {str(e2)[:120]}")
            print(f"[VideoGen] 修复后JSON前200字: {raw[:200]}")
            return None


def _fix_json_string_fields(json_str: str) -> str:
    """
    扫描JSON字符串，找到所有字符串值，如果值包含HTML则修复其中的双引号。
    使用状态机逐字符解析，比正则更可靠。
    """
    result = []
    i = 0
    n = len(json_str)

    while i < n:
        ch = json_str[i]

        # 检测键名："key":
        if ch == '"' and i + 1 < n:
            # 找到这个引号对应的结束引号
            key_end = i + 1
            while key_end < n:
                if json_str[key_end] == '\\' and key_end + 1 < n:
                    key_end += 2
                elif json_str[key_end] == '"':
                    break
                else:
                    key_end += 1
            if key_end >= n:
                result.append(ch)
                i += 1
                continue

            key = json_str[i + 1:key_end]
            # 检查后面是否跟着 :（说明是键名）
            colon_pos = key_end + 1
            while colon_pos < n and json_str[colon_pos] in ' \t\n\r':
                colon_pos += 1
            if colon_pos < n and json_str[colon_pos] == ':' and not key.startswith('\\'):
                # 是键名，保留
                result.append(json_str[i:colon_pos + 1])
                i = colon_pos + 1
                # 跳过空白
                while i < n and json_str[i] in ' \t\n\r':
                    result.append(json_str[i])
                    i += 1
                # 现在应该在值的位置
                if i < n and json_str[i] == '"':
                    # 字符串值，解析到匹配的引号（处理转义）
                    i += 1  # 跳过开头引号
                    val_chars = []
                    while i < n:
                        if json_str[i] == '\\' and i + 1 < n:
                            val_chars.append(json_str[i:i + 2])
                            i += 2
                        elif json_str[i] == '"':
                            # 字符串结束
                            val_content = ''.join(val_chars)
                            # 如果这个值包含HTML标签，修复双引号
                            if '<' in val_content and '>' in val_content:
                                val_content = val_content.replace('"', "'")
                            result.append('"' + val_content + '"')
                            i += 1
                            break
                        else:
                            val_chars.append(json_str[i])
                            i += 1
                continue

        result.append(ch)
        i += 1

    return ''.join(result)


# ==================== 视频大纲规划 ====================

PLANNER_SYSTEM_PROMPT = """你是视频策划师。将视频按每段约15秒拆分为段落大纲。
只输出JSON:
{
    "segments": [
        {"index": 0, "duration": 15, "topic": "开场：Logo和名字展示", "narration_text": "欢迎了解..."},
        {"index": 1, "duration": 15, "topic": "功能展示1", "narration_text": "..."}
    ]
}"""


def _plan_video_structure(prompt: str, duration: int, segment_secs: int = 15) -> List[Dict]:
    """制定视频分段大纲"""
    num_segments = max(1, (duration + segment_secs - 1) // segment_secs)
    plan_prompt = f"""将以下视频需求分解为 {num_segments} 个段落，每段约 {segment_secs} 秒，总时长约 {duration} 秒。

需求: {prompt}

请分配每段的主题和旁白文本。输出JSON。"""

    content = _call_ai(PLANNER_SYSTEM_PROMPT, plan_prompt, 2000)
    if content:
        print(f"[VideoGen] 大纲AI原始输出前500字:\n{content[:500]}")
    data = _extract_json(content) if content else None
    if data and data.get("segments"):
        print(f"[VideoGen] 大纲解析成功: {len(data['segments'])} 个段落")
        return data["segments"]
    print(f"[VideoGen] 大纲AI输出解析失败，使用手动分段")
    # 降级：手动分段
    segments = []
    seg_dur = duration // num_segments
    for i in range(num_segments):
        segments.append({
            "index": i, "duration": seg_dur if i < num_segments - 1 else duration - seg_dur * (num_segments - 1),
            "topic": f"第{i+1}段", "narration_text": ""
        })
    return segments


# ==================== 段落场景设计 ====================

def _design_video_segment(segment: Dict, placeholder_map: dict, full_data_map: dict,
                         work_dir: str, previous_context: str = "",
                         image_gen_available: bool = False) -> Optional[Dict]:
    """为一个段落(约15秒)设计2-3个HTML场景。使用占位符避免base64撑爆上下文。"""
    seg_index = segment.get("index", 0)
    seg_dur = segment.get("duration", 15)
    topic = segment.get("topic", "")

    image_context = ""
    if placeholder_map:
        image_context = "\n## 可用图片（在src中使用 [IMG:name] 占位符）\n"
        for name, desc in placeholder_map.items():
            image_context += f"{desc}\n"
        image_context += "\n示例: <img src='[IMG:logo]' class='logo'>\n"

    gen_img_instruction = ""
    if image_gen_available:
        gen_img_instruction = """
## AI图片生成（你可以自由使用）
你可以在HTML中通过 [GEN_IMG:描述] 让程序实时调用AI生成图片并自动内联到视频中。

### 格式
<img src='[GEN_IMG:你的图片描述]' class='装饰类名'>

### 提示词撰写指南（重要！决定图片质量）

**1. 结构公式**: `[主体] + [风格] + [色调/氛围] + [构图/比例] + [特殊要求]`
   好: `一只简约的几何线条火箭图标，扁平化矢量风格，蓝紫渐变，纯黑背景，1:1正方形`
   差: `火箭`

**2. 透明背景（用于叠加/水印/Logo素材）**:
   - 要求透明背景: 提示词末尾加上 `transparent background, isolated object, no background`
   - 适用场景: Logo、图标、浮动装饰元素、水印
   - 示例: `金色3D盾牌图标，金属质感，transparent background，isolated，用于Logo`

**3. 纯色/渐变背景（用于全屏背景）**:
   - 示例: `抽象科技波浪线条，深蓝到紫色渐变背景，几何网格，16:9`

**4. 抠图素材（主体+背景分离，方便合成）**:
   - 要求主体突出: `产品展示手机，正面视图，白色背景，干净产品摄影，主体居中突出`
   - 此类图片配合CSS混色/遮罩可实现抠图效果

**5. 比例选择**:
   - 全屏背景: 16:9 (1792x1024)
   - Logo/图标: 1:1 (1024x1024)
   - 装饰竖条: 9:16 (1024x1792)
   - 宽横幅: 21:9

**6. 风格关键词速查**:
   - 科技风: `futuristic, holographic, neon glow, dark theme, cyberpunk, glassmorphism`
   - 商务风: `clean, professional, corporate, minimal, elegant, geometric`
   - 温暖风: `warm lighting, soft pastel, cozy, organic shapes, hand-drawn`
   - 自然风: `landscape, botanical, earthy tones, watercolor, natural light`
   - 抽象装饰: `abstract fluid, geometric pattern, gradient mesh, bokeh, particle`
   - 插画风: `flat vector illustration, isometric, line art, duotone, retro poster`

**7. 注意事项**:
   - 视频分辨率1920x1080，背景图建议用16:9
   - 装饰元素用小尺寸(1:1)更省token
   - Logo/水印类务必要求透明背景"""


    design_prompt = f"""设计视频第{seg_index+1}段，约{seg_dur}秒，主题: {topic}。
总视频上下文: {previous_context}
{image_context}
{gen_img_instruction}
输出JSON，含2-3个场景。HTML要极简（每场景≤1500字符），属性用单引号。图片用 [IMG:name] 或 [GEN_IMG:描述] 占位符。"""

    content = _call_ai(VIDEO_DESIGNER_SYSTEM_PROMPT, design_prompt, 8000)
    if content:
        print(f"[VideoGen] 段落{seg_index} AI原始输出前800字:\n{content[:800]}")
    data = _extract_json(content) if content else None
    if data:
        scenes = data.get('scenes', [])
        # 后处理：替换占位符为完整base64
        for s in scenes:
            html = s.get('html', '')
            if full_data_map:
                html = _replace_image_placeholders(html, full_data_map)
            if image_gen_available:
                html = _handle_generated_images(html, work_dir)
            s['html'] = html
        print(f"[VideoGen] 段落{seg_index} 设计了 {len(scenes)} 个场景")
        for idx, s in enumerate(scenes):
            html_preview = s.get('html', '')[:80]
            has_anim = _has_css_animation(s.get('html', ''))
            print(f"[VideoGen]  场景{idx}: duration={s.get('duration',5)}s, has_animation={has_anim}, html_preview={html_preview}")
    else:
        print(f"[VideoGen] 段落{seg_index} AI输出解析失败，原始输出:\n{content[:1000] if content else 'None'}")
    return data


# ==================== 段落渲染 ====================

def _render_segment_to_mp4(segment: Dict, scene_data: Dict, work_dir: str,
                           width: int, height: int, tts_voice: str, fps: int) -> Optional[str]:
    """渲染一个段落为单独的MP4文件（V4: 逐帧捕获CSS动画）"""
    seg_index = segment.get("index", 0)
    scenes = scene_data.get("scenes", [])
    if not scenes:
        return None

    seg_dir = os.path.join(work_dir, f"seg_{seg_index:02d}")
    os.makedirs(seg_dir, exist_ok=True)

    if not PLAYWRIGHT_AVAILABLE:
        return None

    video_clips = []

    for i, scene in enumerate(scenes):
        html = scene.get("html", "")
        dur = scene.get("duration", 5)
        scene_dir = os.path.join(seg_dir, f"scene_{i:03d}")
        os.makedirs(scene_dir, exist_ok=True)

        frames = None
        if _has_css_animation(html):
            frames = _render_html_to_frames(html, width, height, dur, fps, scene_dir, i)
            if frames and len(frames) >= 2 and ImageSequenceClip:
                clip = ImageSequenceClip(frames, fps=fps)
                video_clips.append(clip)
                print(f"[VideoGen] 场景{i} 动画片段: {len(frames)}帧 @{fps}fps")
                continue
            elif frames and len(frames) >= 2 and not ImageSequenceClip:
                print(f"[VideoGen] 警告: MoviePy v1 不支持 ImageSequenceClip，使用首帧静态")
                img_path = frames[0]
                if img_path and os.path.isfile(img_path):
                    video_clips.append(ImageClip(img_path).with_duration(dur))
                    continue

        # 降级：无CSS动画、帧捕获失败、或ImageSequenceClip不可用 → 静态截图
        if frames and len(frames) == 1:
            # 有帧但只有1帧（无动画情况）
            img_path = frames[0]
            if img_path and os.path.isfile(img_path):
                video_clips.append(ImageClip(img_path).with_duration(dur))
                continue

        img_path = _render_html_to_image_fallback(html, width, height, scene_dir, i)
        if img_path and os.path.isfile(img_path):
            video_clips.append(ImageClip(img_path).with_duration(dur))
        else:
            print(f"[VideoGen] 场景{i} 渲染失败，跳过")

    if not video_clips:
        return None

    seg_video = concatenate_videoclips(video_clips)

    # TTS 配音
    narrations = [s.get("narration", "") for s in scenes]
    combined = "".join(narrations)
    if combined.strip():
        tts_path = os.path.join(seg_dir, "narration.mp3")
        tts_result = _generate_tts(combined, tts_path, tts_voice, speed=1.1)
        if not tts_result.startswith("ERROR"):
            try:
                tts_audio = AudioFileClip(tts_result)
                vdur = seg_video.duration
                print(f"[VideoGen] TTS音频时长: {tts_audio.duration:.2f}s, 视频时长: {vdur:.2f}s")
                if tts_audio.duration > vdur + 0.5:
                    tts_audio = _subclip(tts_audio, 0, vdur)
                    print(f"[VideoGen] TTS音频已截短至 {vdur:.2f}s")
                seg_video = seg_video.with_audio(tts_audio)
                print(f"[VideoGen] TTS音频附加成功")
            except Exception as e:
                print(f"[VideoGen] TTS音频附加失败: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

    seg_mp4 = os.path.join(seg_dir, f"segment_{seg_index:02d}.mp4")
    try:
        has_audio = (hasattr(seg_video, 'audio') and seg_video.audio is not None)
        if has_audio:
            seg_video.write_videofile(seg_mp4, fps=fps, codec="libx264", audio_codec="aac",
                                      temp_audiofile=os.path.join(seg_dir, ".tmp.m4a"), remove_temp=True)
        else:
            seg_video.write_videofile(seg_mp4, fps=fps, codec="libx264")
        print(f"[VideoGen] 段落{seg_index} 渲染完成: {seg_mp4} ({os.path.getsize(seg_mp4)/1024:.0f}KB)")
    except Exception as e:
        print(f"[VideoGen] 段落{seg_index} 视频写入失败: {type(e).__name__}: {e}")
        # 回退：尝试纯视频
        try:
            print(f"[VideoGen] 段落{seg_index} 回退：渲染纯视频...")
            seg_video.write_videofile(seg_mp4, fps=fps, codec="libx264")
            print(f"[VideoGen] 段落{seg_index} 渲染完成(纯视频): {seg_mp4}")
        except Exception as e2:
            print(f"[VideoGen] 段落{seg_index} 纯视频渲染也失败: {type(e2).__name__}: {e2}")
            import traceback
            traceback.print_exc()
            return None
    finally:
        seg_video.close()
        for c in video_clips:
            try: c.close()
            except: pass

    return seg_mp4


# ==================== 主生成函数 ====================

def generate_video(
    prompt: str = None,
    scenes: List[Dict] = None,
    output_path: str = None,
    bg_music_path: str = None,
    music_volume: float = 0.3,
    tts_voice: str = None,
    images: dict = None,
    duration: int = 30,
    width: int = 1920,
    height: int = 1080,
    fps: int = 24,
    style: str = "modern",
) -> str:
    """
    V4 Hyperframes对标架构：
    大纲规划 → 子Agent设计CSS动画HTML → Playwright逐帧捕获动画 → ImageSequenceClip → 拼接 → 清理临时文件
    """
    if not MOVIEPY_AVAILABLE:
        return "ERROR: MoviePy 未安装。运行: pip install moviepy"

    output_dir = os.path.abspath("./downloads/generated_videos")
    os.makedirs(output_dir, exist_ok=True)
    work_dir = os.path.abspath(tempfile.mkdtemp(prefix="videogen_", dir=output_dir))

    if not output_path:
        output_path = os.path.join(output_dir, f"video_{int(time.time()*1000)}.mp4")
    else:
        output_path = os.path.abspath(output_path)

    try:
        # 兼容旧格式
        if scenes and not prompt:
            if scenes and "text" in scenes[0] and "html" not in scenes[0]:
                result = _generate_video_legacy(
                    scenes=scenes, output_path=output_path, bg_music_path=bg_music_path,
                    music_volume=music_volume, tts_voice=tts_voice, fps=fps, size=(width, height))
                shutil.rmtree(work_dir, ignore_errors=True)
                return result
            # 直接渲染scenes
            result = _render_scenes_direct(scenes, output_path, work_dir, width, height, tts_voice, fps)
            shutil.rmtree(work_dir, ignore_errors=True)
            return result

        if not prompt:
            return "ERROR: 请提供 prompt。"

        # 加载图片
        images_placeholder, images_full = _load_images_as_base64(images) if images else (None, None)

        # 检测AI图片生成是否可用
        img_gen_available = _is_image_gen_available()
        if img_gen_available:
            print(f"[VideoGen] AI图片生成可用 (provider={config.image_gen_provider})")

        # 第1步：规划大纲
        print(f"[VideoGen] 第1步: 制定分段大纲 (总时长{duration}s)...")
        segments = _plan_video_structure(prompt, duration)
        print(f"[VideoGen] 大纲: {len(segments)} 个段落")

        # 第2步：逐段生成
        segment_mp4s = []
        context = ""
        for seg in segments:
            print(f"[VideoGen] 第2步: 生成段落 {seg['index']+1}/{len(segments)} - {seg.get('topic', '')[:40]}...")

            # 子Agent设计场景（使用占位符避免base64撑爆上下文）
            scene_data = _design_video_segment(seg, images_placeholder, images_full,
                                               work_dir, context, img_gen_available)
            if not scene_data:
                print(f"[VideoGen] 段落{seg['index']} 设计失败，跳过")
                continue

            # 渲染为MP4
            mp4 = _render_segment_to_mp4(seg, scene_data, work_dir, width, height, tts_voice, fps)
            if mp4:
                segment_mp4s.append(mp4)

            # 保存上下文
            context += f"[段落{seg['index']+1}] {seg.get('topic', '')}: {seg.get('narration_text', '')[:100]}\n"

            # 短暂间隔防止API速率限制
            if len(segments) > 2:
                time.sleep(1)

        if not segment_mp4s:
            return "ERROR: 所有段落生成失败。"

        print(f"[VideoGen] 第3步: 拼接 {len(segment_mp4s)} 个段落...")

        # 第3步：拼接所有段落
        segment_clips = [VideoFileClip(mp4) for mp4 in segment_mp4s]
        final_video = concatenate_videoclips(segment_clips)

        # 第4步：背景音乐
        if bg_music_path and os.path.isfile(bg_music_path):
            try:
                bg_audio = AudioFileClip(bg_music_path)
                vdur = final_video.duration
                print(f"[VideoGen] BGM时长: {bg_audio.duration:.2f}s, 视频时长: {vdur:.2f}s")
                if bg_audio.duration < vdur:
                    n_loops = int(vdur / bg_audio.duration) + 1
                    bg_audio = concatenate_audioclips([bg_audio] * n_loops)
                    print(f"[VideoGen] BGM已循环 {n_loops} 次")
                bg_audio = _subclip(bg_audio, 0, vdur).with_volume_scaled(music_volume)
                # 混合已有音频和BGM
                existing_audio = final_video.audio if hasattr(final_video, 'audio') and final_video.audio else None
                if existing_audio:
                    final_video = final_video.with_audio(CompositeAudioClip([existing_audio, bg_audio]))
                    print(f"[VideoGen] BGM已混合到现有音频")
                else:
                    final_video = final_video.with_audio(bg_audio)
                    print(f"[VideoGen] BGM已设置为音频")
            except Exception as e:
                print(f"[VideoGen] BGM失败: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

        # 第5步：输出
        print(f"[VideoGen] 渲染最终视频 {final_video.duration:.1f}s -> {output_path}")
        try:
            has_audio = (hasattr(final_video, 'audio') and final_video.audio is not None)
            if has_audio:
                final_video.write_videofile(output_path, fps=fps, codec="libx264", audio_codec="aac",
                                            temp_audiofile=os.path.join(work_dir, ".final_tmp.m4a"), remove_temp=True)
            else:
                print(f"[VideoGen] 最终视频无音频轨，渲染纯视频")
                final_video.write_videofile(output_path, fps=fps, codec="libx264")
            print(f"[VideoGen] 最终视频渲染成功")
        except Exception as e:
            print(f"[VideoGen] 最终视频渲染失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # 回退：尝试无音频渲染
            try:
                print(f"[VideoGen] 回退：尝试渲染纯视频(无音频)...")
                final_video.write_videofile(output_path, fps=fps, codec="libx264")
                print(f"[VideoGen] 最终视频渲染成功(纯视频)")
            except Exception as e2:
                print(f"[VideoGen] 纯视频渲染也失败: {type(e2).__name__}: {e2}")
                return f"ERROR: 最终视频渲染失败: {str(e2)}"
        finally:
            final_video.close()
            for c in segment_clips:
                try: c.close()
                except: pass

        # 第6步：清理临时段落MP4
        for mp4 in segment_mp4s:
            try:
                os.remove(mp4)
                seg_dir = os.path.dirname(mp4)
                shutil.rmtree(seg_dir, ignore_errors=True)
            except Exception as e:
                print(f"[VideoGen] 清理临时文件失败: {e}")

        shutil.rmtree(work_dir, ignore_errors=True)
        if os.path.isfile(output_path):
            file_size = os.path.getsize(output_path)
            print(f"[VideoGen] 完成! {output_path} ({file_size} bytes)")
            return output_path
        else:
            return f"ERROR: 视频渲染完成但文件丢失: {output_path}"

    except Exception as e:
        print(f"[VideoGen] 生成流程异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        shutil.rmtree(work_dir, ignore_errors=True)
        return f"ERROR: 视频生成失败: {str(e)}"


def _render_scenes_direct(scenes, output_path, work_dir, width, height, tts_voice, fps):
    """直接渲染scenes列表（V4: 逐帧捕获CSS动画）"""
    if not PLAYWRIGHT_AVAILABLE:
        return "ERROR: Playwright 未安装。"

    clips = []
    for i, scene in enumerate(scenes):
        html = scene.get("html", "")
        dur = scene.get("duration", 5)
        scene_dir = os.path.join(work_dir, f"scene_{i:03d}")
        os.makedirs(scene_dir, exist_ok=True)

        frames = None
        if _has_css_animation(html):
            frames = _render_html_to_frames(html, width, height, dur, fps, scene_dir, i)
            if frames and len(frames) >= 2 and ImageSequenceClip:
                clips.append(ImageSequenceClip(frames, fps=fps))
                continue
            elif frames and len(frames) >= 2 and not ImageSequenceClip:
                img_path = frames[0]
                if img_path and os.path.isfile(img_path):
                    clips.append(ImageClip(img_path).with_duration(dur))
                    continue

        # 降级
        if frames and len(frames) == 1:
            img_path = frames[0]
            if img_path and os.path.isfile(img_path):
                clips.append(ImageClip(img_path).with_duration(dur))
                continue

        img_path = _render_html_to_image_fallback(html, width, height, scene_dir, i)
        if img_path and os.path.isfile(img_path):
            clips.append(ImageClip(img_path).with_duration(dur))

    if not clips:
        return "ERROR: 渲染失败。"

    final = concatenate_videoclips(clips)
    narr = "".join([s.get("narration", "") for s in scenes])
    if narr.strip():
        tts_path = os.path.join(work_dir, "tts.mp3")
        tts_result = _generate_tts(narr, tts_path, tts_voice, speed=1.1)
        if not tts_result.startswith("ERROR"):
            try:
                ta = AudioFileClip(tts_result)
                vdur = final.duration
                print(f"[VideoGen] 直接渲染TTS: {ta.duration:.2f}s / 视频: {vdur:.2f}s")
                if ta.duration > vdur + 0.5:
                    ta = _subclip(ta, 0, vdur)
                final = final.with_audio(ta)
                print(f"[VideoGen] 直接渲染TTS附加成功")
            except Exception as e:
                print(f"[VideoGen] 直接渲染TTS附加失败: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
    try:
        final.write_videofile(output_path, fps=fps, codec="libx264", audio_codec="aac")
        print(f"[VideoGen] 直接渲染完成: {output_path}")
    except Exception as e:
        print(f"[VideoGen] 直接渲染失败(尝试无音频): {type(e).__name__}: {e}")
        try:
            final.write_videofile(output_path, fps=fps, codec="libx264")
            print(f"[VideoGen] 直接渲染完成(无音频): {output_path}")
        except Exception as e2:
            print(f"[VideoGen] 直接渲染彻底失败: {type(e2).__name__}: {e2}")
            import traceback
            traceback.print_exc()
            return f"ERROR: 直接渲染失败: {str(e2)}"
    finally:
        final.close()
        for c in clips:
            try: c.close()
            except: pass
    return output_path


# ==================== 兼容旧格式 ====================

def _generate_video_legacy(scenes, output_path, bg_music_path, music_volume, tts_voice, fps, size):
    """旧的 MoviePy PIL 渲染模式（纯文本场景）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return "ERROR: Pillow 未安装。"

    video_clips = []
    for scene_cfg in scenes:
        text = scene_cfg.get("text", "")
        duration = scene_cfg.get("duration", 5.0)
        bg_color = scene_cfg.get("bg_color", "#000000")
        text_color = scene_cfg.get("text_color", "#FFFFFF")
        font_size = scene_cfg.get("font_size", 80)

        bg_img = Image.new("RGB", size, bg_color)
        draw = ImageDraw.Draw(bg_img)

        # 加载中文字体
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
        font = ImageFont.load_default()
        for fp in font_paths:
            if os.path.isfile(fp):
                try:
                    font = ImageFont.truetype(fp, font_size)
                    break
                except:
                    pass

        # 自动换行
        lines = []
        chars_per_line = max(int(size[0] / (font_size * 0.6)), 1)
        for i in range(0, len(text), chars_per_line):
            lines.append(text[i:i + chars_per_line])
        if not lines:
            lines = [text]

        line_h = font_size * 1.5
        total_h = len(lines) * line_h
        start_y = (size[1] - total_h) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (size[0] - tw) // 2
            draw.text((x, start_y + i * line_h), line, fill=text_color, font=font)

        import numpy as np
        clip = ImageClip(np.array(bg_img)).with_duration(duration)
        video_clips.append(clip)

    final_video = concatenate_videoclips(video_clips)

    if bg_music_path and os.path.isfile(bg_music_path):
        try:
            bg_audio = AudioFileClip(bg_music_path)
            video_dur = final_video.duration
            if bg_audio.duration < video_dur:
                n_loops = int(video_dur / bg_audio.duration) + 1
                bg_audio = concatenate_audioclips([bg_audio] * n_loops)
            bg_audio = _subclip(bg_audio, 0, video_dur).with_volume_scaled(music_volume)
            final_video = final_video.with_audio(bg_audio)
            print(f"[VideoGen] Legacy BGM已添加")
        except Exception as e:
            print(f"[VideoGen] Legacy BGM失败: {e}")

    try:
        has_audio = (hasattr(final_video, 'audio') and final_video.audio is not None)
        if has_audio:
            final_video.write_videofile(output_path, fps=fps, codec="libx264", audio_codec="aac")
        else:
            final_video.write_videofile(output_path, fps=fps, codec="libx264")
        print(f"[VideoGen] Legacy渲染完成: {output_path}")
    except Exception as e:
        print(f"[VideoGen] Legacy渲染失败(尝试无音频): {type(e).__name__}: {e}")
        try:
            final_video.write_videofile(output_path, fps=fps, codec="libx264")
            print(f"[VideoGen] Legacy渲染完成(无音频): {output_path}")
        except Exception as e2:
            print(f"[VideoGen] Legacy渲染彻底失败: {type(e2).__name__}: {e2}")
            import traceback
            traceback.print_exc()
            return f"ERROR: Legacy渲染失败: {str(e2)}"
    finally:
        final_video.close()
        for c in video_clips:
            try: c.close()
            except: pass
    return output_path


def list_video_templates() -> str:
    return """可用视频生成方式:
  - 推荐: 提供 prompt 让 AI 自动设计场景
    generate_video(prompt="制作一个30秒产品介绍视频", duration=30)
  - 兼容: 手动提供 scenes 列表（即旧格式）"""


def get_template_scenes(template_name: str) -> List[Dict]:
    return []
