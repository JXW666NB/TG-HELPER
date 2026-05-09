import requests
import subprocess
import time
import os
from local_model_manager import LocalModelManager

class LocalLLM:
    def __init__(self, model_path, base_url="http://localhost:11434"):
        """
        model_path: 可以是本地 GGUF 文件路径，也可以是 Ollama 模型名（如 "qwen2.5:7b"）
        base_url: Ollama API 地址（仅当使用 Ollama 时需要）
        """
        self.model_path = model_path
        self.base_url = base_url
        self._is_ollama = not model_path.endswith(".gguf")
        self.timeout = 300  # 默认超时时间 5 分钟

        if self._is_ollama:
            # Ollama 模型
            if not LocalModelManager.ensure_ollama_installed():
                raise RuntimeError("Ollama 未安装，无法使用本地模型")
            self._start_ollama_service()
            # 预热模型
            self._warmup_model()
        else:
            # GGUF 文件模型（需要 llama.cpp，此处仅做占位，实际未实现）
            # 可扩展使用 llama-cpp-python 或命令行工具
            raise NotImplementedError("GGUF 模型暂不支持，请使用 Ollama 模型")

    def _start_ollama_service(self):
        """启动 Ollama 后台服务"""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if res.status_code == 200:
                print(f"[LocalLLM] Ollama 服务已运行")
                return
        except Exception as e:
            print(f"[LocalLLM] 检查 Ollama 状态: {e}")
        
        print("[LocalLLM] 正在启动 Ollama 服务...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 增加重试次数和等待时间
        for i in range(30):  # 最多等待 30 秒
            try:
                res = requests.get(f"{self.base_url}/api/tags", timeout=2)
                if res.status_code == 200:
                    print("[LocalLLM] Ollama 服务已就绪")
                    break
            except:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Ollama 服务启动失败，请手动检查")

    def _warmup_model(self):
        """预热模型，避免首次调用时加载过慢"""
        try:
            print(f"[LocalLLM] 正在预热模型 {self.model_path}...")
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model_path,
                "prompt": "你好",
                "stream": False,
                "options": {
                    "num_predict": 10,
                    "temperature": 0.7
                }
            }
            # 预热使用较短超时，因为只是简单请求
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                print(f"[LocalLLM] 模型 {self.model_path} 预热完成")
            else:
                print(f"[LocalLLM] 模型预热返回状态码: {response.status_code}")
        except Exception as e:
            print(f"[LocalLLM] 模型预热失败（不影响使用）: {e}")

    def generate(self, prompt, max_tokens=2000, temperature=0.7, stop=None):
        if self._is_ollama:
            return self._generate_ollama(prompt, max_tokens, temperature, stop)
        else:
            # GGUF 模型暂不支持，返回错误
            return "错误: 本地 GGUF 模型暂不支持，请使用 Ollama 模型"

    def _generate_ollama(self, prompt, max_tokens, temperature, stop, retries=2):
        """
        调用 Ollama 生成，带重试机制
        retries: 失败后的重试次数
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_path,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "stop": stop or []
            }
        }
        
        last_error = None
        for attempt in range(retries + 1):
            try:
                print(f"[LocalLLM] 第 {attempt + 1} 次尝试调用 Ollama...")
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "错误: Ollama 返回空响应")
                
            except requests.exceptions.Timeout:
                last_error = f"请求超时（{self.timeout}秒）"
                print(f"[LocalLLM] 第 {attempt + 1} 次尝试超时")
                if attempt < retries:
                    wait_time = 2 ** attempt  # 指数退避: 1, 2, 4...
                    print(f"[LocalLLM] 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                continue
                
            except requests.exceptions.ConnectionError as e:
                return f"错误: 无法连接 Ollama 服务（{self.base_url}），请检查：\n1. Ollama 是否已启动（ollama serve）\n2. 端口 11434 是否被占用\n3. 防火墙设置"
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    return f"错误: 模型 '{self.model_path}' 不存在，请先执行：ollama pull {self.model_path}"
                else:
                    return f"错误: HTTP {e.response.status_code} - {e.response.text}"
                    
            except Exception as e:
                last_error = str(e)
                print(f"[LocalLLM] 第 {attempt + 1} 次尝试出错: {e}")
                if attempt < retries:
                    time.sleep(1)
                continue
        
        # 所有重试都失败
        return f"错误: 调用 Ollama 失败（已重试 {retries} 次）。最后错误: {last_error}\n建议：\n1. 检查系统资源（CPU/内存）是否充足\n2. 尝试重启 Ollama 服务\n3. 使用更小的模型（如 qwen2.5:0.5b）"

    def set_timeout(self, seconds):
        """动态设置超时时间"""
        self.timeout = seconds
        print(f"[LocalLLM] 超时时间已设置为 {seconds} 秒")
