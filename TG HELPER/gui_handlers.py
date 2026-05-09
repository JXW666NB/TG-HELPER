# -*- coding: utf-8 -*-
"""
GUI 按钮回调与设置页面创建函数
"""
import os
import sys
import json
import re
import threading
import time
import tkinter as tk
import subprocess
from tkinter import ttk, scrolledtext, messagebox, Toplevel, DISABLED, NORMAL, LEFT, RIGHT, BOTH, Y, X, W, EW, VERTICAL, HORIZONTAL, GROOVE, FLAT
from tkinter import N, S, E, W, NW, NE, SW, SE
from tkinter import filedialog
import shutil
import random
from datetime import datetime
from PIL import Image, ImageTk
import ttkbootstrap as tb

from config import config, CONFIG_FILE
from skill_manager import SkillManager
from hardware_detector import HardwareDetector
from tkinter import filedialog, messagebox
import json as json_module

# ==================== 辅助函数 ====================
def _get_first_skills_dir():
    """安全获取技能目录列表的第一个有效目录"""
    dirs = getattr(config, 'skills_dirs', ["./skills"])
    if not dirs:
        dirs = ["./skills"]
    return dirs[0]


def bind_handlers(gui_instance):
    """将以下函数绑定为 gui_instance 的方法"""
    gui_instance.create_api_tab = lambda: create_api_tab(gui_instance)
    gui_instance.create_qq_tab = lambda: create_qq_tab(gui_instance)
    gui_instance.create_security_tab = lambda: create_security_tab(gui_instance)
    gui_instance.create_skill_tab = lambda: create_skill_tab(gui_instance)
    gui_instance.create_tasks_tab = lambda: create_tasks_tab(gui_instance)
    gui_instance.create_personality_tab = lambda: create_personality_tab(gui_instance)
    gui_instance.create_debug_tab = lambda: create_debug_tab(gui_instance)
    gui_instance.create_local_model_tab = lambda: create_local_model_tab(gui_instance)
    gui_instance.create_model_selector_tab = lambda: create_model_selector_tab(gui_instance)

    gui_instance.save_api_settings = lambda: save_api_settings(gui_instance)
    gui_instance.save_qq_settings = lambda: save_qq_settings(gui_instance)
    gui_instance.save_security_settings = lambda: save_security_settings(gui_instance)
    gui_instance.refresh_skill_list = lambda: refresh_skill_list(gui_instance)
    gui_instance.open_skills_folder = lambda: open_skills_folder(gui_instance)
    gui_instance.check_skills_security = lambda: check_skills_security(gui_instance)
    gui_instance.generate_skill_by_ai = lambda: generate_skill_by_ai(gui_instance)
    gui_instance.on_skill_select = lambda event: on_skill_select(gui_instance, event)
    gui_instance.save_current_skill_config = lambda: save_current_skill_config(gui_instance)
    gui_instance.open_skill_config_external = lambda: open_skill_config_external(gui_instance)

    gui_instance.refresh_tasks = lambda: refresh_tasks(gui_instance)
    gui_instance.add_task = lambda: add_task(gui_instance)
    gui_instance.edit_task = lambda: edit_task(gui_instance)
    gui_instance.delete_task = lambda: delete_task(gui_instance)

    gui_instance.refresh_personality_list = lambda: refresh_personality_list(gui_instance)
    gui_instance.on_personality_select = lambda event: on_personality_select(gui_instance, event)
    gui_instance.on_apply_personality = lambda: on_apply_personality(gui_instance)
    gui_instance.apply_personality = lambda name: apply_personality(gui_instance, name)
    gui_instance.open_personality_folder = lambda: open_personality_folder(gui_instance)

    gui_instance.export_ai_config = lambda: export_ai_config(gui_instance)
    gui_instance.import_ai_config = lambda: import_ai_config(gui_instance)
    gui_instance.reset_ai_config = lambda: reset_ai_config(gui_instance)

    gui_instance.refresh_model_list = lambda: refresh_model_list(gui_instance)
    gui_instance.add_model_dialog = lambda: add_model_dialog(gui_instance)
    gui_instance.delete_model = lambda: delete_model(gui_instance)
    gui_instance.deploy_recommended_model = lambda: deploy_recommended_model(gui_instance)
    gui_instance.select_model_as_current = lambda: select_model_as_current(gui_instance)
    gui_instance.deploy_model = lambda name: deploy_model(gui_instance, name)
    gui_instance.save_model_selection = lambda: save_model_selection(gui_instance)

    gui_instance.show_about_dialog = lambda: show_about_dialog(gui_instance)
    gui_instance._show_donation_qr = lambda: _show_donation_qr(gui_instance)
    gui_instance._show_task_menu = lambda event: _show_task_menu(gui_instance, event)
    gui_instance._check_skills_thread = lambda skills_dirs_str: _check_skills_thread(gui_instance, skills_dirs_str)
    gui_instance._generate_skill_thread = lambda prompt, skills_dirs_str: _generate_skill_thread(gui_instance, prompt, skills_dirs_str)
    gui_instance.open_theme_selector = lambda: open_theme_selector(gui_instance)

    # ========== 新版 V2 插件管理绑定 ==========
    gui_instance.create_plugin_tab = lambda: create_plugin_tab(gui_instance)
    gui_instance.refresh_plugins_display = lambda: refresh_plugins_display(gui_instance)
    gui_instance.on_plugin_select = lambda event: on_plugin_select(gui_instance, event)
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
    gui_instance.create_multi_agent_tab = lambda: create_multi_agent_tab(gui_instance)
    gui_instance.save_multi_agent_settings = lambda: save_multi_agent_settings(gui_instance)    
