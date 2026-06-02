"""
AI硬件设置页GUI
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSlider, QLineEdit, QComboBox,
    QMessageBox, QProgressBar, QTextEdit, QGroupBox,
    QStackedWidget, QScrollArea, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from ai_hardware.hardware_manager import get_hardware_manager
from ai_hardware.robot_client import TGRobotClient
import config
import os


class FirmwareFlashDialog(QDialog):
    """固件刷写进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("固件刷写")
        self.setMinimumSize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🔧 固件刷写中...")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #4a90d9;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4a90d9;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 当前步骤标签
        self.step_label = QLabel("准备开始...")
        self.step_label.setStyleSheet("font-size: 14px; color: #666;")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.step_label)

        # 日志显示区域
        log_group = QGroupBox("详细日志")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #212529;
                color: #f8f9fa;
                border: none;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        # 按钮区域
        self.button_box = QDialogButtonBox()
        self.cancel_btn = self.button_box.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.button_box)

    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def update_step(self, step: str):
        """更新当前步骤"""
        self.step_label.setText(step)

    def add_log(self, message: str):
        """添加日志"""
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{time_str}] {message}")
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_finished(self, success: bool):
        """设置完成状态"""
        if success:
            self.step_label.setText("✅ 刷写完成！")
            self.step_label.setStyleSheet("font-size: 14px; color: #28a745; font-weight: bold;")
            self.progress_bar.setValue(100)
            self.cancel_btn.setText("关闭")
        else:
            self.step_label.setText("❌ 刷写失败")
            self.step_label.setStyleSheet("font-size: 14px; color: #dc3545; font-weight: bold;")
            self.cancel_btn.setText("关闭")


