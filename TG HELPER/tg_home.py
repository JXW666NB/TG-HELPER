# -*- coding: utf-8 -*-
"""
TG Home - 物联网设备管理
可独立运行，也可从主 GUI 中打开
"""
import json
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import scrolledtext
from datetime import datetime

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
    # 创建一个简单的配置对象用于独立运行
    class DummyConfig:
        gui_theme = "flatly"
        napcat_http_url = ""
        napcat_access_token = ""
        qq_enabled = False
        qq_bot_uin = ""
        qq_whitelist = ""
    config = DummyConfig()

class TGHomeApp:
    def __init__(self, root, theme=None):
        self.root = root
        self.root.title("TG Home - 智能设备管理")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        if theme is None:
            theme = self._load_theme_from_config()
        self.current_theme = theme
        self.style = tb.Style(theme=theme)
        self.style.theme_use()

        self.current_pages = {"devices": 0, "sensors": 0, "triggers": 0}
        self.cards_per_page = 25

        self.main_frame = tb.Frame(root)
        self.main_frame.pack(fill=BOTH, expand=True)

        self._create_toolbar()
        self._create_notebook()
        self._refresh_all()
        self._init_callbacks()

        if not inspector._running:
            inspector.set_ai_callback(self._dummy_ai_callback)
            inspector.set_interval(3600)
            inspector.start()

        self.current_pages = {"devices": 0, "sensors": 0, "triggers": 0}
        self.cards_per_page = 25

        self.main_frame = tb.Frame(root)
        self.main_frame.pack(fill=BOTH, expand=True)

    def _load_theme_from_config(self):
        """从配置文件读取主题，若不存在则返回默认值"""
        config_file = os.path.expanduser("~/.agent_config.json")
        default_theme = "flatly"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("gui_theme", default_theme)
            except:
                pass
        return default_theme

    def _init_callbacks(self):
        """确保 iot_manager 的回调不为空，避免独立运行时出错"""
        # 直接设置占位回调，覆盖可能为空的回调
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
        self.style.theme_use(theme_name)
        # 强制刷新所有数据面板
        self._refresh_all()
        # 如果是日志选项卡，也刷新表格
        if hasattr(self, 'log_tree'):
            self.refresh_log_table()
    def _create_toolbar(self):
        toolbar = tb.Frame(self.main_frame, bootstyle="secondary")
        toolbar.pack(fill=X, padx=5, pady=5)

        btn_group = tb.Frame(toolbar)
        btn_group.pack(side=LEFT)

        tb.Button(btn_group, text="➕ 添加设备", command=self.add_device_wizard,
                  bootstyle="success-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_group, text="📡 添加传感器", command=self.add_sensor_wizard,
                  bootstyle="info-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_group, text="⚡ 添加触发器", command=self.add_trigger_wizard,
                  bootstyle="warning-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_group, text="🔄 刷新", command=self._refresh_all,
                  bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_group, text="📤 导出配置", command=self.export_config,
                  bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_group, text="📥 导入配置", command=self.import_config,
                  bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_group, text="🗑️ 重置配置", command=self.reset_config,
                  bootstyle="danger-outline").pack(side=LEFT, padx=2)
        self.status_label = tb.Label(toolbar, text="就绪", bootstyle="inverse-secondary")
        self.status_label.pack(side=RIGHT, padx=5)

    def _create_notebook(self):
        self.notebook = tb.Notebook(self.main_frame, bootstyle="secondary")
        self.notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.devices_frame = tb.Frame(self.notebook)
        self.notebook.add(self.devices_frame, text="📱 设备")
        self._create_card_area(self.devices_frame, "devices")

        self.sensors_frame = tb.Frame(self.notebook)
        self.notebook.add(self.sensors_frame, text="📡 传感器")
        self._create_card_area(self.sensors_frame, "sensors")

        self.triggers_frame = tb.Frame(self.notebook)
        self.notebook.add(self.triggers_frame, text="⚡ 触发器")
        self._create_card_area(self.triggers_frame, "triggers")

        self.create_log_tab()
        self.create_active_intelligence_tab()
        self.create_servers_tab()
    def _create_card_area(self, parent, category):
        nav_frame = tb.Frame(parent)
        nav_frame.pack(fill=X, pady=5)

        prev_btn = tb.Button(nav_frame, text="◀ 上一页",
                             command=lambda: self._prev_page(category),
                             state=DISABLED, bootstyle="secondary-outline")
        prev_btn.pack(side=LEFT, padx=10)

        page_label = tb.Label(nav_frame, text="第 1 页", font=("微软雅黑", 10),
                              bootstyle="inverse-secondary")
        page_label.pack(side=LEFT, expand=True)

        next_btn = tb.Button(nav_frame, text="下一页 ▶",
                             command=lambda: self._next_page(category),
                             bootstyle="secondary-outline")
        next_btn.pack(side=RIGHT, padx=10)

        setattr(self, f"{category}_prev_btn", prev_btn)
        setattr(self, f"{category}_next_btn", next_btn)
        setattr(self, f"{category}_page_label", page_label)

        canvas = tk.Canvas(parent, bg=self.style.colors.bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=5)

        container = tb.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=container, anchor=NW)

        container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        setattr(self, f"{category}_canvas", canvas)
        setattr(self, f"{category}_container", container)
    def apply_theme(self, theme_name):
        """动态切换主题"""
        self.style.theme_use(theme_name)
    def _refresh_all(self):
        self._refresh_devices()
        self._refresh_sensors()
        self._refresh_triggers()

    def _refresh_devices(self):
        self._refresh_category("devices", iot_manager.devices.values(), self._create_device_card)

    def _refresh_sensors(self):
        self._refresh_category("sensors", iot_manager.sensors.values(), self._create_sensor_card)

    def _refresh_triggers(self):
        self._refresh_category("triggers", iot_manager.triggers.values(), self._create_trigger_card)

    def _refresh_category(self, category, items, card_creator):
        container = getattr(self, f"{category}_container")
        for widget in container.winfo_children():
            widget.destroy()

        total = len(items)
        start = self.current_pages[category] * self.cards_per_page
        end = min(start + self.cards_per_page, total)
        page_items = list(items)[start:end]

        cols = 5
        for idx, item in enumerate(page_items):
            row = idx // cols
            col = idx % cols
            card = card_creator(item, category)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            container.columnconfigure(col, weight=1)
        for i in range((len(page_items) + cols - 1) // cols):
            container.rowconfigure(i, weight=1)

        prev_btn = getattr(self, f"{category}_prev_btn")
        next_btn = getattr(self, f"{category}_next_btn")
        page_label = getattr(self, f"{category}_page_label")
        prev_btn.config(state=NORMAL if self.current_pages[category] > 0 else DISABLED)
        next_btn.config(state=NORMAL if end < total else DISABLED)
        page_label.config(text=f"第 {self.current_pages[category]+1} 页")

    def _prev_page(self, category):
        if self.current_pages[category] > 0:
            self.current_pages[category] -= 1
            getattr(self, f"_refresh_{category}")()
            canvas = getattr(self, f"{category}_canvas")
            canvas.yview_moveto(0)

    def _next_page(self, category):
        total = len(getattr(iot_manager, category))
        if (self.current_pages[category] + 1) * self.cards_per_page < total:
            self.current_pages[category] += 1
            getattr(self, f"_refresh_{category}")()
            canvas = getattr(self, f"{category}_canvas")
            canvas.yview_moveto(0)

    # -------------------- 卡片创建 --------------------
    def _create_device_card(self, dev, category):
        card = tb.Frame(getattr(self, f"{category}_container"), bootstyle="secondary", relief=tk.RAISED, borderwidth=1)
        card.columnconfigure(0, weight=1)

        icon_path = os.path.join("icon", dev.icon) if dev.icon else None
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = tb.Label(card, image=photo)
                icon_label.image = photo
                icon_label.grid(row=0, column=0, pady=10)
            except:
                self._default_icon(card)
        else:
            self._default_icon(card)

        tb.Label(card, text=dev.name, font=("微软雅黑", 11, "bold"),
                 bootstyle="inverse-secondary").grid(row=1, column=0, pady=5)

        if dev.device_type == 'bool':
            btn_frame = tb.Frame(card)
            btn_frame.grid(row=2, column=0, pady=5)
            tb.Button(btn_frame, text="ON", bootstyle="success",
                      command=lambda: self._control_device(dev.name, "on")).pack(side=LEFT, padx=2)
            tb.Button(btn_frame, text="OFF", bootstyle="danger",
                      command=lambda: self._control_device(dev.name, "off")).pack(side=LEFT, padx=2)
        else:
            for i, preset in enumerate(dev.presets[:2]):
                btn = tb.Button(card, text=preset['name'], bootstyle="primary-outline",
                                command=lambda p=preset['name']: self._control_device(dev.name, p))
                btn.grid(row=2+i, column=0, pady=2, sticky="ew")
            if len(dev.presets) > 2:
                more_btn = tb.Button(card, text="更多...", bootstyle="secondary-outline",
                                     command=lambda: self._show_preset_menu(dev))
                more_btn.grid(row=4, column=0, pady=2, sticky="ew")

        del_btn = tb.Button(card, text="删除", bootstyle="danger-outline",
                            command=lambda: self._delete_device(dev.name))
        del_btn.grid(row=5, column=0, pady=10, sticky="ew")
        return card

    def _create_sensor_card(self, sensor, category):
        card = tb.Frame(getattr(self, f"{category}_container"), bootstyle="secondary", relief=tk.RAISED, borderwidth=1)
        card.columnconfigure(0, weight=1)

        icon_path = os.path.join("icon", sensor.icon) if sensor.icon else None
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = tb.Label(card, image=photo)
                icon_label.image = photo
                icon_label.grid(row=0, column=0, pady=10)
            except:
                self._default_icon(card)
        else:
            self._default_icon(card)

        tb.Label(card, text=sensor.name, font=("微软雅黑", 11, "bold"),
                 bootstyle="inverse-secondary").grid(row=1, column=0, pady=5)

        info_text = f"协议: {sensor.protocol}\nIP: {sensor.params.get('ip', '')}\n端口: {sensor.params.get('port', '')}"
        tb.Label(card, text=info_text, font=("微软雅黑", 8),
                 bootstyle="secondary").grid(row=2, column=0, pady=5)

        del_btn = tb.Button(card, text="删除", bootstyle="danger-outline",
                            command=lambda: self._delete_sensor(sensor.name))
        del_btn.grid(row=3, column=0, pady=10, sticky="ew")
        return card

    def _create_trigger_card(self, trigger, category):
        card = tb.Frame(getattr(self, f"{category}_container"), bootstyle="secondary", relief=tk.RAISED, borderwidth=1)
        card.columnconfigure(0, weight=1)

        tb.Label(card, text="⚡", font=("Segoe UI", 36)).grid(row=0, column=0, pady=10)

        tb.Label(card, text=trigger.name, font=("微软雅黑", 11, "bold"),
                 bootstyle="inverse-secondary").grid(row=1, column=0, pady=5)

        # 显示任务列表摘要
        tasks = trigger.tasks
        task_summary = "\n".join([f"- {self._task_desc(t)}" for t in tasks[:3]])
        if len(tasks) > 3:
            task_summary += f"\n... 共{len(tasks)}个任务"
        tb.Label(card, text=task_summary, font=("微软雅黑", 8),
                 bootstyle="secondary", wraplength=150).grid(row=2, column=0, pady=5)

        # 编辑按钮
        edit_btn = tb.Button(card, text="✏️ 编辑任务", bootstyle="primary-outline",
                             command=lambda: self._edit_trigger_tasks(trigger))
        edit_btn.grid(row=3, column=0, pady=2, sticky="ew")

        # 启用/禁用按钮
        def toggle_enable():
            trigger.enabled = not trigger.enabled
            iot_manager._save_triggers()
            self._refresh_triggers()
        status_text = "✅ 已启用" if trigger.enabled else "❌ 已禁用"
        status_btn = tb.Button(card, text=status_text, bootstyle="success-outline" if trigger.enabled else "secondary-outline",
                               command=toggle_enable)
        status_btn.grid(row=4, column=0, pady=2, sticky="ew")

        del_btn = tb.Button(card, text="删除", bootstyle="danger-outline",
                            command=lambda: self._delete_trigger(trigger.name))
        del_btn.grid(row=5, column=0, pady=10, sticky="ew")
        return card

    def _task_desc(self, task):
        ttype = task.get('type')
        if ttype == 'ai_notify':
            prompt = task.get('prompt', '原始消息')
            send_reply = task.get('send_reply', False)
            reply_flag = " 📤回传" if send_reply else ""
            return f"🤖 通知AI: {prompt}{reply_flag}"
        elif ttype in ('control_device', 'control_bool_device'):  # 兼容两种类型
            return f"📟 控制设备 {task.get('device_name')} → {task.get('command')}"
        elif ttype == 'qq_notify':
            target_type = task.get('target_type')
            target_display = "私聊" if target_type == "private" else "群聊"
            return f"💬 QQ{target_display} {task.get('target_id')} → {task.get('content', '')[:20]}"
        return "未知任务"

    def _default_icon(self, parent):
        tb.Label(parent, text="🔌", font=("Segoe UI", 36)).grid(row=0, column=0, pady=10)

    # -------------------- 控制与删除 --------------------
    def _control_device(self, dev_name, command):
        def task():
            result = iot_manager.send_to_device(dev_name, command)
            self.root.after(0, lambda: self.status_label.config(text=result))
        threading.Thread(target=task, daemon=True).start()

    def _delete_device(self, dev_name):
        if messagebox.askyesno("确认", f"确定要删除设备 {dev_name} 吗？"):
            iot_manager.remove_device(dev_name)
            self._refresh_devices()

    def _delete_sensor(self, sensor_name):
        if messagebox.askyesno("确认", f"确定要删除传感器 {sensor_name} 吗？"):
            iot_manager.remove_sensor(sensor_name)
            self._refresh_sensors()

    def _delete_trigger(self, trigger_name):
        if messagebox.askyesno("确认", f"确定要删除触发器 {trigger_name} 吗？"):
            iot_manager.remove_trigger(trigger_name)
            self._refresh_triggers()

    def _show_preset_menu(self, dev):
        menu = tk.Menu(self.root, tearoff=0)
        for preset in dev.presets:
            menu.add_command(label=preset['name'],
                             command=lambda p=preset['name']: self._control_device(dev.name, p))
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

    # -------------------- 添加设备向导 --------------------
    def add_device_wizard(self):
        wizard = tb.Toplevel(self.root)
        wizard.title("添加物联网设备")
        wizard.geometry("550x600")
        wizard.transient(self.root)
        wizard.grab_set()

        frame1 = tb.Frame(wizard, padding=10)
        frame1.pack(fill=BOTH, expand=True)

        tb.Label(frame1, text="设备名称:", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=W, pady=5)
        name_entry = tb.Entry(frame1, width=30)
        name_entry.grid(row=0, column=1, sticky=EW, pady=5)

        tb.Label(frame1, text="通信协议:", font=("微软雅黑", 10)).grid(row=1, column=0, sticky=W, pady=5)
        protocol_var = tk.StringVar(value="udp")
        proto_combo = tb.Combobox(frame1, textvariable=protocol_var, values=["udp", "tcp", "mqtt"],
                                   state="readonly")
        proto_combo.grid(row=1, column=1, sticky=EW, pady=5)

        params_frame = ttk.LabelFrame(frame1, text="通信参数", padding=5)
        params_frame.grid(row=2, column=0, columnspan=2, sticky=EW, pady=10)

        dynamic_widgets = {}

        def update_params(*args):
            for widget in params_frame.winfo_children():
                widget.destroy()
            dynamic_widgets.clear()
            proto = protocol_var.get()
            if proto in ("udp", "tcp"):
                tb.Label(params_frame, text="IP地址:").grid(row=0, column=0, sticky=W, pady=2)
                ip_entry = tb.Entry(params_frame)
                ip_entry.grid(row=0, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="端口:").grid(row=1, column=0, sticky=W, pady=2)
                port_entry = tb.Entry(params_frame)
                port_entry.grid(row=1, column=1, sticky=EW, pady=2)
                dynamic_widgets['ip'] = ip_entry
                dynamic_widgets['port'] = port_entry
            elif proto == "mqtt":
                tb.Label(params_frame, text="Broker地址:").grid(row=0, column=0, sticky=W, pady=2)
                broker_entry = tb.Entry(params_frame)
                broker_entry.grid(row=0, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="端口:").grid(row=1, column=0, sticky=W, pady=2)
                port_entry = tb.Entry(params_frame)
                port_entry.grid(row=1, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="Topic:").grid(row=2, column=0, sticky=W, pady=2)
                topic_entry = tb.Entry(params_frame)
                topic_entry.grid(row=2, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="用户名(可选):").grid(row=3, column=0, sticky=W, pady=2)
                mqtt_user_entry = tb.Entry(params_frame)
                mqtt_user_entry.grid(row=3, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="密码(可选):").grid(row=4, column=0, sticky=W, pady=2)
                mqtt_pass_entry = tb.Entry(params_frame, show="*")
                mqtt_pass_entry.grid(row=4, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="Client ID (可选):").grid(row=5, column=0, sticky=W, pady=2)
                mqtt_client_id_entry = tb.Entry(params_frame)
                mqtt_client_id_entry.grid(row=5, column=1, sticky=EW, pady=2)
                dynamic_widgets['broker'] = broker_entry
                dynamic_widgets['port'] = port_entry
                dynamic_widgets['topic'] = topic_entry
                dynamic_widgets['username'] = mqtt_user_entry
                dynamic_widgets['password'] = mqtt_pass_entry
                dynamic_widgets['client_id'] = mqtt_client_id_entry

        protocol_var.trace_add('write', update_params)
        update_params()

        def next_step():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("错误", "请输入设备名称")
                return
            proto = protocol_var.get()
            params = {}
            try:
                if proto in ("udp", "tcp"):
                    ip = dynamic_widgets['ip'].get().strip()
                    port = dynamic_widgets['port'].get().strip()
                    if not ip or not port:
                        messagebox.showerror("错误", "请填写IP和端口")
                        return
                    params = {"ip": ip, "port": int(port)}
                elif proto == "mqtt":
                    broker = dynamic_widgets['broker'].get().strip()
                    port = dynamic_widgets['port'].get().strip()
                    topic = dynamic_widgets['topic'].get().strip()
                    if not broker or not port or not topic:
                        messagebox.showerror("错误", "请填写Broker、端口和Topic")
                        return
                    params = {
                        "broker": broker,
                        "port": int(port),
                        "topic": topic,
                        "username": dynamic_widgets.get('username', tb.Entry()).get(),
                        "password": dynamic_widgets.get('password', tb.Entry()).get(),
                        "client_id": dynamic_widgets.get('client_id', tb.Entry()).get().strip()
                    }
            except ValueError:
                messagebox.showerror("错误", "端口必须为数字")
                return

            wizard.temp_data = {
                "name": name,
                "protocol": proto,
                "params": params
            }
            frame1.pack_forget()
            show_type_selection()

        tb.Button(frame1, text="下一步", command=next_step, bootstyle="primary").grid(row=3, column=0, columnspan=2, pady=10)

        def show_type_selection():
            frame2 = tb.Frame(wizard, padding=10)
            frame2.pack(fill=BOTH, expand=True)
            tb.Label(frame2, text="选择设备类型:", font=("微软雅黑", 11, "bold")).pack(anchor=W, pady=5)
            type_var = tk.StringVar(value="bool")
            tb.Radiobutton(frame2, text="布尔类 (开关)", variable=type_var, value="bool",
                           bootstyle="primary").pack(anchor=W, pady=2)
            tb.Radiobutton(frame2, text="复杂类 (多指令)", variable=type_var, value="complex",
                           bootstyle="primary").pack(anchor=W, pady=2)

            def next_type():
                dev_type = type_var.get()
                if dev_type == "bool":
                    show_bool_config()
                else:
                    show_complex_config()
                frame2.pack_forget()

            tb.Button(frame2, text="下一步", command=next_type, bootstyle="primary").pack(pady=10)

        def show_bool_config():
            frame3 = tb.Frame(wizard, padding=10)
            frame3.pack(fill=BOTH, expand=True)
            tb.Label(frame3, text="ON指令内容:").grid(row=0, column=0, sticky=W, pady=5)
            on_entry = tb.Entry(frame3, width=30)
            on_entry.grid(row=0, column=1, sticky=EW, pady=5)
            tb.Label(frame3, text="OFF指令内容:").grid(row=1, column=0, sticky=W, pady=5)
            off_entry = tb.Entry(frame3, width=30)
            off_entry.grid(row=1, column=1, sticky=EW, pady=5)

            def finish():
                data = wizard.temp_data
                data["device_type"] = "bool"
                data["on_msg"] = on_entry.get().strip() or "ON"
                data["off_msg"] = off_entry.get().strip() or "OFF"
                data["presets"] = []
                data["notes"] = ""
                data["icon"] = ""
                if iot_manager.add_device(data):
                    messagebox.showinfo("成功", f"设备 {data['name']} 已添加")
                    wizard.destroy()
                    self._refresh_devices()
                else:
                    messagebox.showerror("错误", "设备名称已存在")
            tb.Button(frame3, text="完成", command=finish, bootstyle="success").grid(row=2, column=0, columnspan=2, pady=10)

        def show_complex_config():
            frame3 = tb.Frame(wizard, padding=10)
            frame3.pack(fill=BOTH, expand=True)

            tb.Label(frame3, text="预设指令列表:", font=("微软雅黑", 10, "bold")).pack(anchor=W, pady=5)
            preset_listbox = tk.Listbox(frame3, height=5, bg=self.style.colors.bg, fg=self.style.colors.fg)
            preset_listbox.pack(fill=BOTH, expand=True, pady=5)

            presets = []

            def add_preset():
                add_win = tb.Toplevel(wizard)
                add_win.title("添加预设指令")
                add_win.geometry("400x250")
                add_win.transient(wizard)
                add_win.grab_set()
                tb.Label(add_win, text="指令名称:").pack(pady=5)
                name_entry = tb.Entry(add_win, width=30)
                name_entry.pack()
                tb.Label(add_win, text="指令内容:").pack(pady=5)
                msg_entry = tb.Entry(add_win, width=30)
                msg_entry.pack()
                def save():
                    name = name_entry.get().strip()
                    msg = msg_entry.get().strip()
                    if name and msg:
                        presets.append({"name": name, "msg": msg})
                        preset_listbox.insert(tk.END, f"{name} -> {msg}")
                        add_win.destroy()
                tb.Button(add_win, text="保存", command=save, bootstyle="success").pack(pady=10)

            tb.Button(frame3, text="➕ 添加指令", command=add_preset, bootstyle="success-outline").pack(anchor=W, pady=2)

            tb.Label(frame3, text="给AI的注意事项（可选）:").pack(anchor=W, pady=(10,0))
            notes_text = tk.Text(frame3, height=4, bg=self.style.colors.bg, fg=self.style.colors.fg)
            notes_text.pack(fill=X, pady=5)

            def finish():
                data = wizard.temp_data
                data["device_type"] = "complex"
                data["presets"] = presets
                data["notes"] = notes_text.get("1.0", tk.END).strip()
                data["icon"] = ""
                if iot_manager.add_device(data):
                    messagebox.showinfo("成功", f"设备 {data['name']} 已添加")
                    wizard.destroy()
                    self._refresh_devices()
                else:
                    messagebox.showerror("错误", "设备名称已存在")
            tb.Button(frame3, text="完成", command=finish, bootstyle="success").pack(pady=10)

    # -------------------- 添加传感器向导 --------------------
    def add_sensor_wizard(self):
        wizard = tb.Toplevel(self.root)
        wizard.title("添加传感器")
        wizard.geometry("500x500")
        wizard.transient(self.root)
        wizard.grab_set()

        frame = tb.Frame(wizard, padding=10)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="传感器名称:").grid(row=0, column=0, sticky=W, pady=5)
        name_entry = tb.Entry(frame, width=30)
        name_entry.grid(row=0, column=1, sticky=EW, pady=5)

        tb.Label(frame, text="协议:").grid(row=1, column=0, sticky=W, pady=5)
        proto_var = tk.StringVar(value="udp")
        proto_combo = tb.Combobox(frame, textvariable=proto_var, values=["udp", "tcp", "mqtt"],
                                   state="readonly")
        proto_combo.grid(row=1, column=1, sticky=EW, pady=5)

        params_frame = ttk.LabelFrame(frame, text="通信参数", padding=5)
        params_frame.grid(row=2, column=0, columnspan=2, sticky=EW, pady=10)

        dynamic_widgets = {}

        def update_params(*args):
            for widget in params_frame.winfo_children():
                widget.destroy()
            dynamic_widgets.clear()
            proto = proto_var.get()
            if proto == "udp":
                tb.Label(params_frame, text="监听IP (0.0.0.0):").grid(row=0, column=0, sticky=W, pady=2)
                ip_entry = tb.Entry(params_frame)
                ip_entry.grid(row=0, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="端口:").grid(row=1, column=0, sticky=W, pady=2)
                port_entry = tb.Entry(params_frame)
                port_entry.grid(row=1, column=1, sticky=EW, pady=2)
                dynamic_widgets['ip'] = ip_entry
                dynamic_widgets['port'] = port_entry
            elif proto == "tcp":
                tb.Label(params_frame, text="监听IP (0.0.0.0):").grid(row=0, column=0, sticky=W, pady=2)
                ip_entry = tb.Entry(params_frame)
                ip_entry.grid(row=0, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="端口:").grid(row=1, column=0, sticky=W, pady=2)
                port_entry = tb.Entry(params_frame)
                port_entry.grid(row=1, column=1, sticky=EW, pady=2)
                dynamic_widgets['ip'] = ip_entry
                dynamic_widgets['port'] = port_entry
            elif proto == "mqtt":
                tb.Label(params_frame, text="Broker地址:").grid(row=0, column=0, sticky=W, pady=2)
                broker_entry = tb.Entry(params_frame)
                broker_entry.grid(row=0, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="端口:").grid(row=1, column=0, sticky=W, pady=2)
                port_entry = tb.Entry(params_frame)
                port_entry.grid(row=1, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="Topic:").grid(row=2, column=0, sticky=W, pady=2)
                topic_entry = tb.Entry(params_frame)
                topic_entry.grid(row=2, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="用户名(可选):").grid(row=3, column=0, sticky=W, pady=2)
                user_entry = tb.Entry(params_frame)
                user_entry.grid(row=3, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="密码(可选):").grid(row=4, column=0, sticky=W, pady=2)
                pass_entry = tb.Entry(params_frame, show="*")
                pass_entry.grid(row=4, column=1, sticky=EW, pady=2)
                tb.Label(params_frame, text="Client ID (私钥):").grid(row=5, column=0, sticky=W, pady=2)
                client_id_entry = tb.Entry(params_frame)
                client_id_entry.grid(row=5, column=1, sticky=EW, pady=2)
                dynamic_widgets['client_id'] = client_id_entry
                dynamic_widgets['broker'] = broker_entry
                dynamic_widgets['port'] = port_entry
                dynamic_widgets['topic'] = topic_entry
                dynamic_widgets['username'] = user_entry
                dynamic_widgets['password'] = pass_entry

        proto_var.trace_add('write', update_params)
        update_params()

        def finish():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("错误", "请输入传感器名称")
                return
            proto = proto_var.get()
            params = {}
            try:
                if proto in ("udp", "tcp"):
                    ip = dynamic_widgets['ip'].get().strip() or "0.0.0.0"
                    if ip == '255.255.255.255':
                        if not messagebox.askyesno("提示", "广播地址不能监听，是否改为 0.0.0.0？"):
                            return
                        ip = '0.0.0.0'
                    port = int(dynamic_widgets['port'].get().strip())
                    params = {"ip": ip, "port": port}
                elif proto == "mqtt":
                    broker = dynamic_widgets['broker'].get().strip()
                    port = int(dynamic_widgets['port'].get().strip())
                    topic = dynamic_widgets['topic'].get().strip()
                    if not broker or not topic:
                        messagebox.showerror("错误", "请填写 Broker 和 Topic")
                        return
                    params = {
                        "broker": broker,
                        "port": port,
                        "topic": topic,
                        "username": dynamic_widgets.get('username', tb.Entry()).get(),
                        "password": dynamic_widgets.get('password', tb.Entry()).get(),
                        "client_id": dynamic_widgets.get('client_id', tb.Entry()).get().strip()
                    }
            except ValueError:
                messagebox.showerror("错误", "端口必须为数字")
                return
            data = {
                "name": name,
                "protocol": proto,
                "params": params,
                "icon": ""
            }
            if iot_manager.add_sensor(data):
                messagebox.showinfo("成功", f"传感器 {name} 已添加")
                wizard.destroy()
                self._refresh_sensors()
            else:
                messagebox.showerror("错误", "传感器名称已存在")

        tb.Button(frame, text="完成", command=finish, bootstyle="success").grid(row=3, column=0, columnspan=2, pady=10)

    # -------------------- 添加触发器向导 --------------------
    def add_trigger_wizard(self):
        win = tb.Toplevel(self.root)
        win.title("添加触发器")
        win.geometry("801x309")
        win.transient(self.root)
        win.grab_set()

        frame = tb.Frame(win, padding=10)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="触发器名称:").grid(row=0, column=0, sticky=W, pady=5)
        name_entry = tb.Entry(frame, width=30)
        name_entry.grid(row=0, column=1, sticky=EW, pady=5)

        tb.Label(frame, text="传感器:").grid(row=1, column=0, sticky=W, pady=5)
        sensor_combo = tb.Combobox(frame, values=list(iot_manager.sensors.keys()), state="readonly")
        sensor_combo.grid(row=1, column=1, sticky=EW, pady=5)

        tb.Label(frame, text="匹配模式(包含此字符串即触发，留空则任何消息):").grid(row=2, column=0, sticky=W, pady=5)
        pattern_entry = tb.Entry(frame, width=30)
        pattern_entry.grid(row=2, column=1, sticky=EW, pady=5)

        def create_and_edit():
            name = name_entry.get().strip()
            sensor = sensor_combo.get()
            pattern = pattern_entry.get().strip()
            if not name or not sensor:
                messagebox.showerror("错误", "请填写触发器名称和传感器")
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
                    win.destroy()
                    self._edit_trigger_tasks(trigger)
                else:
                    messagebox.showerror("错误", "触发器创建失败")
                    win.destroy()
            else:
                messagebox.showerror("错误", "触发器名称已存在")

        tb.Button(frame, text="创建并编辑任务", command=create_and_edit, bootstyle="success").grid(row=3, column=0, columnspan=2, pady=20)

    # -------------------- 触发器任务编辑 --------------------
    def _edit_trigger_tasks(self, trigger):
        win = tb.Toplevel(self.root)
        win.title(f"编辑触发器任务 - {trigger.name}")
        win.geometry("832x546")
        win.minsize(500, 500)
        win.transient(self.root)

        main_frame = tb.Frame(win)
        main_frame.pack(fill=BOTH, expand=True)

        # 可滚动区域
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        scrollable_frame = tb.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", on_frame_configure)

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # 任务列表
        listbox = tk.Listbox(scrollable_frame, height=10)
        listbox.pack(fill=BOTH, expand=True, pady=5)

        def refresh_list():
            listbox.delete(0, tk.END)
            for task in trigger.tasks:
                listbox.insert(tk.END, self._task_desc(task))

        refresh_list()

        # 按钮区域（放在 scrollable_frame 内）
        btn_frame_inner = tb.Frame(scrollable_frame)
        btn_frame_inner.pack(fill=X, pady=5)

        def add_task():
            self._add_task_dialog(trigger, refresh_list)

        def edit_task():
            sel = listbox.curselection()
            if sel:
                self._edit_task_dialog(trigger, sel[0], refresh_list)

        def delete_task():
            sel = listbox.curselection()
            if sel:
                trigger.tasks.pop(sel[0])
                iot_manager._save_triggers()
                refresh_list()
                self._refresh_triggers()

        def move_up():
            sel = listbox.curselection()
            if sel and sel[0] > 0:
                idx = sel[0]
                trigger.tasks[idx], trigger.tasks[idx-1] = trigger.tasks[idx-1], trigger.tasks[idx]
                iot_manager._save_triggers()
                refresh_list()
                listbox.selection_set(idx-1)
                self._refresh_triggers()

        def move_down():
            sel = listbox.curselection()
            if sel and sel[0] < len(trigger.tasks)-1:
                idx = sel[0]
                trigger.tasks[idx], trigger.tasks[idx+1] = trigger.tasks[idx+1], trigger.tasks[idx]
                iot_manager._save_triggers()
                refresh_list()
                listbox.selection_set(idx+1)
                self._refresh_triggers()

        tb.Button(btn_frame_inner, text="➕ 添加", command=add_task, bootstyle="success-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_frame_inner, text="✏️ 编辑", command=edit_task, bootstyle="primary-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_frame_inner, text="❌ 删除", command=delete_task, bootstyle="danger-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_frame_inner, text="⬆ 上移", command=move_up, bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_frame_inner, text="⬇ 下移", command=move_down, bootstyle="secondary-outline").pack(side=LEFT, padx=2)

        # 底部固定按钮
        bottom_btn_frame = tb.Frame(main_frame)
        bottom_btn_frame.pack(side=BOTTOM, fill=X, pady=10, padx=10)

        def save_and_close():
            # 所有修改已实时保存，这里仅刷新并关闭
            self._refresh_triggers()
            win.destroy()

        tb.Button(bottom_btn_frame, text="保存并关闭", command=save_and_close, bootstyle="success").pack(side=RIGHT, padx=5)
        tb.Button(bottom_btn_frame, text="取消", command=win.destroy, bootstyle="secondary").pack(side=RIGHT, padx=5)


    def _add_task_dialog(self, trigger, refresh_cb):
        win = tb.Toplevel(self.root)
        win.title("添加任务")
        win.geometry("826x546")
        win.minsize(450, 500)
        win.transient(self.root)

        main_frame = tb.Frame(win)
        main_frame.pack(fill=BOTH, expand=True)

        # 可滚动区域
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        scrollable_frame = tb.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", on_frame_configure)

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        frame = scrollable_frame

        # 类型映射（中文显示）
        type_display_map = {
            "🤖 通知AI": "ai_notify",
            "📟 控制设备": "control_device",
            "💬 QQ通知": "qq_notify"
        }
        type_value_to_display = {v: k for k, v in type_display_map.items()}

        task_type_var = tk.StringVar(value="ai_notify")
        display_var = tk.StringVar(value=type_value_to_display["ai_notify"])

        def on_type_selected(*args):
            display = display_var.get()
            actual = type_display_map.get(display, "ai_notify")
            task_type_var.set(actual)
            update_params()

        display_var.trace_add('write', on_type_selected)

        tb.Label(frame, text="任务类型:").pack(anchor=W, pady=(5,0))
        type_combo = tb.Combobox(frame, textvariable=display_var,
                                 values=list(type_display_map.keys()),
                                 state="readonly")
        type_combo.pack(fill=X, pady=5)

        params_frame = tb.Frame(frame)
        params_frame.pack(fill=BOTH, expand=True, pady=10)

        dynamic_data = {}

        def update_params(*args):
            for w in params_frame.winfo_children():
                w.destroy()
            dynamic_data.clear()
            ttype = task_type_var.get()
            if ttype == "ai_notify":
                tb.Label(params_frame, text="发送给AI的消息（留空则发送原始传感器消息）:").pack(anchor=W)
                prompt_entry = tb.Entry(params_frame, width=50)
                prompt_entry.pack(fill=X, pady=5)
                send_reply_var = tk.BooleanVar(value=False)
                tb.Checkbutton(params_frame, text="将AI回复回传给原设备", variable=send_reply_var,
                               bootstyle="primary").pack(anchor=W, pady=5)
                dynamic_data["prompt"] = prompt_entry
                dynamic_data["send_reply"] = send_reply_var
            elif ttype == "control_device":
                tb.Label(params_frame, text="设备名称:").pack(anchor=W)
                dev_entry = tb.Combobox(params_frame, values=list(iot_manager.devices.keys()), state="readonly")
                dev_entry.pack(fill=X, pady=5)
                tb.Label(params_frame, text="指令:").pack(anchor=W)
                cmd_entry = tb.Entry(params_frame, width=50)
                cmd_entry.pack(fill=X, pady=5)
                dynamic_data["device_name"] = dev_entry
                dynamic_data["command"] = cmd_entry
            elif ttype == "qq_notify":
                tb.Label(params_frame, text="目标类型:").pack(anchor=W)
                target_type_map = {"私聊": "private", "群聊": "group"}
                target_type_var = tk.StringVar(value="private")
                target_display_var = tk.StringVar(value="私聊")
                def on_target_type_selected(*args):
                    display = target_display_var.get()
                    actual = target_type_map.get(display, "private")
                    target_type_var.set(actual)
                target_display_var.trace_add('write', on_target_type_selected)
                target_combo = tb.Combobox(params_frame, textvariable=target_display_var,
                                           values=list(target_type_map.keys()), state="readonly")
                target_combo.pack(fill=X, pady=5)
                tb.Label(params_frame, text="目标ID (QQ号或群号):").pack(anchor=W)
                id_entry = tb.Entry(params_frame, width=50)
                id_entry.pack(fill=X, pady=5)
                tb.Label(params_frame, text="消息内容 (可用 {message} 代替原始传感器消息):").pack(anchor=W)
                content_entry = tb.Entry(params_frame, width=50)
                content_entry.pack(fill=X, pady=5)
                dynamic_data["target_type"] = target_type_var
                dynamic_data["target_id"] = id_entry
                dynamic_data["content"] = content_entry

        update_params()

        # 底部按钮
        bottom_btn_frame = tb.Frame(main_frame)
        bottom_btn_frame.pack(side=BOTTOM, fill=X, pady=10, padx=10)

        def save():
            display_type = display_var.get()
            ttype = type_display_map.get(display_type, "ai_notify")
            task = {"type": ttype}
            if ttype == "ai_notify":
                task["prompt"] = dynamic_data["prompt"].get().strip()
                task["send_reply"] = dynamic_data["send_reply"].get()
            elif ttype == "control_device":
                task["device_name"] = dynamic_data["device_name"].get()
                task["command"] = dynamic_data["command"].get().strip()
            elif ttype == "qq_notify":
                task["target_type"] = dynamic_data["target_type"].get()
                task["target_id"] = dynamic_data["target_id"].get().strip()
                task["content"] = dynamic_data["content"].get().strip()
            trigger.tasks.append(task)
            iot_manager._save_triggers()
            refresh_cb()
            self._refresh_triggers()
            win.destroy()

        tb.Button(bottom_btn_frame, text="保存并关闭", command=save, bootstyle="success").pack(side=LEFT, padx=5)
        tb.Button(bottom_btn_frame, text="取消", command=win.destroy, bootstyle="secondary").pack(side=LEFT, padx=5)

    def _edit_task_dialog(self, trigger, task_index, refresh_cb):
        task = trigger.tasks[task_index]
        win = tb.Toplevel(self.root)
        win.title("编辑任务")
        win.geometry("832x546")
        win.minsize(450, 500)
        win.transient(self.root)

        main_frame = tb.Frame(win)
        main_frame.pack(fill=BOTH, expand=True)

        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        scrollable_frame = tb.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", on_frame_configure)

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        frame = scrollable_frame

        type_display_map = {
            "🤖 通知AI": "ai_notify",
            "📟 控制设备": "control_device",
            "💬 QQ通知": "qq_notify"
        }
        type_value_to_display = {v: k for k, v in type_display_map.items()}

        task_type_var = tk.StringVar(value=task.get('type', 'ai_notify'))
        display_var = tk.StringVar(value=type_value_to_display.get(task.get('type', 'ai_notify'), "🤖 通知AI"))

        def on_type_selected(*args):
            display = display_var.get()
            actual = type_display_map.get(display, "ai_notify")
            task_type_var.set(actual)
            update_params()

        display_var.trace_add('write', on_type_selected)

        tb.Label(frame, text="任务类型:").pack(anchor=W, pady=(5,0))
        type_combo = tb.Combobox(frame, textvariable=display_var,
                                 values=list(type_display_map.keys()),
                                 state="readonly")
        type_combo.pack(fill=X, pady=5)

        params_frame = tb.Frame(frame)
        params_frame.pack(fill=BOTH, expand=True, pady=10)

        dynamic_data = {}

        def update_params(*args):
            for w in params_frame.winfo_children():
                w.destroy()
            dynamic_data.clear()
            ttype = task_type_var.get()
            if ttype == "ai_notify":
                tb.Label(params_frame, text="发送给AI的消息（留空则发送原始传感器消息）:").pack(anchor=W)
                prompt_entry = tb.Entry(params_frame, width=50)
                prompt_entry.insert(0, task.get('prompt', ''))
                prompt_entry.pack(fill=X, pady=5)
                send_reply_var = tk.BooleanVar(value=task.get('send_reply', False))
                tb.Checkbutton(params_frame, text="将AI回复回传给原设备", variable=send_reply_var,
                               bootstyle="primary").pack(anchor=W, pady=5)
                dynamic_data["prompt"] = prompt_entry
                dynamic_data["send_reply"] = send_reply_var
            elif ttype == "control_device":
                tb.Label(params_frame, text="设备名称:").pack(anchor=W)
                dev_entry = tb.Combobox(params_frame, values=list(iot_manager.devices.keys()), state="readonly")
                dev_entry.set(task.get('device_name', ''))
                dev_entry.pack(fill=X, pady=5)
                tb.Label(params_frame, text="指令:").pack(anchor=W)
                cmd_entry = tb.Entry(params_frame, width=50)
                cmd_entry.insert(0, task.get('command', ''))
                cmd_entry.pack(fill=X, pady=5)
                dynamic_data["device_name"] = dev_entry
                dynamic_data["command"] = cmd_entry
            elif ttype == "qq_notify":
                tb.Label(params_frame, text="目标类型:").pack(anchor=W)
                target_type_map = {"私聊": "private", "群聊": "group"}
                target_type_var = tk.StringVar(value=task.get('target_type', 'private'))
                target_display = {v: k for k, v in target_type_map.items()}
                target_display_var = tk.StringVar(value=target_display.get(task.get('target_type', 'private'), "私聊"))
                def on_target_type_selected(*args):
                    display = target_display_var.get()
                    actual = target_type_map.get(display, "private")
                    target_type_var.set(actual)
                target_display_var.trace_add('write', on_target_type_selected)
                target_combo = tb.Combobox(params_frame, textvariable=target_display_var,
                                           values=list(target_type_map.keys()), state="readonly")
                target_combo.pack(fill=X, pady=5)
                tb.Label(params_frame, text="目标ID (QQ号或群号):").pack(anchor=W)
                id_entry = tb.Entry(params_frame, width=50)
                id_entry.insert(0, task.get('target_id', ''))
                id_entry.pack(fill=X, pady=5)
                tb.Label(params_frame, text="消息内容 (可用 {message} 代替原始传感器消息):").pack(anchor=W)
                content_entry = tb.Entry(params_frame, width=50)
                content_entry.insert(0, task.get('content', ''))
                content_entry.pack(fill=X, pady=5)
                dynamic_data["target_type"] = target_type_var
                dynamic_data["target_id"] = id_entry
                dynamic_data["content"] = content_entry

        update_params()

        bottom_btn_frame = tb.Frame(main_frame)
        bottom_btn_frame.pack(side=BOTTOM, fill=X, pady=10, padx=10)

        def save():
            ttype = task_type_var.get()
            new_task = {"type": ttype}
            if ttype == "ai_notify":
                new_task["prompt"] = dynamic_data["prompt"].get().strip()
                new_task["send_reply"] = dynamic_data["send_reply"].get()
            elif ttype == "control_device":
                new_task["device_name"] = dynamic_data["device_name"].get()
                new_task["command"] = dynamic_data["command"].get().strip()
            elif ttype == "qq_notify":
                new_task["target_type"] = dynamic_data["target_type"].get()
                new_task["target_id"] = dynamic_data["target_id"].get().strip()
                new_task["content"] = dynamic_data["content"].get().strip()
            trigger.tasks[task_index] = new_task
            iot_manager._save_triggers()
            refresh_cb()
            self._refresh_triggers()
            win.destroy()

        tb.Button(bottom_btn_frame, text="保存并关闭", command=save, bootstyle="success").pack(side=LEFT, padx=5)
        tb.Button(bottom_btn_frame, text="取消", command=win.destroy, bootstyle="secondary").pack(side=LEFT, padx=5)
    def create_log_tab(self):
        """日志记录表格页"""
        tab = tb.Frame(self.notebook)
        self.notebook.add(tab, text="📋 日志记录")

        # 工具栏
        toolbar = tb.Frame(tab)
        toolbar.pack(fill=X, padx=5, pady=5)
        tb.Button(toolbar, text="🔄 刷新", command=self.refresh_log_table, bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        tb.Button(toolbar, text="🗑️ 清空日志", command=self.clear_logs, bootstyle="danger-outline").pack(side=LEFT, padx=2)

        # 表格
        columns = ("时间", "类型", "设备名称", "内容", "协议")
        self.log_tree = ttk.Treeview(tab, columns=columns, show="headings", height=20)
        for col in columns:
            self.log_tree.heading(col, text=col)
            if col == "时间":
                self.log_tree.column(col, width=160)
            elif col == "设备名称":
                self.log_tree.column(col, width=120)
            elif col == "内容":
                self.log_tree.column(col, width=300)
            else:
                self.log_tree.column(col, width=80)
        scrollbar = ttk.Scrollbar(tab, orient=VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        self.log_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=RIGHT, fill=Y, pady=5)

        self.refresh_log_table()

    def refresh_log_table(self):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        from iot_logger import iot_logger
        logs = iot_logger.get_logs(500)
        for log in logs:
            typ = log.get("type")
            ts = log.get("timestamp", "")[:19]
            if typ == "command":
                type_icon = "📤 指令"
                dev = log.get("device_name", "")
                content = log.get("command", "")
                protocol = log.get("protocol", "")
            elif typ == "sensor":
                type_icon = "📥 传感器"
                dev = log.get("device_name", "")
                content = log.get("message", "")
                protocol = log.get("protocol", "")
            elif typ == "trigger":
                type_icon = "⚡ 触发器"
                dev = log.get("trigger_name", "")
                content = f"传感器: {log.get('sensor_name', '')} | 消息: {log.get('message', '')}"
                protocol = ""
            else:
                continue
            self.log_tree.insert("", tk.END, values=(ts, type_icon, dev, content, protocol))
            
    def clear_logs(self):
        if messagebox.askyesno("确认", "清空所有日志？"):
            from iot_logger import iot_logger
            iot_logger.clear_logs()
            self.refresh_log_table()

    def create_active_intelligence_tab(self):
        """主动智能设置页"""
        tab = tb.Frame(self.notebook)
        self.notebook.add(tab, text="🧠 主动智能")

        main_frame = tb.Frame(tab, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        # 巡检设置组
        group1_frame = tb.Frame(main_frame)
        group1_frame.pack(fill=X, pady=5)
        tb.Label(group1_frame, text="巡检设置", font=("微软雅黑", 9, "bold"),
                 bootstyle="primary").pack(anchor=NW, padx=5, pady=(5,0))
        group1 = tb.Frame(group1_frame, relief=GROOVE, borderwidth=1)
        group1.pack(fill=X, padx=5, pady=5)

        # 启用主动巡检复选框
        self.inspector_enabled_var = tk.BooleanVar(value=config.inspector_enabled)
        tb.Checkbutton(group1, text="启用主动巡检", variable=self.inspector_enabled_var).grid(
            row=0, column=0, columnspan=4, sticky=W, padx=5, pady=5)

        # 巡检间隔设置
        tb.Label(group1, text="巡检间隔:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.inspect_interval_var = tk.IntVar(value=config.inspector_interval)
        interval_spin = tb.Spinbox(group1, from_=60, to=86400, increment=60,
                                   textvariable=self.inspect_interval_var, width=10)
        interval_spin.grid(row=1, column=1, sticky=W, padx=5)
        tb.Label(group1, text="秒 (1分钟~24小时)").grid(row=1, column=2, sticky=W)

        def save_settings():
            config.inspector_enabled = self.inspector_enabled_var.get()
            try:
                config.inspector_interval = self.inspect_interval_var.get()
            except:
                pass
            if hasattr(self, 'main_gui'):
                self.main_gui._save_all_config()   # 持久化到文件
            # 根据启用状态启动或停止巡检器
            if config.inspector_enabled:
                self.start_inspector()
            else:
                self.stop_inspector()
            messagebox.showinfo("成功", "巡检设置已保存")

        tb.Button(group1, text="💾 保存设置", command=save_settings,
                  bootstyle="success-outline").grid(row=1, column=3, padx=10)

        # 手动巡检按钮
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(pady=10)
        tb.Button(btn_frame, text="🔍 立即巡检（手动）", command=self.manual_inspect,
                  bootstyle="primary", width=20).pack(pady=5)

        # 状态显示
        self.inspect_status = tb.Label(main_frame, text="巡检器未启动", foreground="gray")
        self.inspect_status.pack(pady=10)

        # 启动/停止按钮
        ctrl_frame = tb.Frame(main_frame)
        ctrl_frame.pack(pady=5)
        tb.Button(ctrl_frame, text="▶ 启动巡检器", command=self.start_inspector,
                  bootstyle="success").pack(side=LEFT, padx=5)
        tb.Button(ctrl_frame, text="⏹️ 停止巡检器", command=self.stop_inspector,
                  bootstyle="danger").pack(side=LEFT, padx=5)

        # 根据配置决定初始状态，不自动启动
        if config.inspector_enabled:
            self.start_inspector()
        else:
            self.inspect_status.config(text="巡检器已禁用")
        
    def manual_inspect(self):
        from smart_inspector import inspector
        inspector.trigger_inspection("manual")
        self.inspect_status.config(text="手动巡检已触发", foreground="green")
        self.root.after(5000, lambda: self.inspect_status.config(text="巡检器运行中", foreground="white"))

    def start_inspector(self):
        from smart_inspector import inspector
        # 不要重新设置回调！回调已在主窗口 GUI2_0 中设置好了
        # 仅设置间隔并启动
        inspector.set_interval(self.inspect_interval_var.get())
        inspector.start()
        self.inspect_status.config(text="巡检器运行中", foreground="green")

    def stop_inspector(self):
        from smart_inspector import inspector
        inspector.stop()
        self.inspect_status.config(text="巡检器已停止", foreground="red")

    def call_ai_for_inspection(self, prompt, reply_callback):
        """供巡检器调用的 AI 接口（静默运行，不更新 UI，避免线程冲突）"""
        if hasattr(self, 'main_gui') and self.main_gui:
            # 临时替换输出回调为静默函数，不更新聊天界面
            original_callback = self.main_gui.agent.output_callback
            self.main_gui.agent.output_callback = lambda msg: None
            try:
                self.main_gui.agent.run(prompt)
            finally:
                self.main_gui.agent.output_callback = original_callback
        else:
            print("[巡检] 无法调用AI，缺少主窗口引用")

    def export_config(self):
        """导出所有设备、传感器、触发器配置到 JSON 文件"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
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
            messagebox.showinfo("成功", f"配置已导出到 {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")

    def import_config(self):
        """导入配置文件，覆盖当前设备、传感器、触发器"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="导入配置",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if not file_path:
            return
        if not messagebox.askyesno("确认", "导入将覆盖当前所有设备、传感器、触发器配置，是否继续？"):
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 清空现有
            iot_manager.devices.clear()
            iot_manager.sensors.clear()
            iot_manager.triggers.clear()
            # 导入设备
            for dev_data in data.get("devices", []):
                dev = IOTDevice(dev_data)
                iot_manager.devices[dev.name] = dev
            # 导入传感器
            for sen_data in data.get("sensors", []):
                sen = IOTSensor(sen_data)
                iot_manager.sensors[sen.name] = sen
            # 导入触发器
            for trig_data in data.get("triggers", []):
                trig = IOTTrigger(trig_data)
                iot_manager.triggers[trig.name] = trig
            # 保存到文件
            iot_manager._save_devices()
            iot_manager._save_sensors()
            iot_manager._save_triggers()
            # 重新加载监听器（需要重启传感器监听）
            iot_manager._stop_all_listeners()
            iot_manager._start_sensor_listeners()
            self._refresh_all()
            messagebox.showinfo("成功", "配置导入成功，已重新加载")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {e}")

    def reset_config(self):
        """重置所有配置：清空设备、传感器、触发器"""
        if not messagebox.askyesno("确认重置", "此操作将删除所有设备、传感器、触发器配置，且不可恢复。是否继续？"):
            return
        try:
            iot_manager.devices.clear()
            iot_manager.sensors.clear()
            iot_manager.triggers.clear()
            iot_manager._save_devices()
            iot_manager._save_sensors()
            iot_manager._save_triggers()
            # 停止并重启监听器
            iot_manager._stop_all_listeners()
            iot_manager._start_sensor_listeners()
            self._refresh_all()
            messagebox.showinfo("成功", "配置已重置")
        except Exception as e:
            messagebox.showerror("错误", f"重置失败: {e}")

    def create_servers_tab(self):
        try:
            import paho.mqtt.client
        except ImportError:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt"])
        tab = tb.Frame(self.notebook)
        self.notebook.add(tab, text="🚀 内置服务器")

        # 创建 Notebook 子标签页
        inner_notebook = tb.Notebook(tab, bootstyle="secondary")
        inner_notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # MQTT 面板
        mqtt_frame = tb.Frame(inner_notebook)
        inner_notebook.add(mqtt_frame, text="MQTT 服务器")
        self._create_mqtt_panel(mqtt_frame)

        # TCP 面板
        tcp_frame = tb.Frame(inner_notebook)
        inner_notebook.add(tcp_frame, text="TCP 服务器")
        self._create_tcp_panel(tcp_frame)

    def _create_mqtt_panel(self, parent):
        # 控制区域
        control_frame = tb.Frame(parent)
        control_frame.pack(fill=X, padx=5, pady=5)

        tb.Label(control_frame, text="端口:").pack(side=LEFT, padx=2)
        self.mqtt_port_var = tk.IntVar(value=1883)
        tb.Spinbox(control_frame, from_=1024, to=65535, textvariable=self.mqtt_port_var, width=8).pack(side=LEFT, padx=2)

        self.mqtt_status_label = tb.Label(control_frame, text="未启动", foreground="red")
        self.mqtt_status_label.pack(side=LEFT, padx=10)

        self.mqtt_start_btn = tb.Button(control_frame, text="启动", command=self._start_mqtt, bootstyle="success")
        self.mqtt_start_btn.pack(side=LEFT, padx=2)
        self.mqtt_stop_btn = tb.Button(control_frame, text="停止", command=self._stop_mqtt, bootstyle="danger", state=tk.DISABLED)
        self.mqtt_stop_btn.pack(side=LEFT, padx=2)

        # 主题管理区域（使用普通 Frame 模拟 LabelFrame）
        topic_frame = tb.Frame(parent)
        topic_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        tb.Label(topic_frame, text="主题消息记录", font=("微软雅黑", 9, "bold"),
                 bootstyle="primary").pack(anchor=NW, padx=5, pady=(5,0))
        topic_content = tb.Frame(topic_frame, relief=tk.GROOVE, borderwidth=1)
        topic_content.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 左侧主题列表，右侧消息显示（使用 tk.PanedWindow）
        paned = tk.PanedWindow(topic_content, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        paned.pack(fill=BOTH, expand=True)

        left_frame = tb.Frame(paned)
        paned.add(left_frame, width=150)
        tb.Label(left_frame, text="订阅的主题").pack(anchor=W)
        self.topic_listbox = tk.Listbox(left_frame)
        self.topic_listbox.pack(fill=BOTH, expand=True)
        self.topic_listbox.bind('<<ListboxSelect>>', self._on_topic_select)

        btn_frame = tb.Frame(left_frame)
        btn_frame.pack(fill=X, pady=2)
        tb.Button(btn_frame, text="➕ 添加主题", command=self._add_topic, bootstyle="success-outline").pack(side=LEFT, padx=2)
        tb.Button(btn_frame, text="❌ 删除主题", command=self._del_topic, bootstyle="danger-outline").pack(side=LEFT, padx=2)

        right_frame = tb.Frame(paned)
        paned.add(right_frame, width=300)
        tb.Label(right_frame, text="消息记录").pack(anchor=W)
        self.topic_msg_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=15)
        self.topic_msg_text.pack(fill=BOTH, expand=True)
        msg_btn_frame = tb.Frame(right_frame)
        msg_btn_frame.pack(fill=X)
        tb.Button(msg_btn_frame, text="清空记录", command=self._clear_topic_msgs, bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        tb.Button(msg_btn_frame, text="查看历史", command=self._view_topic_history, bootstyle="info-outline").pack(side=LEFT, padx=2)

        # 服务器日志区域（使用普通 Frame 模拟 LabelFrame）
        log_frame = tb.Frame(parent)
        log_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        tb.Label(log_frame, text="服务器日志", font=("微软雅黑", 9, "bold"),
                 bootstyle="secondary").pack(anchor=NW, padx=5, pady=(5,0))
        log_content = tb.Frame(log_frame, relief=tk.GROOVE, borderwidth=1)
        log_content.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.mqtt_log_text = scrolledtext.ScrolledText(log_content, wrap=tk.WORD, height=8)
        self.mqtt_log_text.pack(fill=BOTH, expand=True)

        # 初始化内部 MQTT 客户端（用于订阅所有主题）
        self.mqtt_sub_client = None
        self.mqtt_topics = {}  # topic -> list of messages
        self._load_mqtt_topics()

    def _start_mqtt(self):
        from builtin_servers import mqtt_manager
        port = self.mqtt_port_var.get()
        mqtt_manager.set_log_callback(self._mqtt_log)
        if mqtt_manager.start(port=port):
            self.mqtt_status_label.config(text="运行中", foreground="green")
            self.mqtt_start_btn.config(state=tk.DISABLED)
            self.mqtt_stop_btn.config(state=tk.NORMAL)
            self._start_mqtt_subscriber()

    def _stop_mqtt(self):
        from builtin_servers import mqtt_manager
        mqtt_manager.stop()
        self.mqtt_status_label.config(text="未启动", foreground="red")
        self.mqtt_start_btn.config(state=tk.NORMAL)
        self.mqtt_stop_btn.config(state=tk.DISABLED)
        if self.mqtt_sub_client:
            self.mqtt_sub_client.loop_stop()
            self.mqtt_sub_client.disconnect()
            self.mqtt_sub_client = None

    def _mqtt_log(self, msg):
        def add():
            self.mqtt_log_text.insert(tk.END, msg + "\n")
            self.mqtt_log_text.see(tk.END)
        self.root.after(0, add)

    def _start_mqtt_subscriber(self):
        import paho.mqtt.client as mqtt
        import time

        self.mqtt_sub_client = mqtt.Client()
        self.mqtt_sub_client.on_connect = self._on_subscribe_connect
        self.mqtt_sub_client.on_message = self._on_subscribe_message

        try:
            self.mqtt_sub_client.connect("127.0.0.1", self.mqtt_port_var.get())
            self.mqtt_sub_client.loop_start()

            # 等待连接成功（最多2秒）
            for _ in range(20):
                if self.mqtt_sub_client.is_connected():
                    break
                time.sleep(0.1)

            if not self.mqtt_sub_client.is_connected():
                self._mqtt_log("[订阅客户端] 连接失败，请检查MQTT服务器是否运行")
            else:
                self._mqtt_log("[订阅客户端] 已连接并准备订阅")
        except Exception as e:
            self._mqtt_log(f"[订阅客户端] 启动异常: {e}")

    def _on_subscribe_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("#")
            self._mqtt_log("[订阅客户端] 已订阅所有主题 (#)")
        else:
            self._mqtt_log(f"[订阅客户端] 连接错误，错误码: {rc}")

    def _on_subscribe_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        self._record_mqtt_message(topic, payload)
        self.mqtt_sub_client.loop_start()

    def _record_mqtt_message(self, topic, payload):
        try:
            # 存储到内存
            if topic not in self.mqtt_topics:
                self.mqtt_topics[topic] = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.mqtt_topics[topic].append(f"[{timestamp}] {payload}")
            # 刷新主题列表
            def update():
                if topic not in self.topic_listbox.get(0, tk.END):
                    self.topic_listbox.insert(tk.END, topic)
            self.root.after(0, update)
            # 如果当前选中的主题就是该主题，更新显示
            selection = self.topic_listbox.curselection()
            if selection and self.topic_listbox.get(selection[0]) == topic:
                self._show_topic_messages(topic)
            # 保存到文件
            self._save_mqtt_topics()
        except Exception as e:
            print(f"记录MQTT消息失败: {e}")

    def _show_topic_messages(self, topic):
        self.topic_msg_text.delete(1.0, tk.END)
        if topic in self.mqtt_topics:
            for msg in self.mqtt_topics[topic]:
                self.topic_msg_text.insert(tk.END, msg + "\n")
        self.topic_msg_text.see(tk.END)

    def _on_topic_select(self, event):
        sel = self.topic_listbox.curselection()
        if sel:
            topic = self.topic_listbox.get(sel[0])
            self._show_topic_messages(topic)

    def _add_topic(self):
        win = tb.Toplevel(self.root)
        win.title("添加订阅主题")
        win.geometry("300x150")
        tb.Label(win, text="主题名称:").pack(pady=5)
        topic_entry = tb.Entry(win, width=30)
        topic_entry.pack(pady=5)

        def do_add():
            topic = topic_entry.get().strip()
            if topic:
                if self.mqtt_sub_client and self.mqtt_sub_client.is_connected():
                    self.mqtt_sub_client.subscribe(topic)
                    self._mqtt_log(f"[订阅客户端] 已订阅主题: {topic}")
                else:
                    self._mqtt_log("[订阅客户端] 尚未连接，无法订阅新主题")
                if topic not in self.mqtt_topics:
                    self.mqtt_topics[topic] = []
                self.topic_listbox.insert(tk.END, topic)
                win.destroy()

        tb.Button(win, text="订阅", command=do_add, bootstyle="success").pack(pady=10)

    def _del_topic(self):
        sel = self.topic_listbox.curselection()
        if sel:
            topic = self.topic_listbox.get(sel[0])
            if messagebox.askyesno("确认", f"删除主题 {topic} 的记录？"):
                self.topic_listbox.delete(sel)
                if topic in self.mqtt_topics:
                    del self.mqtt_topics[topic]
                self.topic_msg_text.delete(1.0, tk.END)
                self._save_mqtt_topics()

    def _clear_topic_msgs(self):
        sel = self.topic_listbox.curselection()
        if sel:
            topic = self.topic_listbox.get(sel[0])
            if topic in self.mqtt_topics:
                self.mqtt_topics[topic] = []
                self._show_topic_messages(topic)
                self._save_mqtt_topics()

    def _view_topic_history(self):
        sel = self.topic_listbox.curselection()
        if not sel:
            return
        topic = self.topic_listbox.get(sel[0])
        win = tb.Toplevel(self.root)
        win.title(f"消息历史 - {topic}")
        win.geometry("500x400")
        text = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        text.pack(fill=BOTH, expand=True)
        for msg in self.mqtt_topics.get(topic, []):
            text.insert(tk.END, msg + "\n")
        text.config(state=tk.DISABLED)

    def _load_mqtt_topics(self):
        file_path = "./builtin_servers_data/mqtt_topics.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.mqtt_topics = data
                for topic in self.mqtt_topics:
                    self.topic_listbox.insert(tk.END, topic)

    def _save_mqtt_topics(self):
        os.makedirs("./builtin_servers_data", exist_ok=True)
        with open("./builtin_servers_data/mqtt_topics.json", 'w', encoding='utf-8') as f:
            json.dump(self.mqtt_topics, f, indent=2)

    def _create_tcp_panel(self, parent):
        # 控制区域
        control_frame = tb.Frame(parent)
        control_frame.pack(fill=X, padx=5, pady=5)

        tb.Label(control_frame, text="端口:").pack(side=LEFT, padx=2)
        self.tcp_port_var = tk.IntVar(value=8888)
        tb.Spinbox(control_frame, from_=1024, to=65535, textvariable=self.tcp_port_var, width=8).pack(side=LEFT, padx=2)

        self.tcp_status_label = tb.Label(control_frame, text="未启动", foreground="red")
        self.tcp_status_label.pack(side=LEFT, padx=10)

        self.tcp_start_btn = tb.Button(control_frame, text="启动", command=self._start_tcp, bootstyle="success")
        self.tcp_start_btn.pack(side=LEFT, padx=2)
        self.tcp_stop_btn = tb.Button(control_frame, text="停止", command=self._stop_tcp, bootstyle="danger", state=tk.DISABLED)
        self.tcp_stop_btn.pack(side=LEFT, padx=2)

        # 客户端和消息区域
        main_paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 左侧客户端列表
        left_frame = tb.Frame(main_paned)
        main_paned.add(left_frame, width=150)
        tb.Label(left_frame, text="已连接的客户端").pack(anchor=W)
        self.tcp_clients_listbox = tk.Listbox(left_frame)
        self.tcp_clients_listbox.pack(fill=BOTH, expand=True)
        self.tcp_clients_listbox.bind('<<ListboxSelect>>', self._on_tcp_client_select)

        # 右侧消息显示和发送
        right_frame = tb.Frame(main_paned)
        main_paned.add(right_frame, width=300)

        tb.Label(right_frame, text="来自客户端的消息").pack(anchor=W)
        self.tcp_msg_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=10)
        self.tcp_msg_text.pack(fill=BOTH, expand=True)

        tb.Label(right_frame, text="发送消息到选中客户端").pack(anchor=W, pady=(5,0))
        self.tcp_send_entry = tb.Entry(right_frame)
        self.tcp_send_entry.pack(fill=X, pady=2)
        send_btn = tb.Button(right_frame, text="发送", command=self._tcp_send_to_client, bootstyle="primary")
        send_btn.pack(anchor=W, pady=2)

        # 服务器日志区域（使用普通 Frame 模拟 LabelFrame）
        log_frame = tb.Frame(parent)
        log_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        tb.Label(log_frame, text="服务器日志", font=("微软雅黑", 9, "bold"),
                 bootstyle="secondary").pack(anchor=NW, padx=5, pady=(5,0))
        log_content = tb.Frame(log_frame, relief=tk.GROOVE, borderwidth=1)
        log_content.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.tcp_log_text = scrolledtext.ScrolledText(log_content, wrap=tk.WORD, height=6)
        self.tcp_log_text.pack(fill=BOTH, expand=True)

        self.tcp_clients = []  # 存储 (addr, conn) 信息
        self.current_tcp_client = None

    def _start_tcp(self):
        from builtin_servers import tcp_manager
        port = self.tcp_port_var.get()
        tcp_manager.set_log_callback(self._tcp_log)
        tcp_manager.set_message_callback(self._tcp_message_received)
        if tcp_manager.start(port=port):
            self.tcp_status_label.config(text="运行中", foreground="green")
            self.tcp_start_btn.config(state=tk.DISABLED)
            self.tcp_stop_btn.config(state=tk.NORMAL)
            # 启动客户端列表刷新
            self._refresh_tcp_clients()

    def _stop_tcp(self):
        from builtin_servers import tcp_manager
        tcp_manager.stop()
        self.tcp_status_label.config(text="未启动", foreground="red")
        self.tcp_start_btn.config(state=tk.NORMAL)
        self.tcp_stop_btn.config(state=tk.DISABLED)
        self.tcp_clients_listbox.delete(0, tk.END)
        self.tcp_clients.clear()

    def _tcp_log(self, msg):
        def add():
            self.tcp_log_text.insert(tk.END, msg + "\n")
            self.tcp_log_text.see(tk.END)
        self.root.after(0, add)

    def _tcp_message_received(self, addr, msg):
        # 记录到右侧消息区
        def add():
            self.tcp_msg_text.insert(tk.END, f"[{addr}] {msg}\n")
            self.tcp_msg_text.see(tk.END)
        self.root.after(0, add)
        # 刷新客户端列表（可能新客户端连接）
        self._refresh_tcp_clients()

    def _refresh_tcp_clients(self):
        from builtin_servers import tcp_manager
        # 获取当前客户端列表
        clients = tcp_manager.clients.copy()  # [(conn, addr), ...]
        # 更新 UI
        def update():
            self.tcp_clients_listbox.delete(0, tk.END)
            self.tcp_clients = []
            for conn, addr in clients:
                addr_str = f"{addr[0]}:{addr[1]}"
                self.tcp_clients_listbox.insert(tk.END, addr_str)
                self.tcp_clients.append(addr_str)
        self.root.after(0, update)

    def _on_tcp_client_select(self, event):
        sel = self.tcp_clients_listbox.curselection()
        if sel:
            self.current_tcp_client = self.tcp_clients[sel[0]]

    def _tcp_send_to_client(self):
        if not self.current_tcp_client:
            messagebox.showwarning("提示", "请先选择一个客户端")
            return
        msg = self.tcp_send_entry.get().strip()
        if not msg:
            return
        from builtin_servers import tcp_manager
        # 解析地址为元组
        ip, port = self.current_tcp_client.split(':')
        addr = (ip, int(port))
        if tcp_manager.send_to_client(addr, msg):
            self.tcp_send_entry.delete(0, tk.END)
            self._tcp_log(f"发送到 {self.current_tcp_client}: {msg}")
        else:
            messagebox.showerror("错误", "发送失败，客户端可能已断开")


def main():
    # 独立运行：从配置文件读取主题，若没有则使用默认
    config_file = os.path.expanduser("~/.agent_config.json")
    theme = "flatly"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                theme = data.get("gui_theme", "flatly")
        except:
            pass
    root = tb.Window(themename=theme)
    app = TGHomeApp(root, theme=theme)
    root.mainloop()


if __name__ == "__main__":
    main()
