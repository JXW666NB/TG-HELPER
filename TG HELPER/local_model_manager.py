import os
import json
import platform
import subprocess
import urllib.request
import time
import tempfile
import shutil
import threading
import requests
from tqdm import tqdm

class LocalModelManager:
    def __init__(self, model_dir="./models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.models_file = os.path.join(model_dir, "models.json")
        self._models = self._load_models()
        self.download_threads = []

    def _load_models(self):
        if os.path.exists(self.models_file):
            with open(self.models_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_models(self):
        with open(self.models_file, 'w', encoding='utf-8') as f:
            json.dump(self._models, f, indent=2, ensure_ascii=False)

    def add_model(self, name, path, info=None):
        self._models[name] = {"path": path, "info": info or {}}
        self._save_models()

    def remove_model(self, name):
        if name in self._models:
            del self._models[name]
            self._save_models()
            return True
        return False

    def get_model_path(self, name):
        model = self._models.get(name)
        if model:
            return model['path']
        return None

    def get_all_models(self):
        return self._models.copy()

    # ---------- Ollama 自动安装 ----------
    @staticmethod
    def ensure_ollama_installed():
        if platform.system() != "Windows":
            print("请手动安装 Ollama: https://ollama.com/download")
            return False

        ollama_exe = shutil.which("ollama")
        if ollama_exe:
            return True

        common_paths = [
            r"C:\Program Files\Ollama\ollama.exe",
            r"C:\Program Files (x86)\Ollama\ollama.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe")
        ]
        for path in common_paths:
            if os.path.exists(path):
                bin_dir = os.path.dirname(path)
                os.environ["PATH"] += os.pathsep + bin_dir
                return True

        print("未找到 Ollama，正在下载安装程序...")
        try:
            download_url = "https://ollama.com/download/OllamaSetup.exe"
            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp:
                urllib.request.urlretrieve(download_url, tmp.name)
                installer_path = tmp.name

            print("正在静默安装 Ollama，请稍候...")
            subprocess.run([installer_path, "/S"], check=True, timeout=300)
            time.sleep(5)
            os.unlink(installer_path)

            for path in common_paths:
                if os.path.exists(path):
                    bin_dir = os.path.dirname(path)
                    os.environ["PATH"] += os.pathsep + bin_dir
                    return True
            return False
        except Exception as e:
            print(f"自动安装 Ollama 失败: {e}")
            print("请手动下载并安装: https://ollama.com/download")
            return False

    @staticmethod
    def pull_ollama_model(model_name, callback=None, output_callback=None):
        """
        拉取 Ollama 模型，实时显示进度
        :param output_callback: 实时输出回调函数，接收 (text, is_error) 参数
        """
        if not LocalModelManager.ensure_ollama_installed():
            if callback:
                callback(False, "Ollama 未安装")
            return False

        try:
            # 启动 Ollama 服务
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

            # 使用 Popen 实时获取输出
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并标准错误到标准输出
                text=True,
                encoding='utf-8',
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )

            # 实时读取输出
            full_output = []
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line:
                    full_output.append(line)
                    print(f"[Ollama] {line}")  # 调试输出
                    # 实时回调到 GUI
                    if output_callback:
                        output_callback(line, False)

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                if callback:
                    callback(True, f"Ollama 模型 {model_name} 部署成功")
                return True
            else:
                error_msg = '\n'.join(full_output[-10:])  # 最后10行
                if callback:
                    callback(False, f"部署失败: {error_msg}")
                return False

        except Exception as e:
            if callback:
                callback(False, str(e))
            return False

    # ---------- 模型部署入口 ----------
    def deploy_model(self, model_name, callback=None, output_callback=None):
        """
        部署模型：如果是 Ollama 模型（不以 .gguf 结尾），调用 ollama pull；
        否则视为本地 GGUF 文件路径，直接添加（不下载）。
        """
        if not model_name.endswith(".gguf"):
            # Ollama 模型 - 传递 output_callback 实现实时输出
            return self.pull_ollama_model(model_name, callback, output_callback)
        else:
            # GGUF 文件
            if os.path.exists(model_name):
                self.add_model(os.path.basename(model_name), model_name, {})
                if callback:
                    callback(True, f"已添加本地模型: {model_name}")
                return True
            else:
                if callback:
                    callback(False, f"文件不存在: {model_name}")
                return False
    # ---------- 模型下载（GGUF 多源，可选）----------
    def download_gguf_model(self, url, dest_path, callback=None):
        try:
            r = requests.get(url, stream=True, timeout=30)
            total_size = int(r.headers.get('content-length', 0))
            with open(dest_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(dest_path)) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            if callback:
                callback(True, dest_path)
            return True
        except Exception as e:
            if callback:
                callback(False, str(e))
            return False
