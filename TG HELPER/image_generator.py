# -*- coding: utf-8 -*-
"""
AI 图片生成模块 - 支持全球主流厂商自由配置
支持文生图 + 图生图，支持智能尺寸解析
"""
import os
import time
import json
import base64
from io import BytesIO
import requests
from config import config


ASPECT_RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "square": "1024x1024",
    "正方形": "1024x1024",
    "16:9": "1792x1024",
    "landscape": "1792x1024",
    "横屏": "1792x1024",
    "9:16": "1024x1792",
    "portrait": "1024x1792",
    "竖屏": "1024x1792",
    "4:3": "1152x864",
    "3:4": "864x1152",
    "3:2": "1344x896",
    "2:3": "896x1344",
    "21:9": "1792x768",
}


PROVIDER_CONFIGS = {
    # ===== 国际主流 =====
    "openai": {
        "name": "OpenAI DALL-E",
        "base_url": "https://api.openai.com/v1",
        "endpoint": "/images/generations",
        "default_model": "dall-e-3",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "openai_images",
        "supports_img2img": False,
    },
    "azure_openai": {
        "name": "Azure OpenAI DALL-E",
        "base_url": "",
        "endpoint": "/images/generations",
        "default_model": "dall-e-3",
        "default_size": "1024x1024",
        "auth_header": "api-key",
        "auth_prefix": "",
        "format": "openai_images",
        "supports_img2img": False,
    },
    "gemini": {
        "name": "Google Gemini Imagen",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "endpoint": "/models/imagen-3.0-generate-002:predict",
        "default_model": "imagen-3.0-generate-002",
        "default_size": "1024x1024",
        "auth_header": "x-goog-api-key",
        "auth_prefix": "",
        "format": "gemini",
        "supports_img2img": False,
    },
    "stability": {
        "name": "Stability AI (Stable Diffusion)",
        "base_url": "https://api.stability.ai/v2beta",
        "endpoint": "/stable-image/generate/sd3",
        "default_model": "sd3-medium",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "stability",
        "supports_img2img": True,
    },
    "cloudflare": {
        "name": "Cloudflare Workers AI (SD)",
        "base_url": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run",
        "endpoint": "/@cf/stabilityai/stable-diffusion-xl-base-1.0",
        "default_model": "@cf/stabilityai/stable-diffusion-xl-base-1.0",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "cloudflare",
        "supports_img2img": True,
    },
    "replicate": {
        "name": "Replicate (FLUX/SD)",
        "base_url": "https://api.replicate.com/v1",
        "endpoint": "/models/black-forest-labs/flux-schnell/predictions",
        "default_model": "black-forest-labs/flux-schnell",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Token ",
        "format": "replicate",
        "supports_img2img": True,
    },
    "ideogram": {
        "name": "Ideogram AI",
        "base_url": "https://api.ideogram.ai",
        "endpoint": "/v1/ideogram-v3/generate",
        "default_model": "V_3",
        "default_size": "1024x1024",
        "auth_header": "Api-Key",
        "auth_prefix": "",
        "format": "ideogram",
        "supports_img2img": False,
    },
    "together": {
        "name": "Together AI (FLUX/SD)",
        "base_url": "https://api.together.xyz/v1",
        "endpoint": "/images/generations",
        "default_model": "black-forest-labs/FLUX.1-schnell",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "openai_images",
        "supports_img2img": False,
    },
    # ===== 中国主流 =====
    "volcengine": {
        "name": "字节跳动豆包 Seedream",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "endpoint": "/images/generations",
        "default_model": "doubao-seedream-4-5-251128",
        "default_size": "2K",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "openai_images",
        "supports_img2img": True,
    },
    "dashscope": {
        "name": "阿里云百炼 通义万相",
        "base_url": "https://dashscope.aliyuncs.com/api/v1",
        "endpoint": "/services/aigc/multimodal-generation/generation",
        "default_model": "wan2.6-t2i",
        "default_size": "1024*1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "dashscope",
        "supports_img2img": True,
    },
    "zhipu": {
        "name": "智谱 AI (CogView)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "endpoint": "/images/generations",
        "default_model": "cogview-3-flash",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "openai_images",
        "supports_img2img": False,
    },
    "minimax": {
        "name": "MiniMax (海螺 AI)",
        "base_url": "https://api.minimaxi.com/v1",
        "endpoint": "/image_generation",
        "default_model": "image-01",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "minimax",
        "supports_img2img": True,
    },
    "siliconflow": {
        "name": "硅基流动 (SiliconFlow)",
        "base_url": "https://api.siliconflow.cn/v1",
        "endpoint": "/images/generations",
        "default_model": "stabilityai/stable-diffusion-3-5-large",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "siliconflow",
        "supports_img2img": True,
    },
    "stepfun": {
        "name": "阶跃星辰 (Step-1X)",
        "base_url": "https://api.stepfun.com/v1",
        "endpoint": "/images/generations",
        "default_model": "step-1x-medium",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "openai_images",
        "supports_img2img": False,
    },
    # ===== 自定义 =====
    "custom": {
        "name": "自定义端点",
        "base_url": "",
        "endpoint": "/images/generations",
        "default_model": "",
        "default_size": "1024x1024",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "format": "openai_images",
        "supports_img2img": True,
    },
}


