import os
import json
import tkinter as tk
import subprocess
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import sys
from hardware_detector import HardwareDetector
from local_model_manager import LocalModelManager

CONFIG_FILE = os.path.expanduser("~/.agent_config.json")


def load_config():
    """加载配置，如果文件不存在则启动配置向导"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # 启动配置向导
    root = tk.Tk()
    root.withdraw()
    wizard_root = tk.Toplevel()
    app = ConfigWizard(wizard_root)
    wizard_root.mainloop()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


class ConfigWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("TG helper - 首次配置向导")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        self.config = {}
        self.hardware_grade = HardwareDetector.get_grade()
        self.hardware_info = {
            "cpu": HardwareDetector.get_cpu_info(),
            "memory": HardwareDetector.get_memory_gb(),
            "gpu": HardwareDetector.get_gpu_info(),
            "grade": self.hardware_grade
        }

        # 加载模型推荐表
        try:
            with open("model_recommendations.json", 'r', encoding='utf-8') as f:
                self.model_recs = json.load(f)
        except:
            self.model_recs = {}
        self.recommended_models = self.model_recs.get(self.hardware_grade, [])

        self.current_frame = None
        self.show_welcome()

    def show_welcome(self):
        self.clear_frame()
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        icon_path = os.path.join("icon", "TGAI.png")
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = ttk.Label(frame, image=photo)
                icon_label.image = photo
                icon_label.pack(pady=20)
            except:
                pass

        title = ttk.Label(frame, text="TG HELPER", font=("微软雅黑", 28, "bold"))
        title.pack(pady=10)

        welcome_text = ttk.Label(frame, text="欢迎使用 TG helper！\n您的全能AI私人助手", font=("微软雅黑", 12))
        welcome_text.pack(pady=10)

        btn = ttk.Button(frame, text="开始配置", command=self.show_hardware_info)
        btn.pack(pady=20)

        self.current_frame = frame

    def show_hardware_info(self):
        self.clear_frame()
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(frame, text="硬件检测结果", font=("微软雅黑", 14, "bold")).pack(pady=10)

        info_text = f"""
CPU: {self.hardware_info['cpu']['name']}
核心数: {self.hardware_info['cpu']['cores']}
内存: {self.hardware_info['memory']:.1f} GB
GPU: {self.hardware_info['gpu']['name']}
显存: {self.hardware_info['gpu']['memory_mb']:.0f} MB
硬件等级: {self.hardware_info['grade'].upper()}
"""
        info_label = ttk.Label(frame, text=info_text, justify=tk.LEFT)
        info_label.pack(pady=10)

        ttk.Label(frame, text="推荐部署的本地模型:", font=("微软雅黑", 10, "bold")).pack(pady=5)
        model_list = ttk.Treeview(frame, columns=("name", "size", "ram"), show="headings", height=5)
        model_list.heading("name", text="模型名称")
        model_list.heading("size", text="参数规模")
        model_list.heading("ram", text="推荐内存(GB)")
        for model in self.recommended_models:
            model_list.insert("", tk.END, values=(model["name"], model["size"], model["ram"]))
        model_list.pack(pady=5)

        ttk.Button(frame, text="下一步", command=self.show_model_selection).pack(pady=10)

        self.current_frame = frame

    def show_model_selection(self):
        self.clear_frame()
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(frame, text="选择默认模型", font=("微软雅黑", 14, "bold")).pack(pady=10)

        self.model_var = tk.StringVar(value=self.recommended_models[0]["name"] if self.recommended_models else "")
        model_combo = ttk.Combobox(frame, textvariable=self.model_var, values=[m["name"] for m in self.recommended_models], state="readonly")
        model_combo.pack(pady=10)

        ttk.Label(frame, text="是否一键部署本地模型？").pack(pady=5)
        self.deploy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="是，立即部署", variable=self.deploy_var).pack()

        ttk.Button(frame, text="下一步", command=self.show_api_config).pack(pady=20)

        self.current_frame = frame

    def show_api_config(self):
        self.clear_frame()
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(frame, text="API 配置（云端模型）", font=("微软雅黑", 14, "bold")).pack(pady=10)

        # 创建子框架，用于 grid 布局
        input_frame = ttk.Frame(frame)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(input_frame, width=40)
        self.api_key_entry.grid(row=0, column=1, pady=5)

        ttk.Label(input_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.base_url_entry = ttk.Entry(input_frame, width=40)
        self.base_url_entry.grid(row=1, column=1, pady=5)

        ttk.Label(input_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_entry = ttk.Entry(input_frame, width=40)
        self.model_entry.grid(row=2, column=1, pady=5)

        ttk.Button(frame, text="完成配置", command=self.finish_config).pack(pady=20)

        self.current_frame = frame

    def finish_config(self):
        self.config["ai_api_key"] = self.api_key_entry.get()
        self.config["ai_base_url"] = self.base_url_entry.get()
        self.config["ai_model"] = self.model_entry.get()
        self.config["local_model"] = self.model_var.get()
        self.config["local_model_deploy"] = self.deploy_var.get()
        self.config["hardware_grade"] = self.hardware_grade

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

        if self.deploy_var.get():
            self.start_deploy()
        else:
            self.launch_main()

    def start_deploy(self):
        deploy_win = tk.Toplevel(self.root)
        deploy_win.title("部署本地模型")
        deploy_win.geometry("400x300")
        deploy_win.transient(self.root)
        deploy_win.grab_set()

        ttk.Label(deploy_win, text=f"正在部署 {self.model_var.get()}...", font=("微软雅黑", 12)).pack(pady=20)
        progress = ttk.Progressbar(deploy_win, length=300, mode='indeterminate')
        progress.pack(pady=10)
        progress.start()

        status_label = ttk.Label(deploy_win, text="下载中...")
        status_label.pack(pady=10)

        def deploy_callback(success, result):
            progress.stop()
            if success:
                status_label.config(text="部署成功！")
                ttk.Button(deploy_win, text="启动主程序", command=lambda: self.launch_main_after_deploy(deploy_win)).pack(pady=10)
            else:
                status_label.config(text=f"部署失败: {result}")
                ttk.Button(deploy_win, text="跳过，启动主程序", command=lambda: self.launch_main_after_deploy(deploy_win)).pack(pady=10)

        manager = LocalModelManager()
        threading.Thread(target=lambda: manager.deploy_model(self.model_var.get(), callback=deploy_callback), daemon=True).start()

    def launch_main_after_deploy(self, win):
        win.destroy()
        self.launch_main()

    def launch_main(self):
        # 销毁当前向导窗口
        self.root.destroy()
        # 启动主程序（新进程）
        base_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(base_dir, "main_gui.py")
        if not os.path.exists(main_script):
            main_script = os.path.join(base_dir, "TG HELPER.py")
            args = [sys.executable, main_script, "--skip-launcher"]
        else:
            args = [sys.executable, main_script]
        subprocess.Popen(args)
        # 退出当前进程
        sys.exit(0)

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
