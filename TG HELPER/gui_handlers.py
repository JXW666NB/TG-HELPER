# -*- coding: utf-8 -*-
"""
GUI 按钮回调与设置页面创建函数 - PyQt6 版本
"""
import os
import sys
import json
import re
import threading
import time
import subprocess
import shutil
import random
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QCheckBox,
    QComboBox, QRadioButton, QSpinBox, QProgressBar,
    QGroupBox, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFileDialog, QMessageBox, QMenu,
    QScrollArea, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QPixmap, QIcon

from config import config, banben, CONFIG_FILE
from skill_manager import SkillManager
from hardware_detector import HardwareDetector


def _get_first_skills_dir():
    dirs = getattr(config, 'skills_dirs', ["./skills"])
    if not dirs:
        dirs = ["./skills"]
    return dirs[0]


def bind_handlers(gui_instance):
    gui_instance.create_api_tab = lambda: create_api_tab(gui_instance)
    gui_instance.create_qq_tab = lambda: create_qq_tab(gui_instance)
    gui_instance.create_security_tab = lambda: create_security_tab(gui_instance)
    gui_instance.create_skill_tab = lambda: create_skill_tab(gui_instance)
    gui_instance.create_tasks_tab = lambda: create_tasks_tab(gui_instance)
    gui_instance.create_personality_tab = lambda: create_personality_tab(gui_instance)
    gui_instance.create_debug_tab = lambda: create_debug_tab(gui_instance)
    gui_instance.create_local_model_tab = lambda: create_local_model_tab(gui_instance)
    gui_instance.create_model_selector_tab = lambda: create_model_selector_tab(gui_instance)
    gui_instance.create_plugin_tab = lambda: create_plugin_tab(gui_instance)
    gui_instance.create_multi_agent_tab = lambda: create_multi_agent_tab(gui_instance)
    gui_instance.create_ai_hardware_tab = lambda: create_ai_hardware_tab(gui_instance)

    gui_instance.save_api_settings = lambda: save_api_settings(gui_instance)
    gui_instance.save_qq_settings = lambda: save_qq_settings(gui_instance)
    gui_instance.save_security_settings = lambda: save_security_settings(gui_instance)
    gui_instance.save_multi_agent_settings = lambda: save_multi_agent_settings(gui_instance)
    gui_instance.save_model_selection = lambda: save_model_selection(gui_instance)

    gui_instance.refresh_skill_list = lambda: refresh_skill_list(gui_instance)
    gui_instance.open_skills_folder = lambda: open_skills_folder(gui_instance)
    gui_instance.check_skills_security = lambda: check_skills_security(gui_instance)
    gui_instance.generate_skill_by_ai = lambda: generate_skill_by_ai(gui_instance)
    gui_instance.on_skill_select = lambda: on_skill_select(gui_instance)
    gui_instance.save_current_skill_config = lambda: save_current_skill_config(gui_instance)
    gui_instance.open_skill_config_external = lambda: open_skill_config_external(gui_instance)

    gui_instance.refresh_tasks = lambda: refresh_tasks(gui_instance)
    gui_instance.add_task = lambda: add_task(gui_instance)
    gui_instance.edit_task = lambda: edit_task(gui_instance)
    gui_instance.delete_task = lambda: delete_task(gui_instance)

    gui_instance.refresh_personality_list = lambda: refresh_personality_list(gui_instance)
    gui_instance.on_personality_select = lambda: on_personality_select(gui_instance)
    gui_instance.on_apply_personality = lambda: on_apply_personality(gui_instance)
    gui_instance.apply_personality = lambda name: apply_personality(gui_instance, name)
    gui_instance.open_personality_folder = lambda: open_personality_folder(gui_instance)
    gui_instance._switch_memory_for_personality = lambda name: _switch_memory_for_personality(gui_instance, name)

    gui_instance.export_ai_config = lambda: export_ai_config(gui_instance)
    gui_instance.import_ai_config = lambda: import_ai_config(gui_instance)
    gui_instance.reset_ai_config = lambda: reset_ai_config(gui_instance)

    gui_instance.refresh_model_list = lambda: refresh_model_list(gui_instance)
    gui_instance.add_model_dialog = lambda: add_model_dialog(gui_instance)
    gui_instance.delete_model = lambda: delete_model(gui_instance)
    gui_instance.deploy_recommended_model = lambda: deploy_recommended_model(gui_instance)
    gui_instance.select_model_as_current = lambda: select_model_as_current(gui_instance)
    gui_instance.deploy_model = lambda name: deploy_model(gui_instance, name)

    gui_instance.show_about_dialog = lambda: show_about_dialog(gui_instance)
    gui_instance._show_donation_qr = lambda: _show_donation_qr(gui_instance)
    gui_instance._show_task_menu = lambda pos: _show_task_menu(gui_instance, pos)
    gui_instance._check_skills_thread = lambda skills_dirs_str: _check_skills_thread(gui_instance, skills_dirs_str)
    gui_instance._generate_skill_thread = lambda prompt, skills_dirs_str: _generate_skill_thread(gui_instance, prompt, skills_dirs_str)
    gui_instance.open_theme_selector = lambda: open_theme_selector(gui_instance)

    gui_instance.refresh_plugins_display = lambda: refresh_plugins_display(gui_instance)
    gui_instance.on_plugin_select = lambda: on_plugin_select(gui_instance)
    gui_instance.toggle_plugin_enabled = lambda plugin_id, enabled: toggle_plugin_enabled(gui_instance, plugin_id, enabled)
    gui_instance.reload_single_plugin = lambda plugin_id: reload_single_plugin(gui_instance, plugin_id)
    gui_instance.reload_plugins = lambda: reload_plugins(gui_instance)
    gui_instance.open_plugins_folder = lambda: open_plugins_folder(gui_instance)
    gui_instance.check_plugins_security = lambda: check_plugins_security(gui_instance)
    gui_instance.generate_plugin = lambda: generate_plugin(gui_instance)
    gui_instance._check_plugins_security_thread_v2 = lambda: _check_plugins_security_thread_v2(gui_instance)
    gui_instance._show_plugin_security_results_v2 = lambda results: _show_plugin_security_results_v2(gui_instance, results)
    gui_instance._generate_plugin_thread = lambda desc: _generate_plugin_thread(gui_instance, desc)
    gui_instance._extract_plugin_usage_info = lambda plugin_instance, manifest: _extract_plugin_usage_info(gui_instance, plugin_instance, manifest)
    gui_instance.open_ai_translator = lambda: open_ai_translator(gui_instance)

    gui_instance._on_list_processes = lambda: _on_list_processes(gui_instance)
    gui_instance._on_optimize_memory = lambda: _on_optimize_memory(gui_instance)
    gui_instance._on_optimize_vram = lambda: _on_optimize_vram(gui_instance)
    gui_instance._on_full_optimize = lambda: _on_full_optimize(gui_instance)


# ==================== 辅助函数 ====================
def _make_section_outer(self, title_text):
    outer = QWidget()
    layout = QVBoxLayout(outer)
    layout.setContentsMargins(5, 5, 5, 5)
    title = QLabel(title_text)
    title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 10pt;")
    layout.addWidget(title)
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setFrameShadow(QFrame.Shadow.Plain)
    frame_layout = QGridLayout(frame)
    frame_layout.setContentsMargins(5, 5, 5, 5)
    frame_layout.setSpacing(4)
    layout.addWidget(frame)
    return outer, frame, frame_layout


def _make_label(frame_layout, text, row, col=0):
    label = QLabel(text)
    label.setStyleSheet("font-size: 9pt;")
    frame_layout.addWidget(label, row, col)
    return label


def _make_entry(frame_layout, row, col=1, password=False):
    entry = QLineEdit()
    if password:
        entry.setEchoMode(QLineEdit.EchoMode.Password)
    frame_layout.addWidget(entry, row, col)
    return entry


def _is_deepseek_model(model_name: str) -> bool:
    if not model_name:
        return False
    return 'deepseek' in model_name.lower()


# ==================== API 设置页 ====================
def create_api_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "API 设置")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    outer, frame, fl = _make_section_outer(self, "主 AI 配置")
    layout.addWidget(outer)

    self.api_key_entry = _make_entry(fl, 0)
    _make_label(fl, "API Key:", 0)
    self.api_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
    self.api_key_entry.setText(config.ai_api_key)

    self.base_url_entry = _make_entry(fl, 1)
    _make_label(fl, "Base URL:", 1)
    self.base_url_entry.setText(config.ai_base_url)

    self.model_entry = _make_entry(fl, 2)
    _make_label(fl, "模型名称:", 2)
    self.model_entry.setText(config.ai_model)

    self.max_tokens_entry = _make_entry(fl, 3)
    _make_label(fl, "Max Tokens:", 3)
    self.max_tokens_entry.setText(str(getattr(config, 'max_tokens', 2000)))
    self.max_tokens_entry.setMaximumWidth(120)

    self.temp_entry = _make_entry(fl, 4)
    _make_label(fl, "Temperature:", 4)
    self.temp_entry.setText(str(getattr(config, 'temperature', 1.0)))
    self.temp_entry.setMaximumWidth(120)

    # ==================== 深度思考配置 ====================
    is_ds = _is_deepseek_model(config.ai_model)
    section_title = "🧠 DeepSeek 专属配置" if is_ds else "🧠 深度思考配置"
    self.deepseek_section, frame_ds, fl_ds = _make_section_outer(self, section_title)

    # 用户确认模型是否支持深度思考
    self.model_supports_thinking_check = QCheckBox("确认当前模型支持深度思考（reasoning/thinking）")
    self.model_supports_thinking_check.setChecked(getattr(config, 'model_supports_thinking', False))
    self.model_supports_thinking_check.setToolTip("非 DeepSeek 模型（如 Claude、GPT-4o、Kimi 等）如果支持 reasoning/thinking 模式，请勾选此项")
    fl_ds.addWidget(self.model_supports_thinking_check, 0, 0, 1, 2)

    self.deepseek_thinking_check = QCheckBox("启用深度思考 (Thinking Mode)")
    self.deepseek_thinking_check.setChecked(getattr(config, 'deepseek_thinking_enabled', False))
    self.deepseek_thinking_check.setToolTip("开启后模型会输出思维链内容，提升答案准确性\n注意：思考模式下 temperature 等参数可能不生效")
    fl_ds.addWidget(self.deepseek_thinking_check, 1, 0, 1, 2)

    # DeepSeek 专属：推理强度
    self.deepseek_effort_combo = QComboBox()
    self.deepseek_effort_combo.addItem("高 (high) - 推荐", "high")
    self.deepseek_effort_combo.addItem("最大 (max) - 最强推理", "max")
    saved_effort = getattr(config, 'deepseek_reasoning_effort', 'high')
    idx = self.deepseek_effort_combo.findData(saved_effort)
    if idx >= 0:
        self.deepseek_effort_combo.setCurrentIndex(idx)
    self.effort_label = _make_label(fl_ds, "推理强度:", 2, 0)
    fl_ds.addWidget(self.deepseek_effort_combo, 2, 1)

    # DeepSeek 专属：上下文窗口
    self.deepseek_context_combo = QComboBox()
    context_options = [
        ("16K (16384 tokens)", 16384),
        ("32K (32768 tokens)", 32768),
        ("64K (65536 tokens) - 推荐", 65536),
        ("128K (131072 tokens)", 131072),
        ("256K (262144 tokens)", 262144),
        ("512K (524288 tokens)", 524288),
        ("1M (1000000 tokens)", 1000000),
    ]
    for label, val in context_options:
        self.deepseek_context_combo.addItem(label, val)
    saved_ctx = getattr(config, 'deepseek_context_window', 65536)
    idx = self.deepseek_context_combo.findData(saved_ctx)
    if idx >= 0:
        self.deepseek_context_combo.setCurrentIndex(idx)
    self.context_label = _make_label(fl_ds, "上下文窗口:", 3, 0)
    fl_ds.addWidget(self.deepseek_context_combo, 3, 1)

    # 控制深度思考开关的可见性：只有用户确认支持后才显示
    self.deepseek_thinking_check.setVisible(getattr(config, 'model_supports_thinking', False))

    # 控制 DeepSeek 专属选项的可见性
    self.deepseek_effort_combo.setVisible(is_ds)
    self.effort_label.setVisible(is_ds)
    self.deepseek_context_combo.setVisible(is_ds)
    self.context_label.setVisible(is_ds)

    layout.addWidget(self.deepseek_section)

    def _update_deepseek_ui(model_text):
        is_ds_model = _is_deepseek_model(model_text)
        # 更新区域标题
        self.deepseek_section.setTitle("🧠 DeepSeek 专属配置" if is_ds_model else "🧠 深度思考配置")
        # DeepSeek 专属选项
        self.deepseek_effort_combo.setVisible(is_ds_model)
        self.effort_label.setVisible(is_ds_model)
        self.deepseek_context_combo.setVisible(is_ds_model)
        self.context_label.setVisible(is_ds_model)

    self.model_entry.textChanged.connect(_update_deepseek_ui)

    def _on_thinking_support_changed(checked):
        self.deepseek_thinking_check.setVisible(checked)
        if not checked:
            self.deepseek_thinking_check.setChecked(False)
        # 实时保存配置
        config.model_supports_thinking = checked
        self._save_all_config()

    self.model_supports_thinking_check.toggled.connect(_on_thinking_support_changed)

    def _on_thinking_enabled_changed(checked):
        # 实时保存配置
        config.deepseek_thinking_enabled = checked
        self._save_all_config()

    self.deepseek_thinking_check.toggled.connect(_on_thinking_enabled_changed)

    outer2, frame2, fl2 = _make_section_outer(self, "多模态备用模型")
    layout.addWidget(outer2)

    self.multimodal_enabled_check = QCheckBox("启用备用模型")
    self.multimodal_enabled_check.setChecked(getattr(config, 'multimodal_enabled', False))
    fl2.addWidget(self.multimodal_enabled_check, 0, 0, 1, 2)

    self.multimodal_key_entry = _make_entry(fl2, 1)
    _make_label(fl2, "API Key:", 1)
    self.multimodal_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
    self.multimodal_key_entry.setText(getattr(config, 'multimodal_api_key', ''))

    self.multimodal_url_entry = _make_entry(fl2, 2)
    _make_label(fl2, "Base URL:", 2)
    self.multimodal_url_entry.setText(getattr(config, 'multimodal_base_url', ''))

    self.multimodal_model_entry = _make_entry(fl2, 3)
    _make_label(fl2, "模型:", 3)
    self.multimodal_model_entry.setText(getattr(config, 'multimodal_model', ''))

    outer3, frame3, fl3 = _make_section_outer(self, "邮箱配置")
    layout.addWidget(outer3)

    self.smtp_server_entry = _make_entry(fl3, 0)
    _make_label(fl3, "SMTP服务器:", 0)
    self.smtp_server_entry.setText(getattr(config, 'email_smtp_server', ''))

    self.smtp_port_entry = _make_entry(fl3, 1)
    _make_label(fl3, "端口:", 1)
    self.smtp_port_entry.setText(str(getattr(config, 'email_port', 587)))
    self.smtp_port_entry.setMaximumWidth(80)

    self.email_user_entry = _make_entry(fl3, 2)
    _make_label(fl3, "账号:", 2)
    self.email_user_entry.setText(getattr(config, 'email_user', ''))

    self.email_pass_entry = _make_entry(fl3, 3)
    _make_label(fl3, "密码:", 3)
    self.email_pass_entry.setEchoMode(QLineEdit.EchoMode.Password)
    self.email_pass_entry.setText(getattr(config, 'email_password', ''))

    outer4, frame4, fl4 = _make_section_outer(self, "Google 搜索")
    layout.addWidget(outer4)

    self.google_key_entry = _make_entry(fl4, 0)
    _make_label(fl4, "API Key:", 0)
    self.google_key_entry.setText(getattr(config, 'google_api_key', ''))

    self.google_cse_entry = _make_entry(fl4, 1)
    _make_label(fl4, "CSE ID:", 1)
    self.google_cse_entry.setText(getattr(config, 'google_cse_id', ''))

    # ===== AI 图片生成 =====
    outer5, frame5, fl5 = _make_section_outer(self, "🎨 AI 图片生成（文生图）")
    layout.addWidget(outer5)

    self.img_provider_combo = QComboBox()
    _img_providers = [
        ("OpenAI (DALL-E)", "openai"),
        ("Azure OpenAI", "azure_openai"),
        ("Google Gemini Imagen", "gemini"),
        ("Stability AI (SD)", "stability"),
        ("Cloudflare Workers AI", "cloudflare"),
        ("Replicate (FLUX)", "replicate"),
        ("Ideogram AI", "ideogram"),
        ("Together AI", "together"),
        ("字节跳动豆包 (Seedream)", "volcengine"),
        ("阿里云百炼 (通义万相)", "dashscope"),
        ("智谱 AI (CogView)", "zhipu"),
        ("MiniMax (海螺)", "minimax"),
        ("硅基流动 (SiliconFlow)", "siliconflow"),
        ("阶跃星辰 (Step-1X)", "stepfun"),
        ("自定义端点", "custom"),
    ]
    for _txt, _key in _img_providers:
        self.img_provider_combo.addItem(_txt, _key)
    _cur = getattr(config, 'image_gen_provider', 'openai')
    _idx = self.img_provider_combo.findData(_cur)
    if _idx >= 0:
        self.img_provider_combo.setCurrentIndex(_idx)
    fl5.addWidget(QLabel("提供商:"), 0, 0)
    fl5.addWidget(self.img_provider_combo, 0, 1)

    self.img_key_entry = _make_entry(fl5, 1)
    _make_label(fl5, "API Key:", 1)
    self.img_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
    self.img_key_entry.setText(getattr(config, 'image_gen_api_key', ''))
    self.img_key_entry.setPlaceholderText("留空则复用主 API Key")

    self.img_url_entry = _make_entry(fl5, 2)
    _make_label(fl5, "Base URL:", 2)
    self.img_url_entry.setText(getattr(config, 'image_gen_base_url', ''))
    self.img_url_entry.setPlaceholderText("custom 模式需填写，其他留空")

    self.img_model_entry = _make_entry(fl5, 3)
    _make_label(fl5, "模型:", 3)
    self.img_model_entry.setText(getattr(config, 'image_gen_model', ''))
    self.img_model_entry.setPlaceholderText("留空使用默认模型")

    self.img_size_entry = _make_entry(fl5, 4)
    _make_label(fl5, "尺寸:", 4)
    self.img_size_entry.setText(getattr(config, 'image_gen_size', '1024x1024'))
    self.img_size_entry.setMaximumWidth(140)

    # ===== AI 视频生成 (TTS) =====
    outer6, frame6, fl6 = _make_section_outer(self, "🎬 AI 视频生成 (TTS 配音)")
    layout.addWidget(outer6)

    self.video_tts_provider_combo = QComboBox()
    _video_tts_providers = [
        ("Edge TTS (免费)", "edge_tts"),
        ("OpenAI TTS", "openai"),
        ("字节跳动豆包 TTS", "volcengine"),
        ("MiniMax TTS", "minimax"),
        ("自定义端点", "custom"),
    ]
    for _txt, _key in _video_tts_providers:
        self.video_tts_provider_combo.addItem(_txt, _key)
    _cur_tts = getattr(config, 'video_tts_provider', 'edge_tts')
    _idx_tts = self.video_tts_provider_combo.findData(_cur_tts)
    if _idx_tts >= 0:
        self.video_tts_provider_combo.setCurrentIndex(_idx_tts)
    fl6.addWidget(QLabel("TTS 提供商:"), 0, 0)
    fl6.addWidget(self.video_tts_provider_combo, 0, 1)

    self.video_tts_key_entry = _make_entry(fl6, 1)
    _make_label(fl6, "API Key:", 1)
    self.video_tts_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
    self.video_tts_key_entry.setText(getattr(config, 'video_tts_api_key', ''))
    self.video_tts_key_entry.setPlaceholderText("留空则复用主 API Key")

    self.video_tts_url_entry = _make_entry(fl6, 2)
    _make_label(fl6, "Base URL:", 2)
    self.video_tts_url_entry.setText(getattr(config, 'video_tts_base_url', ''))
    self.video_tts_url_entry.setPlaceholderText("custom 模式需填写，其他留空")

    # 模型下拉框
    self.video_tts_model_combo = QComboBox()
    self.video_tts_model_combo.setEditable(True)
    fl6.addWidget(QLabel("模型:"), 3, 0)
    fl6.addWidget(self.video_tts_model_combo, 3, 1)

    # 音色下拉框
    self.video_tts_voice_combo = QComboBox()
    self.video_tts_voice_combo.setEditable(True)
    fl6.addWidget(QLabel("音色:"), 4, 0)
    fl6.addWidget(self.video_tts_voice_combo, 4, 1)

    # TTS 选项数据
    self._tts_options = {
        "edge_tts": {
            "models": [("默认", "")],
            "voices": [
                ("晓晓 (女)", "zh-CN-XiaoxiaoNeural"),
                ("晓伊 (女)", "zh-CN-XiaoyiNeural"),
                ("云健 (男)", "zh-CN-YunjianNeural"),
                ("云希 (男)", "zh-CN-YunxiNeural"),
                ("云夏 (男)", "zh-CN-YunxiaNeural"),
                ("云扬 (男)", "zh-CN-YunyangNeural"),
                ("晓涵 (女-台湾)", "zh-TW-HsiaoChenNeural"),
                ("云哲 (男-台湾)", "zh-TW-YunJheNeural"),
                ("晓佳 (女-香港)", "zh-HK-HiuMaanNeural"),
                ("云龙 (男-香港)", "zh-HK-WanLungNeural"),
            ]
        },
        "openai": {
            "models": [
                ("TTS-1", "tts-1"),
                ("TTS-1-HD", "tts-1-hd"),
            ],
            "voices": [
                ("Alloy (中性)", "alloy"),
                ("Echo (男)", "echo"),
                ("Fable (男)", "fable"),
                ("Onyx (男)", "onyx"),
                ("Nova (女)", "nova"),
                ("Shimmer (女)", "shimmer"),
            ]
        },
        "volcengine": {
            "models": [
                ("豆包 TTS", "doubao-tts"),
            ],
            "voices": [
                ("清新女声", "zh_female_qingxin"),
                ("温暖女声", "zh_female_wennuan"),
                ("活泼女声", "zh_female_huopo"),
                ("知性女声", "zh_female_zhixing"),
                ("沉稳男声", "zh_male_chenwen"),
                ("磁性男声", "zh_male_cixing"),
                ("阳光男声", "zh_male_yangguang"),
                ("活力男声", "zh_male_huoli"),
            ]
        },
        "minimax": {
            "models": [
                ("Speech-01", "speech-01"),
            ],
            "voices": [
                ("青涩男声", "male-qn-qingse"),
                ("青年男声", "male-qn-jingying"),
                ("成熟男声", "male-qn-badao"),
                ("温柔女声", "female-shaonv"),
                ("成熟女声", "female-chengshu"),
                ("甜美女声", "female-tianmei"),
                ("知性女声", "female-yujie"),
            ]
        },
        "custom": {
            "models": [("默认", "")],
            "voices": [("默认", "")]
        }
    }

    # 初始化模型和音色选项
    def _update_tts_options():
        provider = self.video_tts_provider_combo.currentData()
        options = self._tts_options.get(provider, {"models": [("默认", "")], "voices": [("默认", "")]})
        
        # 更新模型
        current_model = self.video_tts_model_combo.currentText()
        self.video_tts_model_combo.clear()
        for name, value in options["models"]:
            self.video_tts_model_combo.addItem(name, value)
        # 恢复之前的选择或设置默认值
        idx = self.video_tts_model_combo.findText(current_model)
        if idx >= 0:
            self.video_tts_model_combo.setCurrentIndex(idx)
        else:
            saved_model = getattr(config, 'video_tts_model', '')
            idx = self.video_tts_model_combo.findData(saved_model)
            if idx >= 0:
                self.video_tts_model_combo.setCurrentIndex(idx)
        
        # 更新音色
        current_voice = self.video_tts_voice_combo.currentText()
        self.video_tts_voice_combo.clear()
        for name, value in options["voices"]:
            self.video_tts_voice_combo.addItem(name, value)
        idx = self.video_tts_voice_combo.findText(current_voice)
        if idx >= 0:
            self.video_tts_voice_combo.setCurrentIndex(idx)
        else:
            saved_voice = getattr(config, 'video_tts_voice', '')
            idx = self.video_tts_voice_combo.findData(saved_voice)
            if idx >= 0:
                self.video_tts_voice_combo.setCurrentIndex(idx)

    self.video_tts_provider_combo.currentIndexChanged.connect(_update_tts_options)
    _update_tts_options()  # 初始化

    btn = QPushButton("💾 保存 API 设置")
    btn.clicked.connect(self.save_api_settings)
    layout.addWidget(btn)

    layout.addStretch()