def _resolve_size(size_str):
    if not size_str:
        return None
    size_str = str(size_str).strip().lower().replace(" ", "").replace("*", "x")
    if "x" in size_str:
        return size_str
    return ASPECT_RATIO_TO_SIZE.get(size_str)


def _load_image_base64(image_source):
    if not image_source:
        return None, None
    if isinstance(image_source, bytes):
        return image_source, "image/png"
    if isinstance(image_source, str):
        if image_source.startswith("http://") or image_source.startswith("https://"):
            try:
                resp = requests.get(image_source, timeout=30)
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type", "image/png")
                return resp.content, content_type
            except Exception:
                return None, None
        if image_source.startswith("data:"):
            try:
                header, b64_data = image_source.split(",", 1)
                mime = header.split(":")[1].split(";")[0] if ":" in header and ";" in header else "image/png"
                return base64.b64decode(b64_data), mime
            except Exception:
                return None, None
        if os.path.isfile(image_source):
            try:
                with open(image_source, "rb") as f:
                    return f.read(), "image/png"
            except Exception:
                return None, None
    return None, None


def _b64_encode_bytes(data):
    return base64.b64encode(data).decode("utf-8")


def _get_provider_config():
    provider = config.image_gen_provider or "openai"
    if provider not in PROVIDER_CONFIGS:
        provider = "custom"
    return provider, PROVIDER_CONFIGS[provider]


