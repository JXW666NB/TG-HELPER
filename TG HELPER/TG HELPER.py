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
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit, QScrollBar,
    QMessageBox, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QRect, QPoint
from PyQt6.QtGui import QFont, QPixmap, QColor, QPalette, QTextCursor, QMouseEvent

REQUIRED_PACKAGES = [
    "requests", "paho-mqtt", "Pillow", "openai",
    "apscheduler", "watchdog", "pandas", "pydub", "moviepy",
    "edge-tts", "pyautogui", "pyserial", "python-docx",
    "beautifulsoup4", "yt-dlp", "reportlab", "gitpython",
    "websocket-client", "pyyaml", "chromadb", "sentence-transformers"
]

STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
    border: 1px solid #3a3a5c;
    border-radius: 12px;
}

QWidget#centralWidget {
    background-color: #1e1e2e;
    border-radius: 12px;
}

QFrame#titleBar {
    background-color: #252540;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid #3a3a5c;
}

QLabel#titleLabel {
    color: #cdd6f4;
    font-family: "Microsoft YaHei";
    font-size: 13px;
    font-weight: bold;
    padding-left: 15px;
}

QLabel#logoLabel {
    background: transparent;
}

QLabel#appTitle {
    color: #89b4fa;
    font-family: "Microsoft YaHei";
    font-size: 24px;
    font-weight: bold;
    background: transparent;
}

QLabel#statusLabel {
    color: #a6adc8;
    font-family: "Microsoft YaHei";
    font-size: 11px;
    background: transparent;
}

QPushButton#closeBtn {
    color: #f38ba8;
    background: transparent;
    border: none;
    font-size: 16px;
    font-weight: bold;
    padding: 4px 12px;
    border-top-right-radius: 12px;
}

QPushButton#closeBtn:hover {
    background-color: #f38ba8;
    color: #1e1e2e;
    border-top-right-radius: 12px;
}

QPushButton#exitBtn {
    color: #a6adc8;
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 24px;
    font-family: "Microsoft YaHei";
    font-size: 12px;
}

QPushButton#exitBtn:hover {
    background-color: #45475a;
    color: #cdd6f4;
}

QPushButton#exitBtn:disabled {
    color: #585b70;
    background-color: #252540;
    border-color: #313244;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #313244;
    height: 6px;
    min-height: 6px;
    max-height: 6px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #89b4fa,
        stop: 0.5 #b4befe,
        stop: 1 #89b4fa
    );
    border-radius: 4px;
}

QTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 10px;
    font-family: "Consolas", "Courier New";
    font-size: 10px;
    selection-background-color: #45475a;
    selection-color: #cdd6f4;
}