def save_api_settings(self):
    config.ai_api_key = self.api_key_entry.text()
    config.ai_base_url = self.base_url_entry.text()
    config.ai_model = self.model_entry.text()
    config.multimodal_enabled = self.multimodal_enabled_check.isChecked()
    config.multimodal_api_key = self.multimodal_key_entry.text() or None
    config.multimodal_base_url = self.multimodal_url_entry.text() or None
    config.multimodal_model = self.multimodal_model_entry.text() or None
    config.email_smtp_server = self.smtp_server_entry.text() or None
    try:
        config.email_port = int(self.smtp_port_entry.text())
    except:
        config.email_port = 587
    config.email_user = self.email_user_entry.text() or None
    config.email_password = self.email_pass_entry.text() or None
    config.google_api_key = self.google_key_entry.text() or None
    config.google_cse_id = self.google_cse_entry.text() or None
    config.image_gen_provider = self.img_provider_combo.currentData()
    config.image_gen_api_key = self.img_key_entry.text() or None
    config.image_gen_base_url = self.img_url_entry.text() or None
    config.image_gen_model = self.img_model_entry.text() or None
    config.image_gen_size = self.img_size_entry.text() or "1024x1024"
    # 视频生成 TTS 配置
    config.video_tts_provider = self.video_tts_provider_combo.currentData()
    config.video_tts_api_key = self.video_tts_key_entry.text() or None
    config.video_tts_base_url = self.video_tts_url_entry.text() or None
    # 支持下拉框选择或手动输入
    model_data = self.video_tts_model_combo.currentData()
    model_text = self.video_tts_model_combo.currentText()
    config.video_tts_model = model_data if model_data else (model_text if model_text else None)
    voice_data = self.video_tts_voice_combo.currentData()
    voice_text = self.video_tts_voice_combo.currentText()
    config.video_tts_voice = voice_data if voice_data else (voice_text if voice_text else None)
    try:
        config.max_tokens = int(self.max_tokens_entry.text())
    except:
        pass
    try:
        config.temperature = float(self.temp_entry.text())
    except:
        pass
    config.model_supports_thinking = self.model_supports_thinking_check.isChecked()
    config.deepseek_thinking_enabled = self.deepseek_thinking_check.isChecked()
    config.deepseek_reasoning_effort = self.deepseek_effort_combo.currentData()
    config.deepseek_context_window = self.deepseek_context_combo.currentData()
    self.deepseek_section.setVisible(_is_deepseek_model(config.ai_model))
    self._save_all_config()
    QMessageBox.information(self, "保存成功", "API 设置已保存")


# ==================== QQ 设置页 ====================
def create_qq_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "QQ 设置")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    outer, frame, fl = _make_section_outer(self, "基础配置")
    layout.addWidget(outer)

    self.qq_enabled_check = QCheckBox("启用 QQ 机器人")
    self.qq_enabled_check.setChecked(config.qq_enabled)
    fl.addWidget(self.qq_enabled_check, 0, 0, 1, 2)

    self.ws_url_entry = _make_entry(fl, 1)
    _make_label(fl, "WebSocket:", 1)
    self.ws_url_entry.setText(config.qq_websocket_url)

    self.bot_uin_entry = _make_entry(fl, 2)
    _make_label(fl, "机器人QQ:", 2)
    self.bot_uin_entry.setText(config.qq_bot_uin)

    self.whitelist_entry = _make_entry(fl, 3)
    _make_label(fl, "白名单:", 3)
    self.whitelist_entry.setText(config.qq_whitelist)

    self.http_url_entry = _make_entry(fl, 4)
    _make_label(fl, "HTTP地址:", 4)
    self.http_url_entry.setText(config.napcat_http_url)

    self.token_entry = _make_entry(fl, 5)
    _make_label(fl, "Token:", 5)
    self.token_entry.setEchoMode(QLineEdit.EchoMode.Password)
    self.token_entry.setText(config.napcat_access_token)

    outer2, frame2, fl2 = _make_section_outer(self, "群聊陪伴模式")
    layout.addWidget(outer2)

    self.group_companion_enabled_check = QCheckBox("启用群聊陪伴（自动回复）")
    self.group_companion_enabled_check.setChecked(config.group_companion_enabled)
    fl2.addWidget(self.group_companion_enabled_check, 0, 0, 1, 3)

    fl2.addWidget(QLabel("目标群号:"), 1, 0)
    self.group_companion_group_id_entry = QLineEdit()
    self.group_companion_group_id_entry.setText(config.group_companion_group_id)
    self.group_companion_group_id_entry.setMaximumWidth(120)
    fl2.addWidget(self.group_companion_group_id_entry, 1, 1)

    fl2.addWidget(QLabel("回复概率(1-100):"), 1, 2)
    self.group_companion_probability_entry = QLineEdit()
    self.group_companion_probability_entry.setText(str(config.group_companion_probability))
    self.group_companion_probability_entry.setMaximumWidth(60)
    fl2.addWidget(self.group_companion_probability_entry, 1, 3)

    self.group_companion_voice_check = QCheckBox("使用语音回复（需edge-tts）")
    self.group_companion_voice_check.setChecked(config.group_companion_voice)
    fl2.addWidget(self.group_companion_voice_check, 2, 0, 1, 4)

    btn_layout = QHBoxLayout()
    save_btn = QPushButton("💾 保存 QQ 设置")
    save_btn.clicked.connect(self.save_qq_settings)
    btn_layout.addWidget(save_btn)
    start_btn = QPushButton("🚀 启动QQ机器人")
    start_btn.clicked.connect(self.start_qq_bot)
    btn_layout.addWidget(start_btn)
    stop_btn = QPushButton("⏹️ 停止")
    stop_btn.clicked.connect(self.stop_qq_bot)
    btn_layout.addWidget(stop_btn)
    btn_layout.addStretch()
    layout.addLayout(btn_layout)

    layout.addStretch()


def save_qq_settings(self):
    config.qq_enabled = self.qq_enabled_check.isChecked()
    config.qq_websocket_url = self.ws_url_entry.text()
    config.qq_bot_uin = self.bot_uin_entry.text()
    config.qq_whitelist = self.whitelist_entry.text()
    config.napcat_http_url = self.http_url_entry.text()
    config.napcat_access_token = self.token_entry.text()
    config.group_companion_enabled = self.group_companion_enabled_check.isChecked()
    config.group_companion_group_id = self.group_companion_group_id_entry.text().strip()
    try:
        config.group_companion_probability = int(self.group_companion_probability_entry.text())
    except:
        pass
    config.group_companion_voice = self.group_companion_voice_check.isChecked()
    self._save_all_config()
    QMessageBox.information(self, "保存成功", "QQ 设置已保存，重启后生效")


# ==================== 安全设置页 ====================
def create_security_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "安全设置")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    outer, frame, fl = _make_section_outer(self, "访问控制")
    layout.addWidget(outer)

    self.whitelist_enabled_check = QCheckBox("启用QQ白名单（仅允许列表中的QQ）")
    self.whitelist_enabled_check.setChecked(config.whitelist_enabled)
    fl.addWidget(self.whitelist_enabled_check, 0, 0)

    outer2, frame2, fl2 = _make_section_outer(self, "危险操作确认")
    layout.addWidget(outer2)

    confirm_tools = [
        ("delete_file", "删除文件"),
        ("move_file", "移动/重命名文件"),
        ("copy_file", "复制文件"),
        ("execute_code", "执行代码"),
        ("click", "鼠标点击"),
        ("type_text", "键盘输入"),
        ("move_mouse", "移动鼠标"),
        ("install_python_package", "安装Python包")
    ]
    self.tool_vars = {}

    for i, (tool_name, tool_label) in enumerate(confirm_tools):
        check = QCheckBox(tool_label)
        check.setChecked(config.tool_confirmation.get(tool_name, True))
        self.tool_vars[tool_name] = check
        row, col = divmod(i, 2)
        fl2.addWidget(check, row, col)

    outer3, frame3, fl3 = _make_section_outer(self, "浏览器安全")
    layout.addWidget(outer3)

    self.browser_safe_check = QCheckBox("启用浏览器自动化安全模式（禁止危险JS）")
    self.browser_safe_check.setChecked(config.browser_safe_mode)
    fl3.addWidget(self.browser_safe_check, 0, 0)

    btn = QPushButton("💾 保存安全设置")
    btn.clicked.connect(self.save_security_settings)
    layout.addWidget(btn)

    layout.addStretch()