def generate_image(prompt, size=None, n=1, reference_images=None, output_dir="./downloads/generated_images", quality=None):
    provider_key, cfg = _get_provider_config()
    api_key = config.image_gen_api_key or config.ai_api_key
    base_url_override = config.image_gen_base_url or cfg["base_url"]
    model = config.image_gen_model or cfg["default_model"]
    img_size = _resolve_size(size) or config.image_gen_size or cfg["default_size"]

    if not api_key:
        return "ERROR: 未配置图片生成 API Key。请在设置中配置 image_gen_api_key。"
    if not base_url_override:
        return f"ERROR: 未配置图片生成端点 URL。提供商 '{cfg['name']}' 需要 base_url。"
    if not model:
        return f"ERROR: 未配置图片生成模型。请在设置中配置 image_gen_model。"

    os.makedirs(output_dir, exist_ok=True)

    ref_images = []
    ref_warning = ""
    if reference_images:
        if not isinstance(reference_images, list):
            reference_images = [reference_images]
        for ref in reference_images:
            img_data, mime = _load_image_base64(ref)
            if img_data:
                ref_images.append((img_data, mime))
        if ref_images and not cfg.get("supports_img2img", False):
            ref_warning = f"⚠️ 当前提供商 '{cfg['name']}' 不支持图生图，将仅使用文本描述生成。\n"
            ref_images = []

    auth_value = f"{cfg['auth_prefix']}{api_key}"
    headers = {
        "Content-Type": "application/json",
        cfg["auth_header"]: auth_value,
    }

    fmt = cfg["format"]
    url = base_url_override.rstrip("/") + cfg["endpoint"]

    try:
        if fmt == "openai_images":
            payload = {
                "model": model,
                "prompt": prompt,
                "n": n,
                "size": img_size,
            }
            if quality:
                payload["quality"] = quality
            elif provider_key == "openai":
                payload["quality"] = config.image_gen_quality or "standard"
            if ref_images and provider_key == "volcengine":
                try:
                    ref_b64 = _b64_encode_bytes(ref_images[0][0])
                    payload["image"] = ref_b64
                except Exception:
                    pass
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_standard_image_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "dashscope":
            dash_size = img_size.replace("x", "*")
            content_list = []
            if ref_images:
                for img_data, mime in ref_images:
                    content_list.append({"image": f"data:{mime};base64,{_b64_encode_bytes(img_data)}"})
            content_list.append({"text": prompt})
            payload = {
                "model": model,
                "input": {
                    "messages": [
                        {"role": "user", "content": content_list}
                    ]
                },
                "parameters": {
                    "size": dash_size,
                    "n": n,
                },
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_dashscope_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "gemini":
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {"sampleCount": n, "aspectRatio": img_size.replace("x", ":")},
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_gemini_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "stability":
            headers.pop("Content-Type", None)
            files = {
                "prompt": (None, prompt),
                "mode": (None, "text-to-image"),
                "aspect_ratio": (None, img_size.replace("x", ":")),
            }
            if ref_images:
                files["image"] = (f"ref.{ref_images[0][1].split('/')[-1]}", BytesIO(ref_images[0][0]), ref_images[0][1])
            resp = requests.post(url, headers=headers, files=files, timeout=120)
            result = _parse_stability_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "replicate":
            payload = {
                "version": model,
                "input": {"prompt": prompt, "aspect_ratio": img_size.replace("x", ":")},
            }
            if ref_images:
                payload["input"]["image"] = f"data:{ref_images[0][1]};base64,{_b64_encode_bytes(ref_images[0][0])}"
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_replicate_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "ideogram":
            payload = {"prompt": prompt}
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_standard_image_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "cloudflare":
            payload = {"prompt": prompt}
            if ref_images:
                payload["image"] = _b64_encode_bytes(ref_images[0][0])
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_cloudflare_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "minimax":
            payload = {
                "model": model,
                "prompt": prompt,
                "aspect_ratio": img_size.replace("x", ":"),
                "n": n,
            }
            if ref_images:
                payload["subject_reference"] = [{
                    "type": "character",
                    "image_file": f"data:{ref_images[0][1]};base64,{_b64_encode_bytes(ref_images[0][0])}"
                }]
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_minimax_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        elif fmt == "siliconflow":
            payload = {
                "model": model,
                "prompt": prompt,
                "image_size": img_size,
            }
            if ref_images:
                payload["image"] = f"data:{ref_images[0][1]};base64,{_b64_encode_bytes(ref_images[0][0])}"
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            result = _parse_siliconflow_response(resp, output_dir)
            return ref_warning + result if ref_warning else result

        else:
            return f"ERROR: 未知的 API 格式: {fmt}"

    except requests.exceptions.Timeout:
        return "ERROR: 图片生成超时（120秒）。"
    except Exception as e:
        return f"ERROR: 图片生成失败: {str(e)}"


def _save_url_images(url_list, output_dir, prefix="ai_gen"):
    saved = []
    for idx, img_url in enumerate(url_list):
        if not img_url or not isinstance(img_url, str) or not img_url.startswith("http"):
            continue
        timestamp = int(time.time() * 1000)
        save_path = os.path.join(output_dir, f"{prefix}_{timestamp}_{idx}.png")
        try:
            img_bytes = requests.get(img_url, timeout=60).content
            with open(save_path, "wb") as f:
                f.write(img_bytes)
            saved.append(save_path)
        except Exception:
            continue
    return saved


def _save_b64_images(b64_list, output_dir, prefix="ai_gen"):
    saved = []
    for idx, b64_str in enumerate(b64_list):
        if not b64_str:
            continue
        timestamp = int(time.time() * 1000)
        save_path = os.path.join(output_dir, f"{prefix}_{timestamp}_{idx}.png")
        try:
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(b64_str))
            saved.append(save_path)
        except Exception:
            continue
    return saved


def _format_result(saved):
    if not saved:
        return "ERROR: 图片生成成功但无法提取/下载图片数据。"
    result = f"SUCCESS: 已生成 {len(saved)} 张图片:\n"
    for p in saved:
        result += f"  - {p}\n"
    return result


def _parse_standard_image_response(resp, output_dir):
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: 无法解析响应 (HTTP {resp.status_code}): {resp.text[:500]}"
    if resp.status_code != 200:
        err_msg = data.get("error", {}).get("message", resp.text[:300])
        return f"ERROR: API 返回错误 (HTTP {resp.status_code}): {err_msg}"
    images = data.get("data", [])
    if not images:
        return "INFO: API 返回了 0 张图片。"
    url_list = []
    for item in images:
        u = item.get("url") or item.get("b64_json")
        if not u:
            continue
        if u.startswith("http"):
            url_list.append(u)
        else:
            url_list.append(u)
    if url_list and url_list[0].startswith("http"):
        saved = _save_url_images(url_list, output_dir)
    else:
        saved = _save_b64_images(url_list, output_dir)
    result = _format_result(saved)
    revised = data.get("data", [{}])[0].get("revised_prompt", "")
    if revised:
        result += f"(模型优化后提示词: {revised})"
    return result


def _parse_dashscope_response(resp, output_dir):
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: 无法解析 DashScope 响应 (HTTP {resp.status_code}): {resp.text[:500]}"
    if resp.status_code != 200:
        err_msg = data.get("message", resp.text[:300])
        return f"ERROR: DashScope API 错误 (HTTP {resp.status_code}): {err_msg}"
    output = data.get("output", {})
    choices = output.get("choices", [])
    if not choices:
        return "ERROR: DashScope 返回了空结果。"
    url_list = []
    for choice in choices:
        content = choice.get("message", {}).get("content", [])
        for c in content:
            img_url = c.get("image") or c.get("image_url", {}).get("url", "")
            if img_url:
                url_list.append(img_url)
    saved = _save_url_images(url_list, output_dir)
    return _format_result(saved)


