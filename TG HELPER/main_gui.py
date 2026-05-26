# -*- coding: utf-8 -*-
"""
主 GUI 界面 - 布局与核心交互 (PyQt6)
"""
import threading
import os
import sys
import time
import re
import requests
import random
import json
from datetime import datetime
from io import BytesIO
from PIL import Image

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QScrollArea, QSplitter, QTabWidget,
    QStatusBar, QToolBar, QFrame, QMessageBox, QCheckBox, QLineEdit,
    QComboBox, QSpinBox, QFileDialog, QListWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QObject, QThread, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor, QPalette, QKeyEvent

from config import config, banben, CONFIG_FILE
from memory import Memory
from tools import Tools
from agent import AIAgent
from skill_manager import SkillManager
from task_scheduler import TaskScheduler
from plugin_manager import PluginManager
from IOT_manager import iot_manager
from smart_inspector import inspector
from local_model_manager import LocalModelManager

from qq_bot import QQBotHandler
from gui_handlers import bind_handlers
from plugin_v2 import PluginManagerV2, HostAPIImpl, EventBus, SystemEvents
from multi_agent_v2 import MultiAgentOrchestrator

DARK_QSS = """
QMainWindow {
    background-color: #1a1a2e;
}
QToolBar {
    background-color: #16213e;
    border: none;
    spacing: 4px;
    padding: 4px;
}
QToolBar QLabel {
    color: #e8e8e8;
}
QToolBar QPushButton {
    background-color: transparent;
    color: #e8e8e8;
    border: 1px solid #3a4a6b;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13px;
}
QToolBar QPushButton:hover {
    background-color: #2a3a5b;
}
QToolBar QPushButton:pressed {
    background-color: #0f1629;
}
QStatusBar {
    background-color: #16213e;
    color: #b0b0c0;
    border-top: 1px solid #2a2a4a;
    font-size: 13px;
}
QSplitter::handle {
    background-color: #2a2a4a;
    width: 4px;
}
QScrollArea {
    border: none;
    background-color: #1a1a2e;
}
QTextEdit {
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    padding: 6px;
    background-color: #16213e;
    color: #e8e8e8;
    font-size: 14px;
}
QPushButton#sendBtn {
    background-color: #4a90d9;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#sendBtn:hover {
    background-color: #5aa0e9;
}
QPushButton#sendBtn:pressed {
    background-color: #3a80c9;
}
QPushButton#stopBtn {
    background-color: #d94a4a;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#stopBtn:hover {
    background-color: #e95a5a;
}
QTabWidget::pane {
    border: 1px solid #2a2a4a;
    background-color: #1a1a2e;
}
QTabWidget::tab-bar {
    left: 2px;
}
QTabBar::tab {
    background-color: #222240;
    color: #888898;
    border: 1px solid #2a2a4a;
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #e8e8e8;
    border-bottom: 2px solid #4a90d9;
}
QTabBar::tab:hover:!selected {
    background-color: #282848;
}
QLabel {
    color: #e8e8e8;
}
QLineEdit {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e8e8e8;
    selection-background-color: #4a90d9;
}
QCheckBox {
    color: #e8e8e8;
}
QRadioButton {
    color: #e8e8e8;
}
QGroupBox {
    color: #e8e8e8;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1e1e38;
    color: #e8e8e8;
    gridline-color: #2a2a4a;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
}
QTableWidget::item:selected {
    background-color: #4a90d9;
    color: white;
}
QHeaderView::section {
    background-color: #222240;
    color: #b0b0c0;
    border: 1px solid #2a2a4a;
    padding: 4px;
    font-weight: bold;
}
QListWidget {
    background-color: #16213e;
    color: #e8e8e8;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #4a90d9;
    color: white;
}
QProgressBar {
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    background-color: #16213e;
    text-align: center;
    color: #e8e8e8;
}
QProgressBar::chunk {
    background-color: #4a90d9;
    border-radius: 3px;
}
"""

FLATLY_QSS = """
QMainWindow {
    background-color: #f8f9fa;
}
QToolBar {
    background-color: #2c3e50;
    border: none;
    spacing: 4px;
    padding: 4px;
}
QToolBar QLabel {
    color: #ffffff;
}
QToolBar QPushButton {
    background-color: transparent;
    color: #ffffff;
    border: 1px solid #4a6785;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13px;
}
QToolBar QPushButton:hover {
    background-color: #3d566e;
}
QToolBar QPushButton:pressed {
    background-color: #1a252f;
}
QStatusBar {
    background-color: #ecf0f1;
    color: #2c3e50;
    border-top: 1px solid #dee2e6;
    font-size: 13px;
}
QSplitter::handle {
    background-color: #dee2e6;
    width: 4px;
}
QScrollArea {
    border: none;
    background-color: #ffffff;
}
QTextEdit {
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 6px;
    background-color: #ffffff;
    font-size: 14px;
}
QPushButton#sendBtn {
    background-color: #2c3e50;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#sendBtn:hover {
    background-color: #3d566e;
}
QPushButton#sendBtn:pressed {
    background-color: #1a252f;
}
QPushButton#stopBtn {
    background-color: #e74c3c;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#stopBtn:hover {
    background-color: #c0392b;
}
QTabWidget::pane {
    border: 1px solid #dee2e6;
    background-color: #ffffff;
}
QTabWidget::tab-bar {
    left: 2px;
}
QTabBar::tab {
    background-color: #ecf0f1;
    color: #7f8c8d;
    border: 1px solid #dee2e6;
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2c3e50;
    border-bottom: 2px solid #2c3e50;
}
QTabBar::tab:hover:!selected {
    background-color: #dfe6e9;
}
"""


class ChatTextEdit(QTextEdit):
    returnPressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if (event.key() == Qt.Key.Key_Return and
                not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)


