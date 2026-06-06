# -*- coding: utf-8 -*-
"""
本地 AI 图片生成模型管理器
支持 ComfyUI 自动安装、Conda 环境管理、多来源模型下载
"""
import os
import json
import shutil
import subprocess
import platform
import tempfile
import time
import requests
from pathlib import Path


class LocalImageModelManager:
    """本地图片生成模型管理器"""

    def __init__(self, base_dir="./local_image_models"):
        self.base_dir = base_dir
        self.comfyui_dir = os.path.join(base_dir, "ComfyUI")
        self.models_dir = os.path.join(self.comfyui_dir, "models", "checkpoints")
        self.conda_env_name = "comfyui_env"
        self.image_models_file = os.path.join(os.path.dirname(__file__), "models", "image_models.json")
        self._image_models = self._load_image_models()
        self.default_api_port = 8188

        # 确保目录存在
        os.makedirs(self.models_dir, exist_ok=True)

    def _load_image_models(self):
        """加载图片模型推荐配置"""
        if os.path.exists(self.image_models_file):
            with open(self.image_models_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_recommended_models(self, hardware_grade):
        """根据硬件等级获取推荐模型"""
        return self._image_models.get(hardware_grade, [])

    def get_all_models(self):
        """获取所有可用模型（按等级）"""
        all_models = []
        for grade, models in self._image_models.items():
            for model in models:
                model_copy = model.copy()
                model_copy["grade"] = grade
                all_models.append(model_copy)
        return all_models

    # ========== Conda 环境管理 ==========

    _conda_cache_file = os.path.join(os.path.expanduser("~"), ".tg_helper", "conda_path.txt")

    @classmethod
    def find_conda(cls, install_dir=None):
        """查找 Conda 可执行文件（搜索 PATH、缓存记录、用户指定路径、常见安装路径）"""
        # 1. 先从 PATH 中搜索
        conda_from_path = shutil.which("conda")
        if conda_from_path and os.path.exists(conda_from_path):
            return conda_from_path

        mamba_from_path = shutil.which("mamba")
        if mamba_from_path and os.path.exists(mamba_from_path):
            return mamba_from_path

        # 2. 检查缓存记录（上次自动安装的位置）
        if os.path.exists(cls._conda_cache_file):
            try:
                with open(cls._conda_cache_file, 'r', encoding='utf-8') as f:
                    cached_path = f.read().strip()
                if cached_path and os.path.exists(cached_path):
                    return cached_path
            except Exception:
                pass

        # 3. 检查用户指定的安装目录
        if install_dir:
            conda_exe = os.path.join(install_dir, "Scripts", "conda.exe")
            if os.path.exists(conda_exe):
                return conda_exe

        # 4. 常见 Conda 安装路径
        conda_paths = [
            r"C:\ProgramData\anaconda3\Scripts\conda.exe",
            r"C:\ProgramData\miniconda3\Scripts\conda.exe",
            os.path.expanduser(r"~\anaconda3\Scripts\conda.exe"),
            os.path.expanduser(r"~\miniconda3\Scripts\conda.exe"),
        ]
        for path in conda_paths:
            if path and os.path.exists(path):
                return path
        return None

    @classmethod
    def _save_conda_path(cls, conda_path):
        """保存 Conda 路径到缓存文件"""
        try:
            os.makedirs(os.path.dirname(cls._conda_cache_file), exist_ok=True)
            with open(cls._conda_cache_file, 'w', encoding='utf-8') as f:
                f.write(conda_path)
        except Exception:
            pass

    def ensure_conda_installed(self, output_callback=None, use_mirror=False, install_dir=None):
        """确保 Conda 已安装，未安装则自动下载安装 Miniconda"""
        conda_exe = self.find_conda(install_dir)
        if conda_exe:
            if output_callback:
                output_callback(f"✓ Conda 已找到: {conda_exe}", False)
            return conda_exe

        if output_callback:
            output_callback("未找到 Conda，正在自动下载安装 Miniconda...", False)

        # 自动下载安装 Miniconda（支持用户选择安装位置）
        return self._auto_install_miniconda(output_callback, use_mirror, install_dir)

    def _auto_install_miniconda(self, output_callback=None, use_mirror=False, install_dir=None):
        """自动下载并静默安装 Miniconda，支持用户选择安装位置，安装程序会缓存避免重复下载"""
        import urllib.request

        if platform.system() != "Windows":
            if output_callback:
                output_callback("✗ 非 Windows 系统，请手动安装 Miniconda", True)
            return None

        # 使用传入的安装目录或默认路径
        if not install_dir:
            install_dir = os.path.expanduser(r"~\miniconda3")

        # 选择下载源
        if use_mirror:
            download_url = "https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86_64.exe"
        else:
            download_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"

        # 缓存目录
        cache_dir = os.path.join(os.path.expanduser("~"), ".tg_helper", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        installer_path = os.path.join(cache_dir, "Miniconda3-latest-Windows-x86_64.exe")

        try:
            # 检查本地是否已有缓存的安装程序
            if os.path.exists(installer_path):
                if output_callback:
                    output_callback(f"✓ 发现本地缓存的安装程序", False)
            else:
                if output_callback:
                    output_callback(f"正在下载 Miniconda 安装程序...", False)
                # 下载安装程序到缓存
                urllib.request.urlretrieve(download_url, installer_path)
                if output_callback:
                    output_callback(f"✓ 下载完成，已缓存到本地", False)

            if output_callback:
                output_callback(f"将安装到: {install_dir}", False)
                output_callback("正在静默安装（约 1-2 分钟）...", False)

            # /S 必须在前，/D= 必须在最后且不能有空格
            cmd = f'"{installer_path}" /S /D={install_dir}'
            subprocess.run(cmd, shell=True, check=True, timeout=300)

            # 验证安装
            conda_exe = os.path.join(install_dir, "Scripts", "conda.exe")
            if os.path.exists(conda_exe):
                # 添加到 PATH
                os.environ["PATH"] = os.path.join(install_dir, "Scripts") + os.pathsep + os.environ.get("PATH", "")
                os.environ["PATH"] = os.path.join(install_dir, "condabin") + os.pathsep + os.environ.get("PATH", "")
                # 保存路径到缓存，下次直接找到
                self._save_conda_path(conda_exe)
                if output_callback:
                    output_callback(f"✓ Miniconda 安装完成: {conda_exe}", False)
                return conda_exe
            else:
                if output_callback:
                    output_callback("✗ Miniconda 安装后未找到 conda.exe", True)
                return None

        except subprocess.TimeoutExpired:
            if output_callback:
                output_callback("✗ Miniconda 安装超时（超过5分钟）", True)
            return None
        except Exception as e:
            if output_callback:
                output_callback(f"✗ 自动安装 Miniconda 失败: {e}", True)
                output_callback("请手动下载安装: https://www.anaconda.com/download", True)
            return None

    def create_conda_env(self, conda_exe, output_callback=None):
        """创建 ComfyUI Conda 环境，自动接受服务条款"""
        if output_callback:
            output_callback(f"正在创建 Conda 环境: {self.conda_env_name}...", False)

        # 先接受 Anaconda 服务条款（新版 Miniconda 要求）
        channels = [
            "https://repo.anaconda.com/pkgs/main",
            "https://repo.anaconda.com/pkgs/r",
            "https://repo.anaconda.com/pkgs/msys2",
        ]
        for ch in channels:
            try:
                subprocess.run(
                    [conda_exe, "tos", "accept", "--override-channels", "--channel", ch],
                    capture_output=True, text=True, encoding='utf-8',
                    timeout=30
                )
            except Exception:
                pass
        if output_callback:
            output_callback("✓ 已接受 Conda 服务条款", False)

        # 检查环境是否已存在
        try:
            result = subprocess.run(
                [conda_exe, "env", "list"],
                capture_output=True, text=True, encoding='utf-8'
            )
            if self.conda_env_name in result.stdout:
                if output_callback:
                    output_callback(f"✓ Conda 环境 {self.conda_env_name} 已存在", False)
                return True
        except Exception:
            pass

        # 创建环境 (Python 3.11 兼容性最好)
        cmd = [
            conda_exe, "create", "-n", self.conda_env_name,
            "python=3.11", "-y"
        ]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1
            )
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line and output_callback:
                    output_callback(line, False)
            process.wait()

            # 验证环境是否真正创建成功
            verify = subprocess.run(
                [conda_exe, "env", "list"],
                capture_output=True, text=True, encoding='utf-8'
            )
            if self.conda_env_name in verify.stdout:
                if output_callback:
                    output_callback(f"✓ Conda 环境 {self.conda_env_name} 创建完成", False)
                return True
            else:
                if output_callback:
                    output_callback(f"✗ 环境创建失败，输出: {verify.stderr[:300]}", True)
                return False
        except Exception as e:
            if output_callback:
                output_callback(f"✗ 创建 Conda 环境失败: {e}", True)
            return False

    def install_dependencies(self, conda_exe, use_mirror=False, output_callback=None):
        """在 Conda 环境中安装 ComfyUI 依赖"""
        env_python = self._get_conda_python(conda_exe)
        if not env_python:
            if output_callback:
                output_callback("✗ 找不到 Conda 环境中的 Python", True)
            return False

        # pip 镜像配置
        pip_mirror = ""
        if use_mirror:
            pip_mirror = "-i https://pypi.tuna.tsinghua.edu.cn/simple"

        # 设置临时目录到安装盘，避免 C 盘空间不足
        env_dir = os.path.dirname(os.path.dirname(env_python))
        temp_dir = os.path.join(env_dir, "pip_temp")
        os.makedirs(temp_dir, exist_ok=True)
        env = os.environ.copy()
        env["TMP"] = temp_dir
        env["TEMP"] = temp_dir

        packages = [
            ("torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121", True),
            ("transformers", False),
            ("safetensors", False),
            ("pillow", False),
            ("numpy", False),
            ("requests", False),
            ("tqdm", False),
            ("pyyaml", False),
            ("einops", False),
            ("kornia", False),
            ("sentencepiece", False),
            ("spandrel", False),
            ("soundfile", False),
            ("websocket-client", False),
        ]

        for pkg, is_torch in packages:
            if output_callback:
                output_callback(f"正在安装: {pkg}...", False)

            cmd = f'"{env_python}" -m pip install {pkg} {pip_mirror}'
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    shell=True,
                    bufsize=1,
                    env=env
                )
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line and output_callback:
                        output_callback(line, False)
                process.wait()
                # torch 安装失败不阻断（可能已安装 CPU 版本）
                if is_torch and process.returncode != 0:
                    if output_callback:
                        output_callback("⚠ PyTorch 安装可能失败，尝试 CPU 版本...", True)
                    fallback_cmd = f'"{env_python}" -m pip install torch torchvision torchaudio {pip_mirror}'
                    subprocess.run(fallback_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            except Exception as e:
                if output_callback:
                    output_callback(f"✗ 安装 {pkg} 失败: {e}", True)
                if not is_torch:
                    return False

        if output_callback:
            output_callback("✓ 所有依赖安装完成", False)
        return True

    def _get_conda_python(self, conda_exe):
        """获取 Conda 环境中的 Python 路径"""
        try:
            result = subprocess.run(
                [conda_exe, "run", "-n", self.conda_env_name, "python", "-c", "import sys; print(sys.executable)"],
                capture_output=True, text=True, encoding='utf-8'
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    # ========== ComfyUI 安装 ==========

    def install_comfyui(self, conda_exe, use_mirror=False, output_callback=None):
        """自动安装 ComfyUI"""
        if output_callback:
            output_callback("开始安装 ComfyUI...", False)

        # 1. 确保 Conda 环境
        if not self.create_conda_env(conda_exe, output_callback):
            return False

        # 2. 安装依赖
        if not self.install_dependencies(conda_exe, use_mirror, output_callback):
            return False

        # 3. 克隆 ComfyUI
        comfyui_url = "https://github.com/comfyanonymous/ComfyUI.git"
        if use_mirror:
            comfyui_url = "https://gitclone.com/github.com/comfyanonymous/ComfyUI.git"

        if not os.path.exists(os.path.join(self.comfyui_dir, ".git")):
            if output_callback:
                output_callback("正在克隆 ComfyUI...", False)
            try:
                subprocess.run(
                    ["git", "clone", comfyui_url, self.comfyui_dir],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                if output_callback:
                    output_callback("✓ ComfyUI 克隆完成", False)
            except subprocess.CalledProcessError as e:
                if output_callback:
                    output_callback(f"✗ 克隆 ComfyUI 失败: {e.output}", True)
                return False
            except FileNotFoundError:
                if output_callback:
                    output_callback("✗ 未找到 git，请先安装 git", True)
                return False
        else:
            if output_callback:
                output_callback("✓ ComfyUI 已存在", False)

        # 4. 安装 ComfyUI 额外依赖
        env_python = self._get_conda_python(conda_exe)
        if env_python:
            requirements_file = os.path.join(self.comfyui_dir, "requirements.txt")
            if os.path.exists(requirements_file):
                if output_callback:
                    output_callback("正在安装 ComfyUI 额外依赖...", False)
                cmd = f'"{env_python}" -m pip install -r "{requirements_file}"'
                if use_mirror:
                    cmd += " -i https://pypi.tuna.tsinghua.edu.cn/simple"
                try:
                    subprocess.run(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    if output_callback:
                        output_callback("✓ ComfyUI 额外依赖安装完成", False)
                except Exception as e:
                    if output_callback:
                        output_callback(f"✗ 安装依赖失败: {e}", True)

        if output_callback:
            output_callback("✓ ComfyUI 安装完成！", False)
        return True

    # ========== 模型下载 ==========

    def download_model(self, model_info, use_mirror=False, output_callback=None):
        """下载图片生成模型"""
        model_name = model_info.get("name", "unknown")
        dest_path = os.path.join(self.models_dir, f"{model_name}.safetensors")

        if os.path.exists(dest_path):
            if output_callback:
                output_callback(f"✓ 模型 {model_name} 已存在", False)
            return True

        download_urls = model_info.get("download_urls", {})

        # 选择下载源
        url = None
        if use_mirror:
            url = download_urls.get("hf_mirror_cn", "")

        if not url:
            url = download_urls.get("huggingface", "") or download_urls.get("civitai", "")

        if not url:
            if output_callback:
                output_callback(f"✗ 模型 {model_name} 没有可用的下载链接", True)
            return False

        if output_callback:
            output_callback(f"正在下载模型 {model_name}...", False)
            output_callback(f"来源: {url[:80]}...", False)

        try:
            # 使用 requests 流式下载，带进度
            headers = {}
            if "civitai" in url:
                headers["Content-Disposition"] = "attachment"

            r = requests.get(url, stream=True, timeout=300, headers=headers, allow_redirects=True)
            r.raise_for_status()

            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()

            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 显示进度
                        if total_size > 0 and output_callback:
                            progress = (downloaded / total_size) * 100
                            speed = downloaded / (time.time() - start_time + 0.001)
                            speed_str = self._format_speed(speed)
                            if int(progress) % 5 == 0:  # 每 5% 更新一次
                                output_callback(
                                    f"下载中... {progress:.1f}% ({self._format_bytes(downloaded)}/{self._format_bytes(total_size)}) [{speed_str}]",
                                    False
                                )

            if output_callback:
                output_callback(f"✓ 模型 {model_name} 下载完成: {dest_path}", False)
            return True

        except Exception as e:
            if output_callback:
                output_callback(f"✗ 下载模型 {model_name} 失败: {e}", True)
            # 清理未完成的文件
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False

    @staticmethod
    def _format_bytes(size):
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    @staticmethod
    def _format_speed(speed_bytes):
        """格式化速度"""
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if speed_bytes < 1024:
                return f"{speed_bytes:.1f} {unit}"
            speed_bytes /= 1024
        return f"{speed_bytes:.1f} TB/s"

    # ========== ComfyUI 服务管理 ==========

    def start_comfyui(self, conda_exe, port=None, output_callback=None):
        """启动 ComfyUI 服务"""
        if port is None:
            port = self.default_api_port

        env_python = self._get_conda_python(conda_exe)
        if not env_python:
            if output_callback:
                output_callback("✗ 找不到 ComfyUI 环境", True)
            return False

        main_py = os.path.join(self.comfyui_dir, "main.py")
        if not os.path.exists(main_py):
            if output_callback:
                output_callback("✗ ComfyUI 未正确安装", True)
            return False

        if output_callback:
            output_callback(f"正在启动 ComfyUI (端口 {port})...", False)

        try:
            # 启动 ComfyUI 后台进程
            cmd = [
                env_python, main_py,
                "--port", str(port),
                "--listen", "127.0.0.1",  # 仅本地访问
            ]
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )

            # 等待服务就绪
            for i in range(30):
                try:
                    resp = requests.get(f"http://127.0.0.1:{port}/system_stats", timeout=2)
                    if resp.status_code == 200:
                        if output_callback:
                            output_callback(f"✓ ComfyUI 服务已启动: http://127.0.0.1:{port}", False)
                        return True
                except Exception:
                    pass
                time.sleep(1)

            if output_callback:
                output_callback("⚠ ComfyUI 启动中，请稍后再试", True)
            return True  # 即使超时也返回 True，因为可能还在加载

        except Exception as e:
            if output_callback:
                output_callback(f"✗ 启动 ComfyUI 失败: {e}", True)
            return False

    def is_comfyui_running(self, port=None):
        """检查 ComfyUI 是否正在运行"""
        if port is None:
            port = self.default_api_port
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/system_stats", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def stop_comfyui(self, port=None):
        """停止 ComfyUI 服务（通过关闭进程）"""
        # 这里简单地标记服务应停止，实际需要通过进程管理
        # Windows 下可以用 taskkill
        if platform.system() == "Windows":
            try:
                subprocess.run(
                    'taskkill /F /IM python.exe /FI "WINDOWTITLE eq ComfyUI*"',
                    shell=True, capture_output=True
                )
            except Exception:
                pass

    # ========== 模型管理 ==========

    def list_installed_models(self):
        """列出已安装的模型"""
        if not os.path.exists(self.models_dir):
            return []

        models = []
        for f in os.listdir(self.models_dir):
            if f.endswith(('.safetensors', '.ckpt', '.pt')):
                file_path = os.path.join(self.models_dir, f)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                models.append({
                    "name": f,
                    "path": file_path,
                    "size_mb": round(size_mb, 1)
                })
        return models

    def get_model_path(self, model_name):
        """获取模型路径"""
        model_path = os.path.join(self.models_dir, f"{model_name}.safetensors")
        if os.path.exists(model_path):
            return model_path
        # 尝试直接匹配文件名
        full_path = os.path.join(self.models_dir, model_name)
        if os.path.exists(full_path):
            return full_path
        return None

    # ========== 一键部署入口 ==========

    def deploy(self, model_name=None, use_mirror=False, output_callback=None, install_dir=None):
        """
        一键部署本地图片生成环境
        1. 检查/安装 Conda
        2. 创建环境并安装依赖
        3. 安装 ComfyUI
        4. 下载指定模型
        5. 启动 ComfyUI 服务
        """
        # 1. 检查/安装 Conda
        conda_exe = self.ensure_conda_installed(output_callback, use_mirror, install_dir)
        if not conda_exe:
            return False

        # 2. 创建环境
        if not self.create_conda_env(conda_exe, output_callback):
            return False

        # 3. 安装依赖
        if not self.install_dependencies(conda_exe, use_mirror, output_callback):
            return False

        # 4. 安装 ComfyUI
        if not self.install_comfyui(conda_exe, use_mirror, output_callback):
            return False

        # 5. 下载模型
        if model_name:
            # 查找模型信息
            model_info = None
            for grade, models in self._image_models.items():
                for m in models:
                    if m["name"] == model_name:
                        model_info = m
                        break
                if model_info:
                    break

            if model_info:
                if not self.download_model(model_info, use_mirror, output_callback):
                    if output_callback:
                        output_callback("⚠ 模型下载失败，但 ComfyUI 已安装完成", True)
            else:
                # 尝试作为文件路径处理
                if os.path.exists(model_name):
                    dest = os.path.join(self.models_dir, os.path.basename(model_name))
                    if not os.path.exists(dest):
                        shutil.copy2(model_name, dest)
                    if output_callback:
                        output_callback(f"✓ 已复制模型: {model_name}", False)
                else:
                    if output_callback:
                        output_callback(f"⚠ 未找到模型: {model_name}", True)

        # 6. 启动 ComfyUI
        if not self.is_comfyui_running():
            self.start_comfyui(conda_exe, output_callback=output_callback)

        if output_callback:
            output_callback("✓ 部署完成！", False)
        return True
