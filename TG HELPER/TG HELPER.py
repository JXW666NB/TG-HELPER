# -*- coding: utf-8 -*-
"""
TG HELPER 启动器
- 开发环境：检查 Python 环境、安装依赖、启动主界面
- 打包后环境：直接运行主界面，跳过一切检查
"""
import os
import sys
import subprocess
import threading
import time
import urllib.request
import tempfile
import tkinter as tk
from tkinter import messagebox
import json
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# 依赖库列表（仅在开发环境使用）
REQUIRED_PACKAGES = [
    "requests", "paho-mqtt", "Pillow", "ttkbootstrap", "openai",
    "apscheduler", "watchdog", "pandas", "pydub", "moviepy",
    "edge-tts", "pyautogui", "pyserial", "python-docx",
    "beautifulsoup4", "yt-dlp", "reportlab", "gitpython",
    "websocket-client", "pyyaml", "chromadb", "sentence-transformers"
]


def get_python_executable():
    return sys.executable


def check_python_environment():
    python_exe = get_python_executable()
    try:
        subprocess.run([python_exe, "-m", "pip", "--version"], capture_output=True, check=True)
        return True
    except:
        return False


def install_python_guide():
    root = tk.Tk()
    root.withdraw()
    answer = messagebox.askyesno(
        "Python 环境缺失",
        "您的电脑未安装 Python 或 pip 不可用。\n"
        "AI 功能需要 Python 环境来安装库。\n\n"
        "是否现在下载 Python 官方安装程序？\n"
        "（下载后请运行安装程序，并务必勾选“Add Python to PATH”）"
    )
    root.destroy()
    if not answer:
        return False

    url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "python-3.11.9-amd64.exe")
    try:
        urllib.request.urlretrieve(url, installer_path)
    except Exception as e:
        messagebox.showerror("下载失败", f"无法下载 Python 安装程序：{e}\n请手动访问 python.org 下载。")
        return False

    messagebox.showinfo(
        "安装提示",
        "即将打开 Python 安装程序。\n\n"
        "【重要】在安装界面中，请务必勾选底部的 “Add Python to PATH”！\n"
        "然后点击 “Install Now” 开始安装。"
    )
    subprocess.Popen([installer_path])
    messagebox.showinfo("等待安装", "请完成 Python 安装后，点击“确定”继续。")
    return True


def install_package(pkg_name, source="default", log_callback=None):
    python_exe = get_python_executable()
    if source == "default":
        cmd = [python_exe, "-m", "pip", "install", pkg_name]
    elif source == "tsinghua":
        cmd = [python_exe, "-m", "pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", pkg_name]
    elif source == "aliyun":
        cmd = [python_exe, "-m", "pip", "install", "-i", "https://mirrors.aliyun.com/pypi/simple/", pkg_name]
    else:
        return False

    try:
        if log_callback:
            log_callback(f"正在安装 {pkg_name} ({source})...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True
        else:
            if log_callback:
                log_callback(f"安装 {pkg_name} 失败: {result.stderr[:200]}")
            return False
    except Exception as e:
        if log_callback:
            log_callback(f"安装 {pkg_name} 异常: {e}")
        return False


def get_installed_packages():
    python_exe = get_python_executable()
    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "list", "--format=freeze"],
            capture_output=True, text=True, timeout=10
        )
        installed = set()
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '==' in line:
                pkg = line.split('==')[0].lower()
            elif '@' in line:
                pkg = line.split('@')[0].strip().lower()
            else:
                continue
            installed.add(pkg)
            installed.add(pkg.replace('-', '_'))
        return installed
    except Exception as e:
        print(f"获取已安装包列表失败: {e}")
        return set()