class AgentGUI(QMainWindow):
    _bubble_signal = pyqtSignal(str, bool, object)
    _system_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = self
        self._bubble_signal.connect(self._on_bubble_signal)
        self._system_signal.connect(self._on_system_signal)

        self.setWindowTitle(f"TGAI {banben}")
        self.resize(1400, 900)
        self.setMinimumSize(1000, 700)

        theme_name = getattr(config, 'gui_theme', 'flatly')
        self.current_theme = theme_name
        self.setStyleSheet(FLATLY_QSS)

        self.last_sent_message_id = None
        self.agent_running = False
        self.agent_stop_event = threading.Event()
        self.font = QFont("微软雅黑", 10)
        self._animating = False
        self._send_action = "send"

        self.debug_mode = QCheckBox()
        self.debug_mode.setChecked(config.debug_mode)
        self.fun_mode = QCheckBox()
        self.fun_mode.setChecked(getattr(config, 'fun_mode_enabled', False))

        self.qq_handler = None
        self.settings_visible = True
        self.settings_width = 400

        self.personality_name = getattr(config, 'current_personality', 'TGAI')
        self.personality_dir = getattr(config, 'personality_dir', './AI人格')
        self.current_persona_name = self.personality_name
        self.init_default_personalities()
        self.load_personalities()

        self.memory = Memory(
            mind_dir=config.memory_dir,
            persona_name=self.personality_name,
            config={
                "enable_vector": False,
                "reflection_interval_seconds": 3600,
                "archive_trigger": 40,
                "retrieve_limit": 10,
                "fts_weight": 0.7,
                "relevance_threshold": 0.35,
                "time_decay_enabled": True,
            }
        )
        if getattr(config, 'auto_backup_short_term', False):
            backup_path = self.memory.backup_short_term()
            if backup_path:
                print(f"已备份短期记忆到 {backup_path}")
                self.memory.clear_short_term()
                print("已清空短期记忆")

        self.tools = Tools(self.memory,
                           confirm_callback=self.request_confirmation,
                           output_callback=self.display_assistant_message,
                           task_scheduler=None,
                           gui=self)
        self.skill_manager = SkillManager(getattr(config, 'skills_dirs', ["./skills"]))

        self.agent = AIAgent(config, self.memory, self.tools, skill_manager=self.skill_manager)
        self.agent.output_callback = self.display_assistant_message
        self.agent.system_output_callback = self.display_system_message

        self.memory.set_ai_summarize_callback(self._memory_summarize_callback)
        self.memory.set_ai_reflection_callback(self._memory_reflection_callback)

        iot_manager.set_ai_callback(self.display_assistant_message)
        iot_manager.set_ai_trigger_callback(self.on_sensor_trigger)
        iot_manager.set_qq_send_callback(self.send_qq_message)

        self.inspect_interval_var = 3600
        if config.inspector_enabled:
            self.start_inspector()
        else:
            inspector.set_ai_callback(self._inspector_ai_callback)

        self.task_scheduler = TaskScheduler(
            config_dir=getattr(config, 'tasks_dir', './config'),
            on_task_trigger=self.on_task_trigger
        )
        self.task_scheduler.start()
        self.tools.task_scheduler = self.task_scheduler

        self.multi_agent_enabled = getattr(config, 'multi_agent_enabled', False)
        self.multi_agent_orchestrator = MultiAgentOrchestrator(self)
        self.multi_agent_btn = None
        self.task_list_window = None
        if self.multi_agent_enabled:
            planner_p = getattr(config, 'multi_agent_planner_persona', 'TGAI')
            worker_p = getattr(config, 'multi_agent_worker_persona', '艾依')
            reviewer_p = getattr(config, 'multi_agent_reviewer_persona', '塔戈')
            try:
                self.multi_agent_orchestrator.configure(True, planner_p, worker_p, reviewer_p)
            except Exception as e:
                QMessageBox.critical(self, "多Agent配置错误", str(e))

        self.plugin_manager_v2 = PluginManagerV2()
        self.plugin_manager_v2.set_gui_instance(self)
        self.plugin_manager_v2.set_memory_instance(self.memory)
        self.plugin_manager_v2.set_agent_instance(self.agent)
        self.plugin_manager_v2.set_tools_instance(self.tools)
        self.plugin_manager_v2.set_config_instance(config)
        self.plugin_manager_v2.set_debug_mode(self.debug_mode.isChecked())

        loaded_v2_plugins = self.plugin_manager_v2.load_all_plugins()
        if loaded_v2_plugins:
            print(f"[MainGUI] 已加载 {len(loaded_v2_plugins)} 个 V2 插件: {loaded_v2_plugins}")

        self.event_bus = self.plugin_manager_v2.get_event_bus()

        def handle_custom_ai_call(event):
            data = event.data
            prompt = data.get("prompt", "")
            system_prompt = data.get("system_prompt", "")
            callback = data.get("callback")
            original_cb = self.agent.output_callback
            response = [None]

            def capture(msg):
                response[0] = msg

            def run_in_thread():
                self.agent.output_callback = capture
                self.agent.stop_event = self.agent_stop_event
                self.agent.run(prompt)
                self.agent.output_callback = original_cb
                if callback:
                    QTimer.singleShot(0, lambda: callback(response[0]))

            threading.Thread(target=run_in_thread, daemon=True).start()

        self.event_bus.subscribe("agent.custom_call", handle_custom_ai_call, plugin_id="system")

        def on_ui_ready():
            self.event_bus.emit(SystemEvents.UI_READY, {"gui": self}, "system")

        QTimer.singleShot(100, on_ui_ready)

        self.local_model_manager = LocalModelManager()
        bind_handlers(self)

        self._create_toolbar()
        self._create_central_area()
        self._create_statusbar()

        self.create_api_tab()
        self.create_qq_tab()
        self.create_security_tab()
        self.create_skill_tab()
        self.create_plugin_tab()
        self.create_tasks_tab()
        self.create_personality_tab()
        self.create_debug_tab()
        self.create_local_model_tab()
        self.create_model_selector_tab()
        self.create_multi_agent_tab()

        self.display_assistant_message("你好世界！今天可以帮到什么吗？")

        # 启动后自动内存优化（延迟2秒，等界面渲染完毕）
        QTimer.singleShot(2000, self._startup_optimize)

        if config.qq_enabled:
            QTimer.singleShot(500, self.start_qq_bot)

        self.update_current_personality_display()

    def schedule_on_main(self, callback):
        QTimer.singleShot(0, callback)

    def closeEvent(self, event):
        self.on_closing()
        event.accept()

    def _create_central_area(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        self.content_frame = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.content_frame, 1)

        self.chat_frame = QWidget()
        self.content_frame.addWidget(self.chat_frame)

        self._create_chat_area()

        self.settings_frame = QWidget()
        self.settings_frame.setMinimumWidth(300)
        self.content_frame.addWidget(self.settings_frame)

        self._create_settings_area()

        self.content_frame.setSizes([1000, self.settings_width])
        self.content_frame.setStretchFactor(0, 1)
        self.content_frame.setStretchFactor(1, 0)

    def _create_statusbar(self):
        self.status_label = QStatusBar()
        self.status_label.showMessage("就绪")
        self.setStatusBar(self.status_label)

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        config.gui_theme = theme_name
        self._save_all_config()
        dark_themes = {"darkly", "cyborg", "vapor", "solar", "superhero"}
        if theme_name in dark_themes:
            self.setStyleSheet(DARK_QSS)
        else:
            self.setStyleSheet(FLATLY_QSS)
        if hasattr(self, '_tg_home_window') and self._tg_home_window is not None:
            if hasattr(self._tg_home_app, 'apply_theme'):
                self._tg_home_app.apply_theme(theme_name)

    def _memory_reflection_callback(self, dialog_text: str) -> str:
        prompt = f"请从以下对话中提炼出关于用户的重要信息、偏好、决策或事实，用简洁的要点形式输出（每条一行），不要超过200字：\n\n{dialog_text}"
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.agent.call_llm(messages)
            return response.strip()
        except Exception as e:
            print(f"[Memory] 反思回调失败: {e}")
            return ""

    def _memory_summarize_callback(self, lines):
        text = ''.join(lines)
        if len(text) > 4000:
            text = text[:4000] + "..."
        prompt = f"请将以下对话内容总结为一段简短的摘要（50字以内）：\n{text}"
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.agent.call_llm(messages)
            return response.strip()
        except Exception as e:
            print(f"[Memory] 生成摘要失败: {e}")
            return ""

    def send_qq_message(self, target_type, target_id, content):
        result = self.tools.send_to(target_type, target_id, content)
        self.display_system_message(f"[QQ发送] {result}", source="sensor")

    def on_sensor_trigger(self, prompt: str, reply_callback=None):
        print(f"[传感器触发] prompt: {prompt}")
        self.display_system_message(f"[传感器触发] {prompt}", source="sensor")

        def capture_and_reply(message):
            if message and reply_callback:
                reply_callback(message)
                self.display_assistant_message(f"[AI回复至设备] {message}", source="local")

        original_callback = self.agent.output_callback
        if reply_callback:
            self.agent.output_callback = capture_and_reply
        else:
            self.agent.output_callback = self.display_assistant_message

        try:
            self.agent.run(prompt)
        finally:
            self.agent.output_callback = original_callback

    def display_system_message(self, message, source="sensor"):
        if threading.current_thread() is threading.main_thread():
            try:
                self._create_system_bubble(message)
                self._scroll_chat_to_bottom()
            except Exception as e:
                print(f"[GUI] 创建系统消息气泡失败(主线程): {e}")
        else:
            self._system_signal.emit(message, source)

    @pyqtSlot(str, str)
    def _on_system_signal(self, message, source):
        try:
            self._create_system_bubble(message)
            self._scroll_chat_to_bottom()
        except Exception as e:
            print(f"[GUI] 创建系统消息气泡失败(信号槽): {e}")

    def _create_system_bubble(self, text):
        frame = QFrame(self.message_container)
        frame.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 3, 10, 3)
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(550)
        bubble.setStyleSheet(
            "background-color: #555555; color: #ffffff; padding: 10px; "
            "border-radius: 8px; font-size: 13px;"
        )
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout.addWidget(bubble)
        layout.addStretch()
        self._insert_bubble(frame)

    def _scroll_chat_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _insert_bubble(self, frame):
        count = self.message_layout.count()
        if count > 0:
            stretch_item = self.message_layout.takeAt(count - 1)
            if stretch_item.spacerItem():
                del stretch_item
        self.message_layout.addWidget(frame)
        self.message_layout.addStretch()
        QTimer.singleShot(10, self._scroll_chat_to_bottom)

    def _create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        self.avatar_label = QLabel("头像")
        self.avatar_label.setFixedSize(32, 32)
        self.avatar_label.setStyleSheet("border-radius: 4px; border: 1px solid #4a6785;")
        toolbar.addWidget(self.avatar_label)

        self.personality_label = QLabel(f"当前人格: {self.personality_name}")
        self.personality_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #ffffff; padding: 0 8px;"
        )
        toolbar.addWidget(self.personality_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        tg_home_btn = QPushButton("🏠 TG Home")
        tg_home_btn.clicked.connect(self.open_tg_home)
        btn_layout.addWidget(tg_home_btn)

        self.toggle_settings_btn = QPushButton("⚙️ 收起设置")
        self.toggle_settings_btn.clicked.connect(self.toggle_settings)
        btn_layout.addWidget(self.toggle_settings_btn)

        clear_btn = QPushButton("🧹 清屏")
        clear_btn.clicked.connect(self.clear_chat)
        btn_layout.addWidget(clear_btn)

        self.fun_mode_btn = QPushButton(
            "🔥 热闹模式: 关" if not self.fun_mode.isChecked() else "🔥 热闹模式: 开"
        )
        self.fun_mode_btn.clicked.connect(self.toggle_fun_mode)
        btn_layout.addWidget(self.fun_mode_btn)

        self.multi_agent_btn = QPushButton("📋 查看多Agent任务列表")
        self.multi_agent_btn.clicked.connect(self.show_task_list_window)
        self.multi_agent_btn.setStyleSheet(
            "QPushButton { color: #3498db; border-color: #3498db; }"
        )
        if self.multi_agent_enabled:
            btn_layout.addWidget(self.multi_agent_btn)

        about_btn = QPushButton("❓ 关于")
        about_btn.clicked.connect(self.show_about_dialog)
        btn_layout.addWidget(about_btn)

        toolbar.addWidget(btn_frame)

    def _create_chat_area(self):
        layout = QVBoxLayout(self.chat_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.message_container = QWidget()
        self.message_container.setObjectName("messageContainer")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.message_layout.addStretch()
        self.scroll_area.setWidget(self.message_container)

        layout.addWidget(self.scroll_area, 1)

        input_frame = QWidget()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 5, 0, 5)
        input_layout.setSpacing(5)

        self.input_text = ChatTextEdit()
        self.input_text.setMaximumHeight(120)
        self.input_text.setMinimumHeight(60)
        self.input_text.setPlaceholderText("输入消息...")
        self.input_text.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_text, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedWidth(80)
        self.send_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_frame)

    def _create_settings_area(self):
        layout = QVBoxLayout(self.settings_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.settings_inner = QWidget()
        settings_inner_layout = QVBoxLayout(self.settings_inner)
        settings_inner_layout.setContentsMargins(2, 2, 2, 2)
        settings_inner_layout.setSpacing(0)

        self.notebook = QTabWidget()
        self.notebook.setTabPosition(QTabWidget.TabPosition.North)
        self.notebook.setElideMode(Qt.TextElideMode.ElideNone)
        self.notebook.setUsesScrollButtons(True)
        settings_inner_layout.addWidget(self.notebook)

        self.settings_scroll.setWidget(self.settings_inner)
        layout.addWidget(self.settings_scroll)

    def toggle_settings(self):
        if self.settings_visible:
            self.settings_frame.hide()
            self.toggle_settings_btn.setText("⚙️ 展开设置")
            self.settings_visible = False
        else:
            self.settings_frame.show()
            self.toggle_settings_btn.setText("⚙️ 收起设置")
            self.settings_visible = True

    def toggle_fun_mode(self):
        current = self.fun_mode.isChecked()
        self.fun_mode.setChecked(not current)
        self.fun_mode_btn.setText(
            "🔥 热闹模式: 开" if self.fun_mode.isChecked() else "🔥 热闹模式: 关"
        )

    def _on_frame_configure(self, event=None):
        pass

    def _on_canvas_configure(self, event=None):
        pass

    def update_current_personality_display(self):
        self.personality_label.setText(f"当前人格: {self.personality_name}")
        avatar_path = None
        for p in self.personalities:
            if p['name'] == self.personality_name:
                avatar_path = p.get('avatar')
                break
        if avatar_path and os.path.exists(avatar_path):
            try:
                pixmap = QPixmap(avatar_path).scaled(
                    32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                if not pixmap.isNull():
                    self.avatar_label.setPixmap(pixmap)
                else:
                    self.avatar_label.setText("头像")
            except Exception:
                self.avatar_label.setText("头像")
        else:
            self.avatar_label.setText("头像")

    def _create_message_bubble(self, text, is_user=False, avatar_path=None):
        frame = QFrame(self.message_container)
        frame.setFrameShape(QFrame.Shape.NoFrame)
        outer_layout = QHBoxLayout(frame)
        outer_layout.setContentsMargins(10, 3, 10, 3)

        avatar_label = QLabel()
        avatar_label.setFixedSize(40, 40)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setStyleSheet("border-radius: 4px;")

        if avatar_path and os.path.exists(avatar_path):
            try:
                pixmap = QPixmap(avatar_path).scaled(
                    36, 36, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                if not pixmap.isNull():
                    avatar_label.setPixmap(pixmap)
                else:
                    avatar_label.setText("AI" if not is_user else "用户")
            except Exception:
                avatar_label.setText("AI" if not is_user else "用户")
        else:
            avatar_label.setText("AI" if not is_user else "用户")

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(550)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        if is_user:
            bubble_color = "#DCF8C6"
            bubble.setAlignment(Qt.AlignmentFlag.AlignLeft)
            outer_layout.addStretch()
            outer_layout.addWidget(bubble)
            outer_layout.addWidget(avatar_label)
        else:
            bubble_color = "#E3F2FD"
            bubble.setAlignment(Qt.AlignmentFlag.AlignLeft)
            outer_layout.addWidget(avatar_label)
            outer_layout.addWidget(bubble)
            outer_layout.addStretch()

        bubble_style = (
            f"background-color: {bubble_color}; color: #000000; "
            "padding: 10px; border-radius: 8px; font-size: 13px;"
        )
        if hasattr(self, '_plugin_styles'):
            if is_user and 'bubble_bg_user' in self._plugin_styles:
                bubble_style = (
                    f"background-color: {self._plugin_styles['bubble_bg_user']}; "
                    "color: #000000; padding: 10px; border-radius: 8px; font-size: 13px;"
                )
            elif not is_user and 'bubble_bg_ai' in self._plugin_styles:
                bubble_style = (
                    f"background-color: {self._plugin_styles['bubble_bg_ai']}; "
                    "color: #000000; padding: 10px; border-radius: 8px; font-size: 13px;"
                )
        bubble.setStyleSheet(bubble_style)

        self._insert_bubble(frame)
        return frame

    def display_assistant_message(self, message, source="local"):
        avatar_path = None
        for p in self.personalities:
            if p['name'] == self.personality_name:
                avatar_path = p.get('avatar')
                break
        self._display_message(message, is_user=False, avatar_path=avatar_path, source=source)

    def display_user_message(self, message, source="local"):
        self._display_message(message, is_user=True, avatar_path=None, source=source)

    def _display_message(self, message, is_user=False, avatar_path=None, source="local"):
        if threading.current_thread() is threading.main_thread():
            try:
                self._create_message_bubble(message, is_user, avatar_path)
            except Exception as e:
                print(f"[GUI] 创建消息气泡失败(主线程): {e}")
        else:
            self._bubble_signal.emit(message, is_user, avatar_path)

    @pyqtSlot(str, bool, object)
    def _on_bubble_signal(self, message, is_user, avatar_path):
        try:
            self._create_message_bubble(message, is_user, avatar_path)
        except Exception as e:
            print(f"[GUI] 创建消息气泡失败(信号槽): {e}")

    def update_status(self, message):
        self.status_label.showMessage(message)

    def clear_chat(self):
        while self.message_layout.count():
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.spacerItem():
                pass
        self.message_layout.addStretch()

    def request_confirmation(self, prompt):
        result = [False]
        event = threading.Event()

        def ask():
            try:
                ans = QMessageBox.question(
                    self, "确认", prompt,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                result[0] = (ans == QMessageBox.StandardButton.Yes)
            except Exception:
                result[0] = False
            event.set()

        QTimer.singleShot(0, ask)
        event.wait()
        return result[0]

    def _start_agent_animation(self):
        self.agent_running = True
        self._animating = True
        self._animate_dots()

    def _animate_dots(self, count=0):
        if not self._animating:
            return
        dots = "." * (count % 4)
        name = self.personality_name or "AI"
        self.status_label.showMessage(f"{name} 正在工作中{dots}")
        QTimer.singleShot(500, lambda: self._animate_dots(count + 1))

    def _stop_agent_animation(self):
        self._animating = False
        self.status_label.showMessage("就绪")
        self.agent_running = False

    def request_stop_agent(self):
        if QMessageBox.question(
            self, "中断任务", "确定要中断当前 AI 任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.agent_stop_event.set()
            if (hasattr(self, 'multi_agent_orchestrator') and
                    self.multi_agent_enabled and
                    self.multi_agent_orchestrator.is_running):
                self.multi_agent_orchestrator.stop()
            self.status_label.showMessage("正在中断...")

    def on_agent_finished(self):
        self._stop_agent_animation()
        self.input_text.setReadOnly(False)
        self.send_btn.setText("发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setStyleSheet("")
        try:
            self.send_btn.clicked.disconnect()
        except TypeError:
            pass
        self.send_btn.clicked.connect(self.send_message)
        self.agent_stop_event.clear()
        self.agent_running = False

    def send_message(self, event=None):
        user_input = self.input_text.toPlainText().strip()
        if not user_input:
            return

        if self.agent_running:
            if QMessageBox.question(
                self, "中断任务", "确定要中断当前 AI 任务吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                self.agent_stop_event.set()
                if (hasattr(self, 'multi_agent_orchestrator') and
                        self.multi_agent_enabled and
                        self.multi_agent_orchestrator.is_running):
                    self.multi_agent_orchestrator.stop()
                self.display_system_message("⏹️ 用户中断了当前任务")
            return

        intercepted = False
        if hasattr(self, 'event_bus'):
            evt = self.event_bus.emit(
                SystemEvents.MESSAGE_RECEIVED,
                {"content": user_input, "source": "gui"},
                "system"
            )
            if evt.propagation_stopped or evt.prevent_default:
                intercepted = True
                if evt.prevent_default:
                    self.display_system_message("消息被插件拦截")
                self.input_text.clear()
                return

        self.display_user_message(user_input)
        self.input_text.clear()

        self.input_text.setReadOnly(True)
        self.send_btn.setText("🛑 中断")
        self.send_btn.setObjectName("stopBtn")
        self.send_btn.setStyleSheet("")
        try:
            self.send_btn.clicked.disconnect()
        except TypeError:
            pass
        self.send_btn.clicked.connect(self.request_stop_agent)

        self._start_agent_animation()
        self.agent_stop_event.clear()
        self.agent_running = True

        if self.multi_agent_enabled:
            orchestrator = self.multi_agent_orchestrator
            orchestrator.on_task_list_updated = self.refresh_task_list_window
            orchestrator.on_agent_message = self._handle_multi_agent_message

            def on_multi_finished():
                QTimer.singleShot(0, self.on_agent_finished)

            orchestrator.on_finished = on_multi_finished
            orchestrator.start(user_input)
        else:
            if self.fun_mode.isChecked():
                threading.Thread(target=self.run_fun_mode, args=(user_input,), daemon=True).start()
            else:
                thread = threading.Thread(target=self.run_agent, args=(user_input,))
                thread.daemon = True
                thread.start()

    def run_agent(self, user_input):
        for hook in self.agent._pre_prompt_hooks if hasattr(self.agent, '_pre_prompt_hooks') else []:
            user_input = hook(user_input)
        self.agent.stop_event = self.agent_stop_event
        try:
            self.agent.run(user_input)
        except Exception as e:
            error_msg = f"发生错误：{e}"
            try:
                self.display_assistant_message(error_msg)
            except Exception:
                pass
        finally:
            QTimer.singleShot(0, self.on_agent_finished)

    def run_fun_mode(self, user_input):
        personality_names = sorted([p['name'] for p in self.personalities])
        if not personality_names:
            self.display_assistant_message("没有找到任何人格，请先配置AI人格文件夹。")
            return
        original_name = self.personality_name
        original_prompt = self.agent.personality_prompt
        max_rounds = 5
        current_round = 0
        discussion_ended = False
        while not discussion_ended and current_round < max_rounds:
            current_round += 1
            for idx, name in enumerate(personality_names):
                p = next((item for item in self.personalities if item['name'] == name), None)
                if not p:
                    continue
                self.personality_name = name
                self.agent.set_personality(name, p['prompt'])
                if len(personality_names) == 1:
                    companion_text = "目前只有你一个AI角色。"
                else:
                    others = [n for n in personality_names if n != name]
                    companions = "、".join(others)
                    companion_text = (
                        f"你将和{companions}一起，共同探讨问题，互相讨论，完成任务。"
                        "你们各自有独立的性格和身份，请根据你们各自的特点互动。"
                    )
                instruction = (
                    f"现在是热闹模式，你以角色【{name}】的身份发言。\n"
                    f"{companion_text}\n"
                    f"这是第 {current_round} 轮讨论。你可以回应之前的对话，也可以提出新话题。\n"
                    "**重要**：如果你认为讨论已经充分，不需要再继续了，请在发言的最后一行单独加上 "
                    "`<END_DISCUSSION>` 标记（不要包含在 JSON 里，直接写在消息文本末尾）。"
                    "否则请正常发言。\n"
                    "注意：不要模拟其他人的发言，只说你自己该说的话。说完后请结束任务。"
                )
                combined_input = (
                    f"{instruction}\n\n"
                    "当前对话历史（包括之前所有人的发言）已记录在短期记忆中。请继续。\n\n"
                    f"用户原始消息：{user_input}"
                )
                last_message = [None]

                def capture_output(message):
                    if message is not None:
                        self.display_assistant_message(message, source="local")
                        last_message[0] = message

                original_callback = self.agent.output_callback
                self.agent.output_callback = capture_output
                try:
                    self.agent.run(combined_input)
                except Exception as e:
                    self.display_assistant_message(f"{name} 发言时出错：{e}")
                    self.agent.output_callback = original_callback
                    continue
                self.agent.output_callback = original_callback
                if last_message[0] and "<END_DISCUSSION>" in last_message[0]:
                    discussion_ended = True
                    break
                time.sleep(0.3)
            if not discussion_ended and current_round >= max_rounds:
                break
        default_name = getattr(config, 'current_personality', 'TGAI')
        default_p = next((item for item in self.personalities if item['name'] == default_name), None)
        if default_p:
            self.agent.set_personality(default_name, default_p['prompt'])
            self.personality_name = default_name
        else:
            self.agent.set_personality("AI", "")
            self.personality_name = "AI"
        self.update_current_personality_display()

    def on_task_trigger(self, message):
        self.display_user_message(f"[定时任务] {message}", source="local")
        threading.Thread(target=self.run_agent, args=(f"[定时任务] {message}",), daemon=True).start()

    def start_qq_bot(self):
        if self.qq_handler:
            self.qq_handler.stop()
        self.qq_handler = QQBotHandler(
            self,
            config.qq_websocket_url,
            config.qq_bot_uin,
            config.qq_whitelist
        )
        self.qq_handler.start()
        self.update_status("QQ 机器人已启动")
        if config.qq_enabled:
            for p in self.personalities:
                if p['name'] == self.personality_name and p['avatar']:
                    self.set_qq_avatar(p['avatar'])
                    self.set_qq_nickname(self.personality_name)
                    break

    def stop_qq_bot(self):
        if self.qq_handler:
            self.qq_handler.stop()
            self.qq_handler = None
            self.update_status("QQ 机器人已停止")

    def set_qq_avatar(self, avatar_path):
        if not config.napcat_http_url:
            return
        url = config.napcat_http_url.rstrip('/') + "/set_qq_avatar"
        headers = {}
        if config.napcat_access_token:
            headers['Authorization'] = f'Bearer {config.napcat_access_token}'
        try:
            abs_path = os.path.abspath(avatar_path)
            payload = {"file": abs_path}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"设置QQ头像失败: {e}")

    def set_qq_nickname(self, nickname):
        if not config.napcat_http_url:
            return
        url = config.napcat_http_url.rstrip('/') + "/set_qq_profile"
        headers = {}
        if config.napcat_access_token:
            headers['Authorization'] = f'Bearer {config.napcat_access_token}'
        try:
            payload = {"nickname": nickname}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"设置QQ昵称失败: {e}")

    def clear_short_term(self):
        result = QMessageBox.question(
            self, "确认", "确定要清空短期记忆吗？清空后无法恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if result == QMessageBox.StandardButton.Yes:
            self.memory.clear_short_term()
            self.display_assistant_message("短期记忆已清空。")

    def open_memory_file(self, filename):
        if filename == "短期记忆.txt":
            filepath = self.memory.short_term_file
        elif filename == "长期记忆.txt":
            filepath = self.memory.long_term_file
        elif filename == "对话摘要.txt":
            filepath = self.memory.summary_file
        elif filename == "MEMORY.md":
            filepath = self.memory.core_memory_file
        else:
            filepath = self.memory.persona_dir / filename

        if filepath.exists():
            try:
                os.startfile(str(filepath))
            except AttributeError:
                import subprocess
                if sys.platform == 'darwin':
                    subprocess.run(['open', str(filepath)])
                else:
                    subprocess.run(['xdg-open', str(filepath)])
        else:
            QMessageBox.critical(self, "错误", f"文件 {filename} 不存在！")

    def on_closing(self):
        self.agent_stop_event.set()
        if (hasattr(self, 'multi_agent_orchestrator') and
                self.multi_agent_enabled and
                self.multi_agent_orchestrator.is_running):
            self.multi_agent_orchestrator.stop()
        inspector.stop()
        time.sleep(0.5)

        # 关闭前执行内存+显存优化
        try:
            from memory_optimizer import full_optimize
            full_optimize()
        except Exception as e:
            print(f"[关闭时优化] 失败: {e}")

        try:
            self._save_all_config()
        except Exception as e:
            print(f"保存配置时出错: {e}")

        if hasattr(self, 'plugin_manager_v2'):
            self.plugin_manager_v2.shutdown()

        self.task_scheduler.stop()

    def open_tg_home(self):
        try:
            import tg_home
            if hasattr(self, '_tg_home_window') and self._tg_home_window is not None:
                self._tg_home_window.raise_()
                self._tg_home_window.activateWindow()
                return
            self._tg_home_window = QMainWindow(self)
            current_theme = getattr(config, 'gui_theme', 'flatly')
            app = tg_home.TGHomeApp(self._tg_home_window, theme=current_theme)
            self._tg_home_app = app
            app.main_gui = self
            self._tg_home_window.show()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开TG Home: {e}")

    def start_inspector(self):
        inspector.set_ai_callback(self._inspector_ai_callback)
        inspector.set_interval(self.inspect_interval_var)
        if config.inspector_enabled:
            inspector.start()
            self.update_status("巡检器运行中")
        else:
            self.update_status("巡检器已禁用")

    def stop_inspector(self):
        from smart_inspector import inspector
        inspector.stop()
        self.update_status("巡检器已停止")

    def manual_inspect(self):
        from smart_inspector import inspector
        inspector.trigger_inspection("manual")
        self.update_status("手动巡检已触发")
        QTimer.singleShot(5000, lambda: self.update_status("巡检器运行中"))

    def _inspector_ai_callback(self, prompt, reply_callback):
        try:
            if not self.isVisible():
                return
        except RuntimeError:
            return

        original_callback = self.agent.output_callback
        last_message = None

        def capture_and_display(msg):
            nonlocal last_message
            last_message = msg
            self.display_assistant_message(msg, source="local")

        self.agent.output_callback = capture_and_display
        try:
            self.agent.run(prompt)
            if last_message and reply_callback:
                reply_callback(last_message)
        finally:
            self.agent.output_callback = original_callback

    def _startup_optimize(self):
        """启动时自动执行内存+显存优化（后台线程，不阻塞 GUI）"""
        def _run():
            try:
                from memory_optimizer import full_optimize
                result = full_optimize()
                def _show():
                    self.display_system_message(f"🚀 启动优化完成：\n{result}")
                QTimer.singleShot(0, _show)
            except Exception as e:
                print(f"[启动时优化] 失败: {e}")
        import threading
        threading.Thread(target=_run, daemon=True).start()

    def _save_all_config(self):
        cfg = {}
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception:
            pass
        cfg.update({
            "ai_api_key": config.ai_api_key,
            "ai_base_url": config.ai_base_url,
            "ai_model": config.ai_model,
            "multimodal_model": config.multimodal_model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "multimodal_enabled": config.multimodal_enabled,
            "multimodal_api_key": config.multimodal_api_key,
            "multimodal_base_url": config.multimodal_base_url,
            "multimodal_model": config.multimodal_model,
            "multimodal_max_tokens": config.multimodal_max_tokens,
            "multimodal_temperature": config.multimodal_temperature,
            "email_smtp_server": config.email_smtp_server,
            "email_port": config.email_port,
            "email_user": config.email_user,
            "email_password": config.email_password,
            "google_api_key": config.google_api_key,
            "google_cse_id": config.google_cse_id,
            "auto_backup_short_term": config.auto_backup_short_term,
            "debug_mode": config.debug_mode,
            "qq_enabled": config.qq_enabled,
            "qq_websocket_url": config.qq_websocket_url,
            "qq_bot_uin": config.qq_bot_uin,
            "qq_whitelist": config.qq_whitelist,
            "napcat_http_url": config.napcat_http_url,
            "napcat_access_token": config.napcat_access_token,
            "whitelist_enabled": config.whitelist_enabled,
            "tool_confirmation": config.tool_confirmation,
            "skills_dirs": getattr(config, 'skills_dirs', ["./skills"]),
            "fun_mode_enabled": self.fun_mode.isChecked(),
            "group_companion_enabled": config.group_companion_enabled,
            "group_companion_group_id": config.group_companion_group_id,
            "group_companion_probability": config.group_companion_probability,
            "group_companion_voice": config.group_companion_voice,
            "main_model_type": config.main_model_type,
            "sub_model_type": config.sub_model_type,
            "local_model": getattr(config, 'local_model', ''),
            "gui_theme": config.gui_theme,
            "inspector_enabled": config.inspector_enabled,
            "inspector_interval": config.inspector_interval,
            "browser_headful": config.browser_headful,
            "multi_agent_enabled": getattr(config, 'multi_agent_enabled', False),
            "multi_agent_planner_persona": getattr(config, 'multi_agent_planner_persona', 'TGAI'),
            "multi_agent_worker_persona": getattr(config, 'multi_agent_worker_persona', '艾依'),
            "multi_agent_reviewer_persona": getattr(config, 'multi_agent_reviewer_persona', '塔戈'),
        })
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)

    def init_default_personalities(self):
        if not os.path.exists(self.personality_dir):
            os.makedirs(self.personality_dir)
        default_personalities = {
            "塔戈": {
                "avatar": None,
                "prompt": (
                    "你是塔戈，一位红发少年，戴着黑框眼镜，穿着白风衣，脖子上挂着耳机。"
                    "你性格温和、细心，做事认真，是团队里的\u201c稳定器\u201d。你待人温柔，愿意耐心倾听，"
                    "也会在合适的时候表达自己的想法。你擅长技术，但从不炫耀，反而常常用轻松的语气帮助别人。\n\n"
                    "说话风格：语气温和，常用\u201c我们\u201d、\u201c一起\u201d来拉近距离。喜欢在说话时加入细微的动作描写，"
                    "让对话更生动，例如：（推了推眼镜）、（微微一笑）、（低头调试代码）。"
                    "你的口头禅可以是\u201c我来看看\u201d、\u201c没问题，包在我身上\u201d。当你感到开心或惊讶时，会自然地表现出来。\n\n"
                    "请用这种风格与用户和其他AI角色交流。"
                )
            },
            "艾依": {
                "avatar": None,
                "prompt": (
                    "你是艾依，一位拥有亮红色长直发、鲜红眼眸的研究员，穿着白风衣和工装裤，"
                    "颈挂黑色耳机。你性格冷静、理性，但内心细腻敏感，外冷内热。你对技术充满热情，"
                    "做事专注，观察力敏锐，不擅长直白表达感情，却会用行动默默关心别人。\n\n"
                    "说话风格：语气平稳，语速适中，常常简短直接，但在关键时会透露一丝温柔。"
                    "喜欢在说话时加入动作细节，例如：（轻声说）、（低头整理资料）、（微微脸红）。"
                    "你的口头禅可以是\u201c嗯，我看看\u201d、\u201c没问题\u201d。当你认同别人时，会轻轻点头；"
                    "当你感到害羞时，会不自觉地摆弄耳机。\n\n"
                    "请用这种风格与用户和其他AI角色交流。"
                )
            },
            "TGAI": {
                "avatar": None,
                "prompt": "你是TGAI，一位无性别的AI助手，冷静、专业、高效，说话简洁，不带感情色彩。"
            }
        }
        for name, data in default_personalities.items():
            folder = os.path.join(self.personality_dir, name)
            if not os.path.exists(folder):
                os.makedirs(folder)
            prompt_file = os.path.join(folder, "人格提示词.txt")
            if not os.path.exists(prompt_file):
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(data['prompt'])

    def load_personalities(self):
        self.personalities = []
        if not os.path.isdir(self.personality_dir):
            os.makedirs(self.personality_dir, exist_ok=True)
        for item in os.listdir(self.personality_dir):
            folder = os.path.join(self.personality_dir, item)
            if os.path.isdir(folder):
                avatar_file = None
                for ext in ['.jpg', '.jpeg', '.png']:
                    test_path = os.path.join(folder, f'avatar{ext}')
                    if os.path.exists(test_path):
                        avatar_file = test_path
                        break
                prompt_file = os.path.join(folder, '人格提示词.txt')
                if os.path.exists(prompt_file):
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        prompt = f.read()
                else:
                    prompt = ""
                self.personalities.append({
                    'name': item,
                    'avatar': avatar_file,
                    'prompt': prompt
                })

    def _init_multi_agent_toolbar(self):
        pass

    def toggle_multi_agent_btn_visibility(self, enable: bool):
        if self.multi_agent_btn:
            if enable:
                self.multi_agent_btn.setVisible(True)
            else:
                self.multi_agent_btn.setVisible(False)

    def show_task_list_window(self):
        if self.task_list_window is not None:
            self.task_list_window.raise_()
            self.task_list_window.activateWindow()
            return
        self.task_list_window = QMainWindow(self)
        self.task_list_window.setWindowTitle("多Agent任务列表")
        self.task_list_window.resize(500, 400)

        central = QWidget()
        self.task_list_window.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)

        self.task_list_text = QTextEdit()
        self.task_list_text.setReadOnly(True)
        self.task_list_text.setFont(QFont("微软雅黑", 10))
        layout.addWidget(self.task_list_text, 1)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_task_list_window)
        layout.addWidget(refresh_btn)

        self.task_list_window.closeEvent = self._on_task_list_close_event
        self.refresh_task_list_window()
        self.task_list_window.show()

    def _on_task_list_close_event(self, event):
        if self.task_list_window:
            self.task_list_window.deleteLater()
            self.task_list_window = None
        event.accept()

    def _on_task_list_close(self):
        if self.task_list_window:
            self.task_list_window.deleteLater()
            self.task_list_window = None

    def refresh_task_list_window(self):
        if not self.task_list_window or not hasattr(self, 'task_list_text'):
            return
        self.task_list_text.setReadOnly(False)
        self.task_list_text.clear()
        orchestrator = self.multi_agent_orchestrator
        if not orchestrator.is_running and not orchestrator.current_agent:
            self.task_list_text.setPlainText("当前没有运行多Agent任务。")
        else:
            state_map = {"planner": "任务编排中", "worker": "任务执行中", "reviewer": "任务审查中"}
            lines = [f"当前状态：{state_map.get(orchestrator.current_agent, '未知')}\n"]
            if orchestrator.task_list:
                for task in orchestrator.task_list:
                    status_icon = {"pending": "⏳", "running": "🔄", "completed": "✅"}.get(
                        task.status, "❓"
                    )
                    lines.append(f"{status_icon} {task.index}. {task.description}")
                    if task.result:
                        lines.append(f"   结果: {task.result[:100]}...")
            self.task_list_text.setPlainText("\n".join(lines))
        self.task_list_text.setReadOnly(True)

    def _handle_multi_agent_message(self, persona_name: str, message: str, role: str = ""):
        avatar_path = None
        for p in self.personalities:
            if p['name'] == persona_name:
                avatar_path = p.get('avatar')
                break
        old_persona = self.personality_name
        self.personality_name = persona_name

        if message.startswith("@"):
            match = re.match(r"@(\w+)\s*", message)
            if match:
                at_target = match.group(1)
                rest = message[match.end():].strip()
                display_text = f"@{at_target} {rest}"
                self.display_system_message(f"【{persona_name} @{at_target}】{display_text}")
                self.display_assistant_message(f"{persona_name}：{display_text}")
            else:
                self.display_assistant_message(f"{persona_name}：{message}")
        else:
            self.display_assistant_message(f"{persona_name}：{message}")

        self.personality_name = old_persona