def _parse_gemini_response(resp, output_dir):
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: 无法解析 Gemini 响应 (HTTP {resp.status_code}): {resp.text[:500]}"
    if resp.status_code != 200:
        err = data.get("error", {}).get("message", resp.text[:300])
        return f"ERROR: Gemini API 错误 (HTTP {resp.status_code}): {err}"
    predictions = data.get("predictions", [])
    if not predictions:
        return "ERROR: Gemini 返回了空结果。"
    b64_list = [p.get("bytesBase64Encoded", "") for p in predictions]
    saved = _save_b64_images(b64_list, output_dir)
    return _format_result(saved)


def _parse_stability_response(resp, output_dir):
    if resp.status_code != 200:
        try:
            err = resp.json().get("errors", [{}])[0].get("detail", resp.text[:300])
        except Exception:
            err = resp.text[:300]
        return f"ERROR: Stability API 错误 (HTTP {resp.status_code}): {err}"
    content_type = resp.headers.get("Content-Type", "")
    if "image" in content_type:
        timestamp = int(time.time() * 1000)
        save_path = os.path.join(output_dir, f"ai_gen_{timestamp}_0.png")
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return f"SUCCESS: 已生成 1 张图片:\n  - {save_path}"
    try:
        data = resp.json()
        images = data.get("artifacts", data.get("images", []))
    except Exception:
        return f"ERROR: Stability 响应无法解析: {resp.text[:300]}"
    b64_list = [item.get("base64", "") for item in images]
    saved = _save_b64_images(b64_list, output_dir)
    return _format_result(saved)


def _parse_replicate_response(resp, output_dir):
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: 无法解析 Replicate 响应 (HTTP {resp.status_code}): {resp.text[:500]}"
    if resp.status_code not in (200, 201):
        err = data.get("detail", resp.text[:300])
        return f"ERROR: Replicate API 错误 (HTTP {resp.status_code}): {err}"
    urls = data.get("output", [])
    if isinstance(urls, str):
        urls = [urls]
    if not urls:
        return "INFO: Replicate 任务已提交，输出为空，可能需要轮询。"
    saved = _save_url_images(urls, output_dir)
    return _format_result(saved)


def _parse_minimax_response(resp, output_dir):
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: 无法解析 MiniMax 响应 (HTTP {resp.status_code}): {resp.text[:500]}"
    if resp.status_code != 200:
        err = data.get("base_resp", {}).get("status_msg", resp.text[:300])
        return f"ERROR: MiniMax API 错误 (HTTP {resp.status_code}): {err}"
    inner = data.get("data", {})
    url_list = inner.get("image_urls", [])
    if not url_list:
        return "ERROR: MiniMax 返回了空图片列表。"
    saved = _save_url_images(url_list, output_dir)
    return _format_result(saved)


def _parse_siliconflow_response(resp, output_dir):
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: 无法解析 SiliconFlow 响应 (HTTP {resp.status_code}): {resp.text[:500]}"
    if resp.status_code != 200:
        err = data.get("message", resp.text[:300])
        return f"ERROR: SiliconFlow API 错误 (HTTP {resp.status_code}): {err}"
    images = data.get("images", [])
    if not images:
        return "ERROR: SiliconFlow 返回了空结果。"
    url_list = [item.get("url", "") for item in images if item.get("url")]
    saved = _save_url_images(url_list, output_dir)
    return _format_result(saved)


def _parse_cloudflare_response(resp, output_dir):
    try:
        data = resp.json()
    except Exception:
        return f"ERROR: 无法解析 Cloudflare 响应 (HTTP {resp.status_code}): {resp.text[:500]}"
    if resp.status_code != 200:
        err = data.get("errors", [{}])[0].get("message", resp.text[:300])
        return f"ERROR: Cloudflare API 错误 (HTTP {resp.status_code}): {err}"
    result_data = data.get("result", {})
    b64 = result_data.get("image", "")
    if not b64:
        return "ERROR: Cloudflare 返回了空图片数据。"
    saved = _save_b64_images([b64], output_dir)
    return _format_result(saved)


def list_providers():
    lines = ["支持 AI 图片生成的厂商:"]
    for key, info in PROVIDER_CONFIGS.items():
        if key == "custom":
            lines.append(f"  {key} - {info['name']} (任意 OpenAI 兼容端点)")
        else:
            img2img = " ✓图生图" if info.get("supports_img2img") else ""
            lines.append(f"  {key} - {info['name']}{img2img} ({info['base_url']})")
            lines.append(f"           默认模型: {info['default_model']}, 默认尺寸: {info['default_size']}")
    return "\n".join(lines)