# ==================== API 设置页 ====================
def create_api_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="API 设置")

    main_container = tb.Frame(tab)
    main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

    # 主AI配置
    main_frame_outer = tb.Frame(main_container)
    main_frame_outer.pack(fill=X, pady=5)
    tb.Label(main_frame_outer, text="主 AI 配置", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    main_frame = tb.Frame(main_frame_outer, relief=GROOVE, borderwidth=1)
    main_frame.pack(fill=X, pady=2)
    main_frame.columnconfigure(1, weight=1)

    row = 0
    tb.Label(main_frame, text="API Key:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.api_key_var = tk.StringVar(value=config.ai_api_key)
    tb.Entry(main_frame, textvariable=self.api_key_var, show="*").grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1

    tb.Label(main_frame, text="Base URL:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.base_url_var = tk.StringVar(value=config.ai_base_url)
    tb.Entry(main_frame, textvariable=self.base_url_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1

    tb.Label(main_frame, text="模型名称:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.model_var = tk.StringVar(value=config.ai_model)
    tb.Entry(main_frame, textvariable=self.model_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1

    tb.Label(main_frame, text="Max Tokens:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.max_tokens_var = tk.StringVar(value=str(getattr(config, 'max_tokens', 2000)))
    tb.Entry(main_frame, textvariable=self.max_tokens_var, width=15).grid(row=row, column=1, pady=2, padx=5, sticky=W)
    row += 1

    tb.Label(main_frame, text="Temperature:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.temp_var = tk.StringVar(value=str(getattr(config, 'temperature', 1.0)))
    tb.Entry(main_frame, textvariable=self.temp_var, width=15).grid(row=row, column=1, pady=2, padx=5, sticky=W)

    # 多模态配置
    mm_frame_outer = tb.Frame(main_container)
    mm_frame_outer.pack(fill=X, pady=5)
    tb.Label(mm_frame_outer, text="多模态备用模型", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    mm_frame = tb.Frame(mm_frame_outer, relief=GROOVE, borderwidth=1)
    mm_frame.pack(fill=X, pady=2)
    mm_frame.columnconfigure(1, weight=1)

    self.multimodal_enabled_var = tk.BooleanVar(value=getattr(config, 'multimodal_enabled', False))
    tb.Checkbutton(mm_frame, text="启用备用模型", variable=self.multimodal_enabled_var).grid(row=0, column=0, columnspan=2, sticky=W, pady=5, padx=5)

    row = 1
    tb.Label(mm_frame, text="API Key:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.multimodal_key_var = tk.StringVar(value=getattr(config, 'multimodal_api_key', ''))
    tb.Entry(mm_frame, textvariable=self.multimodal_key_var, show="*").grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1

    tb.Label(mm_frame, text="Base URL:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.multimodal_url_var = tk.StringVar(value=getattr(config, 'multimodal_base_url', ''))
    tb.Entry(mm_frame, textvariable=self.multimodal_url_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1

    tb.Label(mm_frame, text="模型:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    self.multimodal_model_var = tk.StringVar(value=getattr(config, 'multimodal_model', ''))
    tb.Entry(mm_frame, textvariable=self.multimodal_model_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)

    # 邮箱配置
    email_frame_outer = tb.Frame(main_container)
    email_frame_outer.pack(fill=X, pady=5)
    tb.Label(email_frame_outer, text="邮箱配置", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    email_frame = tb.Frame(email_frame_outer, relief=GROOVE, borderwidth=1)
    email_frame.pack(fill=X, pady=2)
    email_frame.columnconfigure(1, weight=1)

    row = 0
    self.smtp_server_var = tk.StringVar(value=getattr(config, 'email_smtp_server', ''))
    self.smtp_port_var = tk.StringVar(value=str(getattr(config, 'email_port', 587)))
    self.email_user_var = tk.StringVar(value=getattr(config, 'email_user', ''))
    self.email_pass_var = tk.StringVar(value=getattr(config, 'email_password', ''))

    tb.Label(email_frame, text="SMTP服务器:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(email_frame, textvariable=self.smtp_server_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1
    tb.Label(email_frame, text="端口:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(email_frame, textvariable=self.smtp_port_var, width=10).grid(row=row, column=1, pady=2, padx=5, sticky=W)
    row += 1
    tb.Label(email_frame, text="账号:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(email_frame, textvariable=self.email_user_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1
    tb.Label(email_frame, text="密码:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(email_frame, textvariable=self.email_pass_var, show="*").grid(row=row, column=1, pady=2, padx=5, sticky=EW)

    # Google搜索配置
    google_frame_outer = tb.Frame(main_container)
    google_frame_outer.pack(fill=X, pady=5)
    tb.Label(google_frame_outer, text="Google 搜索", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    google_frame = tb.Frame(google_frame_outer, relief=GROOVE, borderwidth=1)
    google_frame.pack(fill=X, pady=2)
    google_frame.columnconfigure(1, weight=1)

    self.google_key_var = tk.StringVar(value=getattr(config, 'google_api_key', ''))
    self.google_cse_var = tk.StringVar(value=getattr(config, 'google_cse_id', ''))

    tb.Label(google_frame, text="API Key:", font=("微软雅黑", 9)).grid(row=0, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(google_frame, textvariable=self.google_key_var).grid(row=0, column=1, pady=2, padx=5, sticky=EW)
    tb.Label(google_frame, text="CSE ID:", font=("微软雅黑", 9)).grid(row=1, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(google_frame, textvariable=self.google_cse_var).grid(row=1, column=1, pady=2, padx=5, sticky=EW)

    tb.Button(main_container, text="💾 保存 API 设置", bootstyle="primary", command=self.save_api_settings).pack(pady=15, anchor=W)


def save_api_settings(self):
    config.ai_api_key = self.api_key_var.get()
    config.ai_base_url = self.base_url_var.get()
    config.ai_model = self.model_var.get()
    try:
        config.max_tokens = int(self.max_tokens_var.get())
    except:
        pass
    try:
        config.temperature = float(self.temp_var.get())
    except:
        pass
    config.email_smtp_server = self.smtp_server_var.get() or None
    config.email_port = int(self.smtp_port_var.get()) if self.smtp_port_var.get().isdigit() else 587
    config.email_user = self.email_user_var.get() or None
    config.email_password = self.email_pass_var.get() or None
    config.google_api_key = self.google_key_var.get() or None
    config.google_cse_id = self.google_cse_var.get() or None
    config.multimodal_enabled = self.multimodal_enabled_var.get()
    config.multimodal_api_key = self.multimodal_key_var.get() or None
    config.multimodal_base_url = self.multimodal_url_var.get() or None
    config.multimodal_model = self.multimodal_model_var.get() or None
    self._save_all_config()
    messagebox.showinfo("保存成功", "API 设置已保存")


# ==================== QQ 设置页 ====================
def create_qq_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="QQ 设置")

    main_container = tb.Frame(tab)
    main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

    basic_frame_outer = tb.Frame(main_container)
    basic_frame_outer.pack(fill=X, pady=5)
    tb.Label(basic_frame_outer, text="基础配置", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    basic_frame = tb.Frame(basic_frame_outer, relief=GROOVE, borderwidth=1)
    basic_frame.pack(fill=X, pady=2)
    basic_frame.columnconfigure(1, weight=1)

    self.qq_enabled_var = tk.BooleanVar(value=config.qq_enabled)
    tb.Checkbutton(basic_frame, text="启用 QQ 机器人", variable=self.qq_enabled_var).grid(row=0, column=0, columnspan=2, sticky=W, pady=5, padx=5)

    self.ws_url_var = tk.StringVar(value=config.qq_websocket_url)
    self.bot_uin_var = tk.StringVar(value=config.qq_bot_uin)
    self.whitelist_var = tk.StringVar(value=config.qq_whitelist)
    self.http_url_var = tk.StringVar(value=config.napcat_http_url)
    self.token_var = tk.StringVar(value=config.napcat_access_token)

    row = 1
    tb.Label(basic_frame, text="WebSocket:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(basic_frame, textvariable=self.ws_url_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1
    tb.Label(basic_frame, text="机器人QQ:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(basic_frame, textvariable=self.bot_uin_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1
    tb.Label(basic_frame, text="白名单:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(basic_frame, textvariable=self.whitelist_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1
    tb.Label(basic_frame, text="HTTP地址:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(basic_frame, textvariable=self.http_url_var).grid(row=row, column=1, pady=2, padx=5, sticky=EW)
    row += 1
    tb.Label(basic_frame, text="Token:", font=("微软雅黑", 9)).grid(row=row, column=0, sticky=W, pady=2, padx=5)
    tb.Entry(basic_frame, textvariable=self.token_var, show="*").grid(row=row, column=1, pady=2, padx=5, sticky=EW)

    companion_frame_outer = tb.Frame(main_container)
    companion_frame_outer.pack(fill=X, pady=5)
    tb.Label(companion_frame_outer, text="群聊陪伴模式", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    companion_frame = tb.Frame(companion_frame_outer, relief=GROOVE, borderwidth=1)
    companion_frame.pack(fill=X, pady=2)

    self.group_companion_enabled_var = tk.BooleanVar(value=config.group_companion_enabled)
    self.group_companion_group_id_var = tk.StringVar(value=config.group_companion_group_id)
    self.group_companion_probability_var = tk.StringVar(value=str(config.group_companion_probability))
    self.group_companion_voice_var = tk.BooleanVar(value=config.group_companion_voice)

    tb.Checkbutton(companion_frame, text="启用群聊陪伴（自动回复）", variable=self.group_companion_enabled_var).pack(anchor=W, pady=2, padx=5)

    cf = tb.Frame(companion_frame)
    cf.pack(fill=X, padx=5, pady=2)
    tb.Label(cf, text="目标群号:", font=("微软雅黑", 9)).pack(side=LEFT)
    tb.Entry(cf, textvariable=self.group_companion_group_id_var, width=15).pack(side=LEFT, padx=5)

    tb.Label(cf, text="回复概率(1-100):", font=("微软雅黑", 9)).pack(side=LEFT, padx=(10, 0))
    tb.Entry(cf, textvariable=self.group_companion_probability_var, width=5).pack(side=LEFT, padx=5)

    tb.Checkbutton(companion_frame, text="使用语音回复（需edge-tts）", variable=self.group_companion_voice_var).pack(anchor=W, pady=2, padx=5)

    btn_frame = tb.Frame(main_container)
    btn_frame.pack(pady=15, anchor=W)
    tb.Button(btn_frame, text="💾 保存 QQ 设置", bootstyle="primary", command=self.save_qq_settings).pack(side=LEFT, padx=5)
    tb.Button(btn_frame, text="🚀 启动QQ机器人", bootstyle="success", command=self.start_qq_bot).pack(side=LEFT, padx=5)
    tb.Button(btn_frame, text="⏹️ 停止", bootstyle="danger", command=self.stop_qq_bot).pack(side=LEFT, padx=5)


def save_qq_settings(self):
    config.qq_enabled = self.qq_enabled_var.get()
    config.qq_websocket_url = self.ws_url_var.get()
    config.qq_bot_uin = self.bot_uin_var.get()
    config.qq_whitelist = self.whitelist_var.get()
    config.napcat_http_url = self.http_url_var.get()
    config.napcat_access_token = self.token_var.get()
    config.group_companion_enabled = self.group_companion_enabled_var.get()
    config.group_companion_group_id = self.group_companion_group_id_var.get().strip()
    try:
        config.group_companion_probability = int(self.group_companion_probability_var.get())
    except:
        pass
    config.group_companion_voice = self.group_companion_voice_var.get()
    self._save_all_config()
    messagebox.showinfo("保存成功", "QQ 设置已保存，重启后生效")


# ==================== 安全设置页 ====================
def create_security_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="安全设置")

    main_container = tb.Frame(tab)
    main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

    whitelist_frame_outer = tb.Frame(main_container)
    whitelist_frame_outer.pack(fill=X, pady=5)
    tb.Label(whitelist_frame_outer, text="访问控制", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    whitelist_frame = tb.Frame(whitelist_frame_outer, relief=GROOVE, borderwidth=1)
    whitelist_frame.pack(fill=X, pady=2)

    self.whitelist_enabled_var = tk.BooleanVar(value=config.whitelist_enabled)
    tb.Checkbutton(whitelist_frame, text="启用QQ白名单（仅允许列表中的QQ）", variable=self.whitelist_enabled_var).pack(anchor=W, pady=5, padx=5)

    confirm_frame_outer = tb.Frame(main_container)
    confirm_frame_outer.pack(fill=X, pady=5)
    tb.Label(confirm_frame_outer, text="危险操作确认", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    confirm_frame = tb.Frame(confirm_frame_outer, relief=GROOVE, borderwidth=1)
    confirm_frame.pack(fill=X, pady=2)

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
        var = tk.BooleanVar(value=config.tool_confirmation.get(tool_name, True))
        self.tool_vars[tool_name] = var
        row, col = divmod(i, 2)
        tb.Checkbutton(confirm_frame, text=tool_label, variable=var).grid(row=row, column=col, sticky=W, pady=2, padx=5)

    browser_frame_outer = tb.Frame(main_container)
    browser_frame_outer.pack(fill=X, pady=5)
    tb.Label(browser_frame_outer, text="浏览器安全", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    browser_frame = tb.Frame(browser_frame_outer, relief=GROOVE, borderwidth=1)
    browser_frame.pack(fill=X, pady=2)

    self.browser_safe_var = tk.BooleanVar(value=config.browser_safe_mode)
    tb.Checkbutton(browser_frame, text="启用浏览器自动化安全模式（禁止危险JS）", variable=self.browser_safe_var).pack(anchor=W, pady=5, padx=5)

    tb.Button(main_container, text="💾 保存安全设置", bootstyle="primary", command=self.save_security_settings).pack(pady=15, anchor=W)


def save_security_settings(self):
    config.whitelist_enabled = self.whitelist_enabled_var.get()
    for tool_name, var in self.tool_vars.items():
        config.tool_confirmation[tool_name] = var.get()
    config.browser_safe_mode = self.browser_safe_var.get()
    self._save_all_config()
    messagebox.showinfo("保存成功", "安全设置已保存")


# ==================== 技能管理页 ====================
def create_skill_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="技能管理")

    dir_frame = tb.Frame(tab)
    dir_frame.pack(fill=X, pady=5, padx=5)
    tb.Label(dir_frame, text="技能目录:", font=("微软雅黑", 9)).pack(side=LEFT)
    self.skills_dirs_var = tk.StringVar(value=','.join(config.skills_dirs))
    tb.Entry(dir_frame, textvariable=self.skills_dirs_var).pack(side=LEFT, fill=X, expand=True, padx=5)

    toolbar = tb.Frame(tab)
    toolbar.pack(fill=X, pady=2, padx=5)
    tb.Button(toolbar, text="🔄 刷新", command=self.refresh_skill_list, bootstyle="secondary-outline").pack(side=LEFT, padx=2)
    tb.Button(toolbar, text="📂 打开文件夹", command=self.open_skills_folder, bootstyle="secondary-outline").pack(side=LEFT, padx=2)
    tb.Button(toolbar, text="🔒 安全检查", command=self.check_skills_security, bootstyle="warning-outline").pack(side=LEFT, padx=2)

    tb.Label(toolbar, text="AI生成:").pack(side=LEFT, padx=(10, 2))
    self.skill_prompt_entry = tb.Entry(toolbar, width=20)
    self.skill_prompt_entry.pack(side=LEFT, padx=2, fill=X, expand=True)
    tb.Button(toolbar, text="生成", command=self.generate_skill_by_ai, bootstyle="success-outline").pack(side=LEFT, padx=2)

    paned = tb.Panedwindow(tab, orient=HORIZONTAL)
    paned.pack(fill=BOTH, expand=True, pady=5, padx=5)

    left_frame = tb.Frame(paned)
    paned.add(left_frame, weight=1)
    tb.Label(left_frame, text="已发现技能", font=("微软雅黑", 9, "bold")).pack(anchor=NW)
    self.skill_listbox = tk.Listbox(left_frame)
    self.skill_listbox.pack(fill=BOTH, expand=True)
    self.skill_listbox.bind('<<ListboxSelect>>', self.on_skill_select)

    right_frame = tb.Frame(paned)
    paned.add(right_frame, weight=2)

    tb.Label(right_frame, text="技能配置 (config.json)", font=("微软雅黑", 9, "bold")).pack(anchor=NW)
    self.skill_config_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=10)
    self.skill_config_text.pack(fill=BOTH, expand=True, pady=2)

    self.skill_config_status = tb.Label(right_frame, text="", foreground="gray", font=("微软雅黑", 8))
    self.skill_config_status.pack(pady=2)

    btn_frame = tb.Frame(right_frame)
    btn_frame.pack(fill=X, pady=2)
    self.save_skill_config_btn = tb.Button(btn_frame, text="💾 保存配置", command=self.save_current_skill_config,
                                           state=DISABLED, bootstyle="primary")
    self.save_skill_config_btn.pack(side=LEFT, padx=2)
    self.edit_skill_config_btn = tb.Button(btn_frame, text="📝 外部编辑", command=self.open_skill_config_external,
                                           state=DISABLED, bootstyle="secondary")
    self.edit_skill_config_btn.pack(side=LEFT, padx=2)

    self.refresh_skill_list()


def refresh_skill_list(self):
    self.skill_listbox.delete(0, tk.END)
    skills_dirs = [d.strip() for d in self.skills_dirs_var.get().split(',') if d.strip()]
    if not skills_dirs:
        skills_dirs = getattr(config, 'skills_dirs', ["./skills"])
        if not skills_dirs:
            skills_dirs = ["./skills"]
    sm = SkillManager(skills_dirs)
    self.skill_metadata = sm.get_skill_metadata()
    for skill in self.skill_metadata:
        self.skill_listbox.insert(tk.END, f"{skill['name']}")
    self.skill_config_text.delete(1.0, tk.END)
    self.skill_config_status.config(text="")
    self.save_skill_config_btn.config(state=DISABLED)
    self.edit_skill_config_btn.config(state=DISABLED)
    self.current_skill = None


def on_skill_select(self, event):
    selection = self.skill_listbox.curselection()
    if not selection:
        return
    index = selection[0]
    skill = self.skill_metadata[index]
    self.current_skill = skill
    skills_dir = _get_first_skills_dir()
    skill_path = os.path.join(skills_dir, skill['name'])
    config_path = os.path.join(skill_path, "config.json")
    self.skill_config_text.delete(1.0, tk.END)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.skill_config_text.insert(1.0, content)
            self.skill_config_status.config(text="配置文件已加载", foreground="green")
            self.save_skill_config_btn.config(state=NORMAL)
            self.edit_skill_config_btn.config(state=NORMAL)
        except Exception as e:
            self.skill_config_text.insert(1.0, f"读取失败：{str(e)}")
            self.skill_config_status.config(text="读取失败", foreground="red")
    else:
        self.skill_config_text.insert(1.0, "该技能没有配置文件")
        self.skill_config_status.config(text="无配置文件", foreground="gray")
        self.save_skill_config_btn.config(state=DISABLED)
        self.edit_skill_config_btn.config(state=NORMAL)


def save_current_skill_config(self):
    if not self.current_skill:
        messagebox.showwarning("提示", "未选择任何技能")
        return
    skills_dir = _get_first_skills_dir()
    skill_path = os.path.join(skills_dir, self.current_skill['name'])
    config_path = os.path.join(skill_path, "config.json")
    content = self.skill_config_text.get(1.0, tk.END).strip()
    try:
        json.loads(content)
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.skill_config_status.config(text="保存成功", foreground="green")
    except json.JSONDecodeError as e:
        messagebox.showerror("错误", f"JSON 格式错误：{e}")
    except Exception as e:
        messagebox.showerror("错误", f"保存失败：{str(e)}")


def open_skill_config_external(self):
    if not self.current_skill:
        messagebox.showwarning("提示", "未选择任何技能")
        return
    skills_dir = _get_first_skills_dir()
    skill_path = os.path.join(skills_dir, self.current_skill['name'])
    config_path = os.path.join(skill_path, "config.json")
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write("{\n  \n}")
            messagebox.showinfo("提示", "已创建空配置文件")
        except Exception as e:
            messagebox.showerror("错误", f"无法创建配置文件：{str(e)}")
            return
    try:
        os.startfile(config_path)
    except AttributeError:
        import subprocess
        subprocess.run(['open', config_path] if sys.platform == 'darwin' else ['xdg-open', config_path])


def open_skills_folder(self):
    skills_dir = [d.strip() for d in self.skills_dirs_var.get().split(',') if d.strip()]
    if not skills_dir:
        skills_dir = getattr(config, 'skills_dirs', ["./skills"])
        if not skills_dir:
            skills_dir = ["./skills"]
    abs_skills_dir = os.path.abspath(skills_dir[0])
    if not os.path.exists(abs_skills_dir):
        try:
            os.makedirs(abs_skills_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建文件夹：{abs_skills_dir}\n{e}")
            return
    try:
        os.startfile(abs_skills_dir)
    except Exception as e:
        messagebox.showerror("错误", f"无法打开文件夹：{abs_skills_dir}\n{e}")


def check_skills_security(self):
    skills_dirs = [d.strip() for d in self.skills_dirs_var.get().split(',') if d.strip()]
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
        self.root.after(0, lambda: self._show_skill_check_results(results))
    except Exception as e:
        self.display_assistant_message(f"❌ 安全检查失败: {str(e)}")


def _show_skill_check_results(self, results):
    win = Toplevel(self.root)
    win.title("Skill安全检查结果")
    win.geometry("500x400")
    win.transient(self.root)
    text = scrolledtext.ScrolledText(win, wrap=tk.WORD, width=60, height=20)
    text.pack(padx=10, pady=10, fill=BOTH, expand=True)
    for item in results:
        name = item.get('skill_name', '未知')
        safe = item.get('safe', False)
        reason = item.get('reason', '')
        if safe:
            text.insert(tk.END, f"✅ {name}: 安全\n", 'safe')
        else:
            text.insert(tk.END, f"❌ {name}: 可能存在风险\n", 'risk')
        text.insert(tk.END, f"   原因: {reason}\n\n")
    text.tag_config('safe', foreground='green')
    text.tag_config('risk', foreground='red')
    text.config(state='disabled')
    tb.Button(win, text="关闭", command=win.destroy).pack(pady=5)


def generate_skill_by_ai(self):
    prompt = self.skill_prompt_entry.get().strip()
    if not prompt:
        messagebox.showwarning("提示", "请输入Skill描述")
        return
    skills_dirs = [d.strip() for d in self.skills_dirs_var.get().split(',') if d.strip()]
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
        self.root.after(0, self.refresh_skill_list)
    except Exception as e:
        self.display_assistant_message(f"❌ 生成Skill失败: {str(e)}")


# ==================== 插件管理页 ====================
def create_plugin_tab(self):
    """插件管理页 - V2 版本（无嵌套滚动）"""
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="插件管理")

    toolbar = tb.Frame(tab)
    toolbar.pack(fill=X, pady=5, padx=5)
    tb.Button(toolbar, text="🔄 重载所有", command=self.reload_plugins, bootstyle="secondary-outline").pack(side=LEFT, padx=2)
    tb.Button(toolbar, text="📂 打开文件夹", command=self.open_plugins_folder, bootstyle="secondary-outline").pack(side=LEFT, padx=2)
    tb.Button(toolbar, text="🔒 安全检查", command=self.check_plugins_security, bootstyle="warning-outline").pack(side=LEFT, padx=2)
    tb.Button(toolbar, text="🌐 AI 翻译", command=self.open_ai_translator, bootstyle="info-outline").pack(side=LEFT, padx=2)
    
    tb.Label(toolbar, text="AI生成:").pack(side=LEFT, padx=(10, 2))
    self.plugin_desc_entry = tb.Entry(toolbar, width=20)
    self.plugin_desc_entry.pack(side=LEFT, padx=2, fill=X, expand=True)
    tb.Button(toolbar, text="生成", command=self.generate_plugin, bootstyle="success-outline").pack(side=LEFT, padx=2)

    paned = tb.Panedwindow(tab, orient=HORIZONTAL)
    paned.pack(fill=BOTH, expand=True, pady=5, padx=5)

    left_frame = tb.Frame(paned)
    paned.add(left_frame, weight=1)
    tb.Label(left_frame, text="已加载插件 (V2)", font=("微软雅黑", 9, "bold")).pack(anchor=NW)
    self.plugins_listbox = tk.Listbox(left_frame)
    self.plugins_listbox.pack(fill=BOTH, expand=True)
    self.plugins_listbox.bind('<<ListboxSelect>>', self.on_plugin_select)

    right_frame = tb.Frame(paned)
    paned.add(right_frame, weight=2)
    tb.Label(right_frame, text="插件设置", font=("微软雅黑", 9, "bold")).pack(anchor=NW)

    # 普通容器，依靠外层设置页的滚动条
    self.plugin_settings_container = tb.Frame(right_frame)
    self.plugin_settings_container.pack(fill=BOTH, expand=True, pady=5)

    self.refresh_plugins_display()


def refresh_plugins_display(self):
    """刷新 V2 插件列表"""
    self.plugins_listbox.delete(0, tk.END)
    self.current_plugin_list = []

    if not hasattr(self, 'plugin_manager_v2'):
        return

    plugins_info = self.plugin_manager_v2.get_all_plugins_info()
    for info in plugins_info:
        status = "✅" if info["enabled"] else "❌"
        source_tag = f"[{info['source']}]"
        display_text = f"{status} {source_tag} {info['name']} (v{info['version']})"
        self.plugins_listbox.insert(tk.END, display_text)
        self.current_plugin_list.append(info)

    for widget in self.plugin_settings_container.winfo_children():
        widget.destroy()


def on_plugin_select(self, event):
    selection = self.plugins_listbox.curselection()
    if not selection:
        return

    idx = selection[0]
    plugin_info = self.current_plugin_list[idx]

    # 清空旧界面
    for widget in self.plugin_settings_container.winfo_children():
        widget.destroy()

    info_frame = tb.Frame(self.plugin_settings_container)
    info_frame.pack(fill=X, pady=5)

    info_text = (f"ID: {plugin_info['id']}\n"
                 f"名称: {plugin_info['name']}\n"
                 f"版本: {plugin_info['version']}\n"
                 f"来源: {plugin_info['source']}\n"
                 f"描述: {plugin_info['description']}")
    tb.Label(info_frame, text=info_text, font=("微软雅黑", 9), justify=LEFT).pack(anchor=W)

    btn_frame = tb.Frame(self.plugin_settings_container)
    btn_frame.pack(fill=X, pady=5)

    if plugin_info["enabled"]:
        tb.Button(btn_frame, text="禁用", bootstyle="warning-outline",
                  command=lambda: self.toggle_plugin_enabled(plugin_info["id"], False)).pack(side=LEFT, padx=2)
    else:
        tb.Button(btn_frame, text="启用", bootstyle="success-outline",
                  command=lambda: self.toggle_plugin_enabled(plugin_info["id"], True)).pack(side=LEFT, padx=2)

    tb.Button(btn_frame, text="重载", bootstyle="secondary-outline",
              command=lambda: self.reload_single_plugin(plugin_info["id"])).pack(side=LEFT, padx=2)

    plugin_instance = plugin_info["instance"]
    usage_info = self._extract_plugin_usage_info(plugin_instance, plugin_info["manifest"])

    if usage_info:
        usage_outer = tb.Frame(self.plugin_settings_container)
        usage_outer.pack(fill=X, pady=10)

        tb.Label(usage_outer, text="📖 使用说明", font=("微软雅黑", 9, "bold"), bootstyle="primary").pack(anchor=W, pady=(0, 5))

        usage_content = tb.Frame(usage_outer, relief=GROOVE, borderwidth=1)
        usage_content.pack(fill=X, pady=2)

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
            tb.Label(usage_content, text=usage_text.strip(), font=("微软雅黑", 9), justify=LEFT).pack(anchor=W, padx=5, pady=5)

    if hasattr(plugin_instance, 'get_settings_ui'):
        try:
            settings_ui = plugin_instance.get_settings_ui(self.plugin_settings_container)
            if settings_ui is not None:
                settings_outer = tb.Frame(self.plugin_settings_container)
                settings_outer.pack(fill=BOTH, expand=True, pady=10)

                tb.Label(settings_outer, text="⚙️ 插件设置", font=("微软雅黑", 9, "bold"), bootstyle="primary").pack(anchor=W, pady=(0, 5))

                settings_content = tb.Frame(settings_outer, relief=GROOVE, borderwidth=1)
                settings_content.pack(fill=BOTH, expand=True, pady=2)

                settings_ui.pack(in_=settings_content, fill=BOTH, expand=True, padx=5, pady=5)
        except Exception as e:
            tb.Label(self.plugin_settings_container,
                     text=f"加载设置界面失败: {e}",
                     foreground="red").pack(pady=10)

    # 更新画布滚动区域
    self.settings_canvas.update_idletasks()
    self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))


def _extract_plugin_usage_info(self, plugin_instance, manifest):
    """
    从插件实例中提取使用说明信息
    返回字典包含 commands、tools、auto_effect
    """
    info = {"commands": {}, "tools": [], "auto_effect": None}
    
    # 1. 优先尝试调用插件自定义的 get_usage_info 方法
    if hasattr(plugin_instance, 'get_usage_info'):
        try:
            custom_info = plugin_instance.get_usage_info()
            if isinstance(custom_info, dict):
                info.update(custom_info)
                return info
        except:
            pass
    
    # 2. 分析插件源码
    try:
        import inspect
        import re
        
        # 获取 on_load 方法的源码
        source = inspect.getsource(plugin_instance.on_load)
        
        # 提取快捷命令
        # 模式1: if content.startswith("/xxx") 或 if content.strip().lower() == "/xxx"
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
            # 尝试从注释或上下文推断描述（简单处理，显示为"快捷命令"）
            info["commands"] = {cmd: "快捷命令" for cmd in commands}
        
        # 提取注册的工具
        # 模式：host_api.agent.register_tool({ ... }, handler)
        # 使用更宽松的匹配，先找到 register_tool 调用，再提取工具定义
        tool_sections = re.finditer(
            r'host_api\.agent\.register_tool\s*\(\s*(\{[^}]+\})\s*,',
            source,
            re.DOTALL
        )
        for match in tool_sections:
            tool_def_str = match.group(1)
            # 尝试解析工具名称和描述
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', tool_def_str)
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', tool_def_str)
            if name_match:
                tool_name = name_match.group(1)
                tool_desc = desc_match.group(1) if desc_match else "工具"
                info["tools"].append({"name": tool_name, "description": tool_desc})
        
        # 如果既没有命令也没有工具，检查是否有自动效果
        if not info["commands"] and not info["tools"]:
            if 'SystemEvents.UI_READY' in source or 'host_api.ui.display_message' in source:
                info["auto_effect"] = "插件启动后会自动生效。"
                
    except Exception as e:
        # 源码解析失败，忽略
        pass
    
    # 3. 如果仍然没有信息，从 manifest 的 description 中提取
    if not info["commands"] and not info["tools"] and not info["auto_effect"]:
        desc = manifest.description
        if "使用方法" in desc or "命令" in desc or "工具" in desc:
            info["auto_effect"] = desc
        else:
            info["auto_effect"] = "请查看插件描述或文档。"
    
    return info

def toggle_plugin_enabled(self, plugin_id, enabled):
    """切换插件启用状态"""
    if enabled:
        self.plugin_manager_v2.enable_plugin(plugin_id)
    else:
        self.plugin_manager_v2.disable_plugin(plugin_id)
    self.refresh_plugins_display()


def reload_single_plugin(self, plugin_id):
    """重载单个插件"""
    if self.plugin_manager_v2.reload_plugin(plugin_id):
        messagebox.showinfo("成功", f"插件 {plugin_id} 已重载")
    else:
        messagebox.showerror("错误", f"插件 {plugin_id} 重载失败")
    self.refresh_plugins_display()


def reload_plugins(self):
    """重载所有插件"""
    count = 0
    for info in self.current_plugin_list:
        if self.plugin_manager_v2.reload_plugin(info["id"]):
            count += 1
    self.refresh_plugins_display()
    messagebox.showinfo("完成", f"成功重载 {count} 个插件")


def open_plugins_folder(self):
    """打开插件目录"""
    plugins_dir = getattr(self, 'plugins_dir', './plugins')
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir, exist_ok=True)
    os.startfile(os.path.abspath(plugins_dir))


def check_plugins_security(self):
    """启动 AI 安全检查线程"""
    threading.Thread(target=self._check_plugins_security_thread_v2, daemon=True).start()


def _check_plugins_security_thread_v2(self):
    """V2 插件的 AI 安全检查"""
    plugins_info = []
    for info in self.current_plugin_list:
        # 读取插件主文件内容
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

        # 读取 manifest
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

    self.root.after(0, lambda: self._show_plugin_security_results_v2(results))


def _show_plugin_security_results_v2(self, results):
    """显示 V2 安全检查结果窗口"""
    win = Toplevel(self.root)
    win.title("插件安全检查结果 (V2)")
    win.geometry("500x400")
    text = scrolledtext.ScrolledText(win, wrap=tk.WORD, width=60, height=20)
    text.pack(padx=10, pady=10, fill=BOTH, expand=True)

    for item in results:
        pid = item.get('plugin_id', '未知')
        safe = item.get('safe', False)
        reason = item.get('reason', '')
        if safe:
            text.insert(tk.END, f"✅ {pid}: 安全\n", 'safe')
        else:
            text.insert(tk.END, f"❌ {pid}: 可能存在风险\n", 'risk')
        text.insert(tk.END, f"   原因: {reason}\n\n")

    text.tag_config('safe', foreground='green')
    text.tag_config('risk', foreground='red')
    text.config(state='disabled')
    tb.Button(win, text="关闭", command=win.destroy).pack(pady=5)


def generate_plugin(self):
    """生成插件（调用 AI 生成 V2 插件）"""
    desc = self.plugin_desc_entry.get().strip()
    if not desc:
        messagebox.showwarning("提示", "请输入插件描述")
        return
    threading.Thread(target=self._generate_plugin_thread, args=(desc,), daemon=True).start()


def _generate_plugin_thread(self, description):
    """调用 AI 生成 PluginV2 插件（包含 plugin.json 和 main.py）"""
    import re
    import json as json_module
    import os
    import time
    from openai import OpenAI

    # 读取外部提示词模板
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
                prompts = json_module.load(f)
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

    # 使用独立的 OpenAI 客户端，设置更长超时
    client = OpenAI(
        api_key=config.ai_api_key,
        base_url=config.ai_base_url,
        timeout=999.0  # 5 分钟超时
    )

    max_retries = 2
    response = None
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=config.ai_model,
                messages=messages,
                temperature=1,
                max_tokens=8000
            )
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

    # 解析 AI 返回的代码块
    plugin_json_str = None
    main_py_str = None

    # 提取 plugin.json
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
    if json_match:
        plugin_json_str = json_match.group(1).strip()
    else:
        all_code_blocks = re.findall(r'```(?:\w+)?\s*([\s\S]*?)\s*```', response)
        for block in all_code_blocks:
            block_stripped = block.strip()
            if block_stripped.startswith('{') and block_stripped.endswith('}'):
                try:
                    json_module.loads(block_stripped)
                    plugin_json_str = block_stripped
                    break
                except:
                    continue

    # 提取 main.py
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
                json_module.loads(candidate)
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

    # 验证 plugin.json 格式
    try:
        manifest_data = json_module.loads(plugin_json_str)
        if "id" not in manifest_data:
            manifest_data["id"] = f"com.tghelper.{re.sub(r'[^a-z0-9]', '', description.lower())[:20]}"
        if "name" not in manifest_data:
            manifest_data["name"] = description[:30]
        if "version" not in manifest_data:
            manifest_data["version"] = "1.0.0"
        if "entry_point" not in manifest_data:
            manifest_data["entry_point"] = "main.py"
        plugin_json_str = json_module.dumps(manifest_data, indent=2, ensure_ascii=False)
    except Exception as e:
        self.display_assistant_message(f"AI 生成的 plugin.json 格式错误: {e}\n\n内容:\n{plugin_json_str[:500]}")
        return

    # 生成插件文件夹
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
        self.root.after(0, self.refresh_plugins_display)
        
# ==================== 定时任务页 ====================
def create_tasks_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="定时任务")

    toolbar = tb.Frame(tab)
    toolbar.pack(fill=X, pady=5, padx=5)
    tb.Button(toolbar, text="➕ 添加任务", command=self.add_task, bootstyle="success-outline").pack(side=LEFT, padx=2)
    tb.Button(toolbar, text="🔄 刷新", command=self.refresh_tasks, bootstyle="secondary-outline").pack(side=LEFT, padx=2)

    columns = ('ID', '消息', '触发器', '下次运行', '状态')
    self.task_tree = ttk.Treeview(tab, columns=columns, show='headings', height=12)
    for col in columns:
        self.task_tree.heading(col, text=col)
        if col == 'ID':
            self.task_tree.column(col, width=80)
        elif col == '消息':
            self.task_tree.column(col, width=150)
        else:
            self.task_tree.column(col, width=100)

    scrollbar = ttk.Scrollbar(tab, orient=VERTICAL, command=self.task_tree.yview)
    self.task_tree.configure(yscrollcommand=scrollbar.set)

    self.task_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
    scrollbar.pack(side=RIGHT, fill=Y, pady=5)

    self.task_menu = tk.Menu(self.root, tearoff=0)
    self.task_menu.add_command(label="编辑", command=self.edit_task)
    self.task_menu.add_command(label="删除", command=self.delete_task)
    self.task_tree.bind("<Button-3>", self._show_task_menu)

    self.refresh_tasks()


def _show_task_menu(self, event):
    item = self.task_tree.identify_row(event.y)
    if item:
        self.task_tree.selection_set(item)
        self.task_menu.post(event.x_root, event.y_root)


def refresh_tasks(self):
    for item in self.task_tree.get_children():
        self.task_tree.delete(item)
    tasks = self.task_scheduler.get_tasks()
    for task in tasks:
        task_id = task['id']
        msg = task.get('message', '')
        trigger = f"{task.get('trigger')}: {task.get('trigger_args')}"
        next_run = "N/A"
        job = self.task_scheduler.scheduler.get_job(task_id)
        if job and job.next_run_time:
            next_run = job.next_run_time.strftime("%m-%d %H:%M")
        status = "启用" if task.get('enabled', True) else "禁用"
        self.task_tree.insert('', tk.END, values=(task_id[:8], msg[:20]+"...", trigger[:20], next_run, status))


def add_task(self):
    add_win = Toplevel(self.root)
    add_win.title("添加定时任务")
    add_win.geometry("380x350")
    add_win.transient(self.root)
    add_win.grab_set()

    frame = tb.Frame(add_win)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    tb.Label(frame, text="消息内容:", font=("微软雅黑", 9)).grid(row=0, column=0, sticky=W, pady=5)
    msg_entry = tb.Entry(frame, width=40)
    msg_entry.grid(row=0, column=1, pady=5, sticky=EW)

    tb.Label(frame, text="触发方式:", font=("微软雅黑", 9)).grid(row=1, column=0, sticky=W, pady=5)
    trigger_type = tk.StringVar(value="cron")
    tb.Radiobutton(frame, text="Cron", variable=trigger_type, value="cron").grid(row=1, column=1, sticky=W)
    tb.Radiobutton(frame, text="间隔(秒)", variable=trigger_type, value="interval").grid(row=2, column=1, sticky=W)
    tb.Radiobutton(frame, text="一次性", variable=trigger_type, value="date").grid(row=3, column=1, sticky=W)

    tb.Label(frame, text="Cron表达式 (0 8 * * *):", font=("微软雅黑", 9)).grid(row=4, column=0, sticky=W, pady=5)
    cron_entry = tb.Entry(frame, width=30)
    cron_entry.grid(row=4, column=1, pady=5, sticky=EW)

    tb.Label(frame, text="间隔秒数:", font=("微软雅黑", 9)).grid(row=5, column=0, sticky=W, pady=5)
    interval_entry = tb.Entry(frame, width=30)
    interval_entry.grid(row=5, column=1, pady=5, sticky=EW)

    tb.Label(frame, text="时间 (YYYY-MM-DD HH:MM:SS):", font=("微软雅黑", 9)).grid(row=6, column=0, sticky=W, pady=5)
    date_entry = tb.Entry(frame, width=30)
    date_entry.grid(row=6, column=1, pady=5, sticky=EW)

    def save_task():
        msg = msg_entry.get().strip()
        if not msg:
            messagebox.showerror("错误", "消息内容不能为空")
            return
        t_type = trigger_type.get()
        trigger_args = {}
        if t_type == 'cron':
            cron = cron_entry.get().strip()
            if not cron:
                messagebox.showerror("错误", "请输入Cron表达式")
                return
            trigger_args['cron'] = cron
        elif t_type == 'interval':
            try:
                seconds = int(interval_entry.get().strip())
                if seconds <= 0:
                    raise ValueError
                trigger_args['seconds'] = seconds
            except:
                messagebox.showerror("错误", "请输入大于0的整数秒数")
                return
        else:
            date_str = date_entry.get().strip()
            try:
                datetime.fromisoformat(date_str)
                trigger_args['run_date'] = date_str
            except:
                messagebox.showerror("错误", "时间格式错误")
                return
        task_info = {
            'message': msg,
            'trigger': t_type,
            'trigger_args': trigger_args,
            'enabled': True
        }
        self.task_scheduler.add_task(task_info)
        self.refresh_tasks()
        add_win.destroy()

    tb.Button(frame, text="保存", command=save_task, bootstyle="primary").grid(row=7, column=0, columnspan=2, pady=20)


def edit_task(self):
    messagebox.showinfo("提示", "编辑功能在此版本中简化为删除后重新添加")


def delete_task(self):
    selected = self.task_tree.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择一个任务")
        return
    if messagebox.askyesno("确认", "删除该任务？"):
        item = selected[0]
        values = self.task_tree.item(item, 'values')
        task_id_short = values[0]
        tasks = self.task_scheduler.get_tasks()
        for t in tasks:
            if t['id'].startswith(task_id_short):
                self.task_scheduler.remove_task(t['id'])
                break
        self.refresh_tasks()


# ==================== AI人格页 ====================
def create_personality_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="AI人格")

    paned = tb.Panedwindow(tab, orient=HORIZONTAL)
    paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

    left_frame = tb.Frame(paned)
    paned.add(left_frame, weight=1)
    tb.Label(left_frame, text="可选人格", font=("微软雅黑", 9, "bold")).pack(anchor=NW)
    self.personality_listbox = tk.Listbox(left_frame)
    self.personality_listbox.pack(fill=BOTH, expand=True)
    self.personality_listbox.bind('<<ListboxSelect>>', self.on_personality_select)

    right_frame = tb.Frame(paned)
    paned.add(right_frame, weight=2)

    self.avatar_label_personality = tb.Label(right_frame, text="头像预览")
    self.avatar_label_personality.pack(pady=5)

    self.name_label = tb.Label(right_frame, text="名称：", font=("微软雅黑", 11, "bold"))
    self.name_label.pack(anchor=W, pady=2)

    self.prompt_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=8)
    self.prompt_text.pack(fill=BOTH, expand=True, pady=5)

    btn_frame = tb.Frame(right_frame)
    btn_frame.pack(fill=X, pady=5)
    tb.Button(btn_frame, text="✓ 应用人格", command=self.on_apply_personality, bootstyle="primary").pack(side=LEFT, padx=2)
    tb.Button(btn_frame, text="📂 打开文件夹", command=self.open_personality_folder, bootstyle="secondary-outline").pack(side=LEFT, padx=2)

    self.refresh_personality_list()


def refresh_personality_list(self):
    self.personality_listbox.delete(0, tk.END)
    for p in self.personalities:
        self.personality_listbox.insert(tk.END, p['name'])


def on_personality_select(self, event):
    selection = self.personality_listbox.curselection()
    if not selection:
        return
    index = selection[0]
    p = self.personalities[index]
    self.name_label.config(text=f"名称：{p['name']}")
    self.prompt_text.delete(1.0, tk.END)
    self.prompt_text.insert(tk.END, p['prompt'])
    if p['avatar'] and os.path.exists(p['avatar']):
        try:
            img = Image.open(p['avatar'])
            img = img.resize((80, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.avatar_label_personality.config(image=photo)
            self.avatar_label_personality.image = photo
        except:
            self.avatar_label_personality.config(text="头像加载失败")
    else:
        self.avatar_label_personality.config(text="无头像")


def on_apply_personality(self):
    selection = self.personality_listbox.curselection()
    if not selection:
        messagebox.showwarning("提示", "请先选择一个人格")
        return
    index = selection[0]
    p = self.personalities[index]
    self.apply_personality(p['name'])
    messagebox.showinfo("成功", f"已切换到人格：{p['name']}")
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
            if config.qq_enabled and p['avatar']:
                self.set_qq_avatar(p['avatar'])
                self.set_qq_nickname(personality_name)
            break


def open_personality_folder(self):
    abs_personality_dir = os.path.abspath(self.personality_dir)
    if not os.path.exists(abs_personality_dir):
        try:
            os.makedirs(abs_personality_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建文件夹：{abs_personality_dir}\n{e}")
            return
    try:
        os.startfile(abs_personality_dir)
    except Exception as e:
        messagebox.showerror("错误", f"无法打开文件夹：{abs_personality_dir}\n{e}")


# ==================== 调试页 ====================
def create_debug_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="调试")

    frame = tb.Frame(tab)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def toggle_debug():
        config.debug_mode = self.debug_mode.get()
        self._save_all_config()

    tb.Checkbutton(frame, text="调试模式（显示工具调用结果）",
                   variable=self.debug_mode,
                   command=toggle_debug).pack(anchor=W, pady=5)

    def toggle_auto_backup():
        config.auto_backup_short_term = self.auto_backup_var.get()
        self._save_all_config()

    self.auto_backup_var = tk.BooleanVar(value=config.auto_backup_short_term)
    tb.Checkbutton(frame, text="自动备份并清空短期记忆",
                   variable=self.auto_backup_var,
                   command=toggle_auto_backup).pack(anchor=W, pady=5)
    def toggle_browser_headful():
        config.browser_headful = self.browser_headful_var.get()
        self._save_all_config()
    
    self.browser_headful_var = tk.BooleanVar(value=getattr(config, 'browser_headful', False))
    ttk.Checkbutton(frame, text="浏览器有头模式（显示窗口，便于调试）",
                    variable=self.browser_headful_var,
                    command=toggle_browser_headful).pack(anchor=tk.W, pady=5)
    mem_frame_outer = tb.Frame(frame)
    mem_frame_outer.pack(fill=X, pady=10)
    tb.Label(mem_frame_outer, text="记忆管理", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    mem_frame = tb.Frame(mem_frame_outer, relief=GROOVE, borderwidth=1)
    mem_frame.pack(fill=X, pady=2)

    tb.Button(mem_frame, text="打开长期记忆", command=lambda: self.open_memory_file("长期记忆.txt"),
              bootstyle="secondary-outline").pack(side=LEFT, padx=5, pady=5)
    tb.Button(mem_frame, text="打开短期记忆", command=lambda: self.open_memory_file("短期记忆.txt"),
              bootstyle="secondary-outline").pack(side=LEFT, padx=5, pady=5)
    tb.Button(mem_frame, text="清空短期记忆", command=self.clear_short_term,
              bootstyle="danger-outline").pack(side=LEFT, padx=5, pady=5)

    tb.Label(frame, text="说明：调试模式开启后，AI消息下方会显示工具调用详情。\n热闹模式可在顶部工具栏快速切换。",
             foreground="gray", wraplength=380, justify=LEFT).pack(anchor=W, pady=10)

    config_frame_outer = tb.Frame(frame)
    config_frame_outer.pack(fill=X, pady=10)
    tb.Label(config_frame_outer, text="AI 配置管理", font=("微软雅黑", 9, "bold"),
             bootstyle="primary").pack(anchor=NW)
    config_frame = tb.Frame(config_frame_outer, relief=GROOVE, borderwidth=1)
    config_frame.pack(fill=X, pady=2)

    tb.Button(config_frame, text="📤 导出 AI 配置", command=self.export_ai_config,
              bootstyle="secondary-outline").pack(side=LEFT, padx=5, pady=5)
    tb.Button(config_frame, text="📥 导入 AI 配置", command=self.import_ai_config,
              bootstyle="secondary-outline").pack(side=LEFT, padx=5, pady=5)
    tb.Button(config_frame, text="🗑️ 重置 AI 配置", command=self.reset_ai_config,
              bootstyle="danger-outline").pack(side=LEFT, padx=5, pady=5)
    tb.Button(config_frame, text="🎨 主题设置", command=self.open_theme_selector,
              bootstyle="info-outline").pack(side=LEFT, padx=5, pady=5)

def export_ai_config(self):
    source = CONFIG_FILE
    if not os.path.exists(source):
        messagebox.showerror("错误", "配置文件不存在")
        return
    file_path = filedialog.asksaveasfilename(
        title="导出 AI 配置",
        defaultextension=".json",
        filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
    )
    if not file_path:
        return
    try:
        shutil.copy2(source, file_path)
        messagebox.showinfo("成功", f"AI 配置已导出到 {file_path}")
    except Exception as e:
        messagebox.showerror("错误", f"导出失败: {e}")


def import_ai_config(self):
    file_path = filedialog.askopenfilename(
        title="导入 AI 配置",
        filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
    )
    if not file_path:
        return
    if not messagebox.askyesno("确认", "导入将覆盖当前所有 AI 配置（API Key、模型、QQ 设置等），程序将自动重启。是否继续？"):
        return
    try:
        shutil.copy2(file_path, CONFIG_FILE)
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            json.load(f)
        messagebox.showinfo("成功", "AI 配置已导入，程序将自动重启。")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except json.JSONDecodeError as e:
        messagebox.showerror("错误", f"配置文件格式错误: {e}")
    except Exception as e:
        messagebox.showerror("错误", f"导入失败: {e}")


def reset_ai_config(self):
    if not messagebox.askyesno("确认重置", "此操作将删除所有 AI 配置（API Key、模型、QQ 设置等），程序将重启并进入配置向导。是否继续？"):
        return
    try:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        messagebox.showerror("错误", f"重置失败: {e}")


# ==================== 本地模型页 ====================
def create_local_model_tab(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="本地模型")

    self.current_model_frame = ttk.Frame(tab)
    self.current_model_frame.pack(fill=tk.X, pady=5, padx=5)

    ttk.Label(self.current_model_frame, text="当前使用模型:", font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
    self.current_model_label = ttk.Label(self.current_model_frame, text=getattr(config, 'local_model', '未设置'),
                                         foreground="green", font=("微软雅黑", 9))
    self.current_model_label.pack(side=tk.LEFT, padx=5)

    columns = ('模型名称', '文件路径', '状态')
    self.model_tree = ttk.Treeview(tab, columns=columns, show='headings', height=10)
    self.model_tree.heading("模型名称", text="模型名称")
    self.model_tree.heading("文件路径", text="文件路径")
    self.model_tree.heading("状态", text="状态")
    self.model_tree.column("模型名称", width=150)
    self.model_tree.column("文件路径", width=300)
    self.model_tree.column("状态", width=100)
    self.model_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    btn_frame = ttk.Frame(tab)
    btn_frame.pack(fill=tk.X, pady=5)

    ttk.Button(btn_frame, text="添加模型", command=self.add_model_dialog).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="删除模型", command=self.delete_model).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="一键部署推荐模型", command=self.deploy_recommended_model).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="刷新列表", command=self.refresh_model_list).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="✅ 使用此模型", command=self.select_model_as_current, bootstyle="success").pack(side=tk.LEFT, padx=5)

    self.model_progress = ttk.Progressbar(tab, length=400, mode='determinate')
    self.model_progress.pack(pady=5)

    self.refresh_model_list()
    self.root.after(1000, self.refresh_model_list)


def refresh_model_list(self):
    for item in self.model_tree.get_children():
        self.model_tree.delete(item)

    current_model = getattr(config, 'local_model', '')

    for name, info in self.local_model_manager.get_all_models().items():
        if not info.get('path', '').startswith('ollama://'):
            if name == current_model:
                status = "✅ 当前使用"
                tags = ('current',)
            else:
                status = "已就绪"
                tags = ()
            self.model_tree.insert('', tk.END, values=(name, info['path'], status), tags=tags)

    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, encoding='utf-8', timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    size = parts[2]
                    existing = False
                    for item in self.model_tree.get_children():
                        vals = self.model_tree.item(item, 'values')
                        if vals[0] == name:
                            existing = True
                            break
                    if not existing:
                        if name == current_model:
                            status = f"✅ 已安装 ({size})"
                            tags = ('current',)
                        else:
                            status = f"已安装 ({size})"
                            tags = ()
                        self.model_tree.insert('', tk.END, values=(name, f"ollama://{name}", status), tags=tags)
    except Exception as e:
        print(f"获取Ollama模型列表失败: {e}")

    self.model_tree.tag_configure('current', background='#2E7D32', foreground='white')
    self.current_model_label.config(text=current_model if current_model else '未设置')


def add_model_dialog(self):
    dialog = tk.Toplevel(self.root)
    dialog.title("添加本地模型")
    dialog.geometry("400x200")
    dialog.transient(self.root)
    dialog.grab_set()

    ttk.Label(dialog, text="模型名称:").grid(row=0, column=0, padx=5, pady=5)
    name_entry = ttk.Entry(dialog)
    name_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(dialog, text="文件路径:").grid(row=1, column=0, padx=5, pady=5)
    path_entry = ttk.Entry(dialog)
    path_entry.grid(row=1, column=1, padx=5, pady=5)

    def browse():
        fname = filedialog.askopenfilename(title="选择模型文件", filetypes=[("GGUF文件", "*.gguf"), ("所有文件", "*.*")])
        if fname:
            path_entry.delete(0, tk.END)
            path_entry.insert(0, fname)

    ttk.Button(dialog, text="浏览", command=browse).grid(row=1, column=2, padx=5)

    def add():
        name = name_entry.get().strip()
        path = path_entry.get().strip()
        if name and path:
            self.local_model_manager.add_model(name, path, {})
            self.refresh_model_list()
            dialog.destroy()

    ttk.Button(dialog, text="添加", command=add).grid(row=2, column=0, columnspan=3, pady=10)


def delete_model(self):
    selected = self.model_tree.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择一个模型")
        return
    item = selected[0]
    name = self.model_tree.item(item, "values")[0]
    if messagebox.askyesno("确认", f"确定要删除模型 {name} 吗？"):
        self.local_model_manager.remove_model(name)
        self.refresh_model_list()


def deploy_recommended_model(self):
    grade = HardwareDetector.get_grade()
    with open("model_recommendations.json", 'r', encoding='utf-8') as f:
        recs = json.load(f)
    models = recs.get(grade, [])
    if not models:
        messagebox.showinfo("提示", "您的硬件等级没有推荐的模型")
        return
    dialog = tk.Toplevel(self.root)
    dialog.title("选择模型")
    dialog.geometry("400x300")
    dialog.transient(self.root)
    dialog.grab_set()

    ttk.Label(dialog, text="请选择要部署的模型:").pack(pady=10)

    display_names = [f"{m.get('display_name', m['name'])} ({m.get('provider', '未知')}) - {m.get('description', '')[:20]}"
                     for m in models]
    name_to_display = {m["name"]: display_names[i] for i, m in enumerate(models)}
    display_to_name = {display_names[i]: m["name"] for i, m in enumerate(models)}

    model_var = tk.StringVar(value=display_names[0])
    model_combo = ttk.Combobox(dialog, textvariable=model_var, values=display_names, state="readonly", width=50)
    model_combo.pack(pady=5)

    def deploy():
        selected_display = model_var.get()
        selected_model = display_to_name.get(selected_display, selected_display)
        dialog.destroy()
        self.deploy_model(selected_model)

    ttk.Button(dialog, text="部署", command=deploy).pack(pady=10)


def deploy_model(self, model_name):
    deploy_win = tk.Toplevel(self.root)
    deploy_win.title("部署模型")
    deploy_win.geometry("500x400")
    deploy_win.transient(self.root)
    deploy_win.grab_set()

    ttk.Label(deploy_win, text=f"正在部署 {model_name}...", font=("微软雅黑", 12)).pack(pady=10)

    progress = ttk.Progressbar(deploy_win, length=400, mode='indeterminate')
    progress.pack(pady=5)
    progress.start()

    status_label = ttk.Label(deploy_win, text="准备下载...", foreground="gray")
    status_label.pack(pady=5)

    log_frame = ttk.Frame(deploy_win)
    log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, state='disabled')
    log_text.pack(fill=tk.BOTH, expand=True)

    def add_log(text, is_error=False):
        def _add():
            log_text.config(state='normal')
            timestamp = time.strftime("%H:%M:%S")
            tag = "error" if is_error else "normal"
            log_text.insert(tk.END, f"[{timestamp}] {text}\n", tag)
            log_text.see(tk.END)
            log_text.config(state='disabled')
            status_label.config(text=text[:50], foreground="red" if is_error else "green")
        deploy_win.after(0, _add)

    log_text.tag_config("error", foreground="red")
    log_text.tag_config("normal", foreground="white")

    def callback(success, result):
        progress.stop()
        if success:
            add_log("✅ 部署成功！", False)
            status_label.config(text="部署成功！", foreground="green")
            if model_name.endswith(".gguf"):
                self.local_model_manager.add_model(os.path.basename(model_name), result, {})
            else:
                self.local_model_manager.add_model(model_name, f"ollama://{model_name}", {})
            self.refresh_model_list()
        else:
            add_log(f"❌ {result}", True)
            status_label.config(text="部署失败", foreground="red")

    def output_callback(text, is_error):
        add_log(text, is_error)

    threading.Thread(
        target=lambda: self.local_model_manager.deploy_model(model_name, callback=callback, output_callback=output_callback),
        daemon=True
    ).start()

    ttk.Button(deploy_win, text="关闭", command=deploy_win.destroy).pack(pady=10)


def select_model_as_current(self):
    selected = self.model_tree.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择一个模型")
        return

    item = selected[0]
    values = self.model_tree.item(item, 'values')
    model_name = values[0]

    if messagebox.askyesno("确认", f"确定要使用模型 [{model_name}] 吗？\n\n这将立即切换当前使用的本地模型。"):
        config.local_model = model_name
        try:
            self.agent._init_local_model()
            self.current_model_label.config(text=model_name, foreground="green")
            self._save_all_config()
            messagebox.showinfo("成功", f"已切换到模型: {model_name}\n\n请在「模型选择」页确保「主模型」选择为「本地」才能生效。")
        except Exception as e:
            messagebox.showerror("错误", f"切换模型失败: {str(e)}")


# ==================== 模型选择页 ====================
def create_model_selector_tab(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="模型选择")

    ttk.Label(tab, text="主模型（用于对话）").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    self.main_model_type = tk.StringVar(value=getattr(config, 'main_model_type', 'cloud'))
    ttk.Radiobutton(tab, text="云端", variable=self.main_model_type, value="cloud").grid(row=0, column=1)
    ttk.Radiobutton(tab, text="本地", variable=self.main_model_type, value="local").grid(row=0, column=2)

    ttk.Label(tab, text="副模型（用于多模态）").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
    self.sub_model_type = tk.StringVar(value=getattr(config, 'sub_model_type', 'cloud'))
    ttk.Radiobutton(tab, text="云端", variable=self.sub_model_type, value="cloud").grid(row=1, column=1)
    ttk.Radiobutton(tab, text="本地", variable=self.sub_model_type, value="local").grid(row=1, column=2)

    ttk.Button(tab, text="保存模型选择", command=self.save_model_selection).grid(row=2, column=0, columnspan=3, pady=10)


def save_model_selection(self):
    config.main_model_type = self.main_model_type.get()
    config.sub_model_type = self.sub_model_type.get()
    self._save_all_config()
    messagebox.showinfo("成功", "模型选择已保存，重启后生效")


# ==================== 关于对话框 ====================
def show_about_dialog(self):
    win = Toplevel(self.root)
    win.title("关于 TGAI")
    win.geometry("400x500")
    win.transient(self.root)
    win.grab_set()

    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (400 // 2)
    y = (win.winfo_screenheight() // 2) - (500 // 2)
    win.geometry(f'+{x}+{y}')

    title_label = tb.Label(win, text="TG HELPER", font=("微软雅黑", 28, "bold"))
    title_label.pack(pady=(30, 10))

    icon_path = os.path.join("icon", "TGAI.png")
    if os.path.exists(icon_path):
        try:
            img = Image.open(icon_path)
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            icon_label = tb.Label(win, image=photo)
            icon_label.image = photo
            icon_label.pack(pady=10)
        except:
            pass

    version_label = tb.Label(win, text="版本号：v0.1.5", font=("微软雅黑", 10))
    version_label.pack(pady=5)

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
    joke_label = tb.Label(win, text=f"“{random_joke}”", font=("微软雅黑", 9, 'italic'),
                          foreground='gray', wraplength=350)
    joke_label.pack(pady=20)

    donate_btn = tb.Button(win, text="投喂作者", command=self._show_donation_qr, bootstyle="warning")
    donate_btn.pack(pady=20)

    tb.Button(win, text="关闭", command=win.destroy, bootstyle="secondary").pack(pady=10)


def _show_donation_qr(self):
    qr_path = os.path.join("icon", "wechat_pay.png")
    if not os.path.exists(qr_path):
        messagebox.showerror("错误", f"未找到收款码图片，请将 wechat_pay.png 放在 icon 文件夹下。")
        return
    win = Toplevel(self.root)
    win.title("投喂作者")
    win.transient(self.root)
    win.grab_set()
    try:
        pil_img = Image.open(qr_path)
        pil_img = pil_img.resize((300, 300), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(pil_img)
        label = tb.Label(win, image=photo)
        label.image = photo
        label.pack(padx=10, pady=10)
        tb.Label(win, text="感谢您的支持！").pack(pady=5)
    except Exception as e:
        messagebox.showerror("错误", f"无法加载图片：{e}")
        win.destroy()

def open_theme_selector(self):
    """打开主题选择窗口"""
    win = Toplevel(self.root)
    win.title("主题设置")
    win.geometry("400x250")
    win.transient(self.root)
    win.grab_set()

    # 获取 ttkbootstrap 内置主题列表（去掉一些不常用的）
    available_themes = [
        "flatly", "litera", "cosmo", "minty", "lumen", "sandstone",
        "yeti", "pulse", "united", "journal", "simplex", "cerulean",
        "superhero", "darkly", "cyborg", "vapor", "solar"
    ]
    current_theme = getattr(config, 'gui_theme', 'flatly')

    main_frame = tb.Frame(win, padding=15)
    main_frame.pack(fill=BOTH, expand=True)

    tb.Label(main_frame, text="选择主题", font=("微软雅黑", 12, "bold")).pack(pady=(0, 10))

    # 下拉选择框
    theme_var = tk.StringVar(value=current_theme)
    combo = tb.Combobox(main_frame, textvariable=theme_var, values=available_themes,
                        state="readonly", font=("微软雅黑", 10))
    combo.pack(fill=X, pady=5)

    # 预览提示（因为无法在独立窗口实时预览所有控件，这里仅作提示）
    tip_label = tb.Label(main_frame, text="选择后点击“应用”即可切换主题",
                         font=("微软雅黑", 9), bootstyle="secondary")
    tip_label.pack(pady=5)

    def apply_theme():
        selected = theme_var.get()
        if selected:
            self.change_theme(selected)  # 调用主窗口的切换方法
            # 如果 TG Home 窗口打开着，它也会通过 change_theme 中的逻辑更新
            messagebox.showinfo("主题已切换", f"主题已切换为 {selected}")
        win.destroy()

    btn_frame = tb.Frame(main_frame)
    btn_frame.pack(pady=20)
    tb.Button(btn_frame, text="应用", command=apply_theme, bootstyle="primary").pack(side=LEFT, padx=10)
    tb.Button(btn_frame, text="取消", command=win.destroy, bootstyle="secondary").pack(side=LEFT, padx=10)

def open_ai_translator(self):
    """打开 AI 插件翻译向导（增强版：全目录深度扫描，无 padding 错误，后台线程）"""
    import threading
    from config import config
    from openai import OpenAI
    import time

    translator_win = Toplevel(self.root)
    translator_win.title("🌐 AI 插件翻译器")
    translator_win.geometry("750x650")
    translator_win.minsize(650, 550)
    translator_win.transient(self.root)
    translator_win.grab_set()

    current_step = tk.IntVar(value=1)
    selected_type = tk.StringVar(value="xiaoli")
    selected_path = tk.StringVar()
    generated_plugin_json = tk.StringVar()
    generated_main_py = tk.StringVar()
    plugin_summary = tk.StringVar()
    collected_files = []

    main_frame = tb.Frame(translator_win, padding=15)
    main_frame.pack(fill=BOTH, expand=True)

    step_frame = tb.Frame(main_frame)
    step_frame.pack(fill=X, pady=(0, 15))

    steps = ["选择插件", "AI 分析", "预览编辑", "安装"]
    step_labels = []
    for i, text in enumerate(steps, 1):
        label = tb.Label(step_frame, text=f"{i}. {text}", font=("微软雅黑", 10))
        label.pack(side=LEFT, padx=10)
        step_labels.append(label)

    def update_step_display():
        for i, label in enumerate(step_labels, 1):
            if i == current_step.get():
                label.configure(bootstyle="primary", font=("微软雅黑", 10, "bold"))
            elif i < current_step.get():
                label.configure(bootstyle="success", font=("微软雅黑", 10))
            else:
                label.configure(bootstyle="secondary", font=("微软雅黑", 10))

    content_frame = tb.Frame(main_frame)
    content_frame.pack(fill=BOTH, expand=True)

    # ---------- 步骤 1 ----------
    step1_frame = tb.Frame(content_frame)
    tb.Label(step1_frame, text="选择源插件类型", font=("微软雅黑", 12, "bold")).pack(anchor=W, pady=(0, 10))
    type_frame = tb.Frame(step1_frame)
    type_frame.pack(fill=X, pady=5)
    tb.Radiobutton(type_frame, text="🦊 小狸 CLI 插件 (.py 文件)", variable=selected_type, value="xiaoli").pack(anchor=W, pady=2)
    tb.Radiobutton(type_frame, text="🔌 OpenClaw 插件 (文件夹)", variable=selected_type, value="openclaw").pack(anchor=W, pady=2)
    tb.Radiobutton(type_frame, text="📁 自定义 (任意 Python/JavaScript 文件或文件夹)", variable=selected_type, value="custom").pack(anchor=W, pady=2)
    tb.Label(step1_frame, text="选择文件/文件夹", font=("微软雅黑", 10, "bold")).pack(anchor=W, pady=(15, 5))
    path_frame = tb.Frame(step1_frame)
    path_frame.pack(fill=X, pady=5)
    path_entry = tb.Entry(path_frame, textvariable=selected_path, state="readonly")
    path_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

    def browse_path():
        if selected_type.get() == "xiaoli":
            path = filedialog.askopenfilename(title="选择小狸插件文件", filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")])
        elif selected_type.get() == "openclaw":
            path = filedialog.askdirectory(title="选择 OpenClaw 插件文件夹")
        else:
            choice = messagebox.askyesno("选择类型", "选择'是'选择文件夹，选择'否'选择文件")
            if choice:
                path = filedialog.askdirectory(title="选择文件夹")
            else:
                path = filedialog.askopenfilename(title="选择文件")
        if path:
            selected_path.set(path)
            analyze_selected_plugin()

    tb.Button(path_frame, text="浏览", command=browse_path, bootstyle="secondary-outline").pack(side=RIGHT)

    # 摘要区域
    summary_outer = tb.Frame(step1_frame)
    summary_outer.pack(fill=BOTH, expand=True, pady=10)
    tb.Label(summary_outer, text="📋 插件摘要", font=("微软雅黑", 9, "bold"), bootstyle="primary").pack(anchor=W, pady=(0, 5))
    summary_content = tb.Frame(summary_outer, relief=GROOVE, borderwidth=1)
    summary_content.pack(fill=BOTH, expand=True)
    summary_text = scrolledtext.ScrolledText(summary_content, wrap=tk.WORD, height=12, state=tk.DISABLED)
    summary_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

    def analyze_selected_plugin():
        nonlocal collected_files
        collected_files = []
        path = selected_path.get()
        if not path or not os.path.exists(path):
            return
        summary_text.config(state=tk.NORMAL)
        summary_text.delete(1.0, tk.END)
        try:
            if selected_type.get() == "xiaoli":
                with open(path, 'r', encoding='utf-8') as f:
                    code = f.read()
                import re
                name_match = re.search(r'def get_tool_info.*?return\s*{.*?"name":\s*"([^"]+)"', code, re.DOTALL)
                desc_match = re.search(r'"description":\s*"([^"]+)"', code)
                plugin_name = name_match.group(1) if name_match else os.path.basename(path)
                plugin_desc = desc_match.group(1) if desc_match else "无描述"
                summary_text.insert(tk.END, f"插件名称: {plugin_name}\n")
                summary_text.insert(tk.END, f"描述: {plugin_desc}\n")
                summary_text.insert(tk.END, f"类型: 小狸 CLI 插件\n")
                summary_text.insert(tk.END, f"文件大小: {len(code)} 字符\n")
                collected_files = [("主文件", os.path.basename(path), len(code))]
            elif selected_type.get() == "openclaw":
                manifest_path = os.path.join(path, "openclaw.plugin.json")
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    summary_text.insert(tk.END, f"插件 ID: {manifest.get('id', '未知')}\n")
                    summary_text.insert(tk.END, f"名称: {manifest.get('name', '未知')}\n")
                    summary_text.insert(tk.END, f"版本: {manifest.get('version', '未知')}\n")
                    summary_text.insert(tk.END, f"描述: {manifest.get('description', '无')}\n")
                    tools = manifest.get('tools', [])
                    summary_text.insert(tk.END, f"工具数量: {len(tools)}\n")
                    collected_files.append(("清单", "openclaw.plugin.json", os.path.getsize(manifest_path)))
                else:
                    summary_text.insert(tk.END, "未找到 openclaw.plugin.json\n")
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
                summary_text.insert(tk.END, f"\n📁 扫描到 {len(file_list)} 个相关文件:\n")
                for rel_path, size in file_list[:20]:
                    summary_text.insert(tk.END, f"  - {rel_path} ({size} 字节)\n")
                if len(file_list) > 20:
                    summary_text.insert(tk.END, f"  ... 还有 {len(file_list)-20} 个文件\n")
            else:
                summary_text.insert(tk.END, f"路径: {path}\n")
                if os.path.isfile(path):
                    size = os.path.getsize(path)
                    summary_text.insert(tk.END, f"文件大小: {size} 字节\n")
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
                    summary_text.insert(tk.END, f"文件夹，包含 {file_count} 个相关文件\n")
        except Exception as e:
            summary_text.insert(tk.END, f"分析失败: {e}\n")
        summary_text.config(state=tk.DISABLED)

    # ---------- 步骤 2：AI 分析 ----------
    step2_frame = tb.Frame(content_frame)
    progress_label = tb.Label(step2_frame, text="正在收集源码并调用 AI...", font=("微软雅黑", 11))
    progress_label.pack(pady=10)
    progress_bar = tb.Progressbar(step2_frame, mode='indeterminate', length=400, bootstyle="primary-striped")
    progress_bar.pack(pady=10)
    log_text = scrolledtext.ScrolledText(step2_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
    log_text.pack(fill=BOTH, expand=True, pady=10)

    def run_ai_translation_async():
        """在后台线程中执行 AI 翻译"""
        progress_bar.start()
        log_text.config(state=tk.NORMAL)
        log_text.delete(1.0, tk.END)
        log_text.insert(tk.END, "📂 正在收集源文件...\n")
        log_text.see(tk.END)

        path = selected_path.get()
        source_code = ""
        file_manifest = []

        if selected_type.get() == "xiaoli":
            with open(path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            file_manifest.append(f"主文件: {os.path.basename(path)}")
            log_text.insert(tk.END, f"✅ 已读取小狸插件 ({len(source_code)} 字符)\n")
        elif selected_type.get() == "openclaw" or (selected_type.get() == "custom" and os.path.isdir(path)):
            total_chars = 0
            file_count = 0
            for rel_path, full_path, size in collected_files:
                if size > 50000:
                    log_text.insert(tk.END, f"⚠️ 跳过过大文件: {rel_path}\n")
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
                    log_text.insert(tk.END, f"📄 已读取: {rel_path}\n")
                except Exception as e:
                    log_text.insert(tk.END, f"❌ 读取失败 {rel_path}: {e}\n")
            log_text.insert(tk.END, f"✅ 共读取 {file_count} 个文件，总计 {total_chars} 字符\n")
            if total_chars > 120000:
                source_code = source_code[:120000] + "\n\n... (总源码已截断)"
                log_text.insert(tk.END, f"⚠️ 总源码过长，已截断\n")
        else:
            with open(path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            file_manifest.append(f"主文件: {os.path.basename(path)}")
            log_text.insert(tk.END, f"✅ 已读取文件 ({len(source_code)} 字符)\n")

        log_text.insert(tk.END, "\n🤖 正在调用 AI 生成 TG HELPER PluginV2 代码...\n")
        log_text.see(tk.END)

        # 加载翻译模板
        prompts_file = os.path.join("plugin_v2", "ai_generator", "translation_prompt.json")
        system_prompt = "你是一个专业的插件移植专家。"
        template = """请将以下源插件转换为 TG HELPER PluginV2 插件..."""
        api_reference_text = ""

        if os.path.exists(prompts_file):
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    prompts = json_module.load(f)
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
            plugin_type=selected_type.get(),
            plugin_path=path,
            file_manifest=file_manifest_str,
            source_code=source_code,
            api_reference=api_reference_text
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # AI 调用（超时300秒，重试2次）
        client = OpenAI(
            api_key=config.ai_api_key,
            base_url=config.ai_base_url,
            timeout=999.0
        )
        max_retries = 2
        response = None
        for attempt in range(max_retries):
            try:
                completion = client.chat.completions.create(
                    model=config.ai_model,
                    messages=messages,
                    temperature=1,
                    max_tokens=8000
                )
                response = completion.choices[0].message.content
                break
            except Exception as e:
                log_text.insert(tk.END, f"⚠️ 第 {attempt + 1} 次尝试失败: {e}\n")
                log_text.see(tk.END)
                if attempt == max_retries - 1:
                    raise
                time.sleep(3)

        # 显示原始响应（前 2000 字符）
        preview = response[:2000] + ("..." if len(response) > 2000 else "")
        log_text.insert(tk.END, f"\n📝 [AI 原始响应] (前 2000 字符):\n{preview}\n")
        log_text.see(tk.END)

        # 解析响应
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        py_match = re.search(r'```python\s*([\s\S]*?)\s*```', response)

        def update_ui():
            progress_bar.stop()
            log_text.insert(tk.END, f"\n📝 [AI 响应] 长度: {len(response)} 字符\n")
            # 显示前 5000 字符用于调试
            if len(response) > 5000:
                log_text.insert(tk.END, response[:5000] + "\n... (响应过长，已截断显示)\n")
            else:
                log_text.insert(tk.END, response + "\n")
            log_text.see(tk.END)

            import re
            # 提取 plugin.json（支持未闭合代码块）
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if not json_match:
                json_match = re.search(r'```json\s*([\s\S]*?)(?=```|$)', response)
            if json_match:
                generated_plugin_json.set(json_match.group(1).strip())
                log_text.insert(tk.END, "✅ 已提取 plugin.json\n")
            else:
                log_text.insert(tk.END, "⚠️ 未找到 plugin.json 代码块\n")

            # 提取 main.py（支持未闭合代码块）
            py_match = re.search(r'```python\s*([\s\S]*?)\s*```', response)
            if not py_match:
                py_match = re.search(r'```python\s*([\s\S]*?)(?=```|$)', response)
            if py_match:
                code = py_match.group(1).strip()
                if code.endswith('...'):
                    log_text.insert(tk.END, "⚠️ 提取的 main.py 可能不完整（以省略号结尾）\n")
                generated_main_py.set(code)
                log_text.insert(tk.END, "✅ 已提取 main.py\n")
            else:
                log_text.insert(tk.END, "⚠️ 未找到 main.py 代码块，请检查原始响应。\n")

            if json_match:
                try:
                    manifest = json.loads(generated_plugin_json.get())
                    plugin_summary.set(f"{manifest.get('name')} v{manifest.get('version')} - {manifest.get('description', '')}")
                except:
                    plugin_summary.set("插件摘要解析失败")

            log_text.insert(tk.END, "\n🎉 翻译完成！点击「下一步」预览并编辑。\n")
            log_text.config(state=tk.DISABLED)
            next_btn.config(state=tk.NORMAL)

        translator_win.after(0, update_ui)

    # ---------- 步骤 3：预览编辑 ----------
    step3_frame = tb.Frame(content_frame)
    tb.Label(step3_frame, textvariable=plugin_summary, font=("微软雅黑", 10, "bold"), bootstyle="primary").pack(anchor=W, pady=(0, 10))
    notebook = tb.Notebook(step3_frame, bootstyle="secondary")
    notebook.pack(fill=BOTH, expand=True)

    json_tab = tb.Frame(notebook)
    notebook.add(json_tab, text="plugin.json")
    json_editor = scrolledtext.ScrolledText(json_tab, wrap=tk.WORD, font=("Consolas", 10))
    json_editor.pack(fill=BOTH, expand=True)

    def update_json_editor(*args):
        json_editor.delete(1.0, tk.END)
        json_editor.insert(1.0, generated_plugin_json.get())
    generated_plugin_json.trace_add("write", update_json_editor)

    py_tab = tb.Frame(notebook)
    notebook.add(py_tab, text="main.py")
    py_editor = scrolledtext.ScrolledText(py_tab, wrap=tk.WORD, font=("Consolas", 10))
    py_editor.pack(fill=BOTH, expand=True)

    def update_py_editor(*args):
        py_editor.delete(1.0, tk.END)
        py_editor.insert(1.0, generated_main_py.get())
    generated_main_py.trace_add("write", update_py_editor)

    tb.Label(step3_frame, text="💡 您可以直接编辑上方代码，修改后将用于安装。", foreground="gray").pack(pady=5)

    # ---------- 步骤 4：安装 ----------
    step4_frame = tb.Frame(content_frame)
    tb.Label(step4_frame, text="✅ 插件已准备就绪", font=("微软雅黑", 12, "bold"), bootstyle="success").pack(pady=10)
    tb.Label(step4_frame, textvariable=plugin_summary, font=("微软雅黑", 10)).pack(pady=5)
    install_log = scrolledtext.ScrolledText(step4_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
    install_log.pack(fill=BOTH, expand=True, pady=10)

    def do_install():
        install_log.config(state=tk.NORMAL)
        install_log.delete(1.0, tk.END)
        try:
            manifest = json.loads(generated_plugin_json.get())
            plugin_id = manifest.get('id', 'com.tghelper.translated')
            import re
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
                f.write(generated_plugin_json.get())
            install_log.insert(tk.END, f"✅ 已保存 plugin.json 到 {manifest_path}\n")

            main_py_code = generated_main_py.get()
            main_py_path = os.path.join(plugin_folder, "main.py")
            with open(main_py_path, 'w', encoding='utf-8') as f:
                f.write(main_py_code)
            install_log.insert(tk.END, f"✅ 已保存 main.py 到 {main_py_path}\n")

            # ----- 增强的依赖检测与安装 -----
            install_log.insert(tk.END, "🔍 正在检测插件依赖...\n")
            install_log.see(tk.END)

            # 标准库集合
            import sys
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

            # 模块名 → pip 包名 映射表
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

            # 提取导入语句
            import_lines = re.findall(r'^(?:from\s+(\S+)\s+import|import\s+(\S+))', main_py_code, re.MULTILINE)
            modules = set()
            for from_mod, imp_mod in import_lines:
                if from_mod:
                    modules.add(from_mod.split('.')[0])
                if imp_mod:
                    modules.add(imp_mod.split('.')[0])

            # 过滤第三方库
            third_party = []
            for m in modules:
                if m in std_libs or m.startswith('plugin_v2') or m == 'config' or m.startswith('tg_helper'):
                    continue
                third_party.append(m)

            if third_party:
                install_log.insert(tk.END, f"📦 检测到第三方依赖: {', '.join(third_party)}\n")
                install_log.see(tk.END)

                python_exe = sys.executable
                failed_packages = []

                for mod in third_party:
                    pkg = module_to_pip.get(mod, mod)
                    install_log.insert(tk.END, f"  正在安装 {mod} (包名: {pkg})...\n")
                    install_log.see(tk.END)

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
                                install_log.insert(tk.END, f"  ✅ {pkg} 安装成功\n")
                                installed = True
                                break
                            else:
                                err = result.stderr[:100] if result.stderr else "未知错误"
                                install_log.insert(tk.END, f"  ⚠️ 失败: {err}\n")
                        except Exception as e:
                            install_log.insert(tk.END, f"  ❌ 异常: {e}\n")
                    if not installed:
                        failed_packages.append(pkg)
                        install_log.insert(tk.END, f"  ❌ {pkg} 安装失败\n")
                    install_log.see(tk.END)

                if failed_packages:
                    install_log.insert(tk.END, f"\n⚠️ 以下依赖安装失败，插件可能无法正常运行: {', '.join(failed_packages)}\n")
                    install_log.insert(tk.END, f"   请手动执行: pip install {' '.join(failed_packages)}\n")
            else:
                install_log.insert(tk.END, "✅ 未检测到需要安装的第三方依赖\n")

            # ----- 智能导入修复 -----
            install_log.insert(tk.END, "\n🔧 验证关键导入...\n")
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
                        install_log.insert(tk.END, f"  ✅ {import_stmt} 可用\n")
                    except ImportError:
                        install_log.insert(tk.END, f"  ⚠️ {import_stmt} 不可用，尝试自动修复...\n")
                        # 尝试重新安装包
                        subprocess.run([python_exe, "-m", "pip", "install", "--force-reinstall", pkg],
                                       capture_output=True, timeout=120)
                        try:
                            exec(import_stmt)
                            install_log.insert(tk.END, f"  ✅ 修复成功\n")
                        except ImportError:
                            if alt_stmt:
                                try:
                                    exec(alt_stmt)
                                    install_log.insert(tk.END, f"  💡 替代导入可用: {alt_stmt}\n")
                                    if messagebox.askyesno("修复导入", f"导入语句 '{import_stmt}' 不可用，但 '{alt_stmt}' 可用。\n是否自动替换？"):
                                        main_py_code = main_py_code.replace(import_stmt, alt_stmt)
                                        with open(main_py_path, 'w', encoding='utf-8') as f:
                                            f.write(main_py_code)
                                        install_log.insert(tk.END, f"  ✅ 已自动修复\n")
                                except ImportError:
                                    install_log.insert(tk.END, f"  ❌ 替代导入也不可用，请手动检查\n")
                            else:
                                install_log.insert(tk.END, f"  ❌ 无法自动修复，请手动检查\n")
            # ------------------------

            if hasattr(self, 'plugin_manager_v2'):
                loaded_id = self.plugin_manager_v2.load_plugin(plugin_folder)
                if loaded_id:
                    install_log.insert(tk.END, f"✅ 插件已加载: {loaded_id}\n")
                    self.refresh_plugins_display()
                else:
                    install_log.insert(tk.END, f"⚠️ 插件保存成功但加载失败，请检查代码\n")
            else:
                install_log.insert(tk.END, f"✅ 插件已保存到: {plugin_folder}\n")

            install_log.insert(tk.END, "\n🎉 安装完成！")
        except Exception as e:
            install_log.insert(tk.END, f"❌ 安装失败: {e}\n")
            import traceback
            traceback.print_exc()
        install_log.config(state=tk.DISABLED)
    # 底部按钮
    button_frame = tb.Frame(main_frame)
    button_frame.pack(fill=X, pady=(15, 0))
    prev_btn = tb.Button(button_frame, text="◀ 上一步", bootstyle="secondary-outline", state=tk.DISABLED)
    prev_btn.pack(side=LEFT)
    next_btn = tb.Button(button_frame, text="下一步 ▶", bootstyle="primary")
    next_btn.pack(side=RIGHT)

    def update_ui_for_step():
        for f in [step1_frame, step2_frame, step3_frame, step4_frame]:
            f.pack_forget()
        step = current_step.get()
        if step == 1:
            step1_frame.pack(fill=BOTH, expand=True)
            prev_btn.config(state=tk.DISABLED)
            next_btn.config(text="下一步 ▶", state=tk.NORMAL if selected_path.get() else tk.DISABLED)
        elif step == 2:
            step2_frame.pack(fill=BOTH, expand=True)
            prev_btn.config(state=tk.NORMAL)
            next_btn.config(text="下一步 ▶", state=tk.DISABLED)
            threading.Thread(target=run_ai_translation_async, daemon=True).start()
        elif step == 3:
            step3_frame.pack(fill=BOTH, expand=True)
            prev_btn.config(state=tk.NORMAL)
            next_btn.config(text="下一步 ▶", state=tk.NORMAL)
        elif step == 4:
            step4_frame.pack(fill=BOTH, expand=True)
            prev_btn.config(state=tk.NORMAL)
            next_btn.config(text="安装插件", bootstyle="success")
        update_step_display()

    def go_next():
        if current_step.get() == 4:
            do_install()
            messagebox.showinfo("完成", "插件已成功安装！")
            translator_win.destroy()
        else:
            current_step.set(current_step.get() + 1)
            update_ui_for_step()

    def go_prev():
        if current_step.get() > 1:
            current_step.set(current_step.get() - 1)
            update_ui_for_step()

    next_btn.config(command=go_next)
    prev_btn.config(command=go_prev)

    def on_path_change(*args):
        if current_step.get() == 1:
            next_btn.config(state=tk.NORMAL if selected_path.get() else tk.DISABLED)
    selected_path.trace_add("write", on_path_change)

    update_ui_for_step()

def create_multi_agent_tab(self):
    tab = tb.Frame(self.notebook)
    self.notebook.add(tab, text="多Agent模式 (beta)")

    main_frame = tb.Frame(tab, padding=10)
    main_frame.pack(fill=BOTH, expand=True)

    # 说明
    tb.Label(main_frame, text="多Agent协作模式", font=("微软雅黑", 12, "bold")).pack(anchor=W)
    tb.Label(main_frame, text=(
        "启用后，AI将以三个独立人格合作完成任务：\n"
        "① 规划员(Planner) - 分析需求，制定任务列表\n"
        "② 执行员(Worker) - 逐步执行任务，可反馈重新规划\n"
        "③ 审查员(Reviewer) - 检查成果，确保任务完成\n\n"
        "任务执行过程中，可点击顶部按钮查看实时进度。"
    ), wraplength=380, justify=LEFT).pack(anchor=W, pady=10)

    # 启用复选框
    self.multi_agent_enable_var = tk.BooleanVar(value=getattr(config, 'multi_agent_enabled', False))
    tb.Checkbutton(main_frame, text="启用多Agent模式（重启后生效）", variable=self.multi_agent_enable_var).pack(anchor=W, pady=5)

    # 人格选择
    personality_options = [p['name'] for p in self.personalities] if hasattr(self, 'personalities') else ["TGAI", "艾依", "塔戈"]
    if len(personality_options) < 3:
        personality_options.extend(["TGAI", "艾依", "塔戈"])  # 保证至少有3个

    # Planner 人格
    planner_frame = tb.Frame(main_frame)
    planner_frame.pack(fill=X, pady=5)
    tb.Label(planner_frame, text="规划员 (Planner) 人格:").pack(side=LEFT)
    self.multi_agent_planner_var = tk.StringVar(value=getattr(config, 'multi_agent_planner_persona', personality_options[0]))
    planner_combo = tb.Combobox(planner_frame, textvariable=self.multi_agent_planner_var, values=personality_options, state="readonly")
    planner_combo.pack(side=LEFT, padx=5)

    # Worker 人格
    worker_frame = tb.Frame(main_frame)
    worker_frame.pack(fill=X, pady=5)
    tb.Label(worker_frame, text="执行员 (Worker) 人格:").pack(side=LEFT)
    self.multi_agent_worker_var = tk.StringVar(value=getattr(config, 'multi_agent_worker_persona', personality_options[1]))
    worker_combo = tb.Combobox(worker_frame, textvariable=self.multi_agent_worker_var, values=personality_options, state="readonly")
    worker_combo.pack(side=LEFT, padx=5)

    # Reviewer 人格
    reviewer_frame = tb.Frame(main_frame)
    reviewer_frame.pack(fill=X, pady=5)
    tb.Label(reviewer_frame, text="审查员 (Reviewer) 人格:").pack(side=LEFT)
    self.multi_agent_reviewer_var = tk.StringVar(value=getattr(config, 'multi_agent_reviewer_persona', personality_options[2]))
    reviewer_combo = tb.Combobox(reviewer_frame, textvariable=self.multi_agent_reviewer_var, values=personality_options, state="readonly")
    reviewer_combo.pack(side=LEFT, padx=5)

    # 警告提示
    tb.Label(main_frame, text="※ 三个Agent人格不能相同，否则记忆可能错乱。", foreground="red").pack(anchor=W, pady=10)

    # 保存按钮
    tb.Button(main_frame, text="💾 保存设置", bootstyle="primary", command=self.save_multi_agent_settings).pack(pady=15)

def save_multi_agent_settings(self):
    # 1. 获取用户勾选的值
    enabled = self.multi_agent_enable_var.get()
    planner = self.multi_agent_planner_var.get()
    worker = self.multi_agent_worker_var.get()
    reviewer = self.multi_agent_reviewer_var.get()

    # 2. 检查人格是否重复
    if enabled and len({planner, worker, reviewer}) < 3:
        messagebox.showerror("错误", "三个Agent的人格必须各不相同，以免记忆错乱")
        return

    # 3. 更新 config 对象
    config.multi_agent_enabled = enabled
    config.multi_agent_planner_persona = planner
    config.multi_agent_worker_persona = worker
    config.multi_agent_reviewer_persona = reviewer

    # 4. 同步到 GUI 实例自身的 multi_agent_enabled 属性（关键！）
    self.multi_agent_enabled = enabled

    # 5. 保存到文件
    self._save_all_config()

    # 6. 配置 orchestrator 并更新按钮
    if enabled:
        try:
            self.multi_agent_orchestrator.configure(True, planner, worker, reviewer)
            self.toggle_multi_agent_btn_visibility(True)
            messagebox.showinfo("成功", "多Agent模式已启用")
        except Exception as e:
            messagebox.showerror("配置错误", str(e))
    else:
        self.multi_agent_orchestrator.configure(False, "", "", "")
        self.toggle_multi_agent_btn_visibility(False)
        messagebox.showinfo("成功", "多Agent模式已禁用")