class PortSelectionDialog(QDialog):
    """端口选择对话框"""

    def __init__(self, ports: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择开发板端口")
        self.setMinimumSize(400, 300)
        self.selected_port = None
        self.ports = ports
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🔌 检测到多个开发板")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # 说明
        desc = QLabel("请选择要刷写固件的开发板端口：")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # 端口列表
        self.port_list = QListWidget()
        self.port_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #4a90d9;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e7f3ff;
            }
        """)

        for port_info in self.ports:
            port = port_info.get('port', '')
            fqbn = port_info.get('fqbn', 'Unknown')
            item_text = f"{port}  ({fqbn})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, port)
            self.port_list.addItem(item)

        # 默认选中第一个
        if self.port_list.count() > 0:
            self.port_list.setCurrentRow(0)

        layout.addWidget(self.port_list)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """确认选择"""
        current_item = self.port_list.currentItem()
        if current_item:
            self.selected_port = current_item.data(Qt.ItemDataRole.UserRole)
        super().accept()

    def get_selected_port(self):
        """获取选中的端口"""
        return self.selected_port


class FirmwareFlashThread(QThread):
    """固件刷写线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    step_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, firmware_dir: str, board_fqbn: str = "esp32:esp32:esp32s3", port: str = None):
        super().__init__()
        self.firmware_dir = firmware_dir
        self.board_fqbn = board_fqbn
        self.port = port
        self.tools = None
        self._is_running = True

    def stop(self):
        """停止刷写"""
        self._is_running = False

    def run(self):
        try:
            from tools import Tools
            # Tools类需要一些参数，但我们只使用它的静态方法
            self.tools = Tools(memory=None)

            # 步骤定义
            steps = [
                ("检查 arduino-cli 工具", self._check_arduino_cli, 10),
                ("安装 ESP32 板卡核心", self._install_core, 20),
                ("安装必要的库", self._install_libraries, 40),
                ("检测开发板端口", self._detect_port, 50),
                ("编译固件", self._compile_firmware, 75),
                ("上传固件", self._upload_firmware, 100),
            ]

            for step_name, step_func, progress in steps:
                if not self._is_running:
                    self.finished_signal.emit(False, "用户取消")
                    return

                self.step_signal.emit(f"⏳ {step_name}...")
                self.progress_signal.emit(progress - 5)

                result = step_func()
                if result.startswith("ERROR"):
                    self.finished_signal.emit(False, f"{step_name}失败: {result}")
                    return

                self.progress_signal.emit(progress)

            self.finished_signal.emit(True, "固件刷写完成！")

        except Exception as e:
            self.finished_signal.emit(False, f"刷写过程出错: {str(e)}")

    def _check_arduino_cli(self):
        """检查并安装arduino-cli"""
        self.log_signal.emit("检查 arduino-cli 工具...")
        check_result = self.tools._run_arduino_cli(['version'])
        if check_result.startswith("ERROR"):
            self.log_signal.emit("arduino-cli 未安装，正在自动安装...")
            install_result = self.tools.install_arduino_cli()
            if install_result.startswith("ERROR"):
                return f"ERROR: 安装 arduino-cli 失败: {install_result}"
            self.log_signal.emit("arduino-cli 安装成功")
        else:
            self.log_signal.emit("arduino-cli 已安装")
        return "SUCCESS"

    def _install_core(self):
        """安装ESP32板卡核心（已安装则跳过）"""
        self.log_signal.emit("检查 ESP32 板卡核心...")

        # 先检查是否已安装
        core_list = self.tools._run_arduino_cli(['core', 'list'])
        if "esp32:esp32" in core_list:
            self.log_signal.emit("ESP32 板卡核心已安装，跳过")
            return "SUCCESS"

        # 未安装，执行安装
        self.log_signal.emit("正在安装 ESP32 板卡核心（首次约需2-5分钟）...")
        self.log_signal.emit("  下载中，请耐心等待...")
        core_result = self.tools.install_board_core("esp32:esp32")
        if core_result.startswith("ERROR"):
            self.log_signal.emit(f"  警告: {core_result}")
        else:
            self.log_signal.emit("ESP32 板卡核心安装完成")
        return "SUCCESS"

    def _install_libraries(self):
        """安装必要的库（已安装则跳过）"""
        self.log_signal.emit("检查必要的库...")

        # 获取已安装的库列表
        installed = self.tools._run_arduino_cli(['lib', 'list'])
        libraries = [
            ("WebSockets", "WebSockets"),
            ("ArduinoJson", "ArduinoJson"),
            ("ESP32Servo", "ESP32Servo"),
            ("Adafruit SSD1306", "Adafruit SSD1306"),
            ("Adafruit GFX Library", "Adafruit GFX Library"),
        ]
        for lib_name, lib_search in libraries:
            if not self._is_running:
                return "ERROR: 用户取消"

            if lib_search.lower() in installed.lower():
                self.log_signal.emit(f"  ✓ {lib_name} 已安装")
                continue

            self.log_signal.emit(f"  安装 {lib_name}...")
            lib_result = self.tools._run_arduino_cli(['lib', 'install', lib_name], timeout=120)
            if "ERROR" in lib_result:
                self.log_signal.emit(f"  警告: {lib_result.strip()}")
            else:
                self.log_signal.emit(f"  ✓ {lib_name} 安装完成")
        return "SUCCESS"

    def _detect_port(self):
        """检测开发板端口"""
        if self.port:
            self.log_signal.emit(f"使用指定端口: {self.port}")
            return "SUCCESS"

        self.log_signal.emit("自动检测开发板端口...")
        detect_result = self.tools.auto_detect_board_and_port()

        if detect_result.startswith("ERROR"):
            return f"ERROR: 检测失败: {detect_result}"

        # 解析检测到的端口
        ports = []
        lines = detect_result.strip().split('\n')[1:]  # 跳过第一行
        for line in lines:
            if '->' in line:
                parts = line.split('->')
                port = parts[0].strip()
                fqbn = parts[1].strip() if len(parts) > 1 else 'Unknown'
                ports.append({'port': port, 'fqbn': fqbn})

        if not ports:
            return "ERROR: 未检测到开发板，请确保ESP32S3已通过USB连接"

        if len(ports) == 1:
            self.port = ports[0]['port']
            self.log_signal.emit(f"检测到开发板在端口: {self.port}")
            return "SUCCESS"
        else:
            # 多个端口，需要用户选择
            self.log_signal.emit(f"检测到 {len(ports)} 个开发板，需要用户选择...")
            # 通过信号让GUI显示选择对话框
            self.step_signal.emit(f"SELECT_PORT:{ports}")
            # 等待用户选择（这里简化处理，实际应该通过信号机制）
            return "SUCCESS"

    def _compile_firmware(self):
        """编译固件"""
        self.log_signal.emit(f"开始编译固件...")
        self.log_signal.emit(f"  项目目录: {self.firmware_dir}")
        self.log_signal.emit(f"  板卡类型: {self.board_fqbn}")

        compile_result = self.tools.compile_ino(
            project_dir=self.firmware_dir,
            board_fqbn=self.board_fqbn
        )

        if compile_result.startswith("ERROR"):
            return f"ERROR: 编译失败: {compile_result}"

        self.log_signal.emit("编译成功！")
        return "SUCCESS"

    def _upload_firmware(self):
        """上传固件"""
        self.log_signal.emit(f"开始上传固件到 {self.port}...")
        self.log_signal.emit("  提示: 请关闭 Arduino IDE、串口助手等占用端口的程序")

        upload_result = self.tools.upload_ino(
            project_dir=self.firmware_dir,
            board_fqbn=self.board_fqbn,
            port=self.port
        )

        if upload_result.startswith("ERROR"):
            err_msg = upload_result
            if "busy" in upload_result.lower() or "permission" in upload_result.lower() or "doesn't exist" in upload_result.lower():
                err_msg = (f"端口 {self.port} 被占用或不可用！\n\n"
                          f"请检查:\n"
                          f"1. 关闭 Arduino IDE 的串口监视器\n"
                          f"2. 关闭其他串口调试工具\n"
                          f"3. 拔插 USB 后重试\n"
                          f"4. 重启电脑后重试\n\n"
                          f"{upload_result}")
            return f"ERROR: 上传失败: {err_msg}"

        self.log_signal.emit("上传成功！")
        return "SUCCESS"