QScrollBar:vertical {
    background: #1e1e2e;
    width: 8px;
    margin: 2px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #585b70;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}
"""


class SignalBridge(QObject):
    log_message = pyqtSignal(str)
    status_update = pyqtSignal(str)
    progress_start = pyqtSignal()
    progress_stop = pyqtSignal()
    enable_exit_btn = pyqtSignal()
    launch_main_signal = pyqtSignal()


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
    answer = QMessageBox.question(
        None,
        "Python 环境缺失",
        (
            "您的电脑未安装 Python 或 pip 不可用。\n"
            "AI 功能需要 Python 环境来安装库。\n\n"
            "是否现在下载 Python 官方安装程序？\n"
            "（下载后请运行安装程序，并务必勾选\u201cAdd Python to PATH\u201d）"
        ),
    )
    if answer != QMessageBox.StandardButton.Yes:
        return False

    url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "python-3.11.9-amd64.exe")
    try:
        urllib.request.urlretrieve(url, installer_path)
    except Exception as e:
        QMessageBox.critical(None, "下载失败", f"无法下载 Python 安装程序：{e}\n请手动访问 python.org 下载。")
        return False

    QMessageBox.information(
        None,
        "安装提示",
        (
            "即将打开 Python 安装程序。\n\n"
            "【重要】在安装界面中，请务必勾选底部的 \u201cAdd Python to PATH\u201d！\n"
            "然后点击 \u201cInstall Now\u201d 开始安装。"
        ),
    )
    subprocess.Popen([installer_path])
    QMessageBox.information(None, "等待安装", "请完成 Python 安装后，点击\u201c确定\u201d继续。")
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
                log_callback(f"\u274c 无法安装 {pkg}，请手动执行: pip install {pkg}")
            return False
    if log_callback:
        log_callback("\u2705 所有依赖库安装完成。")
    return True


def check_other_environments(log_callback=None):
    pass


class ModernLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window_width = 520
        self.window_height = 460

        self.drag_start_position = QPoint()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(self.window_width, self.window_height)

        self._center_on_screen()

        self.signal_bridge = SignalBridge()
        self.signal_bridge.log_message.connect(self._on_log_message)
        self.signal_bridge.status_update.connect(self._on_status_update)
        self.signal_bridge.progress_start.connect(self._on_progress_start)
        self.signal_bridge.progress_stop.connect(self._on_progress_stop)
        self.signal_bridge.enable_exit_btn.connect(self._on_enable_exit_btn)
        self.signal_bridge.launch_main_signal.connect(self._on_launch_main)

        self._setup_ui()
        self._apply_stylesheet()

        threading.Thread(target=self.run_checks, daemon=True).start()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.window_width) // 2
            y = (screen_geometry.height() - self.window_height) // 2
            self.move(x, y)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(36)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.setSpacing(0)

        title_label = QLabel("\u2003TG HELPER 启动器")
        title_label.setObjectName("titleLabel")
        title_bar_layout.addWidget(title_label)

        title_bar_layout.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(40, 36)
        close_btn.clicked.connect(self.on_close)
        title_bar_layout.addWidget(close_btn)

        main_layout.addWidget(title_bar)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(30, 20, 30, 20)
        inner_layout.setSpacing(8)

        logo_path = os.path.join("icon", "TGAI.png")
        if os.path.exists(logo_path):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    logo_label = QLabel()
                    logo_label.setObjectName("logoLabel")
                    logo_label.setPixmap(pixmap)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    inner_layout.addWidget(logo_label)
            except Exception as e:
                print(f"加载 Logo 失败: {e}")

        app_title = QLabel("TG HELPER")
        app_title.setObjectName("appTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(app_title)

        self.status_label = QLabel("正在初始化...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        inner_layout.addWidget(self.progress_bar)

        log_frame = QWidget()
        log_frame_layout = QHBoxLayout(log_frame)
        log_frame_layout.setContentsMargins(0, 0, 0, 0)
        log_frame_layout.setSpacing(0)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        log_frame_layout.addWidget(self.log_text)

        scrollbar = self.log_text.verticalScrollBar()
        if scrollbar:
            scrollbar.setStyleSheet("")

        inner_layout.addWidget(log_frame, stretch=1)

        self.exit_btn = QPushButton("退出")
        self.exit_btn.setObjectName("exitBtn")
        self.exit_btn.setFixedHeight(36)
        self.exit_btn.setEnabled(False)
        self.exit_btn.clicked.connect(self.on_close)
        inner_layout.addWidget(self.exit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(inner, stretch=1)

    def _apply_stylesheet(self):
        self.setStyleSheet(STYLESHEET)

    def log(self, message):
        self.signal_bridge.log_message.emit(message)

    def _on_log_message(self, message):
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        self.log_text.insertPlainText(message + "\n")
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def update_status(self, text):
        self.signal_bridge.status_update.emit(text)

    def _on_status_update(self, text):
        self.status_label.setText(text)

    def _on_progress_start(self):
        self.progress_bar.setRange(0, 0)

    def _on_progress_stop(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

    def _on_enable_exit_btn(self):
        self.exit_btn.setEnabled(True)

    def _on_launch_main(self):
        self._launch_main_impl()

    def run_checks(self):
        try:
            self.log("=== TG HELPER 启动器 ===")
            self.update_status("检查 Python 环境...")
            self.log("正在检查 Python 环境...")

            if not check_python_environment():
                self.log("\u26a0\ufe0f Python 环境不完整，需要安装或修复。")
                self.update_status("需要安装 Python")
                QTimer.singleShot(0, self.guide_python_install)
                return

            self.log("\u2705 Python 环境正常。")

            self.update_status("检查并安装依赖库...")
            self.log("正在检查依赖库...")
            if not ensure_packages(log_callback=self.log):
                self.log("\u274c 部分依赖库安装失败，程序可能无法正常运行。")
                self.update_status("依赖库安装失败")
                self.signal_bridge.enable_exit_btn.emit()
                return
            else:
                self.log("\u2705 依赖库检查完成。")

            self.update_status("检查其他环境...")
            check_other_environments(self.log)

            self.log("准备启动主程序...")
            self.update_status("启动主程序...")
            QTimer.singleShot(500, self._on_launch_main)

        except Exception as e:
            self.log(f"\u274c 启动过程出错: {e}")
            self.update_status("启动失败")
            self.signal_bridge.enable_exit_btn.emit()

    def guide_python_install(self):
        self.signal_bridge.progress_stop.emit()
        if install_python_guide():
            self.signal_bridge.progress_start.emit()
            threading.Thread(target=self.recheck_after_install, daemon=True).start()
        else:
            self.log("用户取消 Python 安装，无法继续。")
            self.update_status("已取消")
            self.signal_bridge.enable_exit_btn.emit()

    def recheck_after_install(self):
        self.log("重新检查 Python 环境...")
        if check_python_environment():
            self.log("\u2705 Python 环境已就绪。")
            self.update_status("检查并安装依赖库...")
            ensure_packages(log_callback=self.log)
            self.signal_bridge.launch_main_signal.emit()
        else:
            self.log("\u274c Python 环境仍然不可用，请手动安装并添加到 PATH。")
            self.update_status("Python 不可用")
            self.signal_bridge.enable_exit_btn.emit()

    def _launch_main_impl(self):
        self.signal_bridge.progress_stop.emit()
        self.log("正在启动 TG HELPER 主界面...")
        self.update_status("启动中...")

        self.close()

        if getattr(sys, 'frozen', False):
            QTimer.singleShot(100, run_main_gui)
        else:
            python_exe = sys.executable
            script_path = os.path.abspath(__file__)
            env = os.environ.copy()
            env["TG_SKIP_LAUNCHER"] = "1"
            subprocess.Popen([python_exe, script_path, "--skip-launcher"], env=env)

    def on_close(self):
        self.close()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().y() < 36:
                self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_start_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_start_position = QPoint()
        super().mouseReleaseEvent(event)


def run_main_gui():
    import main_gui

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    main_window = main_gui.AgentGUI()
    main_window.show()
    app.exec()


def main():
    if getattr(sys, 'frozen', False):
        run_main_gui()
    elif "--skip-launcher" in sys.argv or os.environ.get("TG_SKIP_LAUNCHER") == "1":
        run_main_gui()
    else:
        app = QApplication(sys.argv)
        launcher = ModernLauncher()
        launcher.show()
        app.exec()


if __name__ == "__main__":
    main()
