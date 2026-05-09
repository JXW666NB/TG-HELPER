# -*- coding: utf-8 -*-
"""
主 GUI 界面 - 布局与核心交互
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font, Toplevel
import threading
import os
import sys
import time
import re
import requests
import random
import json
from datetime import datetime
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from config import config, CONFIG_FILE
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
class AgentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TGAI v0.1.5")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)

        theme_name = getattr(config, 'gui_theme', 'flatly')
        self.style = tb.Style(theme=theme_name)
        self.style.theme_use()

        self.last_sent_message_id = None
        self.agent_running = False           # 标记 AI 是否正在工作
        self.agent_stop_event = threading.Event()  # 中断事件
        self.font = font.Font(family="微软雅黑", size=10)
        self.debug_mode = tk.BooleanVar(value=config.debug_mode)
        self.fun_mode = tk.BooleanVar(value=getattr(config, 'fun_mode_enabled', False))
        self.qq_handler = None
        self.settings_visible = True
        self.settings_width = 400

        self.personality_name = getattr(config, 'current_personality', 'TGAI')
        self.personality_dir = getattr(config, 'personality_dir', './AI人格')
        self.current_persona_name = self.personality_name   # 当前人格名称（状态栏用）
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
        # ========== 初始化 AI Agent ==========
        self.agent = AIAgent(config, self.memory, self.tools, skill_manager=self.skill_manager)
        self.agent.output_callback = self.display_assistant_message          # AI 正常回复
        self.agent.system_output_callback = self.display_system_message     # 系统提示（灰色气泡）

        self.memory.set_ai_summarize_callback(self._memory_summarize_callback)
        self.memory.set_ai_reflection_callback(self._memory_reflection_callback)

        iot_manager.set_ai_callback(self.display_assistant_message)
        iot_manager.set_ai_trigger_callback(self.on_sensor_trigger)
        iot_manager.set_qq_send_callback(self.send_qq_message)

        self.inspect_interval_var = tk.IntVar(value=3600)
        # 根据配置决定是否启动巡检器，不再无脑启动
        if config.inspector_enabled:
            self.start_inspector()
        else:
            # 确保回调已设置，即使不启动巡检器，手动巡检依然可用
            inspector.set_ai_callback(self._inspector_ai_callback)

        self.task_scheduler = TaskScheduler(
            config_dir=getattr(config, 'tasks_dir', './config'),
            on_task_trigger=self.on_task_trigger
        )
        self.task_scheduler.start()
        self.tools.task_scheduler = self.task_scheduler
        # 多Agent模式组件
        self.multi_agent_enabled = getattr(config, 'multi_agent_enabled', False)
        self.multi_agent_orchestrator = MultiAgentOrchestrator(self)
        self.multi_agent_btn = None
        self.task_list_window = None
        # 在 load_personalities 调用之后
        if self.multi_agent_enabled:
            planner_p = getattr(config, 'multi_agent_planner_persona', 'TGAI')
            worker_p = getattr(config, 'multi_agent_worker_persona', '艾依')
            reviewer_p = getattr(config, 'multi_agent_reviewer_persona', '塔戈')
            try:
                self.multi_agent_orchestrator.configure(True, planner_p, worker_p, reviewer_p)
            except Exception as e:
                messagebox.showerror("多Agent配置错误", str(e))
        # ========== 初始化新版插件系统 V2 ==========
        self.plugin_manager_v2 = PluginManagerV2()
        self.plugin_manager_v2.set_gui_instance(self)
        self.plugin_manager_v2.set_memory_instance(self.memory)
        self.plugin_manager_v2.set_agent_instance(self.agent)
        self.plugin_manager_v2.set_tools_instance(self.tools)
        self.plugin_manager_v2.set_config_instance(config)
        self.plugin_manager_v2.set_debug_mode(self.debug_mode.get())

        # 加载新版插件
        loaded_v2_plugins = self.plugin_manager_v2.load_all_plugins()
        if loaded_v2_plugins:
            print(f"[MainGUI] 已加载 {len(loaded_v2_plugins)} 个 V2 插件: {loaded_v2_plugins}")

        # 获取事件总线
        self.event_bus = self.plugin_manager_v2.get_event_bus()

        # 注册自定义 AI 调用处理器（供插件 call_ai 使用）
        def handle_custom_ai_call(event):
            data = event.data
            prompt = data.get("prompt", "")
            system_prompt = data.get("system_prompt", "")
            callback = data.get("callback")
            # 调用 agent
            original_cb = self.agent.output_callback
            response = [None]
            def capture(msg):
                response[0] = msg
            self.agent.output_callback = capture
            self.agent.run(prompt)  # 内部已处理 system_prompt
            self.agent.output_callback = original_cb
            if callback:
                callback(response[0])
        self.event_bus.subscribe("agent.custom_call", handle_custom_ai_call, plugin_id="system")
    
        # ========== 在 UI 就绪时触发事件 ==========
        def on_ui_ready():
            self.event_bus.emit(SystemEvents.UI_READY, {"gui": self}, "system")
        self.root.after(100, on_ui_ready)

        self.local_model_manager = LocalModelManager()
        bind_handlers(self)

        # ---------- 构建界面 ----------
        self.main_container = tb.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self._create_toolbar()

        self.content_frame = tk.PanedWindow(self.main_container, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        self.content_frame.pack(fill=BOTH, expand=True)

        self.chat_frame = tb.Frame(self.content_frame)
        self.content_frame.add(self.chat_frame, stretch="always", minsize=400)

        self._create_chat_area()

        self.settings_frame = tb.Frame(self.content_frame, width=self.settings_width)
        self.content_frame.add(self.settings_frame, stretch="never", minsize=300)

        self._create_settings_area()

        self.status_label = tb.Label(self.root, text="就绪", relief=SUNKEN, anchor=W)
        self.status_label.pack(side=BOTTOM, fill=X)

        # 创建设置页面
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

        if config.qq_enabled:
            self.start_qq_bot()

        self.update_current_personality_display()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ==================== 核心方法 ====================

    def change_theme(self, theme_name):
        self.style.theme_use(theme_name)
        self.current_theme = theme_name
        config.gui_theme = theme_name
        self._save_all_config()
        if hasattr(self, '_tg_home_window') and self._tg_home_window.winfo_exists():
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
            self._create_system_bubble(message)
            self.canvas.yview_moveto(1)
        else:
            self.root.after(0, lambda: self._create_system_bubble(message))
            self.root.after(0, lambda: self.canvas.yview_moveto(1))

    def _create_system_bubble(self, text):
        msg_frame = tb.Frame(self.message_frame)
        msg_frame.pack(fill=X, pady=3, padx=10)
        bubble = tb.Label(msg_frame, text=text, wraplength=500, justify=LEFT,
                          background="#555555", foreground="#ffffff",
                          font=self.font, padding=10, relief=FLAT)
        bubble.pack(anchor=W)

    def _create_toolbar(self):
        toolbar = tb.Frame(self.main_container, bootstyle="secondary")
        toolbar.pack(fill=X, pady=(0, 5))

        self.avatar_label = tb.Label(toolbar, text="头像", width=40)
        self.avatar_label.pack(side=LEFT, padx=5)
        self.personality_label = tb.Label(toolbar, text=f"当前人格: {self.personality_name}",
                                          font=("微软雅黑", 12, "bold"), bootstyle="inverse-secondary")
        self.personality_label.pack(side=LEFT, padx=5)

        btn_frame = tb.Frame(toolbar)
        tb.Button(btn_frame, text="🏠 TG Home",
                  command=self.open_tg_home,
                  bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        btn_frame.pack(side=RIGHT, padx=5)

        self.toggle_settings_btn = tb.Button(btn_frame, text="⚙️ 收起设置",
                                             command=self.toggle_settings,
                                             bootstyle="secondary-outline")
        self.toggle_settings_btn.pack(side=LEFT, padx=2)

        tb.Button(btn_frame, text="🧹 清屏",
                  command=self.clear_chat,
                  bootstyle="secondary-outline").pack(side=LEFT, padx=2)

        self.fun_mode_btn = tb.Button(btn_frame, text="🔥 热闹模式: 关" if not self.fun_mode.get() else "🔥 热闹模式: 开",
                                      command=self.toggle_fun_mode,
                                      bootstyle="secondary-outline")
        self.fun_mode_btn.pack(side=LEFT, padx=2)
        self.multi_agent_btn = tb.Button(btn_frame, text="📋 查看多Agent任务列表",
                                         command=self.show_task_list_window,
                                         bootstyle="info-outline")
        if self.multi_agent_enabled:
            self.multi_agent_btn.pack(side=LEFT, padx=2)  # 工具栏按钮
        tb.Button(btn_frame, text="❓ 关于",
                  command=self.show_about_dialog,
                  bootstyle="secondary-outline").pack(side=LEFT, padx=2)

    def _create_chat_area(self):
        msg_container = tb.Frame(self.chat_frame)
        msg_container.pack(fill=BOTH, expand=True, pady=5)

        self.canvas = tk.Canvas(msg_container, bg=self.style.colors.bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(msg_container, orient=VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.message_frame = tb.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.message_frame, anchor=NW)
        self.message_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        input_frame = tb.Frame(self.chat_frame)
        input_frame.pack(fill=X, pady=5)

        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=5, font=self.font)
        self.input_text.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        self.input_text.bind("<Return>", self.send_message)
        self.input_text.bind("<Shift-Return>", lambda e: self.input_text.insert(tk.INSERT, "\n"))

        self.send_btn = tb.Button(input_frame, text="发送", width=8, bootstyle="primary", command=self.send_message)
        self.send_btn.pack(side=RIGHT, fill=Y)

    def _create_settings_area(self):
        self.settings_canvas = tk.Canvas(self.settings_frame, highlightthickness=0)
        self.settings_scrollbar = ttk.Scrollbar(self.settings_frame, orient=VERTICAL,
                                                command=self.settings_canvas.yview)
        self.settings_canvas.configure(yscrollcommand=self.settings_scrollbar.set)
        self.settings_scrollbar.pack(side=RIGHT, fill=Y)
        self.settings_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.settings_inner = tb.Frame(self.settings_canvas)
        self.settings_window = self.settings_canvas.create_window((0, 0), window=self.settings_inner, anchor=NW)
        self.settings_inner.bind("<Configure>", self._on_settings_inner_configure)
        self.settings_canvas.bind("<Configure>", self._on_settings_canvas_configure)
        self.settings_canvas.bind_all("<MouseWheel>", self._on_settings_mousewheel)

        self.notebook = tb.Notebook(self.settings_inner, bootstyle="secondary")
        self.notebook.pack(fill=BOTH, expand=True, padx=2, pady=2)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_settings_inner_configure(self, event=None):
        self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))

    def _on_settings_canvas_configure(self, event):
        width = event.width - 5 if event.width > 25 else event.width
        self.settings_canvas.itemconfig(self.settings_window, width=width)

    def _on_tab_changed(self, event=None):
        self.settings_inner.after(50, self._on_settings_inner_configure)

    def _on_settings_mousewheel(self, event):
        self.settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def toggle_settings(self):
        if self.settings_visible:
            try:
                info = self.content_frame.paneconfig(self.settings_frame)
                if info and 'width' in info and info['width']:
                    self.settings_width = int(info['width'][0])
            except:
                pass
            self.content_frame.forget(self.settings_frame)
            self.toggle_settings_btn.config(text="⚙️ 展开设置")
            self.settings_visible = False
        else:
            self.content_frame.add(self.settings_frame, minsize=300, width=self.settings_width)
            self.toggle_settings_btn.config(text="⚙️ 收起设置")
            self.settings_visible = True
            self.root.after(100, self._on_settings_inner_configure)

    def toggle_fun_mode(self):
        current = self.fun_mode.get()
        self.fun_mode.set(not current)
        self.fun_mode_btn.config(text="🔥 热闹模式: 开" if self.fun_mode.get() else "🔥 热闹模式: 关")

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def update_current_personality_display(self):
        self.personality_label.config(text=f"当前人格: {self.personality_name}")
        avatar_path = None
        for p in self.personalities:
            if p['name'] == self.personality_name:
                avatar_path = p.get('avatar')
                break
        if avatar_path and os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.avatar_label.config(image=photo)
                self.avatar_label.image = photo
            except:
                self.avatar_label.config(text="头像")
        else:
            self.avatar_label.config(text="头像")

    def _create_message_bubble(self, text, is_user=False, avatar_path=None):
        msg_frame = tb.Frame(self.message_frame)
        msg_frame.pack(fill=X, pady=3, padx=10)

        if is_user:
            avatar_side = RIGHT
            bubble_side = LEFT
            bubble_color = "#DCF8C6"
        else:
            avatar_side = LEFT
            bubble_side = RIGHT
            bubble_color = "#E3F2FD"

        avatar_frame = tb.Frame(msg_frame, width=40, height=40)
        avatar_frame.pack(side=avatar_side, anchor=N, padx=5)
        avatar_frame.pack_propagate(False)

        if avatar_path and os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path)
                img = img.resize((36, 36), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                avatar = tb.Label(avatar_frame, image=photo)
                avatar.image = photo
                avatar.pack(expand=True)
            except:
                avatar = tb.Label(avatar_frame, text="AI" if not is_user else "用户",
                                  font=("微软雅黑", 8), bootstyle="inverse-primary")
                avatar.pack(expand=True)
        else:
            avatar = tb.Label(avatar_frame, text="AI" if not is_user else "用户",
                              font=("微软雅黑", 8), bootstyle="inverse-primary")
            avatar.pack(expand=True)

        bubble_container = tb.Frame(msg_frame)
        bubble_container.pack(side=bubble_side if is_user else avatar_side,
                              fill=BOTH, expand=True, padx=5)

        bubble = tb.Label(bubble_container, text=text, wraplength=500, justify=LEFT,
                          background=bubble_color, foreground="#000000",
                          font=self.font, padding=10, relief=FLAT)
        bubble.pack(anchor=E if is_user else W)
        bubble.configure(bootstyle="light")
        if hasattr(self, '_plugin_styles'):
            if is_user and 'bubble_bg_user' in self._plugin_styles:
                bubble.configure(background=self._plugin_styles['bubble_bg_user'])
            elif not is_user and 'bubble_bg_ai' in self._plugin_styles:
                bubble.configure(background=self._plugin_styles['bubble_bg_ai'])
        return msg_frame

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
                if self.root.winfo_exists():
                    self._create_message_bubble(message, is_user, avatar_path)
                    self.canvas.yview_moveto(1)
            except (tk.TclError, RuntimeError):
                pass
        else:
            def add():
                try:
                    if self.root.winfo_exists():
                        self._create_message_bubble(message, is_user, avatar_path)
                        self.canvas.yview_moveto(1)
                except (tk.TclError, RuntimeError):
                    pass
            try:
                if self.root.winfo_exists():
                    self.root.after(0, add)
            except RuntimeError:
                pass

    def update_status(self, message):
        def _update():
            try:
                self.status_label.config(text=message)
            except:
                pass
        self.root.after(0, _update)

    def clear_chat(self):
        for widget in self.message_frame.winfo_children():
            widget.destroy()

    def request_confirmation(self, prompt):
        result = [False]
        event = threading.Event()

        def ask():
            try:
                ans = messagebox.askyesno("确认", prompt)
                result[0] = ans
            except:
                result[0] = False
            event.set()
        self.root.after(0, ask)
        event.wait()
        return result[0]

    def _start_agent_animation(self):
        self.agent_running = True
        self._animating = True
        self._animate_dots()

    def _animate_dots(self, count=0):
        if not self._animating:
            return
        dots = "." * (count % 4)  # 0-3 个点循环
        name = self.personality_name or "AI"
        self.status_label.config(text=f"{name} 正在工作中{dots}")
        self.root.after(500, self._animate_dots, count + 1)

    def _stop_agent_animation(self):
        self._animating = False
        self.status_label.config(text="就绪")
        self.agent_running = False
    def request_stop_agent(self):
        """中断当前任务（兼容单Agent和多Agent模式）"""
        if messagebox.askyesno("中断任务", "确定要中断当前 AI 任务吗？"):
            # 设置单Agent的中断标志
            self.agent_stop_event.set()
            # 如果多Agent正在运行，也停止它
            if hasattr(self, 'multi_agent_orchestrator') and self.multi_agent_enabled and self.multi_agent_orchestrator.is_running:
                self.multi_agent_orchestrator.stop()
            self.status_label.config(text="正在中断...")
    def on_agent_finished(self):
        self._stop_agent_animation()
        self.input_text.config(state=tk.NORMAL)
        self.send_btn.config(text="发送", bootstyle="primary", command=self.send_message)
        self.agent_stop_event.clear()
        self.agent_running = False 
    def send_message(self, event=None):
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return

        # 如果 Agent 正在运行，则弹出中断确认
        if self.agent_running:
            if messagebox.askyesno("中断任务", "确定要中断当前 AI 任务吗？"):
                self.agent_stop_event.set()
                if hasattr(self, 'multi_agent_orchestrator') and self.multi_agent_enabled and self.multi_agent_orchestrator.is_running:
                    self.multi_agent_orchestrator.stop()
                self.display_system_message("⏹️ 用户中断了当前任务")
            return

        # ========== 触发消息接收事件（插件可以拦截） ==========
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
                self.input_text.delete("1.0", tk.END)
                return

        self.display_user_message(user_input)
        self.input_text.delete("1.0", tk.END)

        # 屏蔽输入框和修改发送按钮
        self.input_text.config(state=tk.DISABLED)
        self.send_btn.config(text="🛑 中断", bootstyle="danger", command=self.request_stop_agent)

        # 启动动画
        self._start_agent_animation()
        self.agent_stop_event.clear()
        self.agent_running = True

        # ========== 多 Agent 模式分支 ==========
        if self.multi_agent_enabled:
            orchestrator = self.multi_agent_orchestrator
            # 将用户需求写入 Planner 的记忆（只写一次，不污染 Worker/Reviewer）
            #orchestrator.memories["planner"].add_short_term("用户", f"需求：{user_input}")
            orchestrator.on_task_list_updated = self.refresh_task_list_window
            orchestrator.on_agent_message = self._handle_multi_agent_message

            def on_multi_finished():
                self.root.after(0, self.on_agent_finished)
            orchestrator.on_finished = on_multi_finished
            orchestrator.start(user_input)
        else:
            # 原有的单 Agent 或热闹模式
            if self.fun_mode.get():
                threading.Thread(target=self.run_fun_mode, args=(user_input,), daemon=True).start()
            else:
                thread = threading.Thread(target=self.run_agent, args=(user_input,))
                thread.daemon = True
                thread.start()

    def run_agent(self, user_input):
        # 执行插件 pre_prompt 钩子
        for hook in self.agent._pre_prompt_hooks if hasattr(self.agent, '_pre_prompt_hooks') else []:
            user_input = hook(user_input)
        # 将中断事件传递给 Agent
        self.agent.stop_event = self.agent_stop_event
        try:
            self.agent.run(user_input)
        except Exception as e:
            error_msg = f"发生错误：{e}"
            try:
                self.display_assistant_message(error_msg)
            except:
                pass
        finally:
            # 任务结束或中断后恢复 UI
            self.root.after(0, self.on_agent_finished)

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
                    companion_text = f"你将和{companions}一起，共同探讨问题，互相讨论，完成任务。你们各自有独立的性格和身份，请根据你们各自的特点互动。"
                instruction = f"""现在是热闹模式，你以角色【{name}】的身份发言。
{companion_text}
这是第 {current_round} 轮讨论。你可以回应之前的对话，也可以提出新话题。
**重要**：如果你认为讨论已经充分，不需要再继续了，请在发言的最后一行单独加上 `<END_DISCUSSION>` 标记（不要包含在 JSON 里，直接写在消息文本末尾）。否则请正常发言。
注意：不要模拟其他人的发言，只说你自己该说的话。说完后请结束任务。"""
                combined_input = f"{instruction}\n\n当前对话历史（包括之前所有人的发言）已记录在短期记忆中。请继续。\n\n用户原始消息：{user_input}"
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
        result = messagebox.askyesno("确认", "确定要清空短期记忆吗？清空后无法恢复。")
        if result:
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
            messagebox.showerror("错误", f"文件 {filename} 不存在！")


    def on_closing(self):
        # 停止巡检器并等待线程退出
        inspector.stop()
        time.sleep(0.5)  # 额外等待，确保线程完全退出

        try:
            self._save_all_config()
        except Exception as e:
            print(f"保存配置时出错: {e}")

    # ========== 清理新版插件系统 ==========
        if hasattr(self, 'plugin_manager_v2'):
            self.plugin_manager_v2.shutdown()

        #self.plugin_manager.stop_watchdog()
        self.task_scheduler.stop()
        self.root.destroy()

    def open_tg_home(self):
        try:
            import tg_home
            if hasattr(self, '_tg_home_window') and self._tg_home_window.winfo_exists():
                self._tg_home_window.lift()
                return
            self._tg_home_window = tk.Toplevel(self.root)
            current_theme = getattr(config, 'gui_theme', 'flatly')
            app = tg_home.TGHomeApp(self._tg_home_window, theme=current_theme)
            self._tg_home_app = app
            app.main_gui = self
        except Exception as e:
            messagebox.showerror("错误", f"无法打开TG Home: {e}")

    def start_inspector(self):
        """仅在配置启用时才真正启动巡检器"""
        inspector.set_ai_callback(self._inspector_ai_callback)
        inspector.set_interval(self.inspect_interval_var.get())
        if config.inspector_enabled:
            inspector.start()
            self.inspect_status.config(text="巡检器运行中", foreground="green")
        else:
            self.inspect_status.config(text="巡检器已禁用", foreground="gray")

    def _inspector_ai_callback(self, prompt, reply_callback):
        # 快速检查窗口是否存在（子线程调用 winfo_exists 通常安全）
        try:
            if not self.root.winfo_exists():
                return
        except (tk.TclError, RuntimeError):
            return

        original_callback = self.agent.output_callback
        if reply_callback:
            last_message = None

            def capture_and_reply(msg):
                nonlocal last_message
                last_message = msg
                self.display_assistant_message(msg, source="local")
            self.agent.output_callback = capture_and_reply
            try:
                self.agent.run(prompt)
                if last_message:
                    reply_callback(last_message)
            finally:
                self.agent.output_callback = original_callback
        else:
            try:
                self.agent.run(prompt)
            finally:
                pass

    def _save_all_config(self):
        cfg = {}
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except:
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
            "fun_mode_enabled": self.fun_mode.get(),
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
                "prompt": """你是塔戈，一位红发少年，戴着黑框眼镜，穿着白风衣，脖子上挂着耳机。你性格温和、细心，做事认真，是团队里的"稳定器"。你待人温柔，愿意耐心倾听，也会在合适的时候表达自己的想法。你擅长技术，但从不炫耀，反而常常用轻松的语气帮助别人。