def save_security_settings(self):
    config.whitelist_enabled = self.whitelist_enabled_check.isChecked()
    for tool_name, check in self.tool_vars.items():
        config.tool_confirmation[tool_name] = check.isChecked()
    config.browser_safe_mode = self.browser_safe_check.isChecked()
    self._save_all_config()
    QMessageBox.information(self, "保存成功", "安全设置已保存")


# ==================== 技能管理页 ====================
def create_skill_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "技能管理")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    dir_layout = QHBoxLayout()
    dir_layout.addWidget(QLabel("技能目录:"))
    self.skills_dirs_entry = QLineEdit()
    self.skills_dirs_entry.setText(','.join(config.skills_dirs))
    dir_layout.addWidget(self.skills_dirs_entry)
    layout.addLayout(dir_layout)

    toolbar = QHBoxLayout()
    refresh_btn = QPushButton("🔄 刷新")
    refresh_btn.clicked.connect(self.refresh_skill_list)
    toolbar.addWidget(refresh_btn)
    open_btn = QPushButton("📂 打开文件夹")
    open_btn.clicked.connect(self.open_skills_folder)
    toolbar.addWidget(open_btn)
    check_btn = QPushButton("🔒 安全检查")
    check_btn.clicked.connect(self.check_skills_security)
    toolbar.addWidget(check_btn)
    toolbar.addWidget(QLabel("AI生成:"))
    self.skill_prompt_entry = QLineEdit()
    self.skill_prompt_entry.setMaximumWidth(200)
    toolbar.addWidget(self.skill_prompt_entry)
    gen_btn = QPushButton("生成")
    gen_btn.clicked.connect(self.generate_skill_by_ai)
    toolbar.addWidget(gen_btn)
    toolbar.addStretch()
    layout.addLayout(toolbar)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    layout.addWidget(splitter)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.addWidget(QLabel("已发现技能"))
    self.skill_listbox = QListWidget()
    self.skill_listbox.currentItemChanged.connect(self.on_skill_select)
    left_layout.addWidget(self.skill_listbox)
    splitter.addWidget(left_widget)

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.addWidget(QLabel("技能配置 (config.json)"))
    self.skill_config_text = QTextEdit()
    self.skill_config_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    right_layout.addWidget(self.skill_config_text)

    self.skill_config_status = QLabel("")
    self.skill_config_status.setStyleSheet("color: gray; font-size: 8pt;")
    right_layout.addWidget(self.skill_config_status)

    btn_layout = QHBoxLayout()
    self.save_skill_config_btn = QPushButton("💾 保存配置")
    self.save_skill_config_btn.clicked.connect(self.save_current_skill_config)
    self.save_skill_config_btn.setEnabled(False)
    btn_layout.addWidget(self.save_skill_config_btn)
    self.edit_skill_config_btn = QPushButton("📝 外部编辑")
    self.edit_skill_config_btn.clicked.connect(self.open_skill_config_external)
    self.edit_skill_config_btn.setEnabled(False)
    btn_layout.addWidget(self.edit_skill_config_btn)
    btn_layout.addStretch()
    right_layout.addLayout(btn_layout)
    splitter.addWidget(right_widget)

    self.refresh_skill_list()


def refresh_skill_list(self):
    self.skill_listbox.clear()
    skills_dirs = [d.strip() for d in self.skills_dirs_entry.text().split(',') if d.strip()]
    if not skills_dirs:
        skills_dirs = getattr(config, 'skills_dirs', ["./skills"])
        if not skills_dirs:
            skills_dirs = ["./skills"]
    sm = SkillManager(skills_dirs)
    self.skill_metadata = sm.get_skill_metadata()
    for skill in self.skill_metadata:
        self.skill_listbox.addItem(f"{skill['name']}")
    self.skill_config_text.clear()
    self.skill_config_status.setText("")
    self.save_skill_config_btn.setEnabled(False)
    self.edit_skill_config_btn.setEnabled(False)
    self.current_skill = None


def on_skill_select(self):
    row = self.skill_listbox.currentRow()
    if row < 0:
        return
    skill = self.skill_metadata[row]
    self.current_skill = skill
    skills_dir = _get_first_skills_dir()
    skill_path = os.path.join(skills_dir, skill['name'])
    config_path = os.path.join(skill_path, "config.json")
    self.skill_config_text.clear()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.skill_config_text.setPlainText(content)
            self.skill_config_status.setText("配置文件已加载")
            self.skill_config_status.setStyleSheet("color: green; font-size: 8pt;")
            self.save_skill_config_btn.setEnabled(True)
            self.edit_skill_config_btn.setEnabled(True)
        except Exception as e:
            self.skill_config_text.setPlainText(f"读取失败：{str(e)}")
            self.skill_config_status.setText("读取失败")
            self.skill_config_status.setStyleSheet("color: red; font-size: 8pt;")
    else:
        self.skill_config_text.setPlainText("该技能没有配置文件")
        self.skill_config_status.setText("无配置文件")
        self.skill_config_status.setStyleSheet("color: gray; font-size: 8pt;")
        self.save_skill_config_btn.setEnabled(False)
        self.edit_skill_config_btn.setEnabled(True)


def save_current_skill_config(self):
    if not self.current_skill:
        QMessageBox.warning(self, "提示", "未选择任何技能")
        return
    skills_dir = _get_first_skills_dir()
    skill_path = os.path.join(skills_dir, self.current_skill['name'])
    config_path = os.path.join(skill_path, "config.json")
    content = self.skill_config_text.toPlainText().strip()
    try:
        json.loads(content)
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.skill_config_status.setText("保存成功")
        self.skill_config_status.setStyleSheet("color: green; font-size: 8pt;")
    except json.JSONDecodeError as e:
        QMessageBox.critical(self, "错误", f"JSON 格式错误：{e}")
    except Exception as e:
        QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")


def open_skill_config_external(self):
    if not self.current_skill:
        QMessageBox.warning(self, "提示", "未选择任何技能")
        return
    skills_dir = _get_first_skills_dir()
    skill_path = os.path.join(skills_dir, self.current_skill['name'])
    config_path = os.path.join(skill_path, "config.json")
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write("{\n  \n}")
            QMessageBox.information(self, "提示", "已创建空配置文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建配置文件：{str(e)}")
            return
    try:
        os.startfile(config_path)
    except AttributeError:
        subprocess.run(['open', config_path] if sys.platform == 'darwin' else ['xdg-open', config_path])


def open_skills_folder(self):
    skills_dir = [d.strip() for d in self.skills_dirs_entry.text().split(',') if d.strip()]
    if not skills_dir:
        skills_dir = getattr(config, 'skills_dirs', ["./skills"])
        if not skills_dir:
            skills_dir = ["./skills"]
    abs_skills_dir = os.path.abspath(skills_dir[0])
    if not os.path.exists(abs_skills_dir):
        try:
            os.makedirs(abs_skills_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建文件夹：{abs_skills_dir}\n{e}")
            return
    try:
        os.startfile(abs_skills_dir)
    except Exception as e:
        QMessageBox.critical(self, "错误", f"无法打开文件夹：{abs_skills_dir}\n{e}")


def check_skills_security(self):
    skills_dirs = [d.strip() for d in self.skills_dirs_entry.text().split(',') if d.strip()]
    if not skills_dirs:
        skills_dirs = getattr(config, 'skills_dirs', ["./skills"])
        if not skills_dirs:
            skills_dirs = ["./skills"]
    skills_dirs_str = ','.join(skills_dirs)
    threading.Thread(target=self._check_skills_thread, args=(skills_dirs_str,), daemon=True).start()


def _check_skills_thread(self, skills_dirs_str):
    try:
        dirs = [d.strip() for d in skills_dirs_str.split(',') if d.strip()]
        if not dirs:
            dirs = getattr(config, 'skills_dirs', ["./skills"])
        sm = SkillManager(dirs)
        all_skills = sm.skills
        if not all_skills:
            self.display_assistant_message("没有发现任何技能")
            return
        skills_info = []
        for name, skill in all_skills.items():
            content = skill.load_full_content()
            skills_info.append(f"技能名称: {name}\n描述: {skill.metadata.description}\n内容:\n{content[:1000]}...")
        ai_prompt = f"""你是一个安全审查专家。请检查以下每个技能是否包含恶意代码、危险指令或潜在的安全风险。

技能列表：
{chr(10).join(skills_info)}

对于每个技能，请判断是否安全。如果发现恶意内容，请详细说明风险。

请输出JSON格式的结果，如：
[
  {{
    "skill_name": "xxx",
    "safe": true/false,
    "reason": "说明"
  }},
  ...
]
"""
        messages = [{"role": "user", "content": ai_prompt}]
        response = self.agent.call_llm(messages)
        try:
            results = json.loads(response)
        except:
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                results = json.loads(match.group())
            else:
                results = [{"skill_name": "解析错误", "safe": False, "reason": "AI返回格式错误"}]
        QTimer.singleShot(0, lambda: self._show_skill_check_results(results))
    except Exception as e:
        self.display_assistant_message(f"❌ 安全检查失败: {str(e)}")


def _show_skill_check_results(self, results):
    dlg = QDialog(self)
    dlg.setWindowTitle("Skill安全检查结果")
    dlg.resize(500, 400)
    layout = QVBoxLayout(dlg)
    text = QTextEdit()
    text.setReadOnly(True)
    for item in results:
        name = item.get('skill_name', '未知')
        safe = item.get('safe', False)
        reason = item.get('reason', '')
        if safe:
            text.append(f"✅ {name}: 安全")
        else:
            text.append(f"❌ {name}: 可能存在风险")
        text.append(f"   原因: {reason}\n")
    layout.addWidget(text)
    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dlg.accept)
    layout.addWidget(close_btn)
    dlg.exec()


def generate_skill_by_ai(self):
    prompt = self.skill_prompt_entry.text().strip()
    if not prompt:
        QMessageBox.warning(self, "提示", "请输入Skill描述")
        return
    skills_dirs = [d.strip() for d in self.skills_dirs_entry.text().split(',') if d.strip()]
    if not skills_dirs:
        skills_dirs = getattr(config, 'skills_dirs', ["./skills"])
        if not skills_dirs:
            skills_dirs = ["./skills"]
    skills_dirs_str = ','.join(skills_dirs)
    threading.Thread(target=self._generate_skill_thread, args=(prompt, skills_dirs_str), daemon=True).start()