class RobotDiscoveryThread(QThread):
    """机器人自动发现线程"""
    robot_found = pyqtSignal(dict)
    finished_signal = pyqtSignal(list)

    def __init__(self, timeout: int = 5):
        super().__init__()
        self.timeout = timeout

    def run(self):
        robots = TGRobotClient.discover_robots(self.timeout)
        self.finished_signal.emit(robots)


class RobotConnectionThread(QThread):
    """机器人连接线程"""
    status_signal = pyqtSignal(str)
    connected_signal = pyqtSignal(bool)

    def __init__(self, ip: str, port: int = 81):
        super().__init__()
        self.ip = ip
        self.port = port
        self.client = None

    def run(self):
        self.status_signal.emit("正在连接机器人...")
        try:
            self.client = TGRobotClient(self.ip, self.port)
            self.client.on_connected = lambda: self.connected_signal.emit(True)
            self.client.on_disconnected = lambda: self.connected_signal.emit(False)

            result = self.client.connect(timeout=15)
            if result:
                self.status_signal.emit("连接成功！")
            else:
                self.status_signal.emit("连接超时！请检查：\n1. 电脑是否和机器人在同一WiFi\n2. 机器人IP是否正确\n3. 防火墙是否阻止了端口81")
                self.connected_signal.emit(False)
        except Exception as e:
            self.status_signal.emit(f"连接错误: {str(e)}")

    def disconnect(self):
        if self.client:
            self.client.disconnect()


