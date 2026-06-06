import os
import json
import subprocess
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QProgressBar, QHeaderView
)
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QPixmap, QFont

from hardware_detector import HardwareDetector
from local_model_manager import LocalModelManager

CONFIG_FILE = os.path.expanduser("~/.agent_config.json")

STYLE_QSS = """
QDialog {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QLabel {
    color: #e0e0e0;
}
QPushButton {
    background-color: #3a7bd5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #4a8de5;
}
QPushButton:pressed {
    background-color: #2a6bc5;
}
QLineEdit {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 13px;
}
QComboBox {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 13px;
}
QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    color: #e0e0e0;
    selection-background-color: #3a7bd5;
}
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}
QTableWidget {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    gridline-color: #555555;
    font-size: 12px;
}
QTableWidget::item {
    padding: 4px;
}
QHeaderView::section {
    background-color: #444444;
    color: #e0e0e0;
    border: 1px solid #555555;
    padding: 6px;
    font-weight: bold;
}
QProgressBar {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #3a7bd5;
    border-radius: 3px;
}
"""


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(STYLE_QSS)
    wizard = ConfigWizard()
    if wizard.exec() == QDialog.DialogCode.Accepted:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}


class ConfigWizard(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TG helper - 首次配置向导")
        self.setFixedSize(800, 600)

        self.config = {}
        self.hardware_grade = HardwareDetector.get_grade()
        self.hardware_info = {
            "cpu": HardwareDetector.get_cpu_info(),
            "memory": HardwareDetector.get_memory_gb(),
            "gpu": HardwareDetector.get_gpu_info(),
            "grade": self.hardware_grade
        }

        try:
            with open(os.path.join(BASE_DIR, "model_recommendations.json"), 'r', encoding='utf-8') as f:
                self.model_recs = json.load(f)
        except:
            self.model_recs = {}
        self.recommended_models = self.model_recs.get(self.hardware_grade, [])

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.current_widget = None
        self.deploy_dialog = None

        self.show_welcome()

    def clear_frame(self):
        if self.current_widget:
            self.main_layout.removeWidget(self.current_widget)
            self.current_widget.deleteLater()
            self.current_widget = None

    def show_welcome(self):
        self.clear_frame()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_path = os.path.join("icon", "TGAI.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    150, 150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label = QLabel()
                icon_label.setPixmap(pixmap)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(icon_label)
                layout.addSpacing(20)

        title = QLabel("TG HELPER")
        title.setFont(QFont("微软雅黑", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(10)

        welcome_text = QLabel("欢迎使用 TG helper！\n您的全能AI私人助手")
        welcome_text.setFont(QFont("微软雅黑", 12))
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_text)
        layout.addSpacing(20)

        btn = QPushButton("开始配置")
        btn.setFixedSize(200, 50)
        btn.clicked.connect(self.show_hardware_info)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(widget)
        self.current_widget = widget

    def show_hardware_info(self):
        self.clear_frame()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("硬件检测结果")
        title.setFont(QFont("微软雅黑", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(10)

        info_text = (
            f"CPU: {self.hardware_info['cpu']['name']}\n"
            f"核心数: {self.hardware_info['cpu']['cores']}\n"
            f"内存: {self.hardware_info['memory']:.1f} GB\n"
            f"GPU: {self.hardware_info['gpu']['name']}\n"
            f"显存: {self.hardware_info['gpu']['memory_mb']:.0f} MB\n"
            f"硬件等级: {self.hardware_info['grade'].upper()}"
        )
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(info_label)
        layout.addSpacing(10)

        model_title = QLabel("推荐部署的本地模型:")
        model_title.setFont(QFont("微软雅黑", 10, QFont.Weight.Bold))
        layout.addWidget(model_title)
        layout.addSpacing(5)

        table = QTableWidget(len(self.recommended_models), 3)
        table.setHorizontalHeaderLabels(["模型名称", "参数规模", "推荐内存(GB)"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setMaximumHeight(150)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for row, model in enumerate(self.recommended_models):
            table.setItem(row, 0, QTableWidgetItem(model["name"]))
            table.setItem(row, 1, QTableWidgetItem(model["size"]))
            table.setItem(row, 2, QTableWidgetItem(str(model["ram"])))
        layout.addWidget(table)
        layout.addSpacing(10)

        btn = QPushButton("下一步")
        btn.clicked.connect(self.show_model_selection)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(widget)
        self.current_widget = widget

    def show_model_selection(self):
        self.clear_frame()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("选择默认模型")
        title.setFont(QFont("微软雅黑", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(10)

        self.model_combo = QComboBox()
        self.model_combo.addItems([m["name"] for m in self.recommended_models])
        if self.recommended_models:
            self.model_combo.setCurrentIndex(0)
        self.model_combo.setFixedWidth(350)
        layout.addWidget(self.model_combo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

        label = QLabel("是否一键部署本地模型？")
        layout.addWidget(label)
        self.deploy_check = QCheckBox("是，立即部署")
        self.deploy_check.setChecked(True)
        layout.addWidget(self.deploy_check)
        layout.addSpacing(20)

        btn = QPushButton("下一步")
        btn.clicked.connect(self.show_api_config)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(widget)
        self.current_widget = widget

    def show_api_config(self):
        # 在清除页面之前，先保存上一页的模型选择状态
        self._saved_model = self.model_combo.currentText()
        self._saved_deploy = self.deploy_check.isChecked()
        self.clear_frame()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("API 配置（云端模型）")
        title.setFont(QFont("微软雅黑", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("API Key:"), 0, 0)
        self.api_key_entry = QLineEdit()
        self.api_key_entry.setMinimumWidth(300)
        grid.addWidget(self.api_key_entry, 0, 1)

        grid.addWidget(QLabel("Base URL:"), 1, 0)
        self.base_url_entry = QLineEdit()
        self.base_url_entry.setMinimumWidth(300)
        grid.addWidget(self.base_url_entry, 1, 1)

        grid.addWidget(QLabel("模型名称:"), 2, 0)
        self.model_entry = QLineEdit()
        self.model_entry.setMinimumWidth(300)
        grid.addWidget(self.model_entry, 2, 1)

        layout.addLayout(grid)
        layout.addSpacing(20)

        btn = QPushButton("完成配置")
        btn.clicked.connect(self.finish_config)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(widget)
        self.current_widget = widget

    def finish_config(self):
        self.config["ai_api_key"] = self.api_key_entry.text()
        self.config["ai_base_url"] = self.base_url_entry.text()
        self.config["ai_model"] = self.model_entry.text()
        self.config["local_model"] = self._saved_model
        self.config["local_model_deploy"] = self._saved_deploy
        self.config["hardware_grade"] = self.hardware_grade

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

        if self._saved_deploy:
            self.start_deploy()
        else:
            self.launch_main()

    def start_deploy(self):
        self.deploy_dialog = QDialog(self)
        self.deploy_dialog.setWindowTitle("部署本地模型")
        self.deploy_dialog.setFixedSize(400, 300)

        deploy_layout = QVBoxLayout(self.deploy_dialog)

        model_name = self._saved_model
        label = QLabel(f"正在部署 {model_name}...")
        label.setFont(QFont("微软雅黑", 12))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        deploy_layout.addWidget(label)
        deploy_layout.addSpacing(20)

        self.deploy_progress = QProgressBar()
        self.deploy_progress.setRange(0, 0)
        self.deploy_progress.setFixedWidth(300)
        deploy_layout.addWidget(self.deploy_progress, alignment=Qt.AlignmentFlag.AlignCenter)
        deploy_layout.addSpacing(10)

        self.deploy_status_label = QLabel("下载中...")
        self.deploy_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        deploy_layout.addWidget(self.deploy_status_label)
        deploy_layout.addSpacing(10)

        self._deploy_layout = deploy_layout

        def deploy_callback(success, result):
            QMetaObject.invokeMethod(
                self,
                "_on_deploy_finished",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, success),
                Q_ARG(str, str(result))
            )

        manager = LocalModelManager()
        threading.Thread(
            target=lambda: manager.deploy_model(
                self._saved_model,
                callback=deploy_callback
            ),
            daemon=True
        ).start()

        self.deploy_dialog.exec()

    @pyqtSlot(bool, str)
    def _on_deploy_finished(self, success, result):
        self.deploy_progress.setRange(0, 100)
        self.deploy_progress.setValue(100)
        if success:
            self.deploy_status_label.setText("部署成功！")
            btn = QPushButton("启动主程序")
            btn.clicked.connect(lambda: self.launch_main_after_deploy(self.deploy_dialog))
            self._deploy_layout.addWidget(btn)
        else:
            self.deploy_status_label.setText(f"部署失败: {result}")
            btn = QPushButton("跳过，启动主程序")
            btn.clicked.connect(lambda: self.launch_main_after_deploy(self.deploy_dialog))
            self._deploy_layout.addWidget(btn)

    def launch_main_after_deploy(self, win):
        win.close()
        self.launch_main()

    def launch_main(self):
        self.accept()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(base_dir, "main_gui.py")
        if not os.path.exists(main_script):
            main_script = os.path.join(base_dir, "TG HELPER.py")
            args = [sys.executable, main_script, "--skip-launcher"]
        else:
            args = [sys.executable, main_script]
        subprocess.Popen(args)
        sys.exit(0)