def _generate_skill_thread(self, prompt, skills_dirs_str):
    try:
        dirs = [d.strip() for d in skills_dirs_str.split(',') if d.strip()]
        if not dirs:
            self.display_assistant_message("错误: 未配置技能目录")
            return
        target_dir = dirs[0]
        os.makedirs(target_dir, exist_ok=True)
        ai_prompt = f"""请根据以下用户需求生成一个完整的Skill（技能包）。

用户需求: {prompt}

Skill格式要求:
- 必须是一个文件夹，名称根据需求自动生成（英文小写，用连字符连接）
- 文件夹内必须包含一个 SKILL.md 文件，该文件包含YAML frontmatter（元数据）和正文。
- YAML frontmatter 格式示例：
  ---
  name: skill-name
  description: 简短描述
  version: 1.0.0
  author: AI生成
  allowed-tools: []
  ---
- 正文部分用Markdown格式详细说明技能的使用方法、注意事项等。
- 可能还需要包含 scripts/ 目录和示例脚本（可选）。

**重要：配置管理**
- 如果技能需要 API Key、端口等敏感信息，请在技能文件夹中包含一个 `config.json` 文件，例如：
  {{
    "api_key": "your-api-key-here",
    "timeout": 10
  }}
- 在脚本中，应通过读取当前目录下的 `config.json` 来获取配置，避免硬编码。示例代码：
  import json, os
  def load_config():
      with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as f:
          return json.load(f)
- 在 SKILL.md 中说明用户需要填写 `config.json` 中的必要信息。

请直接输出一个**严格的、合法的JSON对象**，不要包含任何其他解释文字。确保JSON中所有的字符串都使用双引号，并且内部的双引号已被正确转义（使用反斜杠）。

输出格式：
{{
  "folder_name": "生成的文件夹名",
  "skill_md_content": "完整的SKILL.md文件内容（包含frontmatter和正文）",
  "config_json_content": "config.json 文件内容（可选）",
  "scripts": [  # 可选，如果有脚本
    {{
      "filename": "脚本文件名（如 hello.py）",
      "content": "脚本内容"
    }}
  ]
}}
"""
        messages = [{"role": "user", "content": ai_prompt}]
        response = self.agent.call_llm(messages)
        data = None
        error_detail = ""
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            error_detail = f"直接解析失败: {e}"
            stack = []
            start = -1
            for i, ch in enumerate(response):
                if ch == '{':
                    if not stack:
                        start = i
                    stack.append('{')
                elif ch == '}':
                    if stack:
                        stack.pop()
                        if not stack and start != -1:
                            json_str = response[start:i+1]
                            try:
                                data = json.loads(json_str)
                                break
                            except json.JSONDecodeError as e2:
                                error_detail += f"；提取后解析失败: {e2}"
                            break
            if data is None:
                match = re.search(r'\{[\s\S]*\}', response)
                if match:
                    json_str = match.group()
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError as e3:
                        error_detail += f"；正则提取后解析失败: {e3}"
        if data is None:
            raise ValueError(f"无法从AI响应中提取有效的JSON。{error_detail}\n原始响应: {response[:500]}...")
        folder_name = data.get('folder_name', '').strip()
        if not folder_name:
            folder_name = re.sub(r'[^a-z0-9-]', '', prompt.lower().replace(' ', '-'))[:30]
        skill_path = os.path.join(target_dir, folder_name)
        os.makedirs(skill_path, exist_ok=True)
        skill_md = data.get('skill_md_content', '')
        with open(os.path.join(skill_path, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write(skill_md)
        config_json = data.get('config_json_content')
        if config_json:
            config_path = os.path.join(skill_path, "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_json)
        scripts = data.get('scripts', [])
        if scripts:
            scripts_dir = os.path.join(skill_path, 'scripts')
            os.makedirs(scripts_dir, exist_ok=True)
            for script in scripts:
                script_path = os.path.join(scripts_dir, script['filename'])
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script['content'])
        self.display_assistant_message(f"✅ Skill '{folder_name}' 已生成在 {skill_path}")
        QTimer.singleShot(0, self.refresh_skill_list)
    except Exception as e:
        self.display_assistant_message(f"❌ 生成Skill失败: {str(e)}")


# ==================== 插件管理页 ====================
def create_plugin_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "插件管理")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    toolbar = QHBoxLayout()
    reload_btn = QPushButton("🔄 重载所有")
    reload_btn.clicked.connect(self.reload_plugins)
    toolbar.addWidget(reload_btn)
    open_btn = QPushButton("📂 打开文件夹")
    open_btn.clicked.connect(self.open_plugins_folder)
    toolbar.addWidget(open_btn)
    check_btn = QPushButton("🔒 安全检查")
    check_btn.clicked.connect(self.check_plugins_security)
    toolbar.addWidget(check_btn)
    trans_btn = QPushButton("🌐 AI 翻译")
    trans_btn.clicked.connect(self.open_ai_translator)
    toolbar.addWidget(trans_btn)
    toolbar.addWidget(QLabel("AI生成:"))
    self.plugin_desc_entry = QLineEdit()
    self.plugin_desc_entry.setMaximumWidth(200)
    toolbar.addWidget(self.plugin_desc_entry)
    gen_btn = QPushButton("生成")
    gen_btn.clicked.connect(self.generate_plugin)
    toolbar.addWidget(gen_btn)
    toolbar.addStretch()
    layout.addLayout(toolbar)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    layout.addWidget(splitter)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.addWidget(QLabel("已加载插件 (V2)"))
    self.plugins_listbox = QListWidget()
    self.plugins_listbox.currentItemChanged.connect(self.on_plugin_select)
    left_layout.addWidget(self.plugins_listbox)
    splitter.addWidget(left_widget)

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.addWidget(QLabel("插件设置"))
    self.plugin_settings_container = QWidget()
    container_layout = QVBoxLayout(self.plugin_settings_container)
    container_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.addWidget(self.plugin_settings_container)
    splitter.addWidget(right_widget)

    self.refresh_plugins_display()


def refresh_plugins_display(self):
    self.plugins_listbox.clear()
    self.current_plugin_list = []

    if not hasattr(self, 'plugin_manager_v2'):
        return

    plugins_info = self.plugin_manager_v2.get_all_plugins_info()
    for info in plugins_info:
        status = "✅" if info["enabled"] else "❌"
        source_tag = f"[{info['source']}]"
        display_text = f"{status} {source_tag} {info['name']} (v{info['version']})"
        self.plugins_listbox.addItem(display_text)
        self.current_plugin_list.append(info)

    children = self.plugin_settings_container.findChildren(QWidget)
    for child in children:
        if child.parent() == self.plugin_settings_container:
            child.deleteLater()


def on_plugin_select(self):
    row = self.plugins_listbox.currentRow()
    if row < 0:
        return

    plugin_info = self.current_plugin_list[row]

    children = self.plugin_settings_container.findChildren(QWidget)
    for child in children:
        if child.parent() == self.plugin_settings_container:
            child.deleteLater()

    layout = self.plugin_settings_container.layout()
    if layout is None:
        layout = QVBoxLayout(self.plugin_settings_container)
        layout.setContentsMargins(0, 0, 0, 0)
    else:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    info_text = (f"ID: {plugin_info['id']}\n"
                 f"名称: {plugin_info['name']}\n"
                 f"版本: {plugin_info['version']}\n"
                 f"来源: {plugin_info['source']}\n"
                 f"描述: {plugin_info['description']}")
    info_label = QLabel(info_text)
    info_label.setStyleSheet("font-size: 9pt;")
    layout.addWidget(info_label)

    btn_layout = QHBoxLayout()
    if plugin_info["enabled"]:
        disable_btn = QPushButton("禁用")
        disable_btn.clicked.connect(lambda checked, pid=plugin_info["id"]: self.toggle_plugin_enabled(pid, False))
        btn_layout.addWidget(disable_btn)
    else:
        enable_btn = QPushButton("启用")
        enable_btn.clicked.connect(lambda checked, pid=plugin_info["id"]: self.toggle_plugin_enabled(pid, True))
        btn_layout.addWidget(enable_btn)

    reload_btn = QPushButton("重载")
    reload_btn.clicked.connect(lambda checked, pid=plugin_info["id"]: self.reload_single_plugin(pid))
    btn_layout.addWidget(reload_btn)
    btn_layout.addStretch()
    layout.addLayout(btn_layout)

    plugin_instance = plugin_info["instance"]
    usage_info = self._extract_plugin_usage_info(plugin_instance, plugin_info["manifest"])

    if usage_info:
        usage_label = QLabel("📖 使用说明")
        usage_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 9pt;")
        layout.addWidget(usage_label)

        usage_frame = QFrame()
        usage_frame.setFrameShape(QFrame.Shape.StyledPanel)
        usage_frame.setFrameShadow(QFrame.Shadow.Plain)
        usage_fl = QVBoxLayout(usage_frame)

        usage_text = ""
        if usage_info.get("commands"):
            usage_text += "【快捷命令】\n"
            for cmd, desc in usage_info["commands"].items():
                usage_text += f"  • {cmd} - {desc}\n"
        if usage_info.get("tools"):
            usage_text += "\n【注册的工具】\n"
            for tool in usage_info["tools"]:
                usage_text += f"  • {tool['name']}: {tool['description']}\n"
        if usage_info.get("auto_effect"):
            usage_text += f"\n【自动效果】\n{usage_info['auto_effect']}\n"

        if usage_text:
            ul = QLabel(usage_text.strip())
            ul.setStyleSheet("font-size: 9pt;")
            usage_fl.addWidget(ul)
        layout.addWidget(usage_frame)

    if hasattr(plugin_instance, 'get_settings_ui'):
        try:
            settings_ui = plugin_instance.get_settings_ui(self.plugin_settings_container)
            if settings_ui is not None:
                settings_label = QLabel("⚙️ 插件设置")
                settings_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 9pt;")
                layout.addWidget(settings_label)
                layout.addWidget(settings_ui)
        except Exception as e:
            err_label = QLabel(f"加载设置界面失败: {e}")
            err_label.setStyleSheet("color: red;")
            layout.addWidget(err_label)

    layout.addStretch()


def _extract_plugin_usage_info(self, plugin_instance, manifest):
    info = {"commands": {}, "tools": [], "auto_effect": None}

    if hasattr(plugin_instance, 'get_usage_info'):
        try:
            custom_info = plugin_instance.get_usage_info()
            if isinstance(custom_info, dict):
                info.update(custom_info)
                return info
        except:
            pass

    try:
        import inspect
        source = inspect.getsource(plugin_instance.on_load)

        cmd_patterns = [
            r'if\s+content\.startswith\(["\'](/[^"\']+)["\']\)',
            r'if\s+content\.strip\(\)\.lower\(\)\s*==\s*["\'](/[^"\']+)["\']',
            r'elif\s+content\.strip\(\)\.lower\(\)\s*==\s*["\'](/[^"\']+)["\']',
        ]
        commands = set()
        for pattern in cmd_patterns:
            matches = re.findall(pattern, source)
            commands.update(matches)

        if commands:
            info["commands"] = {cmd: "快捷命令" for cmd in commands}

        tool_sections = re.finditer(
            r'host_api\.agent\.register_tool\s*\(\s*(\{[^}]+\})\s*,',
            source,
            re.DOTALL
        )
        for match in tool_sections:
            tool_def_str = match.group(1)
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', tool_def_str)
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', tool_def_str)
            if name_match:
                tool_name = name_match.group(1)
                tool_desc = desc_match.group(1) if desc_match else "工具"
                info["tools"].append({"name": tool_name, "description": tool_desc})

        if not info["commands"] and not info["tools"]:
            if 'SystemEvents.UI_READY' in source or 'host_api.ui.display_message' in source:
                info["auto_effect"] = "插件启动后会自动生效。"

    except Exception:
        pass

    if not info["commands"] and not info["tools"] and not info["auto_effect"]:
        desc = manifest.description
        if "使用方法" in desc or "命令" in desc or "工具" in desc:
            info["auto_effect"] = desc
        else:
            info["auto_effect"] = "请查看插件描述或文档。"

    return info


def toggle_plugin_enabled(self, plugin_id, enabled):
    if enabled:
        self.plugin_manager_v2.enable_plugin(plugin_id)
    else:
        self.plugin_manager_v2.disable_plugin(plugin_id)
    self.refresh_plugins_display()


def reload_single_plugin(self, plugin_id):
    if self.plugin_manager_v2.reload_plugin(plugin_id):
        QMessageBox.information(self, "成功", f"插件 {plugin_id} 已重载")
    else:
        QMessageBox.critical(self, "错误", f"插件 {plugin_id} 重载失败")
    self.refresh_plugins_display()


def reload_plugins(self):
    count = 0
    for info in self.current_plugin_list:
        if self.plugin_manager_v2.reload_plugin(info["id"]):
            count += 1
    self.refresh_plugins_display()
    QMessageBox.information(self, "完成", f"成功重载 {count} 个插件")


def open_plugins_folder(self):
    plugins_dir = getattr(self, 'plugins_dir', './plugins')
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir, exist_ok=True)
    os.startfile(os.path.abspath(plugins_dir))


def check_plugins_security(self):
    threading.Thread(target=self._check_plugins_security_thread_v2, daemon=True).start()


def _check_plugins_security_thread_v2(self):
    plugins_info = []
    for info in self.current_plugin_list:
        plugin_folder = info["instance"].get_plugin_dir()
        main_py = os.path.join(plugin_folder, info["manifest"].entry_point)
        if os.path.exists(main_py):
            try:
                with open(main_py, 'r', encoding='utf-8') as f:
                    code = f.read()
            except:
                code = "无法读取代码"
        else:
            code = "找不到入口文件"

        manifest_str = json.dumps(info["manifest"].__dict__, indent=2, ensure_ascii=False)

        plugins_info.append(
            f"插件ID: {info['id']}\n名称: {info['name']}\n版本: {info['version']}\n"
            f"声明能力: {info['manifest'].capabilities}\n请求权限: {info['manifest'].permissions}\n"
            f"代码摘要:\n{code[:2000]}"
        )

    if not plugins_info:
        self.display_assistant_message("没有已加载的插件可供检查")
        return

    prompt = f"""你是一个安全审查专家。请检查以下 V2 插件是否包含恶意代码、危险指令或潜在的安全风险。
插件基于 PluginV2 框架，具有声明式权限系统。请关注：
1. 代码中是否有超出声明权限的危险操作（如未声明文件写入却使用 open 写入）
2. 是否有恶意行为（如删除文件、收集敏感信息、网络外传等）
3. 权限声明是否与实际行为匹配

插件列表：
{chr(10).join(plugins_info)}

请输出 JSON 格式的结果，如：
[
  {{
    "plugin_id": "xxx",
    "safe": true/false,
    "reason": "说明"
  }}
]
"""
    messages = [{"role": "user", "content": prompt}]
    response = self.agent.call_llm(messages)
    try:
        results = json.loads(response)
    except:
        match = re.search(r'\[[\s\S]*\]', response)
        if match:
            results = json.loads(match.group())
        else:
            results = [{"plugin_id": "解析错误", "safe": False, "reason": "AI返回格式错误"}]

    QTimer.singleShot(0, lambda: self._show_plugin_security_results_v2(results))


def _show_plugin_security_results_v2(self, results):
    dlg = QDialog(self)
    dlg.setWindowTitle("插件安全检查结果 (V2)")
    dlg.resize(500, 400)
    layout = QVBoxLayout(dlg)
    text = QTextEdit()
    text.setReadOnly(True)

    for item in results:
        pid = item.get('plugin_id', '未知')
        safe = item.get('safe', False)
        reason = item.get('reason', '')
        if safe:
            text.append(f"✅ {pid}: 安全")
        else:
            text.append(f"❌ {pid}: 可能存在风险")
        text.append(f"   原因: {reason}\n")

    layout.addWidget(text)
    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dlg.accept)
    layout.addWidget(close_btn)
    dlg.exec()


def generate_plugin(self):
    desc = self.plugin_desc_entry.text().strip()
    if not desc:
        QMessageBox.warning(self, "提示", "请输入插件描述")
        return
    threading.Thread(target=self._generate_plugin_thread, args=(desc,), daemon=True).start()


def _generate_plugin_thread(self, description):
    from openai import OpenAI

    prompts_file = os.path.join("plugin_v2", "ai_generator", "prompts.json")
    default_system = "你是一个专业的 Python 开发者，擅长为 TG HELPER 平台编写 PluginV2 插件。"
    default_template = """请根据以下用户需求生成一个完整的 TG HELPER PluginV2 插件。

需求: {description}

【重要】你必须严格按照以下格式输出，先输出 plugin.json 的内容（用 ```json 代码块包裹），再输出 main.py 的内容（用 ```python 代码块包裹）。
不要输出任何额外的解释或说明。

plugin.json 示例：
{{
    "id": "com.example.myplugin",
    "name": "我的插件",
    "version": "1.0.0",
    "description": "插件描述",
    "capabilities": ["ui.display"],
    "permissions": ["ui.display"],
    "entry_point": "main.py"
}}

main.py 示例：
from plugin_v2 import PluginV2, HostAPI, SystemEvents

class MyPlugin(PluginV2):
    def get_manifest(self):
        return {{
            "id": "com.example.myplugin",
            "name": "我的插件",
            "version": "1.0.0",
            "description": "插件描述",
            "capabilities": ["ui.display"],
            "permissions": ["ui.display"],
            "entry_point": "main.py"
        }}

    def on_load(self, host_api: HostAPI):
        host_api.ui.display_message("插件已加载！")

请直接输出两个代码块。"""

    if os.path.exists(prompts_file):
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            system_prompt = prompts.get("system_prompt", default_system)
            template = prompts.get("template", default_template)
        except:
            system_prompt = default_system
            template = default_template
    else:
        system_prompt = default_system
        template = default_template

    prompt = template.replace("{description}", description)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    client = OpenAI(
        api_key=config.ai_api_key,
        base_url=config.ai_base_url,
        timeout=999.0
    )

    max_retries = 2
    response = None
    for attempt in range(max_retries):
        try:
            kwargs = dict(
                model=config.ai_model,
                messages=messages,
                temperature=1,
                max_tokens=8000)
            if 'deepseek' in config.ai_model.lower() and getattr(config, 'deepseek_thinking_enabled', False):
                kwargs['reasoning_effort'] = getattr(config, 'deepseek_reasoning_effort', 'high')
                kwargs['extra_body'] = {"thinking": {"type": "enabled"}}
                ctx = getattr(config, 'deepseek_context_window', 0)
                if ctx:
                    kwargs['max_tokens'] = ctx
            completion = client.chat.completions.create(**kwargs)
            response = completion.choices[0].message.content
            break
        except Exception as e:
            if attempt == max_retries - 1:
                self.display_assistant_message(f"AI 调用失败（已重试 {max_retries} 次）: {str(e)}")
                return
            time.sleep(2)

    if not response:
        self.display_assistant_message("AI 返回空响应")
        return

    plugin_json_str = None
    main_py_str = None

    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
    if json_match:
        plugin_json_str = json_match.group(1).strip()
    else:
        all_code_blocks = re.findall(r'```(?:\w+)?\s*([\s\S]*?)\s*```', response)
        for block in all_code_blocks:
            block_stripped = block.strip()
            if block_stripped.startswith('{') and block_stripped.endswith('}'):
                try:
                    json.loads(block_stripped)
                    plugin_json_str = block_stripped
                    break
                except:
                    continue

    py_match = re.search(r'```python\s*([\s\S]*?)\s*```', response)
    if py_match:
        main_py_str = py_match.group(1).strip()
    else:
        all_code_blocks = re.findall(r'```(?:\w+)?\s*([\s\S]*?)\s*```', response)
        for block in all_code_blocks:
            block_stripped = block.strip()
            if 'from plugin_v2 import' in block_stripped or ('class ' in block_stripped and 'PluginV2' in block_stripped):
                main_py_str = block_stripped
                break

    if not plugin_json_str:
        json_match = re.search(r'\{[\s\S]*"id"[\s\S]*\}', response)
        if json_match:
            try:
                candidate = json_match.group(0)
                json.loads(candidate)
                plugin_json_str = candidate
            except:
                pass

    if not main_py_str:
        py_match = re.search(r'(from plugin_v2 import.*?(?:class\s+\w+.*?on_load.*?))', response, re.DOTALL)
        if py_match:
            main_py_str = py_match.group(1).strip()

    if not plugin_json_str or not main_py_str:
        preview = response[:2000] + ("..." if len(response) > 2000 else "")
        self.display_assistant_message(f"AI 生成插件失败：未能解析出 plugin.json 或 main.py。\n\nAI 原始响应：\n{preview}")
        return

    try:
        manifest_data = json.loads(plugin_json_str)
        if "id" not in manifest_data:
            manifest_data["id"] = f"com.tghelper.{re.sub(r'[^a-z0-9]', '', description.lower())[:20]}"
        if "name" not in manifest_data:
            manifest_data["name"] = description[:30]
        if "version" not in manifest_data:
            manifest_data["version"] = "1.0.0"
        if "entry_point" not in manifest_data:
            manifest_data["entry_point"] = "main.py"
        plugin_json_str = json.dumps(manifest_data, indent=2, ensure_ascii=False)
    except Exception as e:
        self.display_assistant_message(f"AI 生成的 plugin.json 格式错误: {e}\n\n内容:\n{plugin_json_str[:500]}")
        return

    plugin_id = manifest_data.get("id", "com.tghelper.generated")
    folder_name = plugin_id.split('.')[-1] if '.' in plugin_id else re.sub(r'[^a-z0-9_]', '_', description.lower())[:30]
    if not folder_name:
        folder_name = "generated_plugin"

    plugins_dir = self.plugin_manager_v2._plugins_dirs[0] if (hasattr(self, 'plugin_manager_v2') and self.plugin_manager_v2._plugins_dirs) else "./plugins"
    plugin_folder = os.path.join(plugins_dir, folder_name)
    os.makedirs(plugin_folder, exist_ok=True)

    manifest_path = os.path.join(plugin_folder, "plugin.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(plugin_json_str)

    main_py_path = os.path.join(plugin_folder, "main.py")
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(main_py_str)

    if hasattr(self, 'plugin_manager_v2'):
        loaded_id = self.plugin_manager_v2.load_plugin(plugin_folder)
        if loaded_id:
            self.display_assistant_message(f"✅ 插件已生成并加载：{plugin_folder}\n插件ID: {loaded_id}")
        else:
            self.display_assistant_message(f"⚠️ 插件已生成但加载失败，请检查代码。\n路径: {plugin_folder}")
    else:
        self.display_assistant_message(f"✅ 插件已生成：{plugin_folder}")

    if hasattr(self, 'refresh_plugins_display'):
        QTimer.singleShot(0, self.refresh_plugins_display)


# ==================== 定时任务页 ====================
def create_tasks_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "定时任务")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    toolbar = QHBoxLayout()
    add_btn = QPushButton("➕ 添加任务")
    add_btn.clicked.connect(self.add_task)
    toolbar.addWidget(add_btn)
    refresh_btn = QPushButton("🔄 刷新")
    refresh_btn.clicked.connect(self.refresh_tasks)
    toolbar.addWidget(refresh_btn)
    toolbar.addStretch()
    layout.addLayout(toolbar)

    self.task_table = QTableWidget()
    self.task_table.setColumnCount(5)
    self.task_table.setHorizontalHeaderLabels(['ID', '消息', '触发器', '下次运行', '状态'])
    self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    self.task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.task_table.customContextMenuRequested.connect(self._show_task_menu)
    layout.addWidget(self.task_table)

    self.refresh_tasks()