def ensure_packages(log_callback=None):
    installed = get_installed_packages()
    missing = []
    for pkg in REQUIRED_PACKAGES:
        pkg_lower = pkg.lower()
        if pkg_lower not in installed and pkg_lower.replace('-', '_') not in installed:
            missing.append(pkg)

    if not missing:
        if log_callback:
            log_callback("所有依赖库已就绪。")
        return True

    if log_callback:
        log_callback(f"发现 {len(missing)} 个缺失的库: {', '.join(missing)}，开始安装...")

    sources = ["default", "tsinghua", "aliyun"]
    for pkg in missing:
        installed_success = False
        for source in sources:
            if install_package(pkg, source, log_callback):
                installed_success = True
                break
            else:
                if log_callback:
                    log_callback(f"尝试 {source} 源失败，切换下一个...")
        if not installed_success:
            if log_callback:
                log_callback(f"❌ 无法安装 {pkg}，请手动执行: pip install {pkg}")
            return False
    if log_callback:
        log_callback("✅ 所有依赖库安装完成。")
    return True


def check_other_environments(log_callback=None):
    pass


class ModernLauncher:
    def __init__(self):
        self.root = tb.Window(themename="flatly")
        self.root.overrideredirect(True)

        self.window_width = 520
        self.window_height = 460
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

        self.drag_start_x = 0
        self.drag_start_y = 0

        self.log_text = None
        self.progress_bar = None
        self.status_label = None
        self.after_ids = []

        self.setup_ui()
        self.start_background_tasks()

    def setup_ui(self):
        title_bar = tb.Frame(self.root, bootstyle="light")
        title_bar.pack(fill=X)
        title_bar.bind("<Button-1>", self.start_drag)
        title_bar.bind("<B1-Motion>", self.on_drag)

        title_label = tb.Label(title_bar, text="TG HELPER 启动器", font=("微软雅黑", 11, "bold"),
                               bootstyle="inverse-light")
        title_label.pack(side=LEFT, padx=15, pady=5)
        title_label.bind("<Button-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.on_drag)

        close_btn = tb.Button(title_bar, text="✕", bootstyle="danger-link",
                              command=self.on_close, padding=(10, 0))
        close_btn.pack(side=RIGHT, padx=5, pady=5)

        main_frame = tb.Frame(self.root, padding=(20, 15))
        main_frame.pack(fill=BOTH, expand=True)

        logo_path = os.path.join("icon", "TGAI.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                logo_label = tb.Label(main_frame, image=self.logo_img)
                logo_label.pack(pady=(10, 5))
            except Exception as e:
                print(f"加载 Logo 失败: {e}")

        title = tb.Label(main_frame, text="TG HELPER", font=("微软雅黑", 22, "bold"),
                         bootstyle="primary")
        title.pack(pady=(5, 5))

        self.status_label = tb.Label(main_frame, text="正在初始化...", font=("微软雅黑", 10),
                                     bootstyle="secondary")
        self.status_label.pack(pady=(0, 15))

        self.progress_bar = tb.Progressbar(main_frame, length=400, mode='indeterminate',
                                           bootstyle="primary-striped")
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.start()

        log_frame = tb.Frame(main_frame)
        log_frame.pack(fill=BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10,
                                bg="#ffffff", fg="#2b3e50", font=("Consolas", 9),
                                bd=1, relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED,
                                selectbackground="#c1d5e8", selectforeground="#2b3e50")
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = tb.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview,
                                 bootstyle="round")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.close_btn = tb.Button(main_frame, text="退出", bootstyle="secondary-outline",
                                   state=tk.DISABLED, command=self.on_close)
        self.close_btn.pack(pady=(10, 0))

    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def safe_after(self, delay_ms, callback):
        if not self.root.winfo_exists():
            return
        try:
            after_id = self.root.after(delay_ms, callback)
            self.after_ids.append(after_id)
            return after_id
        except tk.TclError:
            return None

    def log(self, message):
        def _add():
            if not self.root.winfo_exists():
                return
            try:
                if self.log_text and self.log_text.winfo_exists():
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, message + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)
            except (tk.TclError, RuntimeError):
                pass
        self.safe_after(0, _add)

    def update_status(self, text):
        def _update():
            if not self.root.winfo_exists():
                return
            try:
                if self.status_label and self.status_label.winfo_exists():
                    self.status_label.config(text=text)
            except (tk.TclError, RuntimeError):
                pass
        self.safe_after(0, _update)

    def start_background_tasks(self):
        self.thread = threading.Thread(target=self.run_checks, daemon=True)
        self.thread.start()

    def run_checks(self):
        try:
            self.log("=== TG HELPER 启动器 ===")
            self.update_status("检查 Python 环境...")
            self.log("正在检查 Python 环境...")

            if not check_python_environment():
                self.log("⚠️ Python 环境不完整，需要安装或修复。")
                self.update_status("需要安装 Python")
                self.safe_after(0, self.guide_python_install)
                return

            self.log("✅ Python 环境正常。")

            self.update_status("检查并安装依赖库...")
            self.log("正在检查依赖库...")
            if not ensure_packages(log_callback=self.log):
                self.log("❌ 部分依赖库安装失败，程序可能无法正常运行。")
                self.update_status("依赖库安装失败")
                self.safe_after(0, lambda: self.close_btn.config(state=tk.NORMAL))
                return
            else:
                self.log("✅ 依赖库检查完成。")

            self.update_status("检查其他环境...")
            check_other_environments(self.log)

            self.log("准备启动主程序...")
            self.update_status("启动主程序...")
            self.safe_after(500, self.launch_main)

        except Exception as e:
            self.log(f"❌ 启动过程出错: {e}")
            self.update_status("启动失败")
            self.safe_after(0, lambda: self.close_btn.config(state=tk.NORMAL))

    def guide_python_install(self):
        self.progress_bar.stop()
        if install_python_guide():
            self.progress_bar.start()
            self.thread = threading.Thread(target=self.recheck_after_install, daemon=True)
            self.thread.start()
        else:
            self.log("用户取消 Python 安装，无法继续。")
            self.update_status("已取消")
            self.close_btn.config(state=tk.NORMAL)

    def recheck_after_install(self):
        self.log("重新检查 Python 环境...")
        if check_python_environment():
            self.log("✅ Python 环境已就绪。")
            self.update_status("检查并安装依赖库...")
            ensure_packages(log_callback=self.log)
            self.safe_after(0, self.launch_main)
        else:
            self.log("❌ Python 环境仍然不可用，请手动安装并添加到 PATH。")
            self.update_status("Python 不可用")
            self.safe_after(0, lambda: self.close_btn.config(state=tk.NORMAL))

    def launch_main(self):
        """启动主界面"""
        self.progress_bar.stop()
        for aid in self.after_ids:
            try:
                self.root.after_cancel(aid)
            except:
                pass
        self.after_ids.clear()
        self.log("正在启动 TG HELPER 主界面...")
        self.update_status("启动中...")

        # 销毁启动器窗口，释放所有 Tk 资源
        self.root.quit()
        self.root.destroy()

        # 打包后的环境：直接运行主界面（所有依赖已内置）
        if getattr(sys, 'frozen', False):
            run_main_gui()
        else:
            # 开发环境：启动一个新的 Python 进程来运行主 GUI
            # 这样可以完全隔离两个 Tkinter 实例，避免冲突
            python_exe = sys.executable
            script_path = os.path.abspath(__file__)
            env = os.environ.copy()
            env["TG_SKIP_LAUNCHER"] = "1"
            subprocess.Popen([python_exe, script_path, "--skip-launcher"], env=env)

    def on_close(self):
        for aid in self.after_ids:
            try:
                self.root.after_cancel(aid)
            except:
                pass
        self.after_ids.clear()
        if self.root.winfo_exists():
            self.root.destroy()


def run_main_gui():
    """直接运行主界面（跳过启动器）"""
    import main_gui
    from ttkbootstrap import Window

    config_file = os.path.expanduser("~/.agent_config.json")
    theme_name = "flatly"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                theme_name = user_config.get("gui_theme", "flatly")
        except:
            pass

    root = Window(themename=theme_name)
    app = main_gui.AgentGUI(root)
    root.mainloop()


def main():
    # 打包后的 EXE 直接运行主界面，跳过启动器
    if getattr(sys, 'frozen', False):
        run_main_gui()
    elif "--skip-launcher" in sys.argv or os.environ.get("TG_SKIP_LAUNCHER") == "1":
        run_main_gui()
    else:
        app = ModernLauncher()
        app.root.mainloop()


if __name__ == "__main__":
    main()
