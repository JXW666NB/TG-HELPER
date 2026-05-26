# -*- coding: utf-8 -*-
"""
TG Home - 物联网设备管理 (PyQt6 现代 UI 版本)
可独立运行，也可从主 GUI 中打开
"""
import json
import os
import sys
import subprocess
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QTabWidget, QCheckBox, QRadioButton,
    QSpinBox, QScrollArea, QTextEdit, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QMenu, QSplitter, QDialog,
    QMessageBox, QFileDialog, QFrame, QApplication, QMainWindow,
    QAbstractItemView, QHeaderView, QSizePolicy, QStackedWidget,
    QButtonGroup, QGraphicsDropShadowEffect, QProgressBar, QToolButton,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QRect, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QPixmap, QCursor, QFont, QColor, QPalette, QIcon, QAction, QPainter,
    QPainterPath, QFontDatabase
)

# 确保必要的库已安装
try:
    import paho.mqtt.client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt"])
    import paho.mqtt.client

# 导入项目模块
from IOT_manager import iot_manager, IOTDevice, IOTSensor, IOTTrigger
from iot_logger import iot_logger
from smart_inspector import inspector

# 尝试导入配置，若失败则使用默认值
try:
    from config import config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    class DummyConfig:
        gui_theme = "dark"
        napcat_http_url = ""
        napcat_access_token = ""
        qq_enabled = False
        qq_bot_uin = ""
        qq_whitelist = ""
        inspector_enabled = True
        inspector_interval = 3600
    config = DummyConfig()


# ────────────── 现代暗色主题 QSS ──────────────
DARK_QSS = """
QWidget {
    background-color: #1a1a2e;
    color: #e8e8e8;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #1a1a2e;
}
QTabWidget::pane {
    border: none;
    background-color: #1a1a2e;
}
QTabBar::tab {
    background-color: transparent;
    color: #8b8ba7;
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 8px;
    font-weight: 500;
}
QTabBar::tab:selected {
    color: #4a90d9;
    border-bottom: 2px solid #4a90d9;
}
QTabBar::tab:hover:!selected {
    color: #c0c0d0;
}
QLabel {
    background: transparent;
}
QPushButton {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a3a5e;
    border-radius: 10px;
    padding: 8px 18px;
    min-height: 32px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #1e2f52;
    border-color: #3a4a6e;
}
QPushButton:pressed {
    background-color: #0f3460;
}
QPushButton[cssClass="success"] {
    background-color: #27ae60;
    border-color: #27ae60;
    color: #fff;
}
QPushButton[cssClass="success"]:hover {
    background-color: #2ecc71;
    border-color: #2ecc71;
}
QPushButton[cssClass="danger"] {
    background-color: #e74c3c;
    border-color: #e74c3c;
    color: #fff;
}
QPushButton[cssClass="danger"]:hover {
    background-color: #ff6b6b;
    border-color: #ff6b6b;
}
QPushButton[cssClass="primary"] {
    background-color: #4a90d9;
    border-color: #4a90d9;
    color: #fff;
}
QPushButton[cssClass="primary"]:hover {
    background-color: #5aa0e9;
    border-color: #5aa0e9;
}
QPushButton[cssClass="warning"] {
    background-color: #f39c12;
    border-color: #f39c12;
    color: #fff;
}
QPushButton[cssClass="warning"]:hover {
    background-color: #f1c40f;
    border-color: #f1c40f;
}
QPushButton[cssClass="success-outline"] {
    background-color: transparent;
    border: 1px solid #27ae60;
    color: #27ae60;
}
QPushButton[cssClass="success-outline"]:hover {
    background-color: #27ae60;
    color: #fff;
}
QPushButton[cssClass="info-outline"] {
    background-color: transparent;
    border: 1px solid #4a90d9;
    color: #4a90d9;
}
QPushButton[cssClass="info-outline"]:hover {
    background-color: #4a90d9;
    color: #fff;
}
QPushButton[cssClass="warning-outline"] {
    background-color: transparent;
    border: 1px solid #f39c12;
    color: #f39c12;
}
QPushButton[cssClass="warning-outline"]:hover {
    background-color: #f39c12;
    color: #fff;
}
QPushButton[cssClass="secondary-outline"] {
    background-color: transparent;
    border: 1px solid #5a5a7a;
    color: #8b8ba7;
}
QPushButton[cssClass="secondary-outline"]:hover {
    background-color: #5a5a7a;
    color: #fff;
}
QPushButton[cssClass="primary-outline"] {
    background-color: transparent;
    border: 1px solid #4a90d9;
    color: #4a90d9;
}
QPushButton[cssClass="primary-outline"]:hover {
    background-color: #4a90d9;
    color: #fff;
}
QPushButton[cssClass="danger-outline"] {
    background-color: transparent;
    border: 1px solid #e74c3c;
    color: #e74c3c;
}
QPushButton[cssClass="danger-outline"]:hover {
    background-color: #e74c3c;
    color: #fff;
}
QPushButton:disabled {
    background-color: #2a2a3e;
    color: #555;
    border-color: #333;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a3a5e;
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 28px;
}
QComboBox::drop-down {
    border: none;
    background-color: #0f3460;
    width: 28px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e8e8e8;
    selection-background-color: #4a90d9;
    outline: none;
    border: 1px solid #2a3a5e;
    border-radius: 8px;
}
QTextEdit {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a3a5e;
    border-radius: 8px;
    padding: 6px;
}
QTableWidget {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a3a5e;
    gridline-color: #2a3a5e;
    alternate-background-color: #1a1a2e;
    border-radius: 12px;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #2a3a5e;
}
QHeaderView::section {
    background-color: #0f3460;
    color: #e8e8e8;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid #4a90d9;
    font-weight: 600;
}
QListWidget {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a3a5e;
    border-radius: 8px;
    padding: 4px;
}
QListWidget::item {
    padding: 6px;
    border-radius: 6px;
    margin: 2px 0px;
}
QListWidget::item:selected {
    background-color: #4a90d9;
    color: #fff;
}
QListWidget::item:hover {
    background-color: #1e2f52;
}
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 8px;
    border: none;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background-color: #3a3a5e;
    min-height: 40px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background-color: #4a4a7e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #1a1a2e;
    height: 8px;
    border: none;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background-color: #3a3a5e;
    min-width: 40px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #4a4a7e;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QCheckBox, QRadioButton {
    background-color: transparent;
    color: #e8e8e8;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #4a90d9;
    border-radius: 6px;
    background-color: #16213e;
}
QCheckBox::indicator:checked {
    background-color: #4a90d9;
    border-color: #4a90d9;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #4a90d9;
    border-radius: 9px;
    background-color: #16213e;
}
QRadioButton::indicator:checked {
    background-color: #4a90d9;
    border-color: #4a90d9;
}
QSplitter::handle {
    background-color: #2a3a5e;
    width: 4px;
    height: 4px;
    border-radius: 2px;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #0f3460;
    border: none;
    width: 20px;
    border-radius: 4px;
}
QFrame[cssClass="card"] {
    border: 1px solid #2a3a5e;
    border-radius: 12px;
    background-color: #16213e;
}
QFrame[cssClass="group-frame"] {
    border: 1px solid #2a3a5e;
    border-radius: 12px;
    background-color: #16213e;
    padding: 8px;
}
QFrame[cssClass="stat-card"] {
    border: 1px solid #2a3a5e;
    border-radius: 16px;
    background-color: #16213e;
}
QFrame[cssClass="sidebar"] {
    border: none;
    border-right: 1px solid #2a3a5e;
    background-color: #16213e;
}
QFrame[cssClass="toolbar"] {
    border: none;
    border-bottom: 1px solid #2a3a5e;
    background-color: #16213e;
}
QFrame[cssClass="glass-panel"] {
    border: 1px solid #2a3a5e;
    border-radius: 16px;
    background-color: rgba(22, 33, 62, 180);
}
QProgressBar {
    border: 1px solid #2a3a5e;
    border-radius: 8px;
    background-color: #16213e;
    text-align: center;
    font-weight: 500;
}
QProgressBar::chunk {
    background-color: #4a90d9;
    border-radius: 8px;
}
QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 8px;
    color: #8b8ba7;
    font-weight: 500;
}
QToolButton:hover {
    background-color: #1e2f52;
    color: #e8e8e8;
}
QToolButton:pressed {
    background-color: #0f3460;
}
QDialog {
    background-color: #1a1a2e;
}
"""

LIGHT_QSS = """
QWidget {
    background-color: #f0f2f5;
    color: #2c3e50;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #f0f2f5;
}
QTabWidget::pane {
    border: none;
    background-color: #f0f2f5;
}
QTabBar::tab {
    background-color: transparent;
    color: #7f8c8d;
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 8px;
    font-weight: 500;
}
QTabBar::tab:selected {
    color: #4a90d9;
    border-bottom: 2px solid #4a90d9;
}
QTabBar::tab:hover:!selected {
    color: #5a6a7a;
}
QLabel {
    background: transparent;
}
QPushButton {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 8px 18px;
    min-height: 32px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #f5f5f5;
    border-color: #ccc;
}
QPushButton:pressed {
    background-color: #e8e8e8;
}
QPushButton[cssClass="success"] {
    background-color: #27ae60;
    border-color: #27ae60;
    color: #fff;
}
QPushButton[cssClass="success"]:hover {
    background-color: #2ecc71;
    border-color: #2ecc71;
}
QPushButton[cssClass="danger"] {
    background-color: #e74c3c;
    border-color: #e74c3c;
    color: #fff;
}
QPushButton[cssClass="danger"]:hover {
    background-color: #ff6b6b;
    border-color: #ff6b6b;
}
QPushButton[cssClass="primary"] {
    background-color: #4a90d9;
    border-color: #4a90d9;
    color: #fff;
}
QPushButton[cssClass="primary"]:hover {
    background-color: #5aa0e9;
    border-color: #5aa0e9;
}
QPushButton[cssClass="warning"] {
    background-color: #f39c12;
    border-color: #f39c12;
    color: #fff;
}
QPushButton[cssClass="warning"]:hover {
    background-color: #f1c40f;
    border-color: #f1c40f;
}
QPushButton[cssClass="success-outline"] {
    background-color: transparent;
    border: 1px solid #27ae60;
    color: #27ae60;
}
QPushButton[cssClass="success-outline"]:hover {
    background-color: #27ae60;
    color: #fff;
}
QPushButton[cssClass="info-outline"] {
    background-color: transparent;
    border: 1px solid #4a90d9;
    color: #4a90d9;
}
QPushButton[cssClass="info-outline"]:hover {
    background-color: #4a90d9;
    color: #fff;
}
QPushButton[cssClass="warning-outline"] {
    background-color: transparent;
    border: 1px solid #f39c12;
    color: #f39c12;
}
QPushButton[cssClass="warning-outline"]:hover {
    background-color: #f39c12;
    color: #fff;
}
QPushButton[cssClass="secondary-outline"] {
    background-color: transparent;
    border: 1px solid #95a5a6;
    color: #7f8c8d;
}
QPushButton[cssClass="secondary-outline"]:hover {
    background-color: #95a5a6;
    color: #fff;
}
QPushButton[cssClass="primary-outline"] {
    background-color: transparent;
    border: 1px solid #4a90d9;
    color: #4a90d9;
}
QPushButton[cssClass="primary-outline"]:hover {
    background-color: #4a90d9;
    color: #fff;
}
QPushButton[cssClass="danger-outline"] {
    background-color: transparent;
    border: 1px solid #e74c3c;
    color: #e74c3c;
}
QPushButton[cssClass="danger-outline"]:hover {
    background-color: #e74c3c;
    color: #fff;
}
QPushButton:disabled {
    background-color: #eee;
    color: #aaa;
    border-color: #ddd;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 28px;
}
QComboBox::drop-down {
    border: none;
    background-color: #e8e8e8;
    width: 28px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #2c3e50;
    selection-background-color: #4a90d9;
    outline: none;
    border: 1px solid #ddd;
    border-radius: 8px;
}
QTextEdit {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 6px;
}
QTableWidget {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #ddd;
    gridline-color: #eee;
    alternate-background-color: #f9f9f9;
    border-radius: 12px;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #eee;
}
QHeaderView::section {
    background-color: #f0f0f0;
    color: #2c3e50;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid #4a90d9;
    font-weight: 600;
}
QListWidget {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 4px;
}
QListWidget::item {
    padding: 6px;
    border-radius: 6px;
    margin: 2px 0px;
}
QListWidget::item:selected {
    background-color: #4a90d9;
    color: #fff;
}
QListWidget::item:hover {
    background-color: #f0f0f0;
}
QScrollArea {
    border: none;
}
QCheckBox, QRadioButton {
    background-color: transparent;
    color: #2c3e50;
    spacing: 10px;
}
QSplitter::handle {
    background-color: #ccc;
    width: 4px;
    height: 4px;
    border-radius: 2px;
}
QFrame[cssClass="card"] {
    border: 1px solid #ddd;
    border-radius: 12px;
    background-color: #ffffff;
}
QFrame[cssClass="group-frame"] {
    border: 1px solid #ddd;
    border-radius: 12px;
    background-color: #ffffff;
    padding: 8px;
}
QFrame[cssClass="stat-card"] {
    border: 1px solid #ddd;
    border-radius: 16px;
    background-color: #ffffff;
}
QFrame[cssClass="sidebar"] {
    border: none;
    border-right: 1px solid #ddd;
    background-color: #ffffff;
}
QFrame[cssClass="toolbar"] {
    border: none;
    border-bottom: 1px solid #ddd;
    background-color: #ffffff;
}
QFrame[cssClass="glass-panel"] {
    border: 1px solid #ddd;
    border-radius: 16px;
    background-color: rgba(255, 255, 255, 220);
}
QProgressBar {
    border: 1px solid #ddd;
    border-radius: 8px;
    background-color: #ffffff;
    text-align: center;
    font-weight: 500;
}
QProgressBar::chunk {
    background-color: #4a90d9;
    border-radius: 8px;
}
QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 8px;
    color: #7f8c8d;
    font-weight: 500;
}
QToolButton:hover {
    background-color: #f0f0f0;
    color: #2c3e50;
}
QToolButton:pressed {
    background-color: #e0e0e0;
}
QDialog {
    background-color: #f0f2f5;
}
"""