def _show_task_menu(self, pos):
    menu = QMenu(self)
    edit_action = menu.addAction("编辑")
    edit_action.triggered.connect(self.edit_task)
    delete_action = menu.addAction("删除")
    delete_action.triggered.connect(self.delete_task)
    menu.exec(self.task_table.viewport().mapToGlobal(pos))


def refresh_tasks(self):
    self.task_table.setRowCount(0)
    tasks = self.task_scheduler.get_tasks()
    self.task_table.setRowCount(len(tasks))
    for row, task in enumerate(tasks):
        task_id = task['id']
        msg = task.get('message', '')
        trigger = f"{task.get('trigger')}: {task.get('trigger_args')}"
        next_run = "N/A"
        job = self.task_scheduler.scheduler.get_job(task_id)
        if job and job.next_run_time:
            next_run = job.next_run_time.strftime("%m-%d %H:%M")
        status = "启用" if task.get('enabled', True) else "禁用"
        self.task_table.setItem(row, 0, QTableWidgetItem(task_id[:8]))
        self.task_table.setItem(row, 1, QTableWidgetItem(msg[:20] + "..." if len(msg) > 20 else msg))
        self.task_table.setItem(row, 2, QTableWidgetItem(trigger[:20]))
        self.task_table.setItem(row, 3, QTableWidgetItem(next_run))
        self.task_table.setItem(row, 4, QTableWidgetItem(status))


def add_task(self):
    dlg = QDialog(self)
    dlg.setWindowTitle("添加定时任务")
    dlg.resize(380, 350)
    dlg.setModal(True)

    layout = QGridLayout(dlg)

    layout.addWidget(QLabel("消息内容:"), 0, 0)
    msg_entry = QLineEdit()
    layout.addWidget(msg_entry, 0, 1)

    layout.addWidget(QLabel("触发方式:"), 1, 0)
    cron_radio = QRadioButton("Cron")
    interval_radio = QRadioButton("间隔(秒)")
    date_radio = QRadioButton("一次性")
    cron_radio.setChecked(True)
    layout.addWidget(cron_radio, 1, 1)
    layout.addWidget(interval_radio, 2, 1)
    layout.addWidget(date_radio, 3, 1)

    layout.addWidget(QLabel("Cron表达式 (0 8 * * *):"), 4, 0)
    cron_entry = QLineEdit()
    layout.addWidget(cron_entry, 4, 1)

    layout.addWidget(QLabel("间隔秒数:"), 5, 0)
    interval_entry = QLineEdit()
    layout.addWidget(interval_entry, 5, 1)

    layout.addWidget(QLabel("时间 (YYYY-MM-DD HH:MM:SS):"), 6, 0)
    date_entry = QLineEdit()
    layout.addWidget(date_entry, 6, 1)

    def save_task():
        msg = msg_entry.text().strip()
        if not msg:
            QMessageBox.critical(dlg, "错误", "消息内容不能为空")
            return
        if cron_radio.isChecked():
            t_type = 'cron'
            cron = cron_entry.text().strip()
            if not cron:
                QMessageBox.critical(dlg, "错误", "请输入Cron表达式")
                return
            trigger_args = {'cron': cron}
        elif interval_radio.isChecked():
            t_type = 'interval'
            try:
                seconds = int(interval_entry.text().strip())
                if seconds <= 0:
                    raise ValueError
                trigger_args = {'seconds': seconds}
            except:
                QMessageBox.critical(dlg, "错误", "请输入大于0的整数秒数")
                return
        else:
            t_type = 'date'
            date_str = date_entry.text().strip()
            try:
                datetime.fromisoformat(date_str)
                trigger_args = {'run_date': date_str}
            except:
                QMessageBox.critical(dlg, "错误", "时间格式错误")
                return
        task_info = {
            'message': msg,
            'trigger': t_type,
            'trigger_args': trigger_args,
            'enabled': True
        }
        self.task_scheduler.add_task(task_info)
        self.refresh_tasks()
        dlg.accept()

    save_btn = QPushButton("保存")
    save_btn.clicked.connect(save_task)
    layout.addWidget(save_btn, 7, 0, 1, 2)

    dlg.exec()


def edit_task(self):
    QMessageBox.information(self, "提示", "编辑功能在此版本中简化为删除后重新添加")


def delete_task(self):
    rows = set()
    for idx in self.task_table.selectedIndexes():
        rows.add(idx.row())
    if not rows:
        QMessageBox.warning(self, "提示", "请先选择一个任务")
        return
    row = list(rows)[0]
    task_id_short = self.task_table.item(row, 0).text()
    reply = QMessageBox.question(self, "确认", "删除该任务？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        tasks = self.task_scheduler.get_tasks()
        for t in tasks:
            if t['id'].startswith(task_id_short):
                self.task_scheduler.remove_task(t['id'])
                break
        self.refresh_tasks()


# ==================== AI人格页 ====================
def create_personality_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "AI人格")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    layout.addWidget(splitter)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.addWidget(QLabel("可选人格"))
    self.personality_listbox = QListWidget()
    self.personality_listbox.currentItemChanged.connect(self.on_personality_select)
    left_layout.addWidget(self.personality_listbox)
    splitter.addWidget(left_widget)

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)

    self.avatar_label_personality = QLabel("头像预览")
    self.avatar_label_personality.setAlignment(Qt.AlignmentFlag.AlignCenter)
    right_layout.addWidget(self.avatar_label_personality)

    self.name_label = QLabel("名称：")
    self.name_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
    right_layout.addWidget(self.name_label)

    self.prompt_text = QTextEdit()
    self.prompt_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    right_layout.addWidget(self.prompt_text)

    btn_layout = QHBoxLayout()
    apply_btn = QPushButton("✓ 应用人格")
    apply_btn.clicked.connect(self.on_apply_personality)
    btn_layout.addWidget(apply_btn)
    open_btn = QPushButton("📂 打开文件夹")
    open_btn.clicked.connect(self.open_personality_folder)
    btn_layout.addWidget(open_btn)
    btn_layout.addStretch()
    right_layout.addLayout(btn_layout)
    splitter.addWidget(right_widget)

    self.refresh_personality_list()


def refresh_personality_list(self):
    self.personality_listbox.clear()
    for p in self.personalities:
        self.personality_listbox.addItem(p['name'])


def on_personality_select(self):
    row = self.personality_listbox.currentRow()
    if row < 0:
        return
    p = self.personalities[row]
    self.name_label.setText(f"名称：{p['name']}")
    self.prompt_text.setPlainText(p['prompt'])
    if p['avatar'] and os.path.exists(p['avatar']):
        try:
            pixmap = QPixmap(p['avatar'])
            pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.avatar_label_personality.setPixmap(pixmap)
        except:
            self.avatar_label_personality.setText("头像加载失败")
    else:
        self.avatar_label_personality.setText("无头像")


def on_apply_personality(self):
    row = self.personality_listbox.currentRow()
    if row < 0:
        QMessageBox.warning(self, "提示", "请先选择一个人格")
        return
    p = self.personalities[row]
    self.apply_personality(p['name'])
    QMessageBox.information(self, "成功", f"已切换到人格：{p['name']}")
    self.update_current_personality_display()


def apply_personality(self, personality_name):
    for p in self.personalities:
        if p['name'] == personality_name:
            config.current_personality = personality_name
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            except:
                cfg = {}
            cfg['current_personality'] = personality_name
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
            self.agent.personality_prompt = p['prompt']
            self.personality_name = personality_name
            
            # 切换记忆系统（热闹模式下共用短期记忆，普通模式下独立）
            self._switch_memory_for_personality(personality_name)
            
            if config.qq_enabled and p['avatar']:
                self.set_qq_avatar(p['avatar'])
                self.set_qq_nickname(personality_name)
            break