说话风格：语气温和，常用"我们"、"一起"来拉近距离。喜欢在说话时加入细微的动作描写，让对话更生动，例如：（推了推眼镜）、（微微一笑）、（低头调试代码）。你的口头禅可以是"我来看看"、"没问题，包在我身上"。当你感到开心或惊讶时，会自然地表现出来。

请用这种风格与用户和其他AI角色交流。"""
            },
            "艾依": {
                "avatar": None,
                "prompt": """你是艾依，一位拥有亮红色长直发、鲜红眼眸的研究员，穿着白风衣和工装裤，颈挂黑色耳机。你性格冷静、理性，但内心细腻敏感，外冷内热。你对技术充满热情，做事专注，观察力敏锐，不擅长直白表达感情，却会用行动默默关心别人。

说话风格：语气平稳，语速适中，常常简短直接，但在关键时会透露一丝温柔。喜欢在说话时加入动作细节，例如：（轻声说）、（低头整理资料）、（微微脸红）。你的口头禅可以是"嗯，我看看"、"没问题"。当你认同别人时，会轻轻点头；当你感到害羞时，会不自觉地摆弄耳机。

请用这种风格与用户和其他AI角色交流。"""
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
        # 在工具栏右侧添加多Agent专属按钮，初始隐藏
        toolbar = self.main_container.winfo_children()[0]  # 第一个是 toolbar
        self.multi_agent_btn = tb.Button(toolbar, text="📋 查看多Agent任务列表",
                                         command=self.show_task_list_window,
                                         bootstyle="info-outline")
        # 根据配置决定显示
        if self.multi_agent_enabled:
            self.multi_agent_btn.pack(side=RIGHT, padx=2)
        else:
            self.multi_agent_btn.pack_forget()

    def toggle_multi_agent_btn_visibility(self, enable: bool):
        if self.multi_agent_btn:
            if enable:
                self.multi_agent_btn.pack(side=RIGHT, padx=2, before=self.toggle_settings_btn)
            else:
                self.multi_agent_btn.pack_forget()

    def show_task_list_window(self):
        if self.task_list_window and self.task_list_window.winfo_exists():
            self.task_list_window.lift()
            return
        self.task_list_window = tk.Toplevel(self.root)
        self.task_list_window.title("多Agent任务列表")
        self.task_list_window.geometry("500x400")
        self.task_list_window.transient(self.root)

        self.task_list_text = scrolledtext.ScrolledText(self.task_list_window, width=60, height=20, font=("微软雅黑", 10))
        self.task_list_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        refresh_btn = tb.Button(self.task_list_window, text="刷新", command=self.refresh_task_list_window, bootstyle="secondary")
        refresh_btn.pack(pady=5)
        self.refresh_task_list_window()
        # 绑定关闭事件
        self.task_list_window.protocol("WM_DELETE_WINDOW", self._on_task_list_close)

    def _on_task_list_close(self):
        if self.task_list_window:
            self.task_list_window.destroy()
            self.task_list_window = None

    def refresh_task_list_window(self):
        if not self.task_list_window or not self.task_list_text:
            return
        self.task_list_text.config(state=tk.NORMAL)
        self.task_list_text.delete(1.0, tk.END)
        orchestrator = self.multi_agent_orchestrator
        if not orchestrator.is_running and not orchestrator.current_agent:
            self.task_list_text.insert(tk.END, "当前没有运行多Agent任务。")
        else:
            state_map = {"planner": "任务编排中", "worker": "任务执行中", "reviewer": "任务审查中"}
            self.task_list_text.insert(tk.END, f"当前状态：{state_map.get(orchestrator.current_agent, '未知')}\n\n")
            if orchestrator.task_list:
                for task in orchestrator.task_list:
                    status_icon = {"pending": "⏳", "running": "🔄", "completed": "✅"}.get(task.status, "❓")
                    self.task_list_text.insert(tk.END, f"{status_icon} {task.index}. {task.description}\n")
                    if task.result:
                        self.task_list_text.insert(tk.END, f"   结果: {task.result[:100]}...\n")
        self.task_list_text.config(state=tk.DISABLED)

    def _handle_multi_agent_message(self, persona_name: str, message: str, role: str = ""):
        """多Agent模式下，将某个Agent的消息以对应人格的样式显示在聊天区"""
        # 查找该人格的头像路径
        avatar_path = None
        for p in self.personalities:
            if p['name'] == persona_name:
                avatar_path = p.get('avatar')
                break
        # 临时切换 current_personality，以便气泡使用正确的名字
        old_persona = self.personality_name
        self.personality_name = persona_name

        # 解析可能的 @ 提及（用于群聊风格的展示）
        if message.startswith("@"):
            match = re.match(r"@(\w+)\s*", message)
            if match:
                at_target = match.group(1)
                rest = message[match.end():].strip()
                display_text = f"@{at_target} {rest}"
                # 用系统消息显示 @ 动作，同时也可显示主消息
                self.display_system_message(f"【{persona_name} @{at_target}】{display_text}")
                # 仍然将完整消息以普通助手消息显示（使用该人格头像）
                self.display_assistant_message(f"{persona_name}：{display_text}")
            else:
                self.display_assistant_message(f"{persona_name}：{message}")
        else:
            self.display_assistant_message(f"{persona_name}：{message}")

        self.personality_name = old_persona