def _make_btn(text, css_class, callback, parent=None):
    """创建带 CSS class 属性的按钮"""
    btn = QPushButton(text, parent)
    btn.setProperty("cssClass", css_class)
    btn.clicked.connect(callback)
    btn.setStyleSheet("")  # 触发属性重绘
    return btn


def _make_tool_btn(icon_text, label, color, callback, parent=None):
    """创建现代工具栏按钮（图标+文字垂直排列）"""
    btn = QToolButton(parent)
    btn.setText(label)
    btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    btn.setFixedSize(72, 64)
    btn.setStyleSheet(f"""
        QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: 12px;
            color: {color};
            font-size: 11px;
            font-weight: 500;
            padding: 4px;
        }}
        QToolButton:hover {{
            background-color: rgba(74, 144, 217, 30);
            color: {color};
        }}
        QToolButton:pressed {{
            background-color: rgba(74, 144, 217, 60);
        }}
    """)
    # 使用 QLabel 风格绘制图标文字
    btn.setProperty("icon_text", icon_text)
    btn.clicked.connect(callback)
    return btn


class IconLabel(QLabel):
    """可绘制简单几何图标的标签"""
    def __init__(self, icon_type="device", size=64, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)

        if self.icon_type == "device":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#4a90d9"))
            painter.drawRoundedRect(rect, 12, 12)
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(rect.adjusted(16, 20, -16, -20), 4, 4)
            painter.drawEllipse(rect.center().x() - 6, rect.top() + 12, 12, 12)
        elif self.icon_type == "sensor":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#27ae60"))
            painter.drawEllipse(rect.center(), rect.width() // 2 - 4, rect.height() // 2 - 4)
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(rect.center(), 8, 8)
            painter.setPen(QColor("#27ae60"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect.center(), rect.width() // 2 - 12, rect.height() // 2 - 12)
        elif self.icon_type == "trigger":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#f39c12"))
            path = QPainterPath()
            cx, cy = rect.center().x(), rect.center().y()
            path.moveTo(cx, rect.top() + 8)
            path.lineTo(cx + 16, cy + 8)
            path.lineTo(cx + 6, cy + 8)
            path.lineTo(cx + 10, rect.bottom() - 8)
            path.lineTo(cx - 10, cy - 4)
            path.lineTo(cx, cy - 4)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#7f8c8d"))
            painter.drawRoundedRect(rect, 12, 12)
        painter.end()


class StatusBadge(QLabel):
    """彩色状态标签（药丸形状）"""
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            background-color: {color}22;
            color: {color};
            border: 1px solid {color}44;
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.setFixedHeight(22)


class ModernCard(QFrame):
    """现代卡片组件，带悬停阴影动画"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("cssClass", "card")
        self.setStyleSheet("")
        self.setFixedWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(16)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self._shadow.setOffset(0, 4)
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        self._shadow.setBlurRadius(24)
        self._shadow.setColor(QColor(0, 0, 0, 70))
        self._shadow.setOffset(0, 8)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(16)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self._shadow.setOffset(0, 4)
        super().leaveEvent(event)


class TGHomeApp(QWidget):
    # 信号：线程安全 UI 更新
    status_signal = pyqtSignal(str)
    mqtt_log_signal = pyqtSignal(str)
    topic_update_signal = pyqtSignal(str)
    topic_msg_signal = pyqtSignal(str, str)
    tcp_log_signal = pyqtSignal(str)
    tcp_message_signal = pyqtSignal(str, str)

    def __init__(self, root=None, theme=None):
        super().__init__(root)

        self.root_widget = root
        if root is not None and hasattr(root, 'setWindowTitle'):
            root.setWindowTitle("TG Home - 智能设备管理")
            root.resize(1400, 900)
            root.setMinimumSize(1000, 700)

        if theme is None:
            theme = self._load_theme_from_config()
        self.current_theme = theme

        self.current_pages = {"devices": 0, "sensors": 0, "triggers": 0}
        self.cards_per_page = 25

        # 应用主题样式
        self.apply_theme(theme)

        # 连接信号
        self.status_signal.connect(lambda txt: self.status_label.setText(txt))
        self.mqtt_log_signal.connect(self._on_mqtt_log)
        self.topic_update_signal.connect(self._on_topic_list_update)
        self.topic_msg_signal.connect(self._on_topic_msg_update)
        self.tcp_log_signal.connect(self._on_tcp_log)
        self.tcp_message_signal.connect(self._on_tcp_message)

        # 主布局
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建左侧边栏
        self._create_sidebar()

        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self._create_toolbar()
        self._create_notebook()
        self._refresh_all()
        self._init_callbacks()

        self.main_layout.addWidget(self.content_widget, 1)

        if not inspector._running:
            inspector.set_ai_callback(self._dummy_ai_callback)
            inspector.set_interval(3600)
            inspector.start()

        if root is not None and hasattr(root, 'setCentralWidget'):
            root.setCentralWidget(self)

    def _load_theme_from_config(self):
        config_file = os.path.expanduser("~/.agent_config.json")
        default_theme = "dark"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("gui_theme", default_theme)
            except:
                pass
        return default_theme

    def _init_callbacks(self):
        iot_manager.set_ai_callback(self._dummy_ai_callback)
        iot_manager.set_ai_trigger_callback(self._dummy_trigger_callback)
        iot_manager.set_qq_send_callback(self._dummy_qq_callback)

    def _dummy_ai_callback(self, prompt, reply_callback=None):
        print(f"[TG Home] AI 回调未连接: {prompt[:50]}...")
        if reply_callback:
            reply_callback("AI 服务未连接，无法处理请求。")

    def _dummy_trigger_callback(self, prompt, reply_callback=None):
        print(f"[TG Home] 触发器回调: {prompt[:50]}...")
        if reply_callback:
            reply_callback("触发器响应：AI 服务未连接。")

    def _dummy_qq_callback(self, target_type, target_id, content):
        print(f"[TG Home] QQ 发送: {target_type} {target_id} -> {content}")

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        if theme_name in ("dark", "darkly", "cyborg", "solar", "superhero"):
            qss = DARK_QSS
            self._is_dark = True
        else:
            qss = LIGHT_QSS
            self._is_dark = False
        self.setStyleSheet(qss)
        if hasattr(self, 'status_label'):
            self._refresh_all()
        if hasattr(self, 'log_table'):
            self.refresh_log_table()

    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setProperty("cssClass", "sidebar")
        sidebar.setStyleSheet("")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(6)

        title = QLabel("🏠 TG Home")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title)

        subtitle = QLabel("智能设备管理")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-top: 4px;")
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(24)

        self.sidebar_buttons = {}
        nav_items = [
            ("dashboard", "📊 仪表盘", 0),
            ("devices", "📱 设备", 1),
            ("sensors", "📡 传感器", 2),
            ("triggers", "⚡ 触发器", 3),
            ("logs", "📋 日志", 4),
            ("ai", "🧠 主动智能", 5),
            ("servers", "🚀 服务器", 6),
        ]

        for key, text, idx in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setProperty("cssClass", "secondary-outline")
            btn.setStyleSheet("")
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 16px;
                    border-radius: 10px;
                    border: none;
                    background-color: transparent;
                    color: #8b8ba7;
                    font-weight: 500;
                }
                QPushButton:checked {
                    background-color: #4a90d922;
                    color: #4a90d9;
                    border-left: 3px solid #4a90d9;
                }
                QPushButton:hover:!checked {
                    background-color: #2a2a4a;
                    color: #c0c0d0;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons[key] = btn

        sidebar_layout.addStretch()

        # 底部状态
        status_frame = QFrame()
        status_frame.setProperty("cssClass", "group-frame")
        status_frame.setStyleSheet("")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 8, 12, 8)
        self.sys_status_dot = QLabel("●")
        self.sys_status_dot.setStyleSheet("color: #27ae60; font-size: 16px;")
        status_layout.addWidget(self.sys_status_dot)
        self.sys_status_text = QLabel("系统在线")
        self.sys_status_text.setStyleSheet("font-size: 12px; color: #7f8c8d; font-weight: 500;")
        status_layout.addWidget(self.sys_status_text)
        status_layout.addStretch()
        sidebar_layout.addWidget(status_frame)

        self.main_layout.addWidget(sidebar)
        self.sidebar = sidebar

    def _switch_tab(self, index):
        self.notebook.setCurrentIndex(index)

    def _create_toolbar(self):
        toolbar = QFrame()
        toolbar.setProperty("cssClass", "toolbar")
        toolbar.setStyleSheet("")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        toolbar_layout.setSpacing(12)

        # 现代图标按钮组
        btn_group = QWidget()
        btn_group_layout = QHBoxLayout(btn_group)
        btn_group_layout.setContentsMargins(0, 0, 0, 0)
        btn_group_layout.setSpacing(8)

        tool_buttons = [
            ("➕", "添加设备", "#27ae60", self.add_device_wizard),
            ("📡", "添加传感器", "#4a90d9", self.add_sensor_wizard),
            ("⚡", "添加触发器", "#f39c12", self.add_trigger_wizard),
            ("🔄", "刷新", "#8b8ba7", self._refresh_all),
            ("📤", "导出", "#8b8ba7", self.export_config),
            ("📥", "导入", "#8b8ba7", self.import_config),
            ("🗑", "重置", "#e74c3c", self.reset_config),
        ]

        for icon, label, color, callback in tool_buttons:
            btn = _make_tool_btn(icon, label, color, callback)
            btn_group_layout.addWidget(btn)

        toolbar_layout.addWidget(btn_group)
        toolbar_layout.addStretch()

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: 500;")
        toolbar_layout.addWidget(self.status_label)

        self.content_layout.addWidget(toolbar)

    def _create_notebook(self):
        self.notebook = QTabWidget()
        self.notebook.tabBar().setVisible(False)
        self.content_layout.addWidget(self.notebook)

        # Dashboard
        self.dashboard_frame = QWidget()
        self.notebook.addTab(self.dashboard_frame, "仪表盘")
        self._create_dashboard(self.dashboard_frame)

        self.devices_frame = QWidget()
        self.notebook.addTab(self.devices_frame, "设备")
        self._create_card_area(self.devices_frame, "devices")

        self.sensors_frame = QWidget()
        self.notebook.addTab(self.sensors_frame, "传感器")
        self._create_card_area(self.sensors_frame, "sensors")

        self.triggers_frame = QWidget()
        self.notebook.addTab(self.triggers_frame, "触发器")
        self._create_card_area(self.triggers_frame, "triggers")

        self.create_log_tab()
        self.create_active_intelligence_tab()
        self.create_servers_tab()

        # 默认选中仪表盘
        self.sidebar_buttons["dashboard"].setChecked(True)

    def _create_dashboard(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 统计卡片行
        stats_row = QWidget()
        stats_layout = QHBoxLayout(stats_row)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)

        self.stat_cards = {}
        stat_defs = [
            ("devices", "📱 设备总数", "#4a90d9", "0"),
            ("sensors", "📡 传感器", "#27ae60", "0"),
            ("triggers", "⚡ 触发器", "#f39c12", "0"),
            ("health", "❤️ 系统健康", "#e74c3c", "良好"),
        ]

        for key, title, color, default_val in stat_defs:
            card = QFrame()
            card.setProperty("cssClass", "stat-card")
            card.setStyleSheet("")
            card.setMinimumHeight(120)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 16, 20, 16)
            card_layout.setSpacing(6)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")
            card_layout.addWidget(title_lbl)

            val_lbl = QLabel(default_val)
            val_font = QFont()
            val_font.setBold(True)
            val_font.setPointSize(28)
            val_lbl.setFont(val_font)
            val_lbl.setStyleSheet("color: #e8e8e8;" if self._is_dark else "color: #2c3e50;")
            card_layout.addWidget(val_lbl)

            stats_layout.addWidget(card, 1)
            self.stat_cards[key] = val_lbl

        layout.addWidget(stats_row)

        # 下方两列
        bottom_split = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：最近活动
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        act_title = QLabel("📋 最近活动")
        act_title_font = QFont()
        act_title_font.setBold(True)
        act_title_font.setPointSize(14)
        act_title.setFont(act_title_font)
        left_layout.addWidget(act_title)

        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(320)
        left_layout.addWidget(self.activity_list)

        bottom_split.addWidget(left_widget)

        # 右侧：快捷操作
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        quick_title = QLabel("⚡ 快捷操作")
        quick_title_font = QFont()
        quick_title_font.setBold(True)
        quick_title_font.setPointSize(14)
        quick_title.setFont(quick_title_font)
        right_layout.addWidget(quick_title)

        quick_grid = QWidget()
        quick_grid_layout = QGridLayout(quick_grid)
        quick_grid_layout.setContentsMargins(0, 0, 0, 0)
        quick_grid_layout.setSpacing(12)

        quick_actions = [
            ("🔄 刷新全部", self._refresh_all),
            ("🔍 立即巡检", self.manual_inspect),
            ("📤 导出配置", self.export_config),
            ("🧹 清空日志", self.clear_logs),
        ]

        for i, (text, callback) in enumerate(quick_actions):
            btn = _make_btn(text, "primary-outline", callback)
            btn.setMinimumHeight(56)
            btn.setStyleSheet(btn.styleSheet() + "font-size: 14px; font-weight: 500;")
            quick_grid_layout.addWidget(btn, i // 2, i % 2)

        right_layout.addWidget(quick_grid)
        right_layout.addStretch()

        bottom_split.addWidget(right_widget)
        bottom_split.setSizes([500, 500])

        layout.addWidget(bottom_split, 1)

    def _update_dashboard(self):
        self.stat_cards["devices"].setText(str(len(iot_manager.devices)))
        self.stat_cards["sensors"].setText(str(len(iot_manager.sensors)))
        self.stat_cards["triggers"].setText(str(len(iot_manager.triggers)))

        health = "良好" if len(iot_manager.devices) > 0 or len(iot_manager.sensors) > 0 else "空闲"
        self.stat_cards["health"].setText(health)

        self.activity_list.clear()
        logs = iot_logger.get_logs(5)
        for log in logs:
            typ = log.get("type", "")
            ts = log.get("timestamp", "")[:19]
            if typ == "command":
                text = f"[{ts}] 📤 指令 → {log.get('device_name', '')}: {log.get('command', '')}"
            elif typ == "sensor":
                text = f"[{ts}] 📥 传感器 → {log.get('device_name', '')}: {log.get('message', '')[:40]}"
            elif typ == "trigger":
                text = f"[{ts}] ⚡ 触发器 → {log.get('trigger_name', '')}"
            else:
                text = f"[{ts}] {typ}"
            self.activity_list.addItem(text)

    def _create_card_area(self, parent, tab_name):
        tab_layout = QVBoxLayout(parent)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        # 现代分页导航
        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(20, 12, 20, 12)

        prev_btn = QPushButton("← 上一页")
        prev_btn.setProperty("cssClass", "secondary-outline")
        prev_btn.setStyleSheet("")
        prev_btn.setEnabled(False)
        prev_btn.clicked.connect(lambda: self._prev_page(tab_name))
        prev_btn.setFixedHeight(36)

        page_label = QLabel("第 1 页")
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_label.setStyleSheet("font-weight: 600; color: #8b8ba7;")

        next_btn = QPushButton("下一页 →")
        next_btn.setProperty("cssClass", "secondary-outline")
        next_btn.setStyleSheet("")
        next_btn.clicked.connect(lambda: self._next_page(tab_name))
        next_btn.setFixedHeight(36)

        nav_layout.addStretch()
        nav_layout.addWidget(prev_btn)
        nav_layout.addSpacing(16)
        nav_layout.addWidget(page_label)
        nav_layout.addSpacing(16)
        nav_layout.addWidget(next_btn)
        nav_layout.addStretch()

        tab_layout.addWidget(nav)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        container = QWidget()
        container_layout = QGridLayout(container)
        container_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        container_layout.setContentsMargins(20, 12, 20, 20)
        container_layout.setSpacing(16)
        scroll.setWidget(container)

        tab_layout.addWidget(scroll)

        # 空状态
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon = QLabel("📦")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("font-size: 64px; margin-bottom: 16px;")
        empty_layout.addWidget(empty_icon)
        empty_text = QLabel("暂无设备")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text.setStyleSheet("font-size: 18px; color: #7f8c8d; font-weight: 600;")
        empty_layout.addWidget(empty_text)
        empty_sub = QLabel("点击下方按钮添加您的第一个设备")
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_sub.setStyleSheet("font-size: 13px; color: #95a5a6; margin-top: 4px;")
        empty_layout.addWidget(empty_sub)
        empty_btn = _make_btn("➕ 添加设备", "primary", lambda: self.add_device_wizard())
        empty_btn.setFixedWidth(160)
        empty_btn.setFixedHeight(40)
        empty_btn_layout = QHBoxLayout()
        empty_btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_btn_layout.addWidget(empty_btn)
        empty_layout.addLayout(empty_btn_layout)
        empty_widget.setVisible(False)

        tab_layout.addWidget(empty_widget)

        setattr(self, f"{tab_name}_prev_btn", prev_btn)
        setattr(self, f"{tab_name}_next_btn", next_btn)
        setattr(self, f"{tab_name}_page_label", page_label)
        setattr(self, f"{tab_name}_scroll", scroll)
        setattr(self, f"{tab_name}_container", container)
        setattr(self, f"{tab_name}_container_layout", container_layout)
        setattr(self, f"{tab_name}_empty_widget", empty_widget)

    def _refresh_all(self):
        self._refresh_devices()
        self._refresh_sensors()
        self._refresh_triggers()
        if hasattr(self, '_update_dashboard'):
            self._update_dashboard()

    def _refresh_devices(self):
        self._refresh_category("devices", iot_manager.devices.values(), self._create_device_card)

    def _refresh_sensors(self):
        self._refresh_category("sensors", iot_manager.sensors.values(), self._create_sensor_card)

    def _refresh_triggers(self):
        self._refresh_category("triggers", iot_manager.triggers.values(), self._create_trigger_card)

    def _refresh_category(self, category, items, card_creator):
        container = getattr(self, f"{category}_container")
        layout = getattr(self, f"{category}_container_layout")
        empty_widget = getattr(self, f"{category}_empty_widget")

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total = len(items)
        start = self.current_pages[category] * self.cards_per_page
        end = min(start + self.cards_per_page, total)
        page_items = list(items)[start:end]

        if total == 0:
            empty_widget.setVisible(True)
            container.setVisible(False)
        else:
            empty_widget.setVisible(False)
            container.setVisible(True)

        cols = max(1, container.width() // 300) if container.width() > 0 else 4
        for idx, item_data in enumerate(page_items):
            row = idx // cols
            col = idx % cols
            card = card_creator(item_data, category)
            layout.addWidget(card, row, col)

        for i in range(cols):
            layout.setColumnStretch(i, 1)

        prev_btn = getattr(self, f"{category}_prev_btn")
        next_btn = getattr(self, f"{category}_next_btn")
        page_label = getattr(self, f"{category}_page_label")
        prev_btn.setEnabled(self.current_pages[category] > 0)
        next_btn.setEnabled(end < total)
        page_label.setText(f"第 {self.current_pages[category] + 1} 页")

    def _prev_page(self, category):
        if self.current_pages[category] > 0:
            self.current_pages[category] -= 1
            getattr(self, f"_refresh_{category}")()
            scroll = getattr(self, f"{category}_scroll")
            scroll.verticalScrollBar().setValue(0)

    def _next_page(self, category):
        total = len(getattr(iot_manager, category))
        if (self.current_pages[category] + 1) * self.cards_per_page < total:
            self.current_pages[category] += 1
            getattr(self, f"_refresh_{category}")()
            scroll = getattr(self, f"{category}_scroll")
            scroll.verticalScrollBar().setValue(0)

    # -------------------- 卡片创建 --------------------
    def _create_device_card(self, dev, category):
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        # 顶部：图标 + 名称 + 删除按钮
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        icon_label = IconLabel("device", 48)
        header_layout.addWidget(icon_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        name_label = QLabel(dev.name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(14)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #27ae60; font-size: 10px;")
        status_layout.addWidget(status_dot)
        type_label = QLabel("开关设备" if dev.device_type == 'bool' else "复杂设备")
        type_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        status_layout.addWidget(type_label)
        status_layout.addStretch()
        info_layout.addLayout(status_layout)
        header_layout.addLayout(info_layout, 1)

        # 删除按钮（右上角小图标）
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #7f8c8d;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e74c3c22;
                color: #e74c3c;
            }
        """)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.clicked.connect(lambda: self._delete_device(dev.name))
        header_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

        card_layout.addWidget(header)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a3a5e;")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        # 操作区
        if dev.device_type == 'bool':
            btn_row = QWidget()
            btn_row_layout = QHBoxLayout(btn_row)
            btn_row_layout.setContentsMargins(0, 0, 0, 0)
            btn_row_layout.setSpacing(10)
            on_btn = _make_btn("ON", "success", lambda: self._control_device(dev.name, "on"))
            on_btn.setFixedHeight(36)
            off_btn = _make_btn("OFF", "danger", lambda: self._control_device(dev.name, "off"))
            off_btn.setFixedHeight(36)
            btn_row_layout.addWidget(on_btn)
            btn_row_layout.addWidget(off_btn)
            card_layout.addWidget(btn_row)
        else:
            preset_layout = QVBoxLayout()
            preset_layout.setSpacing(6)
            for i, preset in enumerate(dev.presets[:2]):
                btn = _make_btn(preset['name'], "primary-outline",
                                lambda p=preset['name']: self._control_device(dev.name, p))
                btn.setFixedHeight(32)
                preset_layout.addWidget(btn)
            if len(dev.presets) > 2:
                more_btn = _make_btn("更多...", "secondary-outline",
                                     lambda d=dev: self._show_preset_menu(d))
                more_btn.setFixedHeight(32)
                preset_layout.addWidget(more_btn)
            card_layout.addLayout(preset_layout)

        # IP/端口信息
        ip = dev.params.get('ip', '')
        port = dev.params.get('port', '')
        if ip or port:
            info = QLabel(f"{dev.protocol.upper()}  {ip}:{port}")
            info.setStyleSheet("color: #5a5a7a; font-size: 11px; font-family: 'Consolas', monospace;")
            card_layout.addWidget(info)

        card_layout.addStretch()
        return card

    def _create_sensor_card(self, sensor, category):
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        icon_label = IconLabel("sensor", 48)
        header_layout.addWidget(icon_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        name_label = QLabel(sensor.name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(14)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #27ae60; font-size: 10px;")
        status_layout.addWidget(status_dot)
        proto_label = QLabel(sensor.protocol.upper())
        proto_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        status_layout.addWidget(proto_label)
        status_layout.addStretch()
        info_layout.addLayout(status_layout)
        header_layout.addLayout(info_layout, 1)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #7f8c8d;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e74c3c22;
                color: #e74c3c;
            }
        """)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.clicked.connect(lambda: self._delete_sensor(sensor.name))
        header_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

        card_layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a3a5e;")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        ip = sensor.params.get('ip', '')
        port = sensor.params.get('port', '')
        info_text = f"IP: {ip}\n端口: {port}"
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #8b8ba7; font-size: 12px; line-height: 1.5;")
        card_layout.addWidget(info_label)

        card_layout.addStretch()

        del_btn_bottom = _make_btn("删除传感器", "danger-outline",
                                   lambda: self._delete_sensor(sensor.name))
        del_btn_bottom.setFixedHeight(32)
        card_layout.addWidget(del_btn_bottom)
        return card

    def _create_trigger_card(self, trigger, category):
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        icon_label = IconLabel("trigger", 48)
        header_layout.addWidget(icon_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        name_label = QLabel(trigger.name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(14)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)
        status_color = "#27ae60" if trigger.enabled else "#e74c3c"
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {status_color}; font-size: 10px;")
        status_layout.addWidget(status_dot)
        status_text = "已启用" if trigger.enabled else "已禁用"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: 600;")
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        info_layout.addLayout(status_layout)
        header_layout.addLayout(info_layout, 1)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #7f8c8d;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e74c3c22;
                color: #e74c3c;
            }
        """)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.clicked.connect(lambda: self._delete_trigger(trigger.name))
        header_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

        card_layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a3a5e;")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        tasks = trigger.tasks
        task_summary = "\n".join([f"• {self._task_desc(t)}" for t in tasks[:3]])
        if len(tasks) > 3:
            task_summary += f"\n... 共{len(tasks)}个任务"
        summary_label = QLabel(task_summary)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("color: #8b8ba7; font-size: 12px; line-height: 1.6;")
        summary_label.setMaximumHeight(100)
        card_layout.addWidget(summary_label)

        card_layout.addStretch()

        btn_row = QWidget()
        btn_row_layout = QHBoxLayout(btn_row)
        btn_row_layout.setContentsMargins(0, 0, 0, 0)
        btn_row_layout.setSpacing(8)

        edit_btn = _make_btn("编辑任务", "primary-outline",
                             lambda checked=False, t=trigger: self._edit_trigger_tasks(t))
        edit_btn.setFixedHeight(32)
        btn_row_layout.addWidget(edit_btn)

        def toggle_enable():
            trigger.enabled = not trigger.enabled
            iot_manager._save_triggers()
            self._refresh_triggers()

        status_btn_text = "禁用" if trigger.enabled else "启用"
        status_btn_css = "warning-outline" if trigger.enabled else "success-outline"
        status_btn = _make_btn(status_btn_text, status_btn_css, toggle_enable)
        status_btn.setFixedHeight(32)
        btn_row_layout.addWidget(status_btn)

        card_layout.addWidget(btn_row)
        return card

    def _task_desc(self, task):
        ttype = task.get('type')
        if ttype == 'ai_notify':
            prompt = task.get('prompt', '原始消息')
            send_reply = task.get('send_reply', False)
            reply_flag = " 📤回传" if send_reply else ""
            return f"🤖 通知AI: {prompt}{reply_flag}"
        elif ttype in ('control_device', 'control_bool_device'):
            return f"📟 控制设备 {task.get('device_name')} → {task.get('command')}"
        elif ttype == 'qq_notify':
            target_type = task.get('target_type')
            target_display = "私聊" if target_type == "private" else "群聊"
            return f"💬 QQ{target_display} {task.get('target_id')} → {task.get('content', '')[:20]}"
        return "未知任务"

    def _default_icon(self, layout):
        label = QLabel("🔌")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 32px;")
        layout.addWidget(label)

    # -------------------- 控制与删除 --------------------
    def _control_device(self, dev_name, command):
        def task():
            result = iot_manager.send_to_device(dev_name, command)
            self.status_signal.emit(result)
        threading.Thread(target=task, daemon=True).start()

    def _delete_device(self, dev_name):
        reply = QMessageBox.question(self, "确认", f"确定要删除设备 {dev_name} 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            iot_manager.remove_device(dev_name)
            self._refresh_devices()

    def _delete_sensor(self, sensor_name):
        reply = QMessageBox.question(self, "确认", f"确定要删除传感器 {sensor_name} 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            iot_manager.remove_sensor(sensor_name)
            self._refresh_sensors()

    def _delete_trigger(self, trigger_name):
        reply = QMessageBox.question(self, "确认", f"确定要删除触发器 {trigger_name} 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            iot_manager.remove_trigger(trigger_name)
            self._refresh_triggers()

    def _show_preset_menu(self, dev):
        menu = QMenu(self)
        for preset in dev.presets:
            action = menu.addAction(preset['name'])
            action.triggered.connect(lambda checked, p=preset['name']: self._control_device(dev.name, p))
        menu.exec(QCursor.pos())

    # -------------------- 添加设备向导 --------------------
    def add_device_wizard(self):
        wizard = QDialog(self)
        wizard.setWindowTitle("添加物联网设备")
        wizard.resize(600, 650)
        wizard.setWindowModality(Qt.WindowModality.WindowModal)
        wizard.setMinimumSize(500, 450)

        main_stack = QStackedWidget()
        wizard_layout = QVBoxLayout(wizard)
        wizard_layout.setContentsMargins(0, 0, 0, 0)
        wizard_layout.addWidget(main_stack)

        wizard.temp_data = {}
        dynamic_widgets = {}

        # 步骤指示器
        step_bar = QWidget()
        step_layout = QHBoxLayout(step_bar)
        step_layout.setContentsMargins(20, 16, 20, 8)
        step_layout.setSpacing(0)
        self._step_labels = []
        for i, step_name in enumerate(["基本信息", "类型选择", "详细配置"]):
            step_lbl = QLabel(f"{i+1}. {step_name}")
            step_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_lbl.setStyleSheet("color: #5a5a7a; font-size: 12px; font-weight: 500; padding: 4px 12px;")
            step_layout.addWidget(step_lbl)
            self._step_labels.append(step_lbl)
        wizard_layout.insertWidget(0, step_bar)

        def update_steps(current_idx):
            for i, lbl in enumerate(self._step_labels):
                if i == current_idx:
                    lbl.setStyleSheet("color: #4a90d9; font-size: 12px; font-weight: 600; padding: 4px 12px; border-bottom: 2px solid #4a90d9;")
                elif i < current_idx:
                    lbl.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: 500; padding: 4px 12px;")
                else:
                    lbl.setStyleSheet("color: #5a5a7a; font-size: 12px; font-weight: 500; padding: 4px 12px;")

        # ── 第1页：名称 + 协议 + 参数 ──
        frame1 = QWidget()
        f1_layout = QVBoxLayout(frame1)
        f1_layout.setContentsMargins(24, 20, 24, 20)
        f1_layout.setSpacing(12)

        title1 = QLabel("基本信息")
        title1_font = QFont()
        title1_font.setBold(True)
        title1_font.setPointSize(16)
        title1.setFont(title1_font)
        f1_layout.addWidget(title1)
        f1_layout.addSpacing(8)

        row0 = QWidget()
        r0_layout = QHBoxLayout(row0)
        r0_layout.setContentsMargins(0, 0, 0, 0)
        r0_layout.addWidget(QLabel("设备名称:"))
        name_entry = QLineEdit()
        name_entry.setMinimumWidth(300)
        r0_layout.addWidget(name_entry)
        f1_layout.addWidget(row0)

        row1 = QWidget()
        r1_layout = QHBoxLayout(row1)
        r1_layout.setContentsMargins(0, 0, 0, 0)
        r1_layout.addWidget(QLabel("通信协议:"))
        proto_combo = QComboBox()
        proto_combo.addItems(["udp", "tcp", "mqtt"])
        proto_combo.setEditable(False)
        r1_layout.addWidget(proto_combo)
        f1_layout.addWidget(row1)

        # 参数组
        params_group = QFrame()
        params_group.setProperty("cssClass", "group-frame")
        params_group.setStyleSheet("")
        pg_layout = QVBoxLayout(params_group)
        pg_layout.setContentsMargins(16, 16, 16, 16)

        params_label = QLabel("通信参数")
        params_label_font = QFont()
        params_label_font.setBold(True)
        params_label.setFont(params_label_font)
        pg_layout.addWidget(params_label)
        pg_layout.addSpacing(8)

        params_content = QWidget()
        params_content_layout = QVBoxLayout(params_content)
        params_content_layout.setContentsMargins(0, 0, 0, 0)
        params_content_layout.setSpacing(8)
        pg_layout.addWidget(params_content)

        f1_layout.addWidget(params_group)

        def update_params():
            for i in reversed(range(params_content_layout.count())):
                w = params_content_layout.takeAt(i).widget()
                if w:
                    w.deleteLater()
            dynamic_widgets.clear()
            proto = proto_combo.currentText()
            if proto in ("udp", "tcp"):
                r1w = QWidget()
                r1l = QHBoxLayout(r1w)
                r1l.setContentsMargins(0, 0, 0, 0)
                r1l.addWidget(QLabel("IP地址:"))
                ip_entry = QLineEdit()
                r1l.addWidget(ip_entry)
                params_content_layout.addWidget(r1w)
                r2w = QWidget()
                r2l = QHBoxLayout(r2w)
                r2l.setContentsMargins(0, 0, 0, 0)
                r2l.addWidget(QLabel("端口:"))
                port_entry = QLineEdit()
                r2l.addWidget(port_entry)
                params_content_layout.addWidget(r2w)
                dynamic_widgets['ip'] = ip_entry
                dynamic_widgets['port'] = port_entry
            elif proto == "mqtt":
                fields = [
                    ("Broker地址:", "broker"),
                    ("端口:", "port"),
                    ("Topic:", "topic"),
                    ("用户名(可选):", "username"),
                    ("密码(可选):", "password"),
                    ("Client ID (可选):", "client_id"),
                ]
                for label_text, key in fields:
                    rw = QWidget()
                    rl = QHBoxLayout(rw)
                    rl.setContentsMargins(0, 0, 0, 0)
                    rl.addWidget(QLabel(label_text))
                    entry = QLineEdit()
                    if key == "password":
                        entry.setEchoMode(QLineEdit.EchoMode.Password)
                    rl.addWidget(entry)
                    params_content_layout.addWidget(rw)
                    dynamic_widgets[key] = entry

        proto_combo.currentTextChanged.connect(update_params)
        update_params()

        def next_step():
            name = name_entry.text().strip()
            if not name:
                QMessageBox.critical(wizard, "错误", "请输入设备名称")
                return
            proto = proto_combo.currentText()
            params = {}
            try:
                if proto in ("udp", "tcp"):
                    ip = dynamic_widgets['ip'].text().strip()
                    port = dynamic_widgets['port'].text().strip()
                    if not ip or not port:
                        QMessageBox.critical(wizard, "错误", "请填写IP和端口")
                        return
                    params = {"ip": ip, "port": int(port)}
                elif proto == "mqtt":
                    broker = dynamic_widgets['broker'].text().strip()
                    port = dynamic_widgets['port'].text().strip()
                    topic = dynamic_widgets['topic'].text().strip()
                    if not broker or not port or not topic:
                        QMessageBox.critical(wizard, "错误", "请填写Broker、端口和Topic")
                        return
                    params = {
                        "broker": broker,
                        "port": int(port),
                        "topic": topic,
                        "username": dynamic_widgets.get('username', QLineEdit()).text(),
                        "password": dynamic_widgets.get('password', QLineEdit()).text(),
                        "client_id": dynamic_widgets.get('client_id', QLineEdit()).text().strip()
                    }
            except ValueError:
                QMessageBox.critical(wizard, "错误", "端口必须为数字")
                return

            wizard.temp_data = {
                "name": name,
                "protocol": proto,
                "params": params
            }
            update_steps(1)
            main_stack.setCurrentIndex(1)

        next_btn = _make_btn("下一步", "primary", next_step)
        next_btn.setFixedHeight(40)
        f1_layout.addWidget(next_btn)
        f1_layout.addStretch()

        main_stack.addWidget(frame1)

        # ── 第2页：设备类型选择 ──
        frame2 = QWidget()
        f2_layout = QVBoxLayout(frame2)
        f2_layout.setContentsMargins(24, 20, 24, 20)
        f2_layout.setSpacing(12)

        title2 = QLabel("选择设备类型")
        title2_font = QFont()
        title2_font.setBold(True)
        title2_font.setPointSize(16)
        title2.setFont(title2_font)
        f2_layout.addWidget(title2)
        f2_layout.addSpacing(8)

        type_group = QButtonGroup(self)
        bool_radio = QRadioButton("布尔类 (开关)")
        complex_radio = QRadioButton("复杂类 (多指令)")
        bool_radio.setChecked(True)
        type_group.addButton(bool_radio, 0)
        type_group.addButton(complex_radio, 1)
        f2_layout.addWidget(bool_radio)
        f2_layout.addWidget(complex_radio)
        f2_layout.addSpacing(16)

        def next_type():
            dev_type = "bool" if bool_radio.isChecked() else "complex"
            wizard.temp_data["device_type"] = dev_type
            build_page3(dev_type)
            update_steps(2)
            main_stack.setCurrentIndex(2)

        btn_row2 = QWidget()
        btn_row2_layout = QHBoxLayout(btn_row2)
        btn_row2_layout.setContentsMargins(0, 0, 0, 0)
        btn_row2_layout.setSpacing(10)
        back_btn2 = _make_btn("返回", "secondary-outline", lambda: (update_steps(0), main_stack.setCurrentIndex(0)))
        back_btn2.setFixedHeight(40)
        next_btn2 = _make_btn("下一步", "primary", next_type)
        next_btn2.setFixedHeight(40)
        btn_row2_layout.addWidget(back_btn2)
        btn_row2_layout.addWidget(next_btn2)
        f2_layout.addWidget(btn_row2)
        f2_layout.addStretch()
        main_stack.addWidget(frame2)

        # ── 第3页：布尔/复杂配置 ──
        frame3_container = QWidget()
        f3_container_layout = QVBoxLayout(frame3_container)
        f3_container_layout.setContentsMargins(0, 0, 0, 0)
        main_stack.addWidget(frame3_container)

        def build_page3(dev_type):
            for i in reversed(range(f3_container_layout.count())):
                w = f3_container_layout.takeAt(i).widget()
                if w:
                    w.deleteLater()

            frame3 = QWidget()
            f3_layout = QVBoxLayout(frame3)
            f3_layout.setContentsMargins(24, 20, 24, 20)
            f3_layout.setSpacing(12)

            title3 = QLabel("详细配置")
            title3_font = QFont()
            title3_font.setBold(True)
            title3_font.setPointSize(16)
            title3.setFont(title3_font)
            f3_layout.addWidget(title3)
            f3_layout.addSpacing(8)

            f3_container_layout.addWidget(frame3)

            if dev_type == "bool":
                r1 = QWidget()
                r1l = QHBoxLayout(r1)
                r1l.setContentsMargins(0, 0, 0, 0)
                r1l.addWidget(QLabel("ON指令内容:"))
                on_entry = QLineEdit()
                r1l.addWidget(on_entry)
                f3_layout.addWidget(r1)

                r2 = QWidget()
                r2l = QHBoxLayout(r2)
                r2l.setContentsMargins(0, 0, 0, 0)
                r2l.addWidget(QLabel("OFF指令内容:"))
                off_entry = QLineEdit()
                r2l.addWidget(off_entry)
                f3_layout.addWidget(r2)

                def finish():
                    data = wizard.temp_data
                    data["device_type"] = "bool"
                    data["on_msg"] = on_entry.text().strip() or "ON"
                    data["off_msg"] = off_entry.text().strip() or "OFF"
                    data["presets"] = []
                    data["notes"] = ""
                    data["icon"] = ""
                    if iot_manager.add_device(data):
                        QMessageBox.information(wizard, "成功", f"设备 {data['name']} 已添加")
                        wizard.accept()
                        self._refresh_devices()
                    else:
                        QMessageBox.critical(wizard, "错误", "设备名称已存在")

                btn_row3 = QWidget()
                btn_row3_layout = QHBoxLayout(btn_row3)
                btn_row3_layout.setContentsMargins(0, 0, 0, 0)
                btn_row3_layout.setSpacing(10)
                back_btn3 = _make_btn("返回", "secondary-outline", lambda: (update_steps(1), main_stack.setCurrentIndex(1)))
                back_btn3.setFixedHeight(40)
                finish_btn = _make_btn("完成", "success", finish)
                finish_btn.setFixedHeight(40)
                btn_row3_layout.addWidget(back_btn3)
                btn_row3_layout.addWidget(finish_btn)
                f3_layout.addWidget(btn_row3)
            else:
                QLabel("预设指令列表:").setStyleSheet("font-weight: bold;")
                f3_layout.addWidget(QLabel("预设指令列表:"))

                preset_list = QListWidget()
                preset_list.setMaximumHeight(140)
                f3_layout.addWidget(preset_list)

                presets = []

                def add_preset():
                    add_win = QDialog(wizard)
                    add_win.setWindowTitle("添加预设指令")
                    add_win.resize(450, 280)
                    add_win.setWindowModality(Qt.WindowModality.WindowModal)
                    aw_layout = QVBoxLayout(add_win)
                    aw_layout.setContentsMargins(20, 20, 20, 20)
                    aw_layout.setSpacing(12)

                    aw_layout.addWidget(QLabel("指令名称:"))
                    name_entry_d = QLineEdit()
                    aw_layout.addWidget(name_entry_d)
                    aw_layout.addWidget(QLabel("指令内容:"))
                    msg_entry_d = QLineEdit()
                    aw_layout.addWidget(msg_entry_d)
                    aw_layout.addStretch()

                    def save():
                        pname = name_entry_d.text().strip()
                        pmsg = msg_entry_d.text().strip()
                        if pname and pmsg:
                            presets.append({"name": pname, "msg": pmsg})
                            preset_list.addItem(f"{pname} -> {pmsg}")
                            add_win.accept()

                    aw_layout.addWidget(_make_btn("保存", "success", save))
                    add_win.exec()

                f3_layout.addWidget(_make_btn("➕ 添加指令", "success-outline", add_preset))

                f3_layout.addWidget(QLabel("给AI的注意事项（可选）:"))
                notes_text = QTextEdit()
                notes_text.setMaximumHeight(100)
                f3_layout.addWidget(notes_text)

                def finish():
                    data = wizard.temp_data
                    data["device_type"] = "complex"
                    data["presets"] = presets
                    data["notes"] = notes_text.toPlainText().strip()
                    data["icon"] = ""
                    if iot_manager.add_device(data):
                        QMessageBox.information(wizard, "成功", f"设备 {data['name']} 已添加")
                        wizard.accept()
                        self._refresh_devices()
                    else:
                        QMessageBox.critical(wizard, "错误", "设备名称已存在")

                btn_row3 = QWidget()
                btn_row3_layout = QHBoxLayout(btn_row3)
                btn_row3_layout.setContentsMargins(0, 0, 0, 0)
                btn_row3_layout.setSpacing(10)
                back_btn3 = _make_btn("返回", "secondary-outline", lambda: (update_steps(1), main_stack.setCurrentIndex(1)))
                back_btn3.setFixedHeight(40)
                finish_btn = _make_btn("完成", "success", finish)
                finish_btn.setFixedHeight(40)
                btn_row3_layout.addWidget(back_btn3)
                btn_row3_layout.addWidget(finish_btn)
                f3_layout.addWidget(btn_row3)

            f3_layout.addStretch()

        update_steps(0)
        wizard.exec()

    # -------------------- 添加传感器向导 --------------------
    def add_sensor_wizard(self):
        wizard = QDialog(self)
        wizard.setWindowTitle("添加传感器")
        wizard.resize(550, 550)
        wizard.setWindowModality(Qt.WindowModality.WindowModal)

        frame = QWidget()
        wizard_layout = QVBoxLayout(wizard)
        wizard_layout.setContentsMargins(0, 0, 0, 0)
        wizard_layout.addWidget(frame)

        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(24, 20, 24, 20)
        f_layout.setSpacing(12)

        title = QLabel("添加传感器")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        f_layout.addWidget(title)
        f_layout.addSpacing(8)

        r0 = QWidget()
        r0l = QHBoxLayout(r0)
        r0l.setContentsMargins(0, 0, 0, 0)
        r0l.addWidget(QLabel("传感器名称:"))
        name_entry = QLineEdit()
        r0l.addWidget(name_entry)
        f_layout.addWidget(r0)

        r1 = QWidget()
        r1l = QHBoxLayout(r1)
        r1l.setContentsMargins(0, 0, 0, 0)
        r1l.addWidget(QLabel("协议:"))
        proto_combo = QComboBox()
        proto_combo.addItems(["udp", "tcp", "mqtt"])
        proto_combo.setEditable(False)
        r1l.addWidget(proto_combo)
        f_layout.addWidget(r1)

        params_group = QFrame()
        params_group.setProperty("cssClass", "group-frame")
        params_group.setStyleSheet("")
        pg_layout = QVBoxLayout(params_group)
        pg_layout.setContentsMargins(16, 16, 16, 16)

        plabel = QLabel("通信参数")
        pl_font = QFont()
        pl_font.setBold(True)
        plabel.setFont(pl_font)
        pg_layout.addWidget(plabel)
        pg_layout.addSpacing(8)

        params_content = QWidget()
        params_content_layout = QVBoxLayout(params_content)
        params_content_layout.setContentsMargins(0, 0, 0, 0)
        params_content_layout.setSpacing(8)
        pg_layout.addWidget(params_content)

        f_layout.addWidget(params_group)

        dynamic_widgets = {}

        def update_params():
            for i in reversed(range(params_content_layout.count())):
                w = params_content_layout.takeAt(i).widget()
                if w:
                    w.deleteLater()
            dynamic_widgets.clear()
            proto = proto_combo.currentText()
            if proto in ("udp", "tcp"):
                rw1 = QWidget()
                rl1 = QHBoxLayout(rw1)
                rl1.setContentsMargins(0, 0, 0, 0)
                rl1.addWidget(QLabel("监听IP (0.0.0.0):"))
                ip_entry = QLineEdit()
                rl1.addWidget(ip_entry)
                params_content_layout.addWidget(rw1)
                rw2 = QWidget()
                rl2 = QHBoxLayout(rw2)
                rl2.setContentsMargins(0, 0, 0, 0)
                rl2.addWidget(QLabel("端口:"))
                port_entry = QLineEdit()
                rl2.addWidget(port_entry)
                params_content_layout.addWidget(rw2)
                dynamic_widgets['ip'] = ip_entry
                dynamic_widgets['port'] = port_entry
            elif proto == "mqtt":
                fields = [
                    ("Broker地址:", "broker"),
                    ("端口:", "port"),
                    ("Topic:", "topic"),
                    ("用户名(可选):", "username"),
                    ("密码(可选):", "password"),
                    ("Client ID (私钥):", "client_id"),
                ]
                for label_text, key in fields:
                    rw = QWidget()
                    rl = QHBoxLayout(rw)
                    rl.setContentsMargins(0, 0, 0, 0)
                    rl.addWidget(QLabel(label_text))
                    entry = QLineEdit()
                    if key == "password":
                        entry.setEchoMode(QLineEdit.EchoMode.Password)
                    rl.addWidget(entry)
                    params_content_layout.addWidget(rw)
                    dynamic_widgets[key] = entry

        proto_combo.currentTextChanged.connect(update_params)
        update_params()

        def finish():
            name = name_entry.text().strip()
            if not name:
                QMessageBox.critical(wizard, "错误", "请输入传感器名称")
                return
            proto = proto_combo.currentText()
            params = {}
            try:
                if proto in ("udp", "tcp"):
                    ip = dynamic_widgets['ip'].text().strip() or "0.0.0.0"
                    if ip == '255.255.255.255':
                        reply = QMessageBox.question(wizard, "提示",
                                                     "广播地址不能监听，是否改为 0.0.0.0？",
                                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        if reply != QMessageBox.StandardButton.Yes:
                            return
                        ip = '0.0.0.0'
                    port = int(dynamic_widgets['port'].text().strip())
                    params = {"ip": ip, "port": port}
                elif proto == "mqtt":
                    broker = dynamic_widgets['broker'].text().strip()
                    port = int(dynamic_widgets['port'].text().strip())
                    topic = dynamic_widgets['topic'].text().strip()
                    if not broker or not topic:
                        QMessageBox.critical(wizard, "错误", "请填写 Broker 和 Topic")
                        return
                    params = {
                        "broker": broker,
                        "port": port,
                        "topic": topic,
                        "username": dynamic_widgets.get('username', QLineEdit()).text(),
                        "password": dynamic_widgets.get('password', QLineEdit()).text(),
                        "client_id": dynamic_widgets.get('client_id', QLineEdit()).text().strip()
                    }
            except ValueError:
                QMessageBox.critical(wizard, "错误", "端口必须为数字")
                return
            data = {
                "name": name,
                "protocol": proto,
                "params": params,
                "icon": ""
            }
            if iot_manager.add_sensor(data):
                QMessageBox.information(wizard, "成功", f"传感器 {name} 已添加")
                wizard.accept()
                self._refresh_sensors()
            else:
                QMessageBox.critical(wizard, "错误", "传感器名称已存在")

        f_layout.addWidget(_make_btn("完成", "success", finish))
        f_layout.addStretch()

        wizard.exec()

    # -------------------- 添加触发器向导 --------------------
    def add_trigger_wizard(self):
        win = QDialog(self)
        win.setWindowTitle("添加触发器")
        win.resize(600, 400)
        win.setWindowModality(Qt.WindowModality.WindowModal)

        frame = QWidget()
        win_layout = QVBoxLayout(win)
        win_layout.setContentsMargins(0, 0, 0, 0)
        win_layout.addWidget(frame)

        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(24, 20, 24, 20)
        f_layout.setSpacing(12)

        title = QLabel("添加触发器")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        f_layout.addWidget(title)
        f_layout.addSpacing(8)

        r0 = QWidget()
        r0l = QHBoxLayout(r0)
        r0l.setContentsMargins(0, 0, 0, 0)
        r0l.addWidget(QLabel("触发器名称:"))
        name_entry = QLineEdit()
        r0l.addWidget(name_entry)
        f_layout.addWidget(r0)

        r1 = QWidget()
        r1l = QHBoxLayout(r1)
        r1l.setContentsMargins(0, 0, 0, 0)
        r1l.addWidget(QLabel("传感器:"))
        sensor_combo = QComboBox()
        sensor_combo.addItems(list(iot_manager.sensors.keys()))
        sensor_combo.setEditable(False)
        r1l.addWidget(sensor_combo)
        f_layout.addWidget(r1)

        r2 = QWidget()
        r2l = QHBoxLayout(r2)
        r2l.setContentsMargins(0, 0, 0, 0)
        r2l.addWidget(QLabel("匹配模式(包含此字符串即触发，留空则任何消息):"))
        pattern_entry = QLineEdit()
        r2l.addWidget(pattern_entry)
        f_layout.addWidget(r2)

        def create_and_edit():
            name = name_entry.text().strip()
            sensor = sensor_combo.currentText()
            pattern = pattern_entry.text().strip()
            if not name or not sensor:
                QMessageBox.critical(win, "错误", "请填写触发器名称和传感器")
                return
            data = {
                "name": name,
                "sensor_name": sensor,
                "match_pattern": pattern,
                "tasks": [],
                "enabled": True
            }
            if iot_manager.add_trigger(data):
                trigger = iot_manager.triggers.get(name)
                if trigger:
                    win.accept()
                    self._edit_trigger_tasks(trigger)
                else:
                    QMessageBox.critical(win, "错误", "触发器创建失败")
                    win.reject()
            else:
                QMessageBox.critical(win, "错误", "触发器名称已存在")

        f_layout.addWidget(_make_btn("创建并编辑任务", "success", create_and_edit))
        f_layout.addStretch()

        win.exec()

    # -------------------- 触发器任务编辑 --------------------
    def _edit_trigger_tasks(self, trigger):
        win = QDialog(self)
        win.setWindowTitle(f"编辑触发器任务 - {trigger.name}")
        win.resize(900, 600)
        win.setMinimumSize(600, 500)
        win.setWindowModality(Qt.WindowModality.WindowModal)

        main_layout = QVBoxLayout(win)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title = QLabel(f"触发器: {trigger.name}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        main_layout.addWidget(title)
        main_layout.addSpacing(4)

        listbox = QListWidget()
        listbox.setMinimumHeight(200)
        main_layout.addWidget(listbox)

        def refresh_list():
            listbox.clear()
            for task in trigger.tasks:
                listbox.addItem(self._task_desc(task))

        refresh_list()

        btn_row = QWidget()
        btn_row_layout = QHBoxLayout(btn_row)
        btn_row_layout.setContentsMargins(0, 0, 0, 0)
        btn_row_layout.setSpacing(8)

        def add_task():
            self._add_task_dialog(trigger, refresh_list)

        def edit_task():
            row = listbox.currentRow()
            if row >= 0:
                self._edit_task_dialog(trigger, row, refresh_list)

        def delete_task():
            row = listbox.currentRow()
            if row >= 0:
                trigger.tasks.pop(row)
                iot_manager._save_triggers()
                refresh_list()
                self._refresh_triggers()

        def move_up():
            row = listbox.currentRow()
            if row > 0:
                trigger.tasks[row], trigger.tasks[row-1] = trigger.tasks[row-1], trigger.tasks[row]
                iot_manager._save_triggers()
                refresh_list()
                listbox.setCurrentRow(row - 1)
                self._refresh_triggers()

        def move_down():
            row = listbox.currentRow()
            if row >= 0 and row < len(trigger.tasks) - 1:
                trigger.tasks[row], trigger.tasks[row+1] = trigger.tasks[row+1], trigger.tasks[row]
                iot_manager._save_triggers()
                refresh_list()
                listbox.setCurrentRow(row + 1)
                self._refresh_triggers()

        btn_row_layout.addWidget(_make_btn("➕ 添加", "success-outline", add_task))
        btn_row_layout.addWidget(_make_btn("✏️ 编辑", "primary-outline", edit_task))
        btn_row_layout.addWidget(_make_btn("❌ 删除", "danger-outline", delete_task))
        btn_row_layout.addWidget(_make_btn("⬆ 上移", "secondary-outline", move_up))
        btn_row_layout.addWidget(_make_btn("⬇ 下移", "secondary-outline", move_down))
        btn_row_layout.addStretch()

        main_layout.addWidget(btn_row)

        bottom_row = QWidget()
        bottom_row_layout = QHBoxLayout(bottom_row)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.addStretch()

        def save_and_close():
            self._refresh_triggers()
            win.accept()

        bottom_row_layout.addWidget(_make_btn("取消", "secondary-outline", win.reject))
        bottom_row_layout.addWidget(_make_btn("保存并关闭", "success", save_and_close))

        main_layout.addWidget(bottom_row)

        win.exec()

    def _add_task_dialog(self, trigger, refresh_cb):
        win = QDialog(self)
        win.setWindowTitle("添加任务")
        win.resize(550, 500)
        win.setMinimumSize(450, 400)
        win.setWindowModality(Qt.WindowModality.WindowModal)

        main_layout = QVBoxLayout(win)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        type_display_map = {
            "🤖 通知AI": "ai_notify",
            "📟 控制设备": "control_device",
            "💬 QQ通知": "qq_notify"
        }

        title = QLabel("添加任务")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        main_layout.addWidget(title)
        main_layout.addSpacing(8)

        type_label = QLabel("任务类型:")
        main_layout.addWidget(type_label)

        type_combo = QComboBox()
        type_combo.addItems(list(type_display_map.keys()))
        type_combo.setEditable(False)
        main_layout.addWidget(type_combo)

        params_stack = QStackedWidget()
        main_layout.addWidget(params_stack)

        dynamic_data = {}

        # ai_notify 页
        ai_page = QWidget()
        ai_layout = QVBoxLayout(ai_page)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(8)
        ai_layout.addWidget(QLabel("发送给AI的消息（留空则发送原始传感器消息）:"))
        prompt_entry = QLineEdit()
        ai_layout.addWidget(prompt_entry)
        send_reply_check = QCheckBox("将AI回复回传给原设备")
        ai_layout.addWidget(send_reply_check)
        ai_layout.addStretch()
        params_stack.addWidget(ai_page)

        # control_device 页
        ctrl_page = QWidget()
        ctrl_layout = QVBoxLayout(ctrl_page)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(8)
        ctrl_layout.addWidget(QLabel("设备名称:"))
        dev_combo = QComboBox()
        dev_combo.addItems(list(iot_manager.devices.keys()))
        dev_combo.setEditable(False)
        ctrl_layout.addWidget(dev_combo)
        ctrl_layout.addWidget(QLabel("指令:"))
        cmd_entry = QLineEdit()
        ctrl_layout.addWidget(cmd_entry)
        ctrl_layout.addStretch()
        params_stack.addWidget(ctrl_page)

        # qq_notify 页
        qq_page = QWidget()
        qq_layout = QVBoxLayout(qq_page)
        qq_layout.setContentsMargins(0, 0, 0, 0)
        qq_layout.setSpacing(8)
        qq_layout.addWidget(QLabel("目标类型:"))
        target_combo = QComboBox()
        target_combo.addItems(["私聊", "群聊"])
        target_combo.setEditable(False)
        qq_layout.addWidget(target_combo)
        qq_layout.addWidget(QLabel("目标ID (QQ号或群号):"))
        id_entry = QLineEdit()
        qq_layout.addWidget(id_entry)
        qq_layout.addWidget(QLabel("消息内容 (可用 {message} 代替原始传感器消息):"))
        content_entry = QLineEdit()
        qq_layout.addWidget(content_entry)
        qq_layout.addStretch()
        params_stack.addWidget(qq_page)

        def on_type_changed():
            display = type_combo.currentText()
            actual = type_display_map.get(display, "ai_notify")
            if actual == "ai_notify":
                params_stack.setCurrentIndex(0)
            elif actual == "control_device":
                params_stack.setCurrentIndex(1)
            elif actual == "qq_notify":
                params_stack.setCurrentIndex(2)

        type_combo.currentTextChanged.connect(on_type_changed)

        bottom_row = QWidget()
        bottom_row_layout = QHBoxLayout(bottom_row)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.addStretch()

        def save():
            display = type_combo.currentText()
            ttype = type_display_map.get(display, "ai_notify")
            task = {"type": ttype}
            if ttype == "ai_notify":
                task["prompt"] = prompt_entry.text().strip()
                task["send_reply"] = send_reply_check.isChecked()
            elif ttype == "control_device":
                task["device_name"] = dev_combo.currentText()
                task["command"] = cmd_entry.text().strip()
            elif ttype == "qq_notify":
                target_map = {"私聊": "private", "群聊": "group"}
                task["target_type"] = target_map.get(target_combo.currentText(), "private")
                task["target_id"] = id_entry.text().strip()
                task["content"] = content_entry.text().strip()
            trigger.tasks.append(task)
            iot_manager._save_triggers()
            refresh_cb()
            self._refresh_triggers()
            win.accept()

        bottom_row_layout.addWidget(_make_btn("取消", "secondary-outline", win.reject))
        bottom_row_layout.addWidget(_make_btn("保存并关闭", "success", save))
        main_layout.addWidget(bottom_row)

        win.exec()

    def _edit_task_dialog(self, trigger, task_index, refresh_cb):
        task = trigger.tasks[task_index]
        win = QDialog(self)
        win.setWindowTitle("编辑任务")
        win.resize(550, 500)
        win.setMinimumSize(450, 400)
        win.setWindowModality(Qt.WindowModality.WindowModal)

        main_layout = QVBoxLayout(win)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        type_display_map = {
            "🤖 通知AI": "ai_notify",
            "📟 控制设备": "control_device",
            "💬 QQ通知": "qq_notify"
        }
        type_value_to_display = {v: k for k, v in type_display_map.items()}

        current_type = task.get('type', 'ai_notify')
        current_display = type_value_to_display.get(current_type, "🤖 通知AI")

        title = QLabel("编辑任务")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        main_layout.addWidget(title)
        main_layout.addSpacing(8)

        main_layout.addWidget(QLabel("任务类型:"))

        type_combo = QComboBox()
        type_combo.addItems(list(type_display_map.keys()))
        type_combo.setEditable(False)
        type_combo.setCurrentText(current_display)
        main_layout.addWidget(type_combo)

        params_stack = QStackedWidget()
        main_layout.addWidget(params_stack)

        # ai_notify 页
        ai_page = QWidget()
        ai_layout = QVBoxLayout(ai_page)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(8)
        ai_layout.addWidget(QLabel("发送给AI的消息（留空则发送原始传感器消息）:"))
        prompt_entry = QLineEdit()
        prompt_entry.setText(task.get('prompt', ''))
        ai_layout.addWidget(prompt_entry)
        send_reply_check = QCheckBox("将AI回复回传给原设备")
        send_reply_check.setChecked(task.get('send_reply', False))
        ai_layout.addWidget(send_reply_check)
        ai_layout.addStretch()
        params_stack.addWidget(ai_page)

        # control_device 页
        ctrl_page = QWidget()
        ctrl_layout = QVBoxLayout(ctrl_page)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(8)
        ctrl_layout.addWidget(QLabel("设备名称:"))
        dev_combo = QComboBox()
        dev_combo.addItems(list(iot_manager.devices.keys()))
        dev_combo.setEditable(False)
        dev_combo.setCurrentText(task.get('device_name', ''))
        ctrl_layout.addWidget(dev_combo)
        ctrl_layout.addWidget(QLabel("指令:"))
        cmd_entry = QLineEdit()
        cmd_entry.setText(task.get('command', ''))
        ctrl_layout.addWidget(cmd_entry)
        ctrl_layout.addStretch()
        params_stack.addWidget(ctrl_page)

        # qq_notify 页
        qq_page = QWidget()
        qq_layout = QVBoxLayout(qq_page)
        qq_layout.setContentsMargins(0, 0, 0, 0)
        qq_layout.setSpacing(8)
        qq_layout.addWidget(QLabel("目标类型:"))
        target_combo = QComboBox()
        target_combo.addItems(["私聊", "群聊"])
        target_combo.setEditable(False)
        target_display_map_qq = {"private": "私聊", "group": "群聊"}
        target_combo.setCurrentText(target_display_map_qq.get(task.get('target_type', 'private'), "私聊"))
        qq_layout.addWidget(target_combo)
        qq_layout.addWidget(QLabel("目标ID (QQ号或群号):"))
        id_entry = QLineEdit()
        id_entry.setText(task.get('target_id', ''))
        qq_layout.addWidget(id_entry)
        qq_layout.addWidget(QLabel("消息内容 (可用 {message} 代替原始传感器消息):"))
        content_entry = QLineEdit()
        content_entry.setText(task.get('content', ''))
        qq_layout.addWidget(content_entry)
        qq_layout.addStretch()
        params_stack.addWidget(qq_page)

        def on_type_changed():
            display = type_combo.currentText()
            actual = type_display_map.get(display, "ai_notify")
            if actual == "ai_notify":
                params_stack.setCurrentIndex(0)
            elif actual == "control_device":
                params_stack.setCurrentIndex(1)
            elif actual == "qq_notify":
                params_stack.setCurrentIndex(2)

        type_combo.currentTextChanged.connect(on_type_changed)

        # 设置初始页
        initial_actual = type_display_map.get(current_display, "ai_notify")
        if initial_actual == "control_device":
            params_stack.setCurrentIndex(1)
        elif initial_actual == "qq_notify":
            params_stack.setCurrentIndex(2)
        else:
            params_stack.setCurrentIndex(0)

        bottom_row = QWidget()
        bottom_row_layout = QHBoxLayout(bottom_row)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.addStretch()

        def save():
            display = type_combo.currentText()
            ttype = type_display_map.get(display, "ai_notify")
            new_task = {"type": ttype}
            if ttype == "ai_notify":
                new_task["prompt"] = prompt_entry.text().strip()
                new_task["send_reply"] = send_reply_check.isChecked()
            elif ttype == "control_device":
                new_task["device_name"] = dev_combo.currentText()
                new_task["command"] = cmd_entry.text().strip()
            elif ttype == "qq_notify":
                target_map = {"私聊": "private", "群聊": "group"}
                new_task["target_type"] = target_map.get(target_combo.currentText(), "private")
                new_task["target_id"] = id_entry.text().strip()
                new_task["content"] = content_entry.text().strip()
            trigger.tasks[task_index] = new_task
            iot_manager._save_triggers()
            refresh_cb()
            self._refresh_triggers()
            win.accept()

        bottom_row_layout.addWidget(_make_btn("取消", "secondary-outline", win.reject))
        bottom_row_layout.addWidget(_make_btn("保存并关闭", "success", save))
        main_layout.addWidget(bottom_row)

        win.exec()

    # -------------------- 日志记录 --------------------
    def create_log_tab(self):
        tab = QWidget()
        self.notebook.addTab(tab, "日志记录")

        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(20, 20, 20, 20)
        tab_layout.setSpacing(12)

        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)

        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("🔍 搜索日志...")
        self.log_search.setMinimumWidth(280)
        self.log_search.textChanged.connect(self.refresh_log_table)
        toolbar_layout.addWidget(self.log_search)
        toolbar_layout.addWidget(_make_btn("🔄 刷新", "secondary-outline", self.refresh_log_table))
        toolbar_layout.addWidget(_make_btn("🗑️ 清空日志", "danger-outline", self.clear_logs))
        toolbar_layout.addStretch()
        tab_layout.addWidget(toolbar)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["时间", "类型", "设备名称", "内容", "协议"])
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.log_table.horizontalHeader().setStretchLastSection(True)
        self.log_table.setColumnWidth(0, 160)
        self.log_table.setColumnWidth(1, 100)
        self.log_table.setColumnWidth(2, 140)
        self.log_table.setColumnWidth(3, 400)
        self.log_table.setColumnWidth(4, 100)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setStyleSheet(self.log_table.styleSheet() + "QTableWidget::item { padding: 8px; }")
        tab_layout.addWidget(self.log_table)

        self.refresh_log_table()

    def refresh_log_table(self):
        self.log_table.setRowCount(0)
        logs = iot_logger.get_logs(500)
        search = getattr(self, 'log_search', None)
        if search:
            keyword = search.text().strip().lower()
            if keyword:
                logs = [log for log in logs if keyword in json.dumps(log, ensure_ascii=False).lower()]
        self.log_table.setRowCount(len(logs))
        for row_idx, log in enumerate(logs):
            typ = log.get("type")
            ts = log.get("timestamp", "")[:19]
            if typ == "command":
                type_icon = "📤 指令"
                dev = log.get("device_name", "")
                content = log.get("command", "")
                protocol = log.get("protocol", "")
                badge_color = "#4a90d9"
            elif typ == "sensor":
                type_icon = "📥 传感器"
                dev = log.get("device_name", "")
                content = log.get("message", "")
                protocol = log.get("protocol", "")
                badge_color = "#27ae60"
            elif typ == "trigger":
                type_icon = "⚡ 触发器"
                dev = log.get("trigger_name", "")
                content = f"传感器: {log.get('sensor_name', '')} | 消息: {log.get('message', '')}"
                protocol = ""
                badge_color = "#f39c12"
            else:
                continue

            self.log_table.setItem(row_idx, 0, QTableWidgetItem(ts))

            # 类型使用彩色标签
            type_item = QTableWidgetItem(type_icon)
            type_item.setForeground(QColor(badge_color))
            type_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.log_table.setItem(row_idx, 1, type_item)

            self.log_table.setItem(row_idx, 2, QTableWidgetItem(dev))
            self.log_table.setItem(row_idx, 3, QTableWidgetItem(content))
            self.log_table.setItem(row_idx, 4, QTableWidgetItem(protocol))

    def clear_logs(self):
        reply = QMessageBox.question(self, "确认", "清空所有日志？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            iot_logger.clear_logs()
            self.refresh_log_table()

    # -------------------- 主动智能 --------------------
    def create_active_intelligence_tab(self):
        tab = QWidget()
        self.notebook.addTab(tab, "主动智能")

        main_frame = QWidget()
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(main_frame)

        # 标题
        title = QLabel("🧠 主动智能巡检")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        main_layout.addWidget(title)
        main_layout.addSpacing(8)

        # 巡检设置组
        group1 = QFrame()
        group1.setProperty("cssClass", "group-frame")
        group1.setStyleSheet("")
        g1_layout = QVBoxLayout(group1)
        g1_layout.setContentsMargins(20, 20, 20, 20)
        g1_layout.setSpacing(16)

        section_title = QLabel("巡检设置")
        section_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        g1_layout.addWidget(section_title)

        self.inspector_enabled_check = QCheckBox("启用主动巡检")
        self.inspector_enabled_check.setChecked(getattr(config, 'inspector_enabled', True))
        self.inspector_enabled_check.setStyleSheet("font-size: 14px;")
        g1_layout.addWidget(self.inspector_enabled_check)

        interval_row = QWidget()
        interval_layout = QHBoxLayout(interval_row)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(12)
        interval_layout.addWidget(QLabel("巡检间隔:"))
        self.inspect_interval_spin = QSpinBox()
        self.inspect_interval_spin.setRange(60, 86400)
        self.inspect_interval_spin.setSingleStep(60)
        self.inspect_interval_spin.setValue(getattr(config, 'inspector_interval', 3600))
        self.inspect_interval_spin.setMinimumWidth(120)
        self.inspect_interval_spin.setStyleSheet("font-size: 14px;")
        interval_layout.addWidget(self.inspect_interval_spin)
        interval_layout.addWidget(QLabel("秒 (1分钟~24小时)"))
        interval_layout.addStretch()

        def save_settings():
            config.inspector_enabled = self.inspector_enabled_check.isChecked()
            try:
                config.inspector_interval = self.inspect_interval_spin.value()
            except:
                pass
            if hasattr(self, 'main_gui') and self.main_gui and hasattr(self.main_gui, '_save_all_config'):
                self.main_gui._save_all_config()
            if config.inspector_enabled:
                self.start_inspector()
            else:
                self.stop_inspector()
            QMessageBox.information(self, "成功", "巡检设置已保存")

        interval_layout.addWidget(_make_btn("💾 保存设置", "success-outline", save_settings))
        g1_layout.addWidget(interval_row)
        main_layout.addWidget(group1)

        # 状态与控制
        status_frame = QFrame()
        status_frame.setProperty("cssClass", "group-frame")
        status_frame.setStyleSheet("")
        sf_layout = QVBoxLayout(status_frame)
        sf_layout.setContentsMargins(20, 20, 20, 20)
        sf_layout.setSpacing(16)

        status_title = QLabel("巡检状态")
        status_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        sf_layout.addWidget(status_title)

        self.inspect_status = QLabel("巡检器未启动")
        self.inspect_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inspect_status.setStyleSheet("font-size: 16px; color: #7f8c8d; font-weight: 600; padding: 12px;")
        sf_layout.addWidget(self.inspect_status)

        btn_frame = QWidget()
        bf_layout = QHBoxLayout(btn_frame)
        bf_layout.setContentsMargins(0, 0, 0, 0)
        bf_layout.setSpacing(12)
        bf_layout.addStretch()
        bf_layout.addWidget(_make_btn("▶ 启动巡检器", "success", self.start_inspector))
        bf_layout.addWidget(_make_btn("🔍 立即巡检", "primary", self.manual_inspect))
        bf_layout.addWidget(_make_btn("⏹️ 停止巡检器", "danger", self.stop_inspector))
        bf_layout.addStretch()
        sf_layout.addWidget(btn_frame)

        main_layout.addWidget(status_frame)
        main_layout.addStretch()

        if getattr(config, 'inspector_enabled', True):
            self.start_inspector()
        else:
            self.inspect_status.setText("巡检器已禁用")

    def manual_inspect(self):
        inspector.trigger_inspection("manual")
        self.inspect_status.setText("手动巡检已触发")
        self.inspect_status.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: 600; padding: 12px;")
        QTimer.singleShot(5000, lambda: self._reset_inspect_status())

    def _reset_inspect_status(self):
        self.inspect_status.setText("巡检器运行中")
        self.inspect_status.setStyleSheet("color: white; font-size: 16px; font-weight: 600; padding: 12px;" if self._is_dark else "color: #2c3e50; font-size: 16px; font-weight: 600; padding: 12px;")

    def start_inspector(self):
        inspector.set_interval(self.inspect_interval_spin.value())
        inspector.start()
        self.inspect_status.setText("巡检器运行中")
        self.inspect_status.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: 600; padding: 12px;")

    def stop_inspector(self):
        inspector.stop()
        self.inspect_status.setText("巡检器已停止")
        self.inspect_status.setStyleSheet("color: #e74c3c; font-size: 16px; font-weight: 600; padding: 12px;")

    def call_ai_for_inspection(self, prompt, reply_callback):
        if hasattr(self, 'main_gui') and self.main_gui:
            original_callback = self.main_gui.agent.output_callback
            self.main_gui.agent.output_callback = lambda msg: None
            try:
                self.main_gui.agent.run(prompt)
            finally:
                self.main_gui.agent.output_callback = original_callback
        else:
            print("[巡检] 无法调用AI，缺少主窗口引用")

    # -------------------- 配置导入导出 --------------------
    def export_config(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON 文件 (*.json);;所有文件 (*.*)"
        )
        if not file_path:
            return
        try:
            config_data = {
                "devices": [dev.to_dict() for dev in iot_manager.devices.values()],
                "sensors": [sen.to_dict() for sen in iot_manager.sensors.values()],
                "triggers": [trig.to_dict() for trig in iot_manager.triggers.values()]
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", f"配置已导出到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def import_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON 文件 (*.json);;所有文件 (*.*)"
        )
        if not file_path:
            return
        reply = QMessageBox.question(self, "确认",
                                     "导入将覆盖当前所有设备、传感器、触发器配置，是否继续？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            iot_manager.devices.clear()
            iot_manager.sensors.clear()
            iot_manager.triggers.clear()
            for dev_data in data.get("devices", []):
                dev = IOTDevice(dev_data)
                iot_manager.devices[dev.name] = dev
            for sen_data in data.get("sensors", []):
                sen = IOTSensor(sen_data)
                iot_manager.sensors[sen.name] = sen
            for trig_data in data.get("triggers", []):
                trig = IOTTrigger(trig_data)
                iot_manager.triggers[trig.name] = trig
            iot_manager._save_devices()
            iot_manager._save_sensors()
            iot_manager._save_triggers()
            iot_manager._stop_all_listeners()
            iot_manager._start_sensor_listeners()
            self._refresh_all()
            QMessageBox.information(self, "成功", "配置导入成功，已重新加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def reset_config(self):
        reply = QMessageBox.question(self, "确认重置",
                                     "此操作将删除所有设备、传感器、触发器配置，且不可恢复。是否继续？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            iot_manager.devices.clear()
            iot_manager.sensors.clear()
            iot_manager.triggers.clear()
            iot_manager._save_devices()
            iot_manager._save_sensors()
            iot_manager._save_triggers()
            iot_manager._stop_all_listeners()
            iot_manager._start_sensor_listeners()
            self._refresh_all()
            QMessageBox.information(self, "成功", "配置已重置")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重置失败: {e}")

    # -------------------- 内置服务器 --------------------
    def create_servers_tab(self):
        try:
            import paho.mqtt.client
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt"])

        tab = QWidget()
        self.notebook.addTab(tab, "内置服务器")

        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(20, 20, 20, 20)
        tab_layout.setSpacing(16)

        title = QLabel("🚀 内置服务器")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        tab_layout.addWidget(title)
        tab_layout.addSpacing(4)

        inner_notebook = QTabWidget()
        tab_layout.addWidget(inner_notebook)

        mqtt_frame = QWidget()
        inner_notebook.addTab(mqtt_frame, "MQTT 服务器")
        self._create_mqtt_panel(mqtt_frame)

        tcp_frame = QWidget()
        inner_notebook.addTab(tcp_frame, "TCP 服务器")
        self._create_tcp_panel(tcp_frame)

    # ── MQTT 面板 ──
    def _create_mqtt_panel(self, parent):
        parent_layout = QVBoxLayout(parent)
        parent_layout.setContentsMargins(0, 0, 0, 0)
        parent_layout.setSpacing(16)

        # 控制面板
        control_frame = QFrame()
        control_frame.setProperty("cssClass", "group-frame")
        control_frame.setStyleSheet("")
        cf_layout = QHBoxLayout(control_frame)
        cf_layout.setContentsMargins(20, 16, 20, 16)
        cf_layout.setSpacing(16)

        cf_layout.addWidget(QLabel("端口:"))
        self.mqtt_port_spin = QSpinBox()
        self.mqtt_port_spin.setRange(1024, 65535)
        self.mqtt_port_spin.setValue(1883)
        self.mqtt_port_spin.setFixedWidth(100)
        cf_layout.addWidget(self.mqtt_port_spin)

        cf_layout.addSpacing(16)
        self.mqtt_status_label = QLabel("未启动")
        self.mqtt_status_label.setStyleSheet("color: #e74c3c; font-weight: 600; font-size: 14px;")
        cf_layout.addWidget(self.mqtt_status_label)
        cf_layout.addStretch()

        self.mqtt_start_btn = _make_btn("▶ 启动", "success", self._start_mqtt)
        self.mqtt_stop_btn = _make_btn("⏹ 停止", "danger", self._stop_mqtt)
        self.mqtt_stop_btn.setEnabled(False)
        self.mqtt_start_btn.setFixedHeight(36)
        self.mqtt_stop_btn.setFixedHeight(36)
        cf_layout.addWidget(self.mqtt_start_btn)
        cf_layout.addWidget(self.mqtt_stop_btn)

        parent_layout.addWidget(control_frame)

        # 主题管理
        topic_frame = QWidget()
        tf_layout = QVBoxLayout(topic_frame)
        tf_layout.setContentsMargins(0, 0, 0, 0)
        tf_layout.setSpacing(12)

        topic_title = QLabel("📡 主题消息记录")
        topic_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        tf_layout.addWidget(topic_title)

        topic_content = QFrame()
        topic_content.setProperty("cssClass", "group-frame")
        topic_content.setStyleSheet("")
        tc_layout = QVBoxLayout(topic_content)
        tc_layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        tc_layout.addWidget(splitter)

        left_frame = QWidget()
        lf_layout = QVBoxLayout(left_frame)
        lf_layout.setContentsMargins(0, 0, 0, 0)
        lf_layout.setSpacing(8)
        lf_layout.addWidget(QLabel("订阅的主题"))
        self.topic_listbox = QListWidget()
        self.topic_listbox.currentRowChanged.connect(self._on_topic_select_row)
        lf_layout.addWidget(self.topic_listbox)

        topic_btn_row = QWidget()
        tbr_layout = QHBoxLayout(topic_btn_row)
        tbr_layout.setContentsMargins(0, 0, 0, 0)
        tbr_layout.setSpacing(8)
        tbr_layout.addWidget(_make_btn("➕ 添加主题", "success-outline", self._add_topic))
        tbr_layout.addWidget(_make_btn("❌ 删除主题", "danger-outline", self._del_topic))
        lf_layout.addWidget(topic_btn_row)

        splitter.addWidget(left_frame)

        right_frame = QWidget()
        rf_layout = QVBoxLayout(right_frame)
        rf_layout.setContentsMargins(0, 0, 0, 0)
        rf_layout.setSpacing(8)
        rf_layout.addWidget(QLabel("消息记录"))
        self.topic_msg_text = QTextEdit()
        self.topic_msg_text.setReadOnly(True)
        self.topic_msg_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px;")
        rf_layout.addWidget(self.topic_msg_text)

        msg_btn_row = QWidget()
        mbr_layout = QHBoxLayout(msg_btn_row)
        mbr_layout.setContentsMargins(0, 0, 0, 0)
        mbr_layout.setSpacing(8)
        mbr_layout.addWidget(_make_btn("清空记录", "secondary-outline", self._clear_topic_msgs))
        mbr_layout.addWidget(_make_btn("查看历史", "info-outline", self._view_topic_history))
        mbr_layout.addStretch()
        rf_layout.addWidget(msg_btn_row)

        splitter.addWidget(right_frame)
        splitter.setSizes([200, 450])

        tf_layout.addWidget(topic_content)
        parent_layout.addWidget(topic_frame)

        # 服务器日志
        log_frame_w = QWidget()
        lfw_layout = QVBoxLayout(log_frame_w)
        lfw_layout.setContentsMargins(0, 0, 0, 0)
        lfw_layout.setSpacing(8)

        log_title = QLabel("📝 服务器日志")
        log_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        lfw_layout.addWidget(log_title)

        log_content = QFrame()
        log_content.setProperty("cssClass", "group-frame")
        log_content.setStyleSheet("")
        lc_layout = QVBoxLayout(log_content)
        lc_layout.setContentsMargins(12, 12, 12, 12)
        self.mqtt_log_text = QTextEdit()
        self.mqtt_log_text.setReadOnly(True)
        self.mqtt_log_text.setMaximumHeight(180)
        self.mqtt_log_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px; background-color: #0d1117;")
        lc_layout.addWidget(self.mqtt_log_text)

        lfw_layout.addWidget(log_content)
        parent_layout.addWidget(log_frame_w)

        self.mqtt_sub_client = None
        self.mqtt_topics = {}
        self._load_mqtt_topics()

    # ── MQTT 信号处理 ──
    def _on_mqtt_log(self, msg):
        self.mqtt_log_text.append(msg)

    def _on_topic_list_update(self, topic):
        items = [self.topic_listbox.item(i).text() for i in range(self.topic_listbox.count())]
        if topic not in items:
            self.topic_listbox.addItem(topic)

    def _on_topic_msg_update(self, topic, _dummy):
        sel = self.topic_listbox.currentRow()
        if sel >= 0 and self.topic_listbox.item(sel).text() == topic:
            self._show_topic_messages(topic)

    # ── MQTT 操作 ──
    def _start_mqtt(self):
        from builtin_servers import mqtt_manager
        port = self.mqtt_port_spin.value()
        mqtt_manager.set_log_callback(lambda msg: self.mqtt_log_signal.emit(msg))
        if mqtt_manager.start(port=port):
            self.mqtt_status_label.setText("运行中")
            self.mqtt_status_label.setStyleSheet("color: #27ae60; font-weight: 600; font-size: 14px;")
            self.mqtt_start_btn.setEnabled(False)
            self.mqtt_stop_btn.setEnabled(True)
            self._start_mqtt_subscriber()

    def _stop_mqtt(self):
        from builtin_servers import mqtt_manager
        mqtt_manager.stop()
        self.mqtt_status_label.setText("未启动")
        self.mqtt_status_label.setStyleSheet("color: #e74c3c; font-weight: 600; font-size: 14px;")
        self.mqtt_start_btn.setEnabled(True)
        self.mqtt_stop_btn.setEnabled(False)
        if self.mqtt_sub_client:
            self.mqtt_sub_client.loop_stop()
            self.mqtt_sub_client.disconnect()
            self.mqtt_sub_client = None

    def _start_mqtt_subscriber(self):
        import paho.mqtt.client as mqtt
        import time

        self.mqtt_sub_client = mqtt.Client()
        self.mqtt_sub_client.on_connect = self._on_subscribe_connect
        self.mqtt_sub_client.on_message = self._on_subscribe_message

        try:
            self.mqtt_sub_client.connect("127.0.0.1", self.mqtt_port_spin.value())
            self.mqtt_sub_client.loop_start()

            for _ in range(20):
                if self.mqtt_sub_client.is_connected():
                    break
                time.sleep(0.1)

            if not self.mqtt_sub_client.is_connected():
                self.mqtt_log_signal.emit("[订阅客户端] 连接失败，请检查MQTT服务器是否运行")
            else:
                self.mqtt_log_signal.emit("[订阅客户端] 已连接并准备订阅")
        except Exception as e:
            self.mqtt_log_signal.emit(f"[订阅客户端] 启动异常: {e}")

    def _on_subscribe_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("#")
            self.mqtt_log_signal.emit("[订阅客户端] 已订阅所有主题 (#)")
        else:
            self.mqtt_log_signal.emit(f"[订阅客户端] 连接错误，错误码: {rc}")

    def _on_subscribe_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        self._record_mqtt_message(topic, payload)
        if self.mqtt_sub_client:
            self.mqtt_sub_client.loop_start()

    def _record_mqtt_message(self, topic, payload):
        try:
            if topic not in self.mqtt_topics:
                self.mqtt_topics[topic] = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.mqtt_topics[topic].append(f"[{timestamp}] {payload}")
            self.topic_update_signal.emit(topic)
            sel = self.topic_listbox.currentRow()
            if sel >= 0 and self.topic_listbox.item(sel).text() == topic:
                QTimer.singleShot(0, lambda: self._show_topic_messages(topic))
            self._save_mqtt_topics()
        except Exception as e:
            print(f"记录MQTT消息失败: {e}")

    def _show_topic_messages(self, topic):
        self.topic_msg_text.clear()
        if topic in self.mqtt_topics:
            for msg in self.mqtt_topics[topic]:
                self.topic_msg_text.append(msg)

    def _on_topic_select_row(self, row):
        if row >= 0:
            topic = self.topic_listbox.item(row).text()
            self._show_topic_messages(topic)

    def _add_topic(self):
        win = QDialog(self)
        win.setWindowTitle("添加订阅主题")
        win.resize(350, 180)
        win.setWindowModality(Qt.WindowModality.WindowModal)
        win_layout = QVBoxLayout(win)
        win_layout.setContentsMargins(20, 20, 20, 20)
        win_layout.setSpacing(12)

        win_layout.addWidget(QLabel("主题名称:"))
        topic_entry = QLineEdit()
        win_layout.addWidget(topic_entry)

        def do_add():
            topic = topic_entry.text().strip()
            if topic:
                if self.mqtt_sub_client and self.mqtt_sub_client.is_connected():
                    self.mqtt_sub_client.subscribe(topic)
                    self.mqtt_log_signal.emit(f"[订阅客户端] 已订阅主题: {topic}")
                else:
                    self.mqtt_log_signal.emit("[订阅客户端] 尚未连接，无法订阅新主题")
                if topic not in self.mqtt_topics:
                    self.mqtt_topics[topic] = []
                items = [self.topic_listbox.item(i).text() for i in range(self.topic_listbox.count())]
                if topic not in items:
                    self.topic_listbox.addItem(topic)
                win.accept()

        win_layout.addWidget(_make_btn("订阅", "success", do_add))
        win.exec()

    def _del_topic(self):
        row = self.topic_listbox.currentRow()
        if row >= 0:
            topic = self.topic_listbox.item(row).text()
            reply = QMessageBox.question(self, "确认", f"删除主题 {topic} 的记录？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.topic_listbox.takeItem(row)
                if topic in self.mqtt_topics:
                    del self.mqtt_topics[topic]
                self.topic_msg_text.clear()
                self._save_mqtt_topics()

    def _clear_topic_msgs(self):
        row = self.topic_listbox.currentRow()
        if row >= 0:
            topic = self.topic_listbox.item(row).text()
            if topic in self.mqtt_topics:
                self.mqtt_topics[topic] = []
                self._show_topic_messages(topic)
                self._save_mqtt_topics()

    def _view_topic_history(self):
        row = self.topic_listbox.currentRow()
        if row < 0:
            return
        topic = self.topic_listbox.item(row).text()
        win = QDialog(self)
        win.setWindowTitle(f"消息历史 - {topic}")
        win.resize(600, 450)
        win_layout = QVBoxLayout(win)
        win_layout.setContentsMargins(12, 12, 12, 12)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px;")
        win_layout.addWidget(text)
        for msg in self.mqtt_topics.get(topic, []):
            text.append(msg)
        win.exec()

    def _load_mqtt_topics(self):
        file_path = "./builtin_servers_data/mqtt_topics.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.mqtt_topics = data
                for topic in self.mqtt_topics:
                    self.topic_listbox.addItem(topic)

    def _save_mqtt_topics(self):
        os.makedirs("./builtin_servers_data", exist_ok=True)
        with open("./builtin_servers_data/mqtt_topics.json", 'w', encoding='utf-8') as f:
            json.dump(self.mqtt_topics, f, indent=2)

    # ── TCP 面板 ──
    def _create_tcp_panel(self, parent):
        parent_layout = QVBoxLayout(parent)
        parent_layout.setContentsMargins(0, 0, 0, 0)
        parent_layout.setSpacing(16)

        control_frame = QFrame()
        control_frame.setProperty("cssClass", "group-frame")
        control_frame.setStyleSheet("")
        cf_layout = QHBoxLayout(control_frame)
        cf_layout.setContentsMargins(20, 16, 20, 16)
        cf_layout.setSpacing(16)

        cf_layout.addWidget(QLabel("端口:"))
        self.tcp_port_spin = QSpinBox()
        self.tcp_port_spin.setRange(1024, 65535)
        self.tcp_port_spin.setValue(8888)
        self.tcp_port_spin.setFixedWidth(100)
        cf_layout.addWidget(self.tcp_port_spin)

        cf_layout.addSpacing(16)
        self.tcp_status_label = QLabel("未启动")
        self.tcp_status_label.setStyleSheet("color: #e74c3c; font-weight: 600; font-size: 14px;")
        cf_layout.addWidget(self.tcp_status_label)
        cf_layout.addStretch()

        self.tcp_start_btn = _make_btn("▶ 启动", "success", self._start_tcp)
        self.tcp_stop_btn = _make_btn("⏹ 停止", "danger", self._stop_tcp)
        self.tcp_stop_btn.setEnabled(False)
        self.tcp_start_btn.setFixedHeight(36)
        self.tcp_stop_btn.setFixedHeight(36)
        cf_layout.addWidget(self.tcp_start_btn)
        cf_layout.addWidget(self.tcp_stop_btn)

        parent_layout.addWidget(control_frame)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        parent_layout.addWidget(main_splitter)

        left_frame = QWidget()
        lf_layout = QVBoxLayout(left_frame)
        lf_layout.setContentsMargins(0, 0, 0, 0)
        lf_layout.setSpacing(8)
        lf_layout.addWidget(QLabel("已连接的客户端"))
        self.tcp_clients_listbox = QListWidget()
        self.tcp_clients_listbox.currentRowChanged.connect(self._on_tcp_client_select_row)
        lf_layout.addWidget(self.tcp_clients_listbox)
        main_splitter.addWidget(left_frame)

        right_frame = QWidget()
        rf_layout = QVBoxLayout(right_frame)
        rf_layout.setContentsMargins(0, 0, 0, 0)
        rf_layout.setSpacing(10)

        rf_layout.addWidget(QLabel("来自客户端的消息"))
        self.tcp_msg_text = QTextEdit()
        self.tcp_msg_text.setReadOnly(True)
        self.tcp_msg_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px;")
        rf_layout.addWidget(self.tcp_msg_text)

        rf_layout.addWidget(QLabel("发送消息到选中客户端"))
        self.tcp_send_entry = QLineEdit()
        rf_layout.addWidget(self.tcp_send_entry)
        send_btn = _make_btn("发送", "primary", self._tcp_send_to_client)
        send_btn.setFixedHeight(36)
        rf_layout.addWidget(send_btn)
        rf_layout.addStretch()

        main_splitter.addWidget(right_frame)
        main_splitter.setSizes([200, 450])

        # 服务器日志
        log_frame_w = QWidget()
        lfw_layout = QVBoxLayout(log_frame_w)
        lfw_layout.setContentsMargins(0, 0, 0, 0)
        lfw_layout.setSpacing(8)

        log_title = QLabel("📝 服务器日志")
        log_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        lfw_layout.addWidget(log_title)

        log_content = QFrame()
        log_content.setProperty("cssClass", "group-frame")
        log_content.setStyleSheet("")
        lc_layout = QVBoxLayout(log_content)
        lc_layout.setContentsMargins(12, 12, 12, 12)
        self.tcp_log_text = QTextEdit()
        self.tcp_log_text.setReadOnly(True)
        self.tcp_log_text.setMaximumHeight(150)
        self.tcp_log_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px; background-color: #0d1117;")
        lc_layout.addWidget(self.tcp_log_text)

        lfw_layout.addWidget(log_content)
        parent_layout.addWidget(log_frame_w)

        self.tcp_clients = []
        self.current_tcp_client = None

    # ── TCP 信号处理 ──
    def _on_tcp_log(self, msg):
        self.tcp_log_text.append(msg)

    def _on_tcp_message(self, addr, msg):
        self.tcp_msg_text.append(f"[{addr}] {msg}")

    # ── TCP 操作 ──
    def _start_tcp(self):
        from builtin_servers import tcp_manager
        port = self.tcp_port_spin.value()
        tcp_manager.set_log_callback(lambda msg: self.tcp_log_signal.emit(msg))
        tcp_manager.set_message_callback(lambda addr, msg: self.tcp_message_signal.emit(str(addr), msg))
        if tcp_manager.start(port=port):
            self.tcp_status_label.setText("运行中")
            self.tcp_status_label.setStyleSheet("color: #27ae60; font-weight: 600; font-size: 14px;")
            self.tcp_start_btn.setEnabled(False)
            self.tcp_stop_btn.setEnabled(True)
            self._refresh_tcp_clients()

    def _stop_tcp(self):
        from builtin_servers import tcp_manager
        tcp_manager.stop()
        self.tcp_status_label.setText("未启动")
        self.tcp_status_label.setStyleSheet("color: #e74c3c; font-weight: 600; font-size: 14px;")
        self.tcp_start_btn.setEnabled(True)
        self.tcp_stop_btn.setEnabled(False)
        self.tcp_clients_listbox.clear()
        self.tcp_clients.clear()

    def _refresh_tcp_clients(self):
        from builtin_servers import tcp_manager
        clients = tcp_manager.clients.copy()
        self.tcp_clients_listbox.clear()
        self.tcp_clients = []
        for conn, addr in clients:
            addr_str = f"{addr[0]}:{addr[1]}"
            self.tcp_clients_listbox.addItem(addr_str)
            self.tcp_clients.append(addr_str)

    def _on_tcp_client_select_row(self, row):
        if row >= 0 and row < len(self.tcp_clients):
            self.current_tcp_client = self.tcp_clients[row]

    def _tcp_send_to_client(self):
        if not self.current_tcp_client:
            QMessageBox.warning(self, "提示", "请先选择一个客户端")
            return
        msg = self.tcp_send_entry.text().strip()
        if not msg:
            return
        from builtin_servers import tcp_manager
        ip, port = self.current_tcp_client.split(':')
        addr = (ip, int(port))
        if tcp_manager.send_to_client(addr, msg):
            self.tcp_send_entry.clear()
            self.tcp_log_signal.emit(f"发送到 {self.current_tcp_client}: {msg}")
        else:
            QMessageBox.critical(self, "错误", "发送失败，客户端可能已断开")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    config_file = os.path.expanduser("~/.agent_config.json")
    theme = "dark"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                theme = data.get("gui_theme", "dark")
        except:
            pass

    window = QMainWindow()
    tg_app = TGHomeApp(root=window, theme=theme)
    window.setCentralWidget(tg_app)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()