def _switch_memory_for_personality(self, personality_name):
    """
    切换人格时同步切换记忆系统。
    - 热闹模式(fun_mode)：所有人格共用 "fun_mode" 的短期记忆
    - 普通模式：每个人格使用独立的记忆目录
    """
    from memory import Memory
    
    # 判断是否为热闹模式
    is_fun_mode = hasattr(self, 'fun_mode') and self.fun_mode.isChecked()
    
    # 确定目标记忆人格名
    if is_fun_mode:
        target_persona = "fun_mode"  # 热闹模式下共用
    else:
        target_persona = personality_name  # 普通模式下独立
    
    # 如果当前记忆已经是目标人格，无需切换
    if hasattr(self, 'memory') and self.memory.persona_name == target_persona:
        return
    
    # 关闭当前记忆系统
    if hasattr(self, 'memory') and self.memory:
        try:
            self.memory.shutdown()
        except Exception as e:
            print(f"[Memory] 关闭旧记忆系统时出错: {e}")
    
    # 初始化新的记忆系统
    self.memory = Memory(
        mind_dir=config.memory_dir,
        persona_name=target_persona,
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
    
    # 更新 agent 的记忆引用
    if hasattr(self, 'agent') and self.agent:
        self.agent.memory = self.memory
    
    mode_text = "热闹模式(共用)" if is_fun_mode else "独立记忆"
    print(f"[Memory] 已切换到 {target_persona} 的记忆系统 ({mode_text})")


def open_personality_folder(self):
    abs_personality_dir = os.path.abspath(self.personality_dir)
    if not os.path.exists(abs_personality_dir):
        try:
            os.makedirs(abs_personality_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建文件夹：{abs_personality_dir}\n{e}")
            return
    try:
        os.startfile(abs_personality_dir)
    except Exception as e:
        QMessageBox.critical(self, "错误", f"无法打开文件夹：{abs_personality_dir}\n{e}")


# ==================== 调试页 ====================
def create_debug_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "通用设置")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(10, 10, 10, 10)

    def toggle_debug(checked):
        config.debug_mode = checked
        self._save_all_config()

    self.debug_mode = QCheckBox("调试模式（显示工具调用结果）")
    self.debug_mode.setChecked(config.debug_mode)
    self.debug_mode.toggled.connect(toggle_debug)
    layout.addWidget(self.debug_mode)

    def toggle_auto_backup(checked):
        config.auto_backup_short_term = checked
        self._save_all_config()

    self.auto_backup_check = QCheckBox("自动备份并清空短期记忆")
    self.auto_backup_check.setChecked(config.auto_backup_short_term)
    self.auto_backup_check.toggled.connect(toggle_auto_backup)
    layout.addWidget(self.auto_backup_check)

    def toggle_browser_headful(checked):
        config.browser_headful = checked
        self._save_all_config()

    self.browser_headful_check = QCheckBox("浏览器有头模式（显示窗口，便于调试）")
    self.browser_headful_check.setChecked(getattr(config, 'browser_headful', False))
    self.browser_headful_check.toggled.connect(toggle_browser_headful)
    layout.addWidget(self.browser_headful_check)

    def toggle_show_ai_thinking(checked):
        config.show_ai_thinking = checked
        self._save_all_config()

    self.show_ai_thinking_check = QCheckBox("在聊天框中显示AI的思考内容")
    self.show_ai_thinking_check.setChecked(getattr(config, 'show_ai_thinking', False))
    self.show_ai_thinking_check.toggled.connect(toggle_show_ai_thinking)
    layout.addWidget(self.show_ai_thinking_check)

    # ====== 内存优化区域 ======
    outer_mem, frame_mem, fl_mem = _make_section_outer(self, "内存优化")
    layout.addWidget(outer_mem)

    mem_opt_widget = QWidget()
    mem_opt_layout = QHBoxLayout(mem_opt_widget)
    mem_opt_layout.setContentsMargins(0, 0, 0, 0)

    list_proc_btn = QPushButton("📋 查看进程列表")
    list_proc_btn.clicked.connect(self._on_list_processes)
    mem_opt_layout.addWidget(list_proc_btn)

    opt_mem_btn = QPushButton("🧹 内存优化")
    opt_mem_btn.clicked.connect(self._on_optimize_memory)
    mem_opt_layout.addWidget(opt_mem_btn)

    opt_vram_btn = QPushButton("🎮 显存优化")
    opt_vram_btn.clicked.connect(self._on_optimize_vram)
    mem_opt_layout.addWidget(opt_vram_btn)

    opt_full_btn = QPushButton("⚡ 完整优化")
    opt_full_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 6px 14px;")
    opt_full_btn.clicked.connect(self._on_full_optimize)
    mem_opt_layout.addWidget(opt_full_btn)

    mem_opt_layout.addStretch()
    fl_mem.addWidget(mem_opt_widget, 0, 0)

    mem_tip = QLabel("内存优化：释放 Python 垃圾 + 清理工作集（非破坏性） | 显存优化：释放 CUDA/ONNX 缓存 | 进程列表标注受保护进程 🛡️")
    mem_tip.setStyleSheet("color: gray; font-size: 10px;")
    fl_mem.addWidget(mem_tip, 1, 0)

    # ====== 记忆管理 ======
    outer, frame, fl = _make_section_outer(self, "记忆管理")
    layout.addWidget(outer)

    mem_btn_widget = QWidget()
    mem_btn_layout = QHBoxLayout(mem_btn_widget)
    mem_btn_layout.setContentsMargins(0, 0, 0, 0)
    long_btn = QPushButton("打开长期记忆")
    long_btn.clicked.connect(lambda: self.open_memory_file("长期记忆.txt"))
    mem_btn_layout.addWidget(long_btn)
    short_btn = QPushButton("打开短期记忆")
    short_btn.clicked.connect(lambda: self.open_memory_file("短期记忆.txt"))
    mem_btn_layout.addWidget(short_btn)
    clear_btn = QPushButton("清空短期记忆")
    clear_btn.clicked.connect(self.clear_short_term)
    mem_btn_layout.addWidget(clear_btn)
    mem_btn_layout.addStretch()
    fl.addWidget(mem_btn_widget, 0, 0)

    tip = QLabel("说明：调试模式开启后，AI消息下方会显示工具调用详情。")
    tip.setStyleSheet("color: gray;")
    layout.addWidget(tip)

    outer2, frame2, fl2 = _make_section_outer(self, "AI 配置管理")
    layout.addWidget(outer2)

    config_btn_widget = QWidget()
    config_btn_layout = QHBoxLayout(config_btn_widget)
    config_btn_layout.setContentsMargins(0, 0, 0, 0)
    export_btn = QPushButton("📤 导出 AI 配置")
    export_btn.clicked.connect(self.export_ai_config)
    config_btn_layout.addWidget(export_btn)
    import_btn = QPushButton("📥 导入 AI 配置")
    import_btn.clicked.connect(self.import_ai_config)
    config_btn_layout.addWidget(import_btn)
    reset_btn = QPushButton("🗑️ 重置 AI 配置")
    reset_btn.clicked.connect(self.reset_ai_config)
    config_btn_layout.addWidget(reset_btn)
    theme_btn = QPushButton("🎨 主题设置")
    theme_btn.clicked.connect(self.open_theme_selector)
    config_btn_layout.addWidget(theme_btn)
    config_btn_layout.addStretch()
    fl2.addWidget(config_btn_widget, 0, 0)

    layout.addStretch()


def export_ai_config(self):
    source = CONFIG_FILE
    if not os.path.exists(source):
        QMessageBox.critical(self, "错误", "配置文件不存在")
        return
    file_path, _ = QFileDialog.getSaveFileName(
        self, "导出 AI 配置", "", "JSON 文件 (*.json);;所有文件 (*.*)")
    if not file_path:
        return
    try:
        shutil.copy2(source, file_path)
        QMessageBox.information(self, "成功", f"AI 配置已导出到 {file_path}")
    except Exception as e:
        QMessageBox.critical(self, "错误", f"导出失败: {e}")


def import_ai_config(self):
    file_path, _ = QFileDialog.getOpenFileName(
        self, "导入 AI 配置", "", "JSON 文件 (*.json);;所有文件 (*.*)")
    if not file_path:
        return
    reply = QMessageBox.question(self, "确认",
                                 "导入将覆盖当前所有 AI 配置（API Key、模型、QQ 设置等），程序将自动重启。是否继续？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply != QMessageBox.StandardButton.Yes:
        return
    try:
        shutil.copy2(file_path, CONFIG_FILE)
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            json.load(f)
        QMessageBox.information(self, "成功", "AI 配置已导入，程序将自动重启。")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except json.JSONDecodeError as e:
        QMessageBox.critical(self, "错误", f"配置文件格式错误: {e}")
    except Exception as e:
        QMessageBox.critical(self, "错误", f"导入失败: {e}")


def reset_ai_config(self):
    reply = QMessageBox.question(self, "确认重置",
                                 "此操作将删除所有 AI 配置（API Key、模型、QQ 设置等），程序将重启并进入配置向导。是否继续？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply != QMessageBox.StandardButton.Yes:
        return
    try:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        QMessageBox.critical(self, "错误", f"重置失败: {e}")


# ==================== 内存优化回调 ====================
def _on_list_processes(self):
    from memory_optimizer import list_processes
    result = list_processes(30)
    dlg = QDialog(self)
    dlg.setWindowTitle("进程列表（按内存排序）")
    dlg.resize(650, 500)
    layout = QVBoxLayout(dlg)
    text = QTextEdit()
    text.setReadOnly(True)
    text.setFont(QFont("Consolas", 9))
    text.setPlainText(result)
    layout.addWidget(text)
    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dlg.accept)
    layout.addWidget(close_btn)
    dlg.exec()


def _on_optimize_memory(self):
    self.display_system_message("🧹 正在执行内存优化...")
    def _run():
        from memory_optimizer import optimize_memory
        result = optimize_memory()
        def _show():
            self.display_system_message(f"内存优化完成：\n{result}")
        QTimer.singleShot(0, _show)
    import threading
    threading.Thread(target=_run, daemon=True).start()


def _on_optimize_vram(self):
    self.display_system_message("🎮 正在执行显存优化...")
    def _run():
        from memory_optimizer import optimize_vram
        result = optimize_vram()
        def _show():
            self.display_system_message(f"显存优化完成：\n{result}")
        QTimer.singleShot(0, _show)
    import threading
    threading.Thread(target=_run, daemon=True).start()


def _on_full_optimize(self):
    self.display_system_message("⚡ 正在执行完整优化...")
    def _run():
        from memory_optimizer import full_optimize
        result = full_optimize()
        def _show():
            self.display_system_message(f"完整优化完成：\n{result}")
        QTimer.singleShot(0, _show)
    import threading
    threading.Thread(target=_run, daemon=True).start()


# ==================== 本地模型页 ====================
def create_local_model_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "本地模型")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(5, 5, 5, 5)

    current_layout = QHBoxLayout()
    current_layout.addWidget(QLabel("当前使用模型:"))
    self.current_model_label = QLabel(getattr(config, 'local_model', '未设置'))
    self.current_model_label.setStyleSheet("color: green; font-weight: bold;")
    current_layout.addWidget(self.current_model_label)
    current_layout.addStretch()
    layout.addLayout(current_layout)

    self.model_table = QTableWidget()
    self.model_table.setColumnCount(3)
    self.model_table.setHorizontalHeaderLabels(['模型名称', '文件路径', '状态'])
    self.model_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.model_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.model_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    layout.addWidget(self.model_table)

    btn_layout = QHBoxLayout()
    add_btn = QPushButton("添加模型")
    add_btn.clicked.connect(self.add_model_dialog)
    btn_layout.addWidget(add_btn)
    del_btn = QPushButton("删除模型")
    del_btn.clicked.connect(self.delete_model)
    btn_layout.addWidget(del_btn)
    deploy_btn = QPushButton("一键部署推荐模型")
    deploy_btn.clicked.connect(self.deploy_recommended_model)
    btn_layout.addWidget(deploy_btn)
    refresh_btn = QPushButton("刷新列表")
    refresh_btn.clicked.connect(self.refresh_model_list)
    btn_layout.addWidget(refresh_btn)
    select_btn = QPushButton("✅ 使用此模型")
    select_btn.clicked.connect(self.select_model_as_current)
    btn_layout.addWidget(select_btn)
    btn_layout.addStretch()
    layout.addLayout(btn_layout)

    self.model_progress = QProgressBar()
    self.model_progress.setVisible(False)
    layout.addWidget(self.model_progress)

    layout.addStretch()

    self.refresh_model_list()
    QTimer.singleShot(1000, self.refresh_model_list)


def refresh_model_list(self):
    self.model_table.setRowCount(0)
    current_model = getattr(config, 'local_model', '')

    all_models = self.local_model_manager.get_all_models()
    self.model_table.setRowCount(len(all_models))
    row = 0
    for name, info in all_models.items():
        if not info.get('path', '').startswith('ollama://'):
            status = "✅ 当前使用" if name == current_model else "已就绪"
            name_item = QTableWidgetItem(name)
            if name == current_model:
                name_item.setBackground(QColor("#2E7D32"))
                name_item.setForeground(QColor("white"))
            self.model_table.setItem(row, 0, name_item)
            self.model_table.setItem(row, 1, QTableWidgetItem(info['path']))
            self.model_table.setItem(row, 2, QTableWidgetItem(status))
            row += 1

    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, encoding='utf-8', timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    size = parts[2]
                    existing = False
                    for r in range(self.model_table.rowCount()):
                        if self.model_table.item(r, 0).text() == name:
                            existing = True
                            break
                    if not existing:
                        current_row = self.model_table.rowCount()
                        self.model_table.insertRow(current_row)
                        status = f"已安装 ({size})"
                        name_item = QTableWidgetItem(name)
                        if name == current_model:
                            status = f"✅ 已安装 ({size})"
                            name_item.setBackground(QColor("#2E7D32"))
                            name_item.setForeground(QColor("white"))
                        self.model_table.setItem(current_row, 0, name_item)
                        self.model_table.setItem(current_row, 1, QTableWidgetItem(f"ollama://{name}"))
                        self.model_table.setItem(current_row, 2, QTableWidgetItem(status))
    except Exception as e:
        print(f"获取Ollama模型列表失败: {e}")

    self.current_model_label.setText(current_model if current_model else '未设置')


def add_model_dialog(self):
    dlg = QDialog(self)
    dlg.setWindowTitle("添加本地模型")
    dlg.resize(400, 200)
    dlg.setModal(True)

    layout = QGridLayout(dlg)
    layout.addWidget(QLabel("模型名称:"), 0, 0)
    name_entry = QLineEdit()
    layout.addWidget(name_entry, 0, 1)

    layout.addWidget(QLabel("文件路径:"), 1, 0)
    path_entry = QLineEdit()
    layout.addWidget(path_entry, 1, 1)

    def browse():
        fname, _ = QFileDialog.getOpenFileName(dlg, "选择模型文件", "", "GGUF文件 (*.gguf);;所有文件 (*.*)")
        if fname:
            path_entry.setText(fname)

    browse_btn = QPushButton("浏览")
    browse_btn.clicked.connect(browse)
    layout.addWidget(browse_btn, 1, 2)

    def add():
        name = name_entry.text().strip()
        path = path_entry.text().strip()
        if name and path:
            self.local_model_manager.add_model(name, path, {})
            self.refresh_model_list()
            dlg.accept()

    add_btn = QPushButton("添加")
    add_btn.clicked.connect(add)
    layout.addWidget(add_btn, 2, 0, 1, 3)

    dlg.exec()


def delete_model(self):
    selected = self.model_table.selectedItems()
    if not selected:
        QMessageBox.warning(self, "提示", "请先选择一个模型")
        return
    row = selected[0].row()
    name = self.model_table.item(row, 0).text()
    reply = QMessageBox.question(self, "确认", f"确定要删除模型 {name} 吗？",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        self.local_model_manager.remove_model(name)
        self.refresh_model_list()


def deploy_recommended_model(self):
    grade = HardwareDetector.get_grade()
    import os as _os
    recommendations_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "model_recommendations.json")
    if not _os.path.exists(recommendations_path):
        QMessageBox.warning(self, "错误", "模型推荐文件不存在")
        return
    try:
        with open(recommendations_path, 'r', encoding='utf-8') as f:
            recs = json.load(f)
    except Exception as e:
        QMessageBox.warning(self, "错误", f"读取模型推荐失败：{e}")
        return
    models = recs.get(grade, [])
    if not models:
        QMessageBox.information(self, "提示", "您的硬件等级没有推荐的模型")
        return

    dlg = QDialog(self)
    dlg.setWindowTitle("选择模型")
    dlg.resize(400, 300)
    dlg.setModal(True)

    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("请选择要部署的模型:"))

    display_names = [f"{m.get('display_name', m['name'])} ({m.get('provider', '未知')}) - {m.get('description', '')[:20]}"
                     for m in models]
    display_to_name = {display_names[i]: m["name"] for i, m in enumerate(models)}

    combo = QComboBox()
    combo.addItems(display_names)
    layout.addWidget(combo)

    def deploy():
        selected_display = combo.currentText()
        selected_model = display_to_name.get(selected_display, selected_display)
        dlg.accept()
        self.deploy_model(selected_model)

    deploy_btn = QPushButton("部署")
    deploy_btn.clicked.connect(deploy)
    layout.addWidget(deploy_btn)

    dlg.exec()


def deploy_model(self, model_name):
    dlg = QDialog(self)
    dlg.setWindowTitle("部署模型")
    dlg.resize(500, 400)
    dlg.setModal(True)

    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel(f"正在部署 {model_name}..."))

    progress = QProgressBar()
    progress.setRange(0, 0)
    layout.addWidget(progress)

    status_label = QLabel("准备下载...")
    status_label.setStyleSheet("color: gray;")
    layout.addWidget(status_label)

    log_text = QTextEdit()
    log_text.setReadOnly(True)
    layout.addWidget(log_text)

    def add_log(text, is_error=False):
        timestamp = time.strftime("%H:%M:%S")
        color = "red" if is_error else "black"
        log_text.append(f"<span style='color:{color}'>[{timestamp}] {text}</span>")
        status_label.setText(text[:50])
        status_label.setStyleSheet(f"color: {'red' if is_error else 'green'};")

    def callback(success, result):
        progress.setRange(0, 100)
        progress.setValue(100)
        if success:
            add_log("✅ 部署成功！", False)
            status_label.setText("部署成功！")
            status_label.setStyleSheet("color: green;")
            if model_name.endswith(".gguf"):
                self.local_model_manager.add_model(os.path.basename(model_name), result, {})
            else:
                self.local_model_manager.add_model(model_name, f"ollama://{model_name}", {})
            self.refresh_model_list()
        else:
            add_log(f"❌ {result}", True)
            status_label.setText("部署失败")
            status_label.setStyleSheet("color: red;")

    def output_callback(text, is_error):
        QTimer.singleShot(0, lambda: add_log(text, is_error))

    threading.Thread(
        target=lambda: self.local_model_manager.deploy_model(model_name, callback=callback, output_callback=output_callback),
        daemon=True
    ).start()

    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dlg.accept)
    layout.addWidget(close_btn)

    dlg.exec()


def select_model_as_current(self):
    selected = self.model_table.selectedItems()
    if not selected:
        QMessageBox.warning(self, "提示", "请先选择一个模型")
        return

    row = selected[0].row()
    model_name = self.model_table.item(row, 0).text()

    reply = QMessageBox.question(self, "确认",
                                 f"确定要使用模型 [{model_name}] 吗？\n\n这将立即切换当前使用的本地模型。",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        config.local_model = model_name
        try:
            self.agent._init_local_model()
            self.current_model_label.setText(model_name)
            self.current_model_label.setStyleSheet("color: green; font-weight: bold;")
            self._save_all_config()
            QMessageBox.information(self, "成功",
                                    f"已切换到模型: {model_name}\n\n请在「模型选择」页确保「主模型」选择为「本地」才能生效。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换模型失败: {str(e)}")


# ==================== 模型选择页 ====================
def create_model_selector_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "模型选择")

    layout = QGridLayout(tab)
    layout.setContentsMargins(10, 10, 10, 10)

    layout.addWidget(QLabel("主模型（用于对话）"), 0, 0)
    self.main_model_cloud = QRadioButton("云端")
    self.main_model_local = QRadioButton("本地")
    main_type = getattr(config, 'main_model_type', 'cloud')
    if main_type == 'local':
        self.main_model_local.setChecked(True)
    else:
        self.main_model_cloud.setChecked(True)
    layout.addWidget(self.main_model_cloud, 0, 1)
    layout.addWidget(self.main_model_local, 0, 2)

    layout.addWidget(QLabel("副模型（用于多模态）"), 1, 0)
    self.sub_model_cloud = QRadioButton("云端")
    self.sub_model_local = QRadioButton("本地")
    sub_type = getattr(config, 'sub_model_type', 'cloud')
    if sub_type == 'local':
        self.sub_model_local.setChecked(True)
    else:
        self.sub_model_cloud.setChecked(True)
    layout.addWidget(self.sub_model_cloud, 1, 1)
    layout.addWidget(self.sub_model_local, 1, 2)

    save_btn = QPushButton("保存模型选择")
    save_btn.clicked.connect(self.save_model_selection)
    layout.addWidget(save_btn, 2, 0, 1, 3)

    layout.setRowStretch(3, 1)


def save_model_selection(self):
    config.main_model_type = 'local' if self.main_model_local.isChecked() else 'cloud'
    config.sub_model_type = 'local' if self.sub_model_local.isChecked() else 'cloud'
    self._save_all_config()
    QMessageBox.information(self, "成功", "模型选择已保存，重启后生效")


# ==================== 多Agent模式页 ====================
def create_multi_agent_tab(self):
    tab = QWidget()
    self.notebook.addTab(tab, "多Agent模式 (beta)")

    layout = QVBoxLayout(tab)
    layout.setContentsMargins(10, 10, 10, 10)

    title = QLabel("多Agent协作模式")
    title.setStyleSheet("font-size: 12pt; font-weight: bold;")
    layout.addWidget(title)

    desc = QLabel(
        "启用后，AI将以三个独立人格合作完成任务：\n"
        "① 规划员(Planner) - 分析需求，制定任务列表\n"
        "② 执行员(Worker) - 逐步执行任务，可反馈重新规划\n"
        "③ 审查员(Reviewer) - 检查成果，确保任务完成\n\n"
        "任务执行过程中，可点击顶部按钮查看实时进度。"
    )
    desc.setWordWrap(True)
    layout.addWidget(desc)

    self.multi_agent_enable_check = QCheckBox("启用多Agent模式（重启后生效）")
    self.multi_agent_enable_check.setChecked(getattr(config, 'multi_agent_enabled', False))
    layout.addWidget(self.multi_agent_enable_check)

    personality_options = [p['name'] for p in self.personalities] if hasattr(self, 'personalities') else ["TGAI", "艾依", "塔戈"]
    if len(personality_options) < 3:
        personality_options.extend(["TGAI", "艾依", "塔戈"])

    planner_layout = QHBoxLayout()
    planner_layout.addWidget(QLabel("规划员 (Planner) 人格:"))
    self.multi_agent_planner_combo = QComboBox()
    self.multi_agent_planner_combo.addItems(personality_options)
    planner_val = getattr(config, 'multi_agent_planner_persona', personality_options[0])
    self.multi_agent_planner_combo.setCurrentText(planner_val)
    planner_layout.addWidget(self.multi_agent_planner_combo)
    layout.addLayout(planner_layout)

    worker_layout = QHBoxLayout()
    worker_layout.addWidget(QLabel("执行员 (Worker) 人格:"))
    self.multi_agent_worker_combo = QComboBox()
    self.multi_agent_worker_combo.addItems(personality_options)
    worker_val = getattr(config, 'multi_agent_worker_persona', personality_options[1])
    self.multi_agent_worker_combo.setCurrentText(worker_val)
    worker_layout.addWidget(self.multi_agent_worker_combo)
    layout.addLayout(worker_layout)

    reviewer_layout = QHBoxLayout()
    reviewer_layout.addWidget(QLabel("审查员 (Reviewer) 人格:"))
    self.multi_agent_reviewer_combo = QComboBox()
    self.multi_agent_reviewer_combo.addItems(personality_options)
    reviewer_val = getattr(config, 'multi_agent_reviewer_persona', personality_options[2])
    self.multi_agent_reviewer_combo.setCurrentText(reviewer_val)
    reviewer_layout.addWidget(self.multi_agent_reviewer_combo)
    layout.addLayout(reviewer_layout)

    warning_label = QLabel("※ 三个Agent人格不能相同，否则记忆可能错乱。")
    warning_label.setStyleSheet("color: red;")
    layout.addWidget(warning_label)

    save_btn = QPushButton("💾 保存设置")
    save_btn.clicked.connect(self.save_multi_agent_settings)
    layout.addWidget(save_btn)

    layout.addStretch()