class AIHardwareTab(QWidget):
    """AI硬件设置选项卡"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hw_manager = get_hardware_manager()
        self.connection_thread = None
        self.discovery_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 标题
        title = QLabel("🤖 AI 智能设备")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # 设备选择区域
        devices_frame = QFrame()
        devices_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        devices_layout = QVBoxLayout(devices_frame)

        devices_label = QLabel("选择要连接的智能设备")
        devices_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        devices_layout.addWidget(devices_label)

        # 设备按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # TG桌面机器人按钮
        self.robot_btn = QPushButton("🤖\nTG桌面机器人")
        self.robot_btn.setMinimumSize(200, 120)
        self.robot_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        self.robot_btn.clicked.connect(self.show_robot_menu)
        buttons_layout.addWidget(self.robot_btn)

        # TG智能眼镜按钮（预留）
        self.glasses_btn = QPushButton("👓\nTG智能眼镜\n(即将推出)")
        self.glasses_btn.setMinimumSize(200, 120)
        self.glasses_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.glasses_btn.clicked.connect(self.show_glasses_menu)
        buttons_layout.addWidget(self.glasses_btn)

        buttons_layout.addStretch()
        devices_layout.addLayout(buttons_layout)
        layout.addWidget(devices_frame)

        # 堆叠窗口：用于切换不同页面
        self.stack = QStackedWidget()

        # 主菜单页面（空白或提示）
        self.main_page = QWidget()
        main_layout = QVBoxLayout(self.main_page)
        hint = QLabel("👆 请点击上方按钮选择要连接的设备")
        hint.setStyleSheet("font-size: 14px; color: #6c757d;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(hint)
        self.stack.addWidget(self.main_page)

        # 机器人二级菜单页面
        self.robot_page = self._create_robot_page()
        self.stack.addWidget(self.robot_page)

        # 智能眼镜二级菜单页面（预留）
        self.glasses_page = self._create_glasses_page()
        self.stack.addWidget(self.glasses_page)

        layout.addWidget(self.stack)
        layout.addStretch()

    def _create_robot_page(self) -> QWidget:
        """创建机器人二级菜单页面"""
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 返回按钮
        back_btn = QPushButton("← 返回设备选择")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        back_btn.clicked.connect(self.show_main_menu)
        layout.addWidget(back_btn)

        # 机器人标题
        robot_title = QLabel("🤖 TG桌面机器人")
        robot_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(robot_title)

        # 连接状态区域
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)

        self.status_label = QLabel("🔴 未连接")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #856404;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.connect_btn = QPushButton("连接设备")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.connect_btn.clicked.connect(self.connect_robot)
        status_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("断开连接")
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_robot)
        self.disconnect_btn.setVisible(False)
        status_layout.addWidget(self.disconnect_btn)

        layout.addWidget(status_frame)

        # 自动发现按钮
        discover_frame = QFrame()
        discover_frame.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border: 1px solid #4a90d9;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        discover_layout = QHBoxLayout(discover_frame)
        discover_label = QLabel("🔍 自动发现: 在同一WiFi下自动查找机器人")
        discover_label.setStyleSheet("color: #004085;")
        discover_layout.addWidget(discover_label)
        discover_layout.addStretch()

        self.discover_btn = QPushButton("开始发现")
        self.discover_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        self.discover_btn.clicked.connect(self.discover_robots)
        discover_layout.addWidget(self.discover_btn)
        layout.addWidget(discover_frame)

        # IP设置（可选，自动发现失败时手动输入）
        ip_frame = QFrame()
        ip_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        ip_layout = QHBoxLayout(ip_frame)
        ip_layout.addWidget(QLabel("机器人IP地址 (手动输入):"))
        self.ip_input = QLineEdit("192.168.4.1")
        self.ip_input.setPlaceholderText("可选：自动发现失败时手动输入")
        self.ip_input.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")
        ip_layout.addWidget(self.ip_input)
        layout.addWidget(ip_frame)

        # WiFi配网区域
        wifi_frame = QGroupBox("📶 WiFi配网")
        wifi_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #4a90d9;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4a90d9;
            }
        """)
        wifi_layout = QVBoxLayout(wifi_frame)

        # 配网说明
        wifi_hint = QLabel(
            "💡 机器人启动后会创建开放热点 (TG-Robot-XXXX，无密码)。\n"
            "   电脑连接到该热点后，即可在此配置机器人WiFi。"
        )
        wifi_hint.setStyleSheet("color: #004085; font-size: 11px; background-color: #e7f3ff; padding: 8px; border-radius: 5px;")
        wifi_hint.setWordWrap(True)
        wifi_layout.addWidget(wifi_hint)

        # 扫描按钮行
        scan_row = QHBoxLayout()
        scan_row.addWidget(QLabel("扫描周围WiFi:"))
        scan_row.addStretch()
        self.wifi_scan_btn = QPushButton("📡 扫描WiFi")
        self.wifi_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.wifi_scan_btn.clicked.connect(self.scan_wifi)
        self.wifi_scan_btn.setEnabled(True)
        scan_row.addWidget(self.wifi_scan_btn)
        wifi_layout.addLayout(scan_row)

        # WiFi列表
        self.wifi_list = QListWidget()
        self.wifi_list.setMaximumHeight(120)
        self.wifi_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 3px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #4a90d9;
                color: white;
            }
        """)
        self.wifi_list.itemSelectionChanged.connect(self.on_wifi_selected)
        wifi_layout.addWidget(self.wifi_list)

        # 密码输入行
        pwd_row = QHBoxLayout()
        pwd_row.addWidget(QLabel("WiFi密码:"))
        self.wifi_password_input = QLineEdit()
        self.wifi_password_input.setPlaceholderText("输入WiFi密码")
        self.wifi_password_input.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")
        self.wifi_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_row.addWidget(self.wifi_password_input)
        self.wifi_show_pwd_btn = QPushButton("👁")
        self.wifi_show_pwd_btn.setFixedWidth(35)
        self.wifi_show_pwd_btn.setCheckable(True)
        self.wifi_show_pwd_btn.toggled.connect(self.toggle_wifi_pwd_visible)
        pwd_row.addWidget(self.wifi_show_pwd_btn)
        wifi_layout.addLayout(pwd_row)

        # 配置按钮
        self.wifi_config_btn = QPushButton("🔗 配置WiFi并重启")
        self.wifi_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.wifi_config_btn.clicked.connect(self.configure_wifi)
        self.wifi_config_btn.setEnabled(False)
        wifi_layout.addWidget(self.wifi_config_btn)

        layout.addWidget(wifi_frame)

        # 功能按钮区域
        func_frame = QFrame()
        func_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        func_layout = QGridLayout(func_frame)

        # 第一行功能按钮
        self.self_test_btn = QPushButton("🔧 设备自检")
        self.self_test_btn.clicked.connect(self.run_self_test)
        self.self_test_btn.setEnabled(False)
        func_layout.addWidget(self.self_test_btn, 0, 0)

        self.flash_btn = QPushButton("💾 固件刷写")
        self.flash_btn.clicked.connect(self.flash_firmware)
        func_layout.addWidget(self.flash_btn, 0, 1)

        # 第二行功能按钮
        self.wave_left_btn = QPushButton("👋 挥左手")
        self.wave_left_btn.clicked.connect(lambda: self.perform_action("wave_left"))
        self.wave_left_btn.setEnabled(False)
        func_layout.addWidget(self.wave_left_btn, 1, 0)

        self.wave_right_btn = QPushButton("👋 挥右手")
        self.wave_right_btn.clicked.connect(lambda: self.perform_action("wave_right"))
        self.wave_right_btn.setEnabled(False)
        func_layout.addWidget(self.wave_right_btn, 1, 1)

        self.dance_btn = QPushButton("💃 跳舞")
        self.dance_btn.clicked.connect(lambda: self.perform_action("dance"))
        self.dance_btn.setEnabled(False)
        func_layout.addWidget(self.dance_btn, 1, 2)

        layout.addWidget(func_frame)

        # 音量控制
        volume_frame = QFrame()
        volume_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        volume_layout = QHBoxLayout(volume_frame)
        volume_layout.addWidget(QLabel("🔊 音量:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.setEnabled(False)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel("80%")
        volume_layout.addWidget(self.volume_label)
        layout.addWidget(volume_frame)

        # 舵机控制
        servo_frame = QGroupBox("舵机控制")
        servo_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        servo_layout = QGridLayout(servo_frame)

        # 左手
        servo_layout.addWidget(QLabel("左手:"), 0, 0)
        self.left_hand_slider = QSlider(Qt.Orientation.Horizontal)
        self.left_hand_slider.setMinimum(0)
        self.left_hand_slider.setMaximum(180)
        self.left_hand_slider.setValue(90)
        self.left_hand_slider.setEnabled(False)
        self.left_hand_slider.valueChanged.connect(lambda v: self.on_servo_changed("left_hand", v))
        servo_layout.addWidget(self.left_hand_slider, 0, 1)
        self.left_hand_label = QLabel("90°")
        servo_layout.addWidget(self.left_hand_label, 0, 2)

        # 右手
        servo_layout.addWidget(QLabel("右手:"), 1, 0)
        self.right_hand_slider = QSlider(Qt.Orientation.Horizontal)
        self.right_hand_slider.setMinimum(0)
        self.right_hand_slider.setMaximum(180)
        self.right_hand_slider.setValue(90)
        self.right_hand_slider.setEnabled(False)
        self.right_hand_slider.valueChanged.connect(lambda v: self.on_servo_changed("right_hand", v))
        servo_layout.addWidget(self.right_hand_slider, 1, 1)
        self.right_hand_label = QLabel("90°")
        servo_layout.addWidget(self.right_hand_label, 1, 2)

        # 头部
        servo_layout.addWidget(QLabel("头部:"), 2, 0)
        self.head_slider = QSlider(Qt.Orientation.Horizontal)
        self.head_slider.setMinimum(0)
        self.head_slider.setMaximum(180)
        self.head_slider.setValue(90)
        self.head_slider.setEnabled(False)
        self.head_slider.valueChanged.connect(lambda v: self.on_servo_changed("head", v))
        servo_layout.addWidget(self.head_slider, 2, 1)
        self.head_label = QLabel("90°")
        servo_layout.addWidget(self.head_label, 2, 2)

        layout.addWidget(servo_frame)

        # 语音设置（简化：只保留科大讯飞STT配置，TTS使用Edge TTS无需配置）
        voice_frame = QGroupBox("语音设置 (Edge TTS 无需配置)")
        voice_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        voice_layout = QGridLayout(voice_frame)

        voice_layout.addWidget(QLabel("科大讯飞 AppID:"), 0, 0)
        self.stt_appid_input = QLineEdit()
        self.stt_appid_input.setPlaceholderText("讯飞语音听写 AppID")
        voice_layout.addWidget(self.stt_appid_input, 0, 1)

        voice_layout.addWidget(QLabel("科大讯飞 API Key:"), 1, 0)
        self.stt_key_input = QLineEdit()
        self.stt_key_input.setPlaceholderText("讯飞语音听写 API Key")
        voice_layout.addWidget(self.stt_key_input, 1, 1)

        voice_layout.addWidget(QLabel("科大讯飞 API Secret:"), 2, 0)
        self.stt_secret_input = QLineEdit()
        self.stt_secret_input.setPlaceholderText("讯飞语音听写 API Secret")
        voice_layout.addWidget(self.stt_secret_input, 2, 1)

        # 说明标签
        note = QLabel("💡 文字转语音使用 Edge TTS (免费，无需配置)\n   语音转文字使用科大讯飞API (需配置上方三项)")
        note.setStyleSheet("color: #6c757d; font-size: 11px;")
        voice_layout.addWidget(note, 3, 0, 1, 2)

        layout.addWidget(voice_frame)

        # 日志输出
        log_frame = QFrame()
        log_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        log_layout = QVBoxLayout(log_frame)
        log_layout.addWidget(QLabel("📋 操作日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #212529;
                color: #f8f9fa;
                border: none;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_frame)

        layout.addStretch()
        return scroll

    def _create_glasses_page(self) -> QWidget:
        """创建智能眼镜预留页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 返回按钮
        back_btn = QPushButton("← 返回设备选择")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        back_btn.clicked.connect(self.show_main_menu)
        layout.addWidget(back_btn)

        # 标题
        title = QLabel("👓 TG智能眼镜")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # 即将推出提示
        coming_soon = QFrame()
        coming_soon.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border: 2px dashed #4a90d9;
                border-radius: 15px;
                padding: 30px;
            }
        """)
        cs_layout = QVBoxLayout(coming_soon)

        icon = QLabel("👓")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cs_layout.addWidget(icon)

        cs_title = QLabel("即将推出")
        cs_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #004085;")
        cs_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cs_layout.addWidget(cs_title)

        cs_desc = QLabel("TG智能眼镜正在研发中，敬请期待！")
        cs_desc.setStyleSheet("font-size: 14px; color: #004085;")
        cs_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cs_layout.addWidget(cs_desc)

        # 功能预览列表
        features = QLabel(
            "🎯 计划功能:\n"
            "  • 语音助手 - 语音唤醒与AI对话\n"
            "  • AI视觉 - 实时物体识别与场景理解\n"
            "  • 实时翻译 - 语音实时翻译显示\n"
            "  • AR导航 - 增强现实导航指引\n"
            "  • 通知推送 - 手机消息实时显示\n"
            "  • 拍照录像 - 第一视角影像记录"
        )
        features.setStyleSheet("font-size: 13px; color: #333; padding: 15px;")
        cs_layout.addWidget(features)

        layout.addWidget(coming_soon)
        layout.addStretch()
        return page

    def show_robot_menu(self):
        """显示机器人二级菜单"""
        self.stack.setCurrentIndex(1)

    def show_glasses_menu(self):
        """显示智能眼镜二级菜单"""
        self.stack.setCurrentIndex(2)

    def show_main_menu(self):
        """显示主菜单"""
        self.stack.setCurrentIndex(0)

    def log(self, message: str):
        """添加日志"""
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{time_str}] {message}")

    def discover_robots(self):
        """自动发现机器人"""
        self.discover_btn.setEnabled(False)
        self.discover_btn.setText("发现中...")
        self.log("开始自动发现机器人...")

        self.discovery_thread = RobotDiscoveryThread(timeout=5)
        self.discovery_thread.finished_signal.connect(self.on_discovery_finished)
        self.discovery_thread.start()

    def on_discovery_finished(self, robots: list):
        """发现完成回调"""
        self.discover_btn.setEnabled(True)
        self.discover_btn.setText("开始发现")

        if not robots:
            self.log("未发现机器人，请确保机器人和电脑在同一WiFi下")
            QMessageBox.information(
                self, "发现结果",
                "未发现机器人。\n\n"
                "请确保:\n"
                "1. 机器人已开机并连接WiFi\n"
                "2. 电脑和机器人在同一局域网\n"
                "3. 可尝试手动输入IP地址连接"
            )
            return

        # 自动连接第一个发现的机器人
        robot = robots[0]
        self.log(f"发现机器人: {robot['name']} @ {robot['ip']}")
        self.ip_input.setText(robot['ip'])

        # 询问是否连接
        reply = QMessageBox.question(
            self, "发现机器人",
            f"发现机器人: {robot['name']}\n"
            f"IP: {robot['ip']}\n\n"
            f"是否立即连接？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.connect_robot()

    def connect_robot(self):
        """连接机器人"""
        ip = self.ip_input.text().strip()
        if not ip:
            # 如果没有输入IP，先尝试自动发现
            self.discover_robots()
            return

        self.connect_btn.setEnabled(False)
        self.log(f"正在连接机器人 {ip}...")

        # 启动连接线程
        self.connection_thread = RobotConnectionThread(ip)
        self.connection_thread.status_signal.connect(self.log)
        self.connection_thread.connected_signal.connect(self.on_connection_result)
        self.connection_thread.start()

    def on_connection_result(self, success: bool):
        """连接结果回调"""
        if success:
            self.status_label.setText("🟢 已连接")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #155724;")
            self.connect_btn.setVisible(False)
            self.disconnect_btn.setVisible(True)
            self._enable_controls(True)
            self.log("机器人连接成功！")

            # 同步 robot_client 到硬件管理器
            if self.connection_thread and self.connection_thread.client:
                self.hw_manager.robot_client = self.connection_thread.client
                self.hw_manager.is_robot_connected = True

            # 设置WiFi回调
            if self.hw_manager.robot_client:
                self.hw_manager.robot_client.on_wifi_scanned = self._on_wifi_scanned
                self.hw_manager.robot_client.on_wifi_saved = self._on_wifi_saved
        else:
            self.status_label.setText("🔴 连接失败")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #721c24;")
            self.connect_btn.setEnabled(True)
            self.log("机器人连接失败")

    def disconnect_robot(self):
        """断开机器人连接"""
        if self.connection_thread:
            self.connection_thread.disconnect()
            self.connection_thread = None

        self.hw_manager.disconnect_robot()

        self.status_label.setText("🔴 未连接")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #856404;")
        self.connect_btn.setVisible(True)
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setVisible(False)
        self._enable_controls(False)
        self.log("已断开机器人连接")

    # ========== WiFi配网相关 ==========

    def scan_wifi(self):
        """扫描机器人周围的WiFi网络（异步）"""
        if not self.hw_manager.is_robot_connected or not self.hw_manager.robot_client:
            QMessageBox.information(
                self, "提示",
                "请先点击上方\"连接设备\"按钮连接到机器人。\n\n"
                "机器人IP默认: 192.168.4.1"
            )
            return

        self.wifi_scan_btn.setEnabled(False)
        self.wifi_scan_btn.setText("扫描中...")
        self.wifi_list.clear()
        self.log("正在扫描机器人周围的WiFi...")

        # 使用QTimer延迟执行，避免阻塞
        QTimer.singleShot(100, self._do_wifi_scan_async)

    def _do_wifi_scan_async(self):
        """异步执行WiFi扫描"""
        try:
            result = self.hw_manager.scan_robot_wifi()
            # 扫描完成后在主线程更新UI
            if result:
                self._on_wifi_scanned(result)
            else:
                self.wifi_scan_btn.setEnabled(True)
                self.wifi_scan_btn.setText("📡 扫描WiFi")
                self.log("WiFi扫描失败或超时")
        except Exception as e:
            self.wifi_scan_btn.setEnabled(True)
            self.wifi_scan_btn.setText("📡 扫描WiFi")
            self.log(f"WiFi扫描出错: {e}")

    def _on_wifi_scanned(self, networks: list):
        """WiFi扫描结果回调"""
        self.wifi_scan_btn.setEnabled(True)
        self.wifi_scan_btn.setText("📡 扫描WiFi")
        self.wifi_list.clear()

        if not networks:
            self.log("未扫描到WiFi网络")
            return

        # 按信号强度排序
        networks_sorted = sorted(networks, key=lambda x: x.get("rssi", -100), reverse=True)

        for net in networks_sorted:
            ssid = net.get("ssid", "Unknown")
            rssi = net.get("rssi", -100)
            enc = net.get("enc", "open")

            # 信号强度图标
            if rssi > -50:
                signal = "📶📶📶📶"
            elif rssi > -70:
                signal = "📶📶📶"
            elif rssi > -85:
                signal = "📶📶"
            else:
                signal = "📶"

            lock = "🔒" if enc == "secure" else "🔓"
            item_text = f"{signal}{lock}  {ssid}  ({rssi}dBm)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, ssid)
            self.wifi_list.addItem(item)

        self.log(f"扫描完成，共发现 {len(networks)} 个WiFi网络")

    def on_wifi_selected(self):
        """WiFi列表选中事件"""
        item = self.wifi_list.currentItem()
        if item:
            ssid = item.data(Qt.ItemDataRole.UserRole)
            self.wifi_password_input.setFocus()
            self.wifi_config_btn.setEnabled(True)

    def toggle_wifi_pwd_visible(self, checked: bool):
        """切换密码可见"""
        if checked:
            self.wifi_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.wifi_show_pwd_btn.setText("🙈")
        else:
            self.wifi_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.wifi_show_pwd_btn.setText("👁")

    def configure_wifi(self):
        """配置WiFi"""
        if not self.hw_manager.is_robot_connected or not self.hw_manager.robot_client:
            QMessageBox.information(
                self, "提示",
                "请先点击上方\"连接设备\"按钮连接到机器人。\n\n"
                "机器人IP默认: 192.168.4.1"
            )
            return

        item = self.wifi_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个WiFi网络")
            return

        ssid = item.data(Qt.ItemDataRole.UserRole)
        password = self.wifi_password_input.text().strip()

        if not password:
            reply = QMessageBox.question(
                self, "确认",
                f"WiFi '{ssid}' 似乎没有密码？\n\n确定使用空密码连接吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.log(f"正在配置WiFi: {ssid}...")
        self.wifi_config_btn.setEnabled(False)
        self.wifi_config_btn.setText("配置中...")
        self.hw_manager.set_robot_wifi(ssid, password)

    def _on_wifi_saved(self, data: dict):
        """WiFi配置保存回调"""
        message = data.get("message", "")
        self.log(f"WiFi配置: {message}")
        self.wifi_config_btn.setText("🔗 配置WiFi并重启")

        QMessageBox.information(
            self, "WiFi配置",
            f"✅ {message}\n\n"
            "机器人正在重启...\n"
            "重启后机器人将连接到新WiFi。\n"
            "请等待约30秒后重新搜索设备。"
        )

        # 机器人即将重启断开，更新状态
        self.status_label.setText("🔴 重启中...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #856404;")
        self.disconnect_btn.setVisible(False)
        self.connect_btn.setVisible(True)
        self.connect_btn.setEnabled(True)
        self._enable_controls(False)

    def _enable_controls(self, enabled: bool):
        """启用/禁用控制按钮"""
        self.self_test_btn.setEnabled(enabled)
        self.wave_left_btn.setEnabled(enabled)
        self.wave_right_btn.setEnabled(enabled)
        self.dance_btn.setEnabled(enabled)
        self.volume_slider.setEnabled(enabled)
        self.left_hand_slider.setEnabled(enabled)
        self.right_hand_slider.setEnabled(enabled)
        self.head_slider.setEnabled(enabled)

    def run_self_test(self):
        """运行设备自检"""
        self.log("开始设备自检...")
        self.hw_manager.self_test()

    def flash_firmware(self):
        """刷写固件 - 使用tools.py中的arduino-cli工具"""
        reply = QMessageBox.question(
            self, "固件刷写",
            "这将自动编译并上传机器人固件到ESP32S3。\n"
            "请确保：\n"
            "1. ESP32S3已通过USB连接到电脑\n"
            "2. 已安装CH340/CP210x等USB转串口驱动\n\n"
            "是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 获取固件目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        firmware_dir = os.path.join(current_dir, "firmware")

        if not os.path.exists(firmware_dir):
            QMessageBox.critical(self, "错误", f"固件目录不存在:\n{firmware_dir}")
            return

        # 先检测可用的端口
        self.log("检测可用的开发板端口...")
        try:
            from tools import Tools
            tools = Tools(memory=None)
            detect_result = tools.auto_detect_board_and_port()

            selected_port = None

            if detect_result.startswith("SUCCESS"):
                # 解析检测到的端口
                ports = []
                lines = detect_result.strip().split('\n')[1:]  # 跳过第一行
                for line in lines:
                    if '->' in line:
                        parts = line.split('->')
                        port = parts[0].strip()
                        fqbn = parts[1].strip() if len(parts) > 1 else 'Unknown'
                        ports.append({'port': port, 'fqbn': fqbn})

                if len(ports) == 0:
                    QMessageBox.warning(
                        self, "未检测到开发板",
                        "未检测到ESP32S3开发板。\n\n"
                        "请检查:\n"
                        "1. ESP32S3是否通过USB连接到电脑\n"
                        "2. USB驱动是否已安装\n"
                        "3. 是否有其他程序占用串口"
                    )
                    return
                elif len(ports) == 1:
                    selected_port = ports[0]['port']
                    self.log(f"自动选择端口: {selected_port}")
                else:
                    # 多个端口，显示选择对话框
                    dialog = PortSelectionDialog(ports, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        selected_port = dialog.get_selected_port()
                        if selected_port:
                            self.log(f"用户选择端口: {selected_port}")
                    else:
                        self.log("用户取消端口选择")
                        return
            else:
                QMessageBox.warning(
                    self, "检测失败",
                    f"无法检测开发板端口:\n{detect_result}\n\n"
                    "请确保ESP32S3已正确连接。"
                )
                return

            if not selected_port:
                QMessageBox.warning(self, "未选择端口", "请选择一个端口进行刷写。")
                return

            # 创建并显示进度对话框
            self.flash_dialog = FirmwareFlashDialog(self)
            self.flash_dialog.show()

            # 启动刷写线程
            self.flash_thread = FirmwareFlashThread(firmware_dir, port=selected_port)
            self.flash_thread.log_signal.connect(self.flash_dialog.add_log)
            self.flash_thread.progress_signal.connect(self.flash_dialog.update_progress)
            self.flash_thread.step_signal.connect(self.flash_dialog.update_step)
            self.flash_thread.finished_signal.connect(self.on_flash_finished)

            # 连接取消按钮
            self.flash_dialog.cancel_btn.clicked.connect(self.cancel_flash)

            self.flash_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动刷写失败: {str(e)}")

    def cancel_flash(self):
        """取消刷写"""
        if self.flash_thread and self.flash_thread.isRunning():
            self.flash_thread.stop()
            self.flash_thread.wait(1000)
        if self.flash_dialog:
            self.flash_dialog.reject()

    def on_flash_finished(self, success: bool, message: str):
        """刷写完成回调"""
        if self.flash_dialog:
            self.flash_dialog.set_finished(success)

        if success:
            QMessageBox.information(
                self, "成功",
                "✅ 固件刷写完成！\n\n"
                "机器人将自动重启。\n"
                "重启后请使用'开始发现'功能连接机器人。"
            )
        else:
            QMessageBox.critical(
                self, "失败",
                f"❌ 固件刷写失败:\n{message}\n\n"
                f"请检查:\n"
                f"1. ESP32S3是否正确连接\n"
                f"2. USB驱动是否安装\n"
                f"3. 是否有其他程序占用串口\n"
                f"4. 端口选择是否正确"
            )

    def perform_action(self, action: str):
        """执行预设动作"""
        self.log(f"执行动作: {action}")
        self.hw_manager.perform_action(action)

    def on_volume_changed(self, value: int):
        """音量改变"""
        self.volume_label.setText(f"{value}%")
        self.hw_manager.set_volume(value)

    def on_servo_changed(self, servo_name: str, value: int):
        """舵机角度改变"""
        if servo_name == "left_hand":
            self.left_hand_label.setText(f"{value}°")
        elif servo_name == "right_hand":
            self.right_hand_label.setText(f"{value}°")
        elif servo_name == "head":
            self.head_label.setText(f"{value}°")

        self.hw_manager.control_servo(servo_name, value)