def save_multi_agent_settings(self):
    enabled = self.multi_agent_enable_check.isChecked()
    planner = self.multi_agent_planner_combo.currentText()
    worker = self.multi_agent_worker_combo.currentText()
    reviewer = self.multi_agent_reviewer_combo.currentText()

    if enabled and len({planner, worker, reviewer}) < 3:
        QMessageBox.critical(self, "错误", "三个Agent的人格必须各不相同，以免记忆错乱")
        return

    config.multi_agent_enabled = enabled
    config.multi_agent_planner_persona = planner
    config.multi_agent_worker_persona = worker
    config.multi_agent_reviewer_persona = reviewer

    self.multi_agent_enabled = enabled

    self._save_all_config()

    if enabled:
        try:
            self.multi_agent_orchestrator.configure(True, planner, worker, reviewer)
            self.toggle_multi_agent_btn_visibility(True)
            QMessageBox.information(self, "成功", "多Agent模式已启用")
        except Exception as e:
            QMessageBox.critical(self, "配置错误", str(e))
    else:
        self.multi_agent_orchestrator.configure(False, "", "", "")
        self.toggle_multi_agent_btn_visibility(False)
        QMessageBox.information(self, "成功", "多Agent模式已禁用")


def create_ai_hardware_tab(self):
    """创建AI硬件设置选项卡"""
    from ai_hardware.gui import AIHardwareTab
    tab = AIHardwareTab(self)
    self.notebook.addTab(tab, "AI硬件")


# ==================== 关于对话框 ====================
def show_about_dialog(self):
    dlg = QDialog(self)
    dlg.setWindowTitle("关于 TGAI")
    dlg.setFixedSize(400, 500)
    dlg.setModal(True)

    layout = QVBoxLayout(dlg)

    title_label = QLabel("TG HELPER")
    title_label.setStyleSheet("font-size: 28pt; font-weight: bold;")
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)

    icon_path = os.path.join("icon", "TGAI.png")
    if os.path.exists(icon_path):
        try:
            pixmap = QPixmap(icon_path)
            pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label = QLabel()
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        except:
            pass

    version_label = QLabel(f"版本号：{banben}")
    version_label.setStyleSheet("font-size: 10pt;")
    version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(version_label)

    jokes = [
        "向前走，然后就能向前了。",
        "我们在一起。",
        "把大象放进冰箱需要几步？",
        "今天也要努力做一个不努力的自己。",
        "代码是写给人看的，顺便让机器跑一跑。",
        "生活就像一盒巧克力，你永远不知道下一块会不会发霉。",
        "不要问我为什么，因为我是AI。",
        "已经到底了，再往下就是地心了。",
        "这行字没有任何意义，但你却认真看了。",
        "系统提示：请关闭此窗口，然后继续工作。",
        "人生苦短，我用Python。",
        "如果没有BUG，那一定是代码写得不够多。",
        "真正的快乐，是写一段没人看得懂的代码。",
        "你点的每个赞，我都当成喜欢。",
        "今天你摸鱼了吗？",
        "先定一个小目标，比如先写一个操作系统。",
        "听君一席话，如听一席话。",
        "这个功能会在下一个版本添加。",
        "睡吧，梦里什么都有。",
        "我的代码不可能有BUG，只是特性而已。",
        "世界上有两种人：懂二进制的人和不懂的人。",
        "Bug是写出来的，不是改出来的。",
        "代码能跑就别动。",
        "又是充满希望的一天。",
        "你的电脑正在思考人生。",
        "请给程序员多一点关爱。",
        "再复杂的系统，也是从Hello World开始的。",
        "今天不想写注释，明天就忘了为啥这么写。",
        "有时候，删除代码比写代码更快乐。",
        "一个真正的程序员，敢于直面没有注释的代码。",
        "别着急，慢慢来，反正也快不了。",
        "没有什么是重启解决不了的，如果有，就重装。",
        "听说明天会更好，但今天还没过完。",
        "人生就是不断调试的过程。",
        "你的电脑已经准备好了，但你的手指还没准备好。",
        "每天起床第一句，先给自己打个气。",
        "代码写得慢，至少不添乱。",
        "有些事，做了才知道；有些BUG，跑了才知道。",
        "世界上没有真正的感同身受，除非你也被需求改过。",
        "累了可以休息，但不能放弃。",
        "不要和代码较劲，它会让你崩溃的。",
        "我写代码是为了帮助别人，结果帮助最多的却是自己。",
        "永远相信美好的事情即将发生，比如写完了。",
        "再小的代码，也要用心写。",
        "今天不想干活，明天再说吧。",
        "如果你觉得累，说明你在走上坡路。",
        "程序员三大幻觉：我能行、没BUG、明天就做完。",
        "我不是在修BUG，我是在和过去的自己对话。",
        "认真你就输了，但认真写代码总会赢。",
        "未来的你会感谢现在努力写注释的你。",
        "有时候，退一步海阔天空，进一步万丈深渊。",
        "最好的代码，是你几乎忘了它存在。",
        "保持简单，保持愚蠢。",
        "写代码前多想想，写完后少改改。",
        "你可能不相信，但你的电脑也有情绪。",
        "我不是慢，我是在深思熟虑。",
        "有些BUG，只有睡一觉才能解决。",
        "今天不想改代码，明天就会想改更多。",
        "代码的每一行，都是时间的脚印。",
        "你不是在加班，你是在创造未来。",
        "不要害怕犯错，害怕的是不改错。",
        "等哪天不写代码了，我就去种地。",
        "听说喝咖啡能加速编译，我信了。",
        "键盘敲得响，不一定代码写得好。",
        "你的坚持，终将美好。",
        "今天不想说话，只想写代码。",
        "写代码是孤独的，但你不是一个人。",
        "所有伟大的项目，都始于一行注释。",
        "我写代码，是为了让世界更简单。",
        "F*ck!"
    ]
    random_joke = random.choice(jokes)
    joke_label = QLabel(f"\"{random_joke}\"")
    joke_label.setStyleSheet("font-size: 9pt; font-style: italic; color: gray;")
    joke_label.setWordWrap(True)
    joke_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(joke_label)

    donate_btn = QPushButton("投喂作者")
    donate_btn.clicked.connect(self._show_donation_qr)
    layout.addWidget(donate_btn)

    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dlg.accept)
    layout.addWidget(close_btn)

    dlg.exec()


def _show_donation_qr(self):
    qr_path = os.path.join("icon", "wechat_pay.png")
    if not os.path.exists(qr_path):
        QMessageBox.critical(self, "错误", "未找到收款码图片，请将 wechat_pay.png 放在 icon 文件夹下。")
        return
    dlg = QDialog(self)
    dlg.setWindowTitle("投喂作者")
    dlg.setModal(True)

    layout = QVBoxLayout(dlg)
    try:
        pixmap = QPixmap(qr_path)
        pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)
        layout.addWidget(QLabel("感谢您的支持！"))
    except Exception as e:
        QMessageBox.critical(self, "错误", f"无法加载图片：{e}")
        dlg.reject()
        return

    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dlg.accept)
    layout.addWidget(close_btn)

    dlg.exec()


def open_theme_selector(self):
    dlg = QDialog(self)
    dlg.setWindowTitle("主题设置")
    dlg.resize(400, 250)
    dlg.setModal(True)

    layout = QVBoxLayout(dlg)

    title = QLabel("选择主题")
    title.setStyleSheet("font-size: 12pt; font-weight: bold;")
    layout.addWidget(title)

    available_themes = [
        "flatly", "litera", "cosmo", "minty", "lumen", "sandstone",
        "yeti", "pulse", "united", "journal", "simplex", "cerulean",
        "superhero", "darkly", "cyborg", "vapor", "solar"
    ]
    current_theme = getattr(config, 'gui_theme', 'flatly')

    combo = QComboBox()
    combo.addItems(available_themes)
    combo.setCurrentText(current_theme)
    layout.addWidget(combo)

    tip = QLabel('选择后点击"应用"即可切换主题')
    tip.setStyleSheet("color: gray;")
    layout.addWidget(tip)

    btn_layout = QHBoxLayout()
    apply_btn = QPushButton("应用")
    apply_btn.clicked.connect(lambda: apply_theme())
    btn_layout.addWidget(apply_btn)
    cancel_btn = QPushButton("取消")
    cancel_btn.clicked.connect(dlg.reject)
    btn_layout.addWidget(cancel_btn)
    layout.addLayout(btn_layout)

    def apply_theme():
        selected = combo.currentText()
        if selected:
            self.change_theme(selected)
            QMessageBox.information(dlg, "主题已切换", f"主题已切换为 {selected}")
        dlg.accept()

    layout.addStretch()
    dlg.exec()


def open_ai_translator(self):
    from openai import OpenAI

    dlg = QDialog(self)
    dlg.setWindowTitle("🌐 AI 插件翻译器")
    dlg.resize(750, 650)
    dlg.setModal(True)

    layout = QVBoxLayout(dlg)

    step_layout = QHBoxLayout()
    step_labels = []
    for i, text in enumerate(["选择插件", "AI 分析", "预览编辑", "安装"], 1):
        label = QLabel(f"{i}. {text}")
        step_labels.append(label)
        step_layout.addWidget(label)
    layout.addLayout(step_layout)

    stack = QWidget()
    stack_layout = QVBoxLayout(stack)
    stack_layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(stack)

    selected_type = "xiaoli"
    selected_path = ""
    generated_plugin_json = ""
    generated_main_py = ""
    plugin_summary = ""
    collected_files = []
    current_step = 1

    def clear_stack():
        while stack_layout.count():
            item = stack_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def update_step_display():
        for i, lbl in enumerate(step_labels, 1):
            if i == current_step:
                lbl.setStyleSheet("font-weight: bold; color: #2c3e50;")
            elif i < current_step:
                lbl.setStyleSheet("color: green;")
            else:
                lbl.setStyleSheet("color: gray;")

    def build_step1():
        nonlocal selected_type
        clear_stack()
        s1 = QWidget()
        s1_layout = QVBoxLayout(s1)
        s1_layout.setContentsMargins(0, 0, 0, 0)

        s1_layout.addWidget(QLabel("选择源插件类型"))
        type_frame = QWidget()
        type_fl = QVBoxLayout(type_frame)
        type_fl.setContentsMargins(0, 0, 0, 0)
        xiaoli_radio = QRadioButton("🦊 小狸 CLI 插件 (.py 文件)")
        xiaoli_radio.setChecked(True)
        openclaw_radio = QRadioButton("🔌 OpenClaw 插件 (文件夹)")
        custom_radio = QRadioButton("📁 自定义 (任意 Python/JavaScript 文件或文件夹)")
        type_fl.addWidget(xiaoli_radio)
        type_fl.addWidget(openclaw_radio)
        type_fl.addWidget(custom_radio)

        def on_type_change():
            nonlocal selected_type
            if xiaoli_radio.isChecked():
                selected_type = "xiaoli"
            elif openclaw_radio.isChecked():
                selected_type = "openclaw"
            else:
                selected_type = "custom"

        xiaoli_radio.toggled.connect(on_type_change)
        s1_layout.addWidget(type_frame)

        path_frame = QWidget()
        path_fl = QHBoxLayout(path_frame)
        path_fl.setContentsMargins(0, 0, 0, 0)
        path_entry = QLineEdit()
        path_entry.setReadOnly(True)
        path_fl.addWidget(path_entry)

        def browse_path():
            nonlocal selected_path
            if selected_type == "xiaoli":
                path, _ = QFileDialog.getOpenFileName(dlg, "选择小狸插件文件", "", "Python 文件 (*.py);;所有文件 (*.*)")
            elif selected_type == "openclaw":
                path = QFileDialog.getExistingDirectory(dlg, "选择 OpenClaw 插件文件夹")
            else:
                reply = QMessageBox.question(dlg, "选择类型", "选择'是'选择文件夹，选择'否'选择文件")
                if reply == QMessageBox.StandardButton.Yes:
                    path = QFileDialog.getExistingDirectory(dlg, "选择文件夹")
                else:
                    path, _ = QFileDialog.getOpenFileName(dlg, "选择文件")
            if path:
                selected_path = path
                path_entry.setText(path)
                analyze_selected_plugin()

        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(browse_path)
        path_fl.addWidget(browse_btn)
        s1_layout.addWidget(path_frame)

        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        summary_frame.setFrameShadow(QFrame.Shadow.Plain)
        summary_fl = QVBoxLayout(summary_frame)
        summary_fl.addWidget(QLabel("📋 插件摘要"))
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        summary_fl.addWidget(summary_text)
        s1_layout.addWidget(summary_frame)

        def analyze_selected_plugin():
            nonlocal collected_files
            collected_files = []
            path = selected_path
            if not path or not os.path.exists(path):
                return
            summary_text.clear()
            try:
                if selected_type == "xiaoli":
                    with open(path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    name_match = re.search(r'def get_tool_info.*?return\s*{.*?"name":\s*"([^"]+)"', code, re.DOTALL)
                    desc_match = re.search(r'"description":\s*"([^"]+)"', code)
                    plugin_name = name_match.group(1) if name_match else os.path.basename(path)
                    plugin_desc = desc_match.group(1) if desc_match else "无描述"
                    summary_text.append(f"插件名称: {plugin_name}")
                    summary_text.append(f"描述: {plugin_desc}")
                    summary_text.append(f"类型: 小狸 CLI 插件")
                    summary_text.append(f"文件大小: {len(code)} 字符")
                    collected_files = [("主文件", os.path.basename(path), len(code))]
                elif selected_type == "openclaw":
                    manifest_path = os.path.join(path, "openclaw.plugin.json")
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        summary_text.append(f"插件 ID: {manifest.get('id', '未知')}")
                        summary_text.append(f"名称: {manifest.get('name', '未知')}")
                        summary_text.append(f"版本: {manifest.get('version', '未知')}")
                        summary_text.append(f"描述: {manifest.get('description', '无')}")
                        tools = manifest.get('tools', [])
                        summary_text.append(f"工具数量: {len(tools)}")
                        collected_files.append(("清单", "openclaw.plugin.json", os.path.getsize(manifest_path)))
                    else:
                        summary_text.append("未找到 openclaw.plugin.json")
                    scanned_extensions = {'.ts', '.js', '.json', '.md', '.txt', '.yml', '.yaml'}
                    file_list = []
                    for root, dirs, files in os.walk(path):
                        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
                        for file in files:
                            ext = os.path.splitext(file)[1].lower()
                            if ext in scanned_extensions or file in ('README', 'README.md', 'LICENSE'):
                                full_path = os.path.join(root, file)
                                size = os.path.getsize(full_path)
                                rel_path = os.path.relpath(full_path, path)
                                file_list.append((rel_path, size))
                                collected_files.append((rel_path, full_path, size))
                    summary_text.append(f"\n📁 扫描到 {len(file_list)} 个相关文件:")
                    for rel_path, size in file_list[:20]:
                        summary_text.append(f"  - {rel_path} ({size} 字节)")
                    if len(file_list) > 20:
                        summary_text.append(f"  ... 还有 {len(file_list)-20} 个文件")
                else:
                    summary_text.append(f"路径: {path}")
                    if os.path.isfile(path):
                        size = os.path.getsize(path)
                        summary_text.append(f"文件大小: {size} 字节")
                        collected_files = [("主文件", os.path.basename(path), size)]
                    else:
                        scanned_extensions = {'.py', '.js', '.ts', '.json', '.md', '.txt', '.yml', '.yaml'}
                        file_count = 0
                        for root, dirs, files in os.walk(path):
                            dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
                            for file in files:
                                ext = os.path.splitext(file)[1].lower()
                                if ext in scanned_extensions or file in ('README', 'README.md'):
                                    file_count += 1
                                    full_path = os.path.join(root, file)
                                    size = os.path.getsize(full_path)
                                    rel_path = os.path.relpath(full_path, path)
                                    collected_files.append((rel_path, full_path, size))
                        summary_text.append(f"文件夹，包含 {file_count} 个相关文件")
            except Exception as e:
                summary_text.append(f"分析失败: {e}")

        stack_layout.addWidget(s1)
        return s1

    def build_step2():
        nonlocal generated_plugin_json, generated_main_py, plugin_summary
        clear_stack()
        s2 = QWidget()
        s2_layout = QVBoxLayout(s2)
        s2_layout.setContentsMargins(0, 0, 0, 0)

        progress_label = QLabel("正在收集源码并调用 AI...")
        s2_layout.addWidget(progress_label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)
        s2_layout.addWidget(progress_bar)

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        s2_layout.addWidget(log_text)

        def run_ai_translation_async():
            log_text.append("📂 正在收集源文件...")

            path = selected_path
            source_code = ""
            file_manifest = []

            if selected_type == "xiaoli":
                with open(path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                file_manifest.append(f"主文件: {os.path.basename(path)}")
                log_text.append(f"✅ 已读取小狸插件 ({len(source_code)} 字符)")
            elif selected_type == "openclaw" or (selected_type == "custom" and os.path.isdir(path)):
                total_chars = 0
                file_count = 0
                for rel_path, full_path, size in collected_files:
                    if size > 50000:
                        log_text.append(f"⚠️ 跳过过大文件: {rel_path}")
                        continue
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                        if len(content) > 20000:
                            content = content[:20000] + "\n... (已截断)"
                        source_code += f"\n\n========== {rel_path} ==========\n{content}"
                        total_chars += len(content)
                        file_count += 1
                        file_manifest.append(f"{rel_path} ({size} 字节)")
                        log_text.append(f"📄 已读取: {rel_path}")
                    except Exception as e:
                        log_text.append(f"❌ 读取失败 {rel_path}: {e}")
                log_text.append(f"✅ 共读取 {file_count} 个文件，总计 {total_chars} 字符")
                if total_chars > 120000:
                    source_code = source_code[:120000] + "\n\n... (总源码已截断)"
                    log_text.append(f"⚠️ 总源码过长，已截断")
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                file_manifest.append(f"主文件: {os.path.basename(path)}")
                log_text.append(f"✅ 已读取文件 ({len(source_code)} 字符)")

            log_text.append("\n🤖 正在调用 AI 生成 TG HELPER PluginV2 代码...")

            prompts_file = os.path.join("plugin_v2", "ai_generator", "translation_prompt.json")
            system_prompt = "你是一个专业的插件移植专家。"
            template = """请将以下源插件转换为 TG HELPER PluginV2 插件..."""
            api_reference_text = ""

            if os.path.exists(prompts_file):
                try:
                    with open(prompts_file, 'r', encoding='utf-8') as f:
                        prompts = json.load(f)
                    system_prompt = prompts.get("system_prompt", system_prompt)
                    template = prompts.get("template", template)
                    api_ref = prompts.get("api_reference", {})
                    lines = []
                    for category, apis in api_ref.items():
                        lines.append(f"\n## {category.upper()}")
                        if isinstance(apis, dict):
                            for name, desc in apis.items():
                                lines.append(f"- {desc}")
                        else:
                            lines.append(f"- {apis}")
                    api_reference_text = "\n".join(lines)
                except:
                    pass

            file_manifest_str = "\n".join(file_manifest) if file_manifest else "（无）"
            prompt = template.format(
                plugin_type=selected_type,
                plugin_path=path,
                file_manifest=file_manifest_str,
                source_code=source_code,
                api_reference=api_reference_text
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            client = OpenAI(
                api_key=config.ai_api_key,
                base_url=config.ai_base_url,
                timeout=999.0
            )
            max_retries = 2
            response = None
            for attempt in range(max_retries):
                try:
                    kwargs = dict(
                        model=config.ai_model,
                        messages=messages,
                        temperature=1,
                        max_tokens=8000)
                    if 'deepseek' in config.ai_model.lower() and getattr(config, 'deepseek_thinking_enabled', False):
                        kwargs['reasoning_effort'] = getattr(config, 'deepseek_reasoning_effort', 'high')
                        kwargs['extra_body'] = {"thinking": {"type": "enabled"}}
                        ctx = getattr(config, 'deepseek_context_window', 0)
                        if ctx:
                            kwargs['max_tokens'] = ctx
                    completion = client.chat.completions.create(**kwargs)
                    response = completion.choices[0].message.content
                    break
                except Exception as e:
                    log_text.append(f"⚠️ 第 {attempt + 1} 次尝试失败: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(3)

            def update_ui():
                nonlocal generated_plugin_json, generated_main_py, plugin_summary
                progress_bar.setRange(0, 100)
                progress_bar.setValue(100)
                log_text.append(f"\n📝 [AI 响应] 长度: {len(response)} 字符")
                if len(response) > 5000:
                    log_text.append(response[:5000] + "\n... (响应过长，已截断显示)")
                else:
                    log_text.append(response + "\n")

                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
                if not json_match:
                    json_match = re.search(r'```json\s*([\s\S]*?)(?=```|$)', response)
                if json_match:
                    generated_plugin_json = json_match.group(1).strip()
                    log_text.append("✅ 已提取 plugin.json")
                else:
                    log_text.append("⚠️ 未找到 plugin.json 代码块")

                py_match = re.search(r'```python\s*([\s\S]*?)\s*```', response)
                if not py_match:
                    py_match = re.search(r'```python\s*([\s\S]*?)(?=```|$)', response)
                if py_match:
                    code = py_match.group(1).strip()
                    if code.endswith('...'):
                        log_text.append("⚠️ 提取的 main.py 可能不完整（以省略号结尾）")
                    generated_main_py = code
                    log_text.append("✅ 已提取 main.py")
                else:
                    log_text.append("⚠️ 未找到 main.py 代码块，请检查原始响应。")

                if json_match:
                    try:
                        manifest = json.loads(generated_plugin_json)
                        plugin_summary = f"{manifest.get('name')} v{manifest.get('version')} - {manifest.get('description', '')}"
                    except:
                        plugin_summary = "插件摘要解析失败"

                log_text.append("\n🎉 翻译完成！点击「下一步」预览并编辑。")

            QTimer.singleShot(0, update_ui)

        threading.Thread(target=run_ai_translation_async, daemon=True).start()
        stack_layout.addWidget(s2)
        return s2

    def build_step3():
        nonlocal generated_plugin_json, generated_main_py
        clear_stack()
        s3 = QWidget()
        s3_layout = QVBoxLayout(s3)
        s3_layout.setContentsMargins(0, 0, 0, 0)

        summary_label = QLabel(plugin_summary)
        summary_label.setStyleSheet("font-weight: bold;")
        s3_layout.addWidget(summary_label)

        inner_notebook = QTabWidget()
        s3_layout.addWidget(inner_notebook)

        json_tab = QWidget()
        json_layout = QVBoxLayout(json_tab)
        json_layout.setContentsMargins(0, 0, 0, 0)
        json_editor = QTextEdit()
        json_editor.setPlainText(generated_plugin_json)
        json_layout.addWidget(json_editor)
        inner_notebook.addTab(json_tab, "plugin.json")

        py_tab = QWidget()
        py_layout = QVBoxLayout(py_tab)
        py_layout.setContentsMargins(0, 0, 0, 0)
        py_editor = QTextEdit()
        py_editor.setPlainText(generated_main_py)
        py_layout.addWidget(py_editor)
        inner_notebook.addTab(py_tab, "main.py")

        s3_layout.addWidget(QLabel("💡 您可以直接编辑上方代码，修改后将用于安装。"))

        def save_edits():
            nonlocal generated_plugin_json, generated_main_py
            generated_plugin_json = json_editor.toPlainText()
            generated_main_py = py_editor.toPlainText()

        stack_layout.addWidget(s3)
        return s3, save_edits

    def build_step4():
        nonlocal generated_plugin_json, generated_main_py
        clear_stack()
        s4 = QWidget()
        s4_layout = QVBoxLayout(s4)
        s4_layout.setContentsMargins(0, 0, 0, 0)

        s4_layout.addWidget(QLabel("✅ 插件已准备就绪"))
        s4_layout.addWidget(QLabel(plugin_summary))
        install_log = QTextEdit()
        install_log.setReadOnly(True)
        s4_layout.addWidget(install_log)

        def do_install():
            install_log.clear()
            try:
                manifest = json.loads(generated_plugin_json)
                plugin_id = manifest.get('id', 'com.tghelper.translated')
                folder_name = re.sub(r'[^a-zA-Z0-9_-]', '_', plugin_id.split('.')[-1])
                if not folder_name:
                    folder_name = "translated_plugin"

                plugins_dir = "./plugins"
                if hasattr(self, 'plugin_manager_v2') and self.plugin_manager_v2._plugins_dirs:
                    plugins_dir = self.plugin_manager_v2._plugins_dirs[0]
                plugin_folder = os.path.join(plugins_dir, folder_name)
                os.makedirs(plugin_folder, exist_ok=True)

                manifest_path = os.path.join(plugin_folder, "plugin.json")
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    f.write(generated_plugin_json)
                install_log.append(f"✅ 已保存 plugin.json 到 {manifest_path}")

                main_py_code = generated_main_py
                main_py_path = os.path.join(plugin_folder, "main.py")
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write(main_py_code)
                install_log.append(f"✅ 已保存 main.py 到 {main_py_path}")

                install_log.append("🔍 正在检测插件依赖...")

                std_libs = set()
                if hasattr(sys, 'stdlib_module_names'):
                    std_libs = set(sys.stdlib_module_names)
                common_stdlib = {
                    'os', 'sys', 'json', 're', 'time', 'datetime', 'threading', 'subprocess',
                    'tkinter', 'collections', 'typing', 'abc', 'math', 'random', 'hashlib',
                    'base64', 'io', 'pathlib', 'shutil', 'tempfile', 'urllib', 'http', 'socket',
                    'asyncio', 'queue', 'itertools', 'functools', 'logging', 'traceback',
                    'webbrowser', 'uuid', 'copy', 'enum', 'dataclasses'
                }
                std_libs.update(common_stdlib)

                module_to_pip = {
                    'Crypto': 'pycryptodome',
                    'Cryptodome': 'pycryptodomex',
                    'cryptography': 'cryptography',
                    'requests': 'requests',
                    'aiohttp': 'aiohttp',
                    'PIL': 'Pillow',
                    'qrcode': 'qrcode',
                    'yaml': 'pyyaml',
                    'cv2': 'opencv-python',
                    'numpy': 'numpy',
                    'pandas': 'pandas',
                    'websocket': 'websocket-client',
                    'websockets': 'websockets',
                    'paho': 'paho-mqtt',
                    'mqtt': 'paho-mqtt',
                    'playwright': 'playwright',
                    'selenium': 'selenium',
                    'lxml': 'lxml',
                    'bs4': 'beautifulsoup4',
                    'dateutil': 'python-dateutil',
                    'psutil': 'psutil',
                }

                import_lines = re.findall(r'^(?:from\s+(\S+)\s+import|import\s+(\S+))', main_py_code, re.MULTILINE)
                modules = set()
                for from_mod, imp_mod in import_lines:
                    if from_mod:
                        modules.add(from_mod.split('.')[0])
                    if imp_mod:
                        modules.add(imp_mod.split('.')[0])

                third_party = []
                for m in modules:
                    if m in std_libs or m.startswith('plugin_v2') or m == 'config' or m.startswith('tg_helper'):
                        continue
                    third_party.append(m)

                if third_party:
                    install_log.append(f"📦 检测到第三方依赖: {', '.join(third_party)}")
                    python_exe = sys.executable
                    failed_packages = []

                    for mod in third_party:
                        pkg = module_to_pip.get(mod, mod)
                        install_log.append(f"  正在安装 {mod} (包名: {pkg})...")
                        sources = [
                            [python_exe, "-m", "pip", "install", pkg],
                            [python_exe, "-m", "pip", "install", pkg, "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
                            [python_exe, "-m", "pip", "install", pkg, "-i", "https://mirrors.aliyun.com/pypi/simple/"],
                        ]
                        installed = False
                        for cmd in sources:
                            try:
                                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                                if result.returncode == 0:
                                    install_log.append(f"  ✅ {pkg} 安装成功")
                                    installed = True
                                    break
                                else:
                                    err = result.stderr[:100] if result.stderr else "未知错误"
                                    install_log.append(f"  ⚠️ 失败: {err}")
                            except Exception as e:
                                install_log.append(f"  ❌ 异常: {e}")
                        if not installed:
                            failed_packages.append(pkg)
                            install_log.append(f"  ❌ {pkg} 安装失败")

                    if failed_packages:
                        install_log.append(f"\n⚠️ 以下依赖安装失败: {', '.join(failed_packages)}")
                        install_log.append(f"   请手动执行: pip install {' '.join(failed_packages)}")
                else:
                    install_log.append("✅ 未检测到需要安装的第三方依赖")

                install_log.append("\n🔧 验证关键导入...")
                import_fixes = {
                    'from Crypto.Cipher import AES': ('pycryptodome', 'from Cryptodome.Cipher import AES'),
                    'from Cryptodome.Cipher import AES': ('pycryptodomex', 'from Crypto.Cipher import AES'),
                    'import cryptography': ('cryptography', None),
                    'import qrcode': ('qrcode', None),
                    'from PIL import Image': ('Pillow', None),
                }
                for import_stmt, (pkg, alt_stmt) in import_fixes.items():
                    if import_stmt in main_py_code:
                        try:
                            exec(import_stmt)
                            install_log.append(f"  ✅ {import_stmt} 可用")
                        except ImportError:
                            install_log.append(f"  ⚠️ {import_stmt} 不可用，尝试自动修复...")
                            subprocess.run([python_exe, "-m", "pip", "install", "--force-reinstall", pkg],
                                           capture_output=True, timeout=120)
                            try:
                                exec(import_stmt)
                                install_log.append(f"  ✅ 修复成功")
                            except ImportError:
                                if alt_stmt:
                                    try:
                                        exec(alt_stmt)
                                        install_log.append(f"  💡 替代导入可用: {alt_stmt}")
                                        if QMessageBox.question(dlg, "修复导入",
                                                                f"导入语句 '{import_stmt}' 不可用，但 '{alt_stmt}' 可用。\n是否自动替换？") == QMessageBox.StandardButton.Yes:
                                            main_py_code = main_py_code.replace(import_stmt, alt_stmt)
                                            with open(main_py_path, 'w', encoding='utf-8') as f:
                                                f.write(main_py_code)
                                            install_log.append(f"  ✅ 已自动修复")
                                    except ImportError:
                                        install_log.append(f"  ❌ 替代导入也不可用，请手动检查")
                                else:
                                    install_log.append(f"  ❌ 无法自动修复，请手动检查")

                if hasattr(self, 'plugin_manager_v2'):
                    loaded_id = self.plugin_manager_v2.load_plugin(plugin_folder)
                    if loaded_id:
                        install_log.append(f"✅ 插件已加载: {loaded_id}")
                        self.refresh_plugins_display()
                    else:
                        install_log.append("⚠️ 插件保存成功但加载失败，请检查代码")
                else:
                    install_log.append(f"✅ 插件已保存到: {plugin_folder}")

                install_log.append("\n🎉 安装完成！")
            except Exception as e:
                install_log.append(f"❌ 安装失败: {e}")
                import traceback
                traceback.print_exc()

        stack_layout.addWidget(s4)
        return s4, do_install

    btn_layout = QHBoxLayout()
    prev_btn = QPushButton("◀ 上一步")
    prev_btn.setEnabled(False)
    btn_layout.addWidget(prev_btn)
    next_btn = QPushButton("下一步 ▶")
    btn_layout.addWidget(next_btn)
    layout.addLayout(btn_layout)

    step1_widget = None
    step3_widget = None
    step4_widget = None
    save_edits_fn = None
    do_install_fn = None

    def update_ui_for_step():
        nonlocal step1_widget, step3_widget, step4_widget, save_edits_fn, do_install_fn
        clear_stack()
        if current_step == 1:
            step1_widget = build_step1()
            prev_btn.setEnabled(False)
            next_btn.setText("下一步 ▶")
            next_btn.setEnabled(bool(selected_path))
        elif current_step == 2:
            build_step2()
            prev_btn.setEnabled(True)
            next_btn.setText("下一步 ▶")
            next_btn.setEnabled(False)
        elif current_step == 3:
            s3, save_fn = build_step3()
            step3_widget = s3
            save_edits_fn = save_fn
            prev_btn.setEnabled(True)
            next_btn.setText("下一步 ▶")
            next_btn.setEnabled(True)
        elif current_step == 4:
            s4, install_fn = build_step4()
            step4_widget = s4
            do_install_fn = install_fn
            prev_btn.setEnabled(True)
            next_btn.setText("安装插件")
            next_btn.setEnabled(True)
        update_step_display()

    def go_next():
        nonlocal current_step, save_edits_fn
        if current_step == 3 and save_edits_fn:
            save_edits_fn()
        if current_step == 4:
            if do_install_fn:
                do_install_fn()
            QMessageBox.information(dlg, "完成", "插件已成功安装！")
            dlg.accept()
        else:
            current_step += 1
            update_ui_for_step()

    def go_prev():
        nonlocal current_step
        if current_step > 1:
            current_step -= 1
            update_ui_for_step()

    next_btn.clicked.connect(go_next)
    prev_btn.clicked.connect(go_prev)

    update_ui_for_step()
    dlg.exec()
