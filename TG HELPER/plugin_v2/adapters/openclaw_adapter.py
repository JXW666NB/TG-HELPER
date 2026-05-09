# -*- coding: utf-8 -*-
"""
OpenClaw 插件适配器（完整版 - 修复布局问题）
"""
import os
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
import ttkbootstrap as tb
from typing import Dict, Any, Optional, List, Callable
from .base_adapter import BaseAdapter
from ..base import PluginV2, HostAPI, PluginManifest
from ..events import SystemEvents


class OpenClawAdapter(BaseAdapter):
    """OpenClaw 插件适配器"""

    MANIFEST_FILE = "openclaw.plugin.json"

    def can_handle(self) -> bool:
        manifest_path = os.path.join(self.plugin_path, self.MANIFEST_FILE)
        return os.path.exists(manifest_path)

    def load_metadata(self) -> Dict[str, Any]:
        manifest_path = os.path.join(self.plugin_path, self.MANIFEST_FILE)
        with open(manifest_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)

        self.metadata = raw
        self.plugin_id = raw.get("id", f"openclaw.{os.path.basename(self.plugin_path)}")
        self.plugin_name = raw.get("name", self.plugin_id)

        capabilities = self._map_capabilities(raw.get("permissions", []))

        return {
            "id": self.plugin_id,
            "name": self.plugin_name,
            "version": raw.get("version", "1.0.0"),
            "description": raw.get("description", ""),
            "capabilities": capabilities,
            "permissions": capabilities,
            "entry_point": "__adapter__",
            "author": raw.get("author", ""),
            "config_schema": raw.get("configSchema", {}),
            "ui_hints": raw.get("uiHints", {}),
            "tools": raw.get("tools", []),
            "commands": raw.get("commands", []),
        }

    def _map_capabilities(self, permissions: List[str]) -> List[str]:
        mapping = {
            "fs:read": "fs.read",
            "fs:write": "fs.write",
            "net:http": "network.http",
            "ui:display": "ui.display",
            "ai:call": "agent.intercept",
            "tool:register": "agent.tool_register",
            "channel": "network.websocket",
        }
        mapped = []
        for perm in permissions:
            if perm in mapping:
                mapped.append(mapping[perm])
            else:
                mapped.append(perm.replace(":", "."))
        return list(set(mapped))

    def _is_channel_plugin(self) -> bool:
        capabilities = self.metadata.get("capabilities", [])
        kind = self.metadata.get("kind", "")
        permissions = self.metadata.get("permissions", [])
        channels = self.metadata.get("channels", [])
        return ("channel" in capabilities or 
                kind == "channel" or 
                "channel" in permissions or
                len(channels) > 0)

    def create_plugin_instance(self, host_api):
        if self._is_channel_plugin():
            print(f"[OpenClawAdapter] 检测到通道插件: {self.plugin_id}")
            return self._create_channel_plugin_instance(host_api)
        else:
            print(f"[OpenClawAdapter] 检测到工具插件: {self.plugin_id}")
            return self._create_tool_plugin_instance(host_api)

    def _create_tool_plugin_instance(self, host_api):
        adapter = self
        metadata = self.load_metadata()

        class OpenClawRuntimePlugin(PluginV2):
            def get_manifest(self):
                return PluginManifest(**metadata)

            def get_usage_info(self):
                info = {"commands": {}, "tools": []}
                for cmd in metadata.get("commands", []):
                    info["commands"][cmd.get("name", "")] = cmd.get("description", "")
                for tool in metadata.get("tools", []):
                    info["tools"].append({
                        "name": tool.get("name", ""),
                        "description": tool.get("description", "")
                    })
                return info

            def on_load(self, host_api: HostAPI):
                self.host_api = host_api
                for tool_def in metadata.get("tools", []):
                    tool_name = tool_def.get("name")
                    if tool_name:
                        def make_handler(t_name, t_def):
                            def handler(params):
                                args_str = json.dumps(params, ensure_ascii=False)
                                return f"[OpenClaw工具 {t_name}] 执行参数: {args_str}"
                            return handler
                        host_api.agent.register_tool(
                            {
                                "name": tool_name,
                                "description": tool_def.get("description", ""),
                                "parameters": tool_def.get("parameters", {"type": "object", "properties": {}})
                            },
                            make_handler(tool_name, tool_def)
                        )

                commands = metadata.get("commands", [])
                if commands:
                    def on_message(event):
                        content = event.data.get("content", "").strip()
                        for cmd in commands:
                            cmd_name = cmd.get("name", "")
                            if content.startswith(cmd_name):
                                host_api.ui.display_message(f"[OpenClaw命令] {cmd_name} 已触发", is_user=False)
                                event.stop_propagation()
                                break
                    host_api.events.subscribe(SystemEvents.MESSAGE_RECEIVED, on_message, plugin_id=metadata["id"])

            def get_settings_ui(self, parent):
                main_frame = tb.Frame(parent, height=450)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                main_frame.pack_propagate(False)  # 防止压缩
                return adapter.generate_gui_config_panel(
                    parent,
                    host_api.get_plugin_config(),
                    lambda cfg: host_api.save_plugin_config(cfg)
                )

        return OpenClawRuntimePlugin()

    def _create_channel_plugin_instance(self, host_api):
        adapter = self
        metadata = self.load_metadata()

        class OpenClawChannelPlugin(PluginV2):
            def __init__(self):
                super().__init__()
                self.bridge = None
                self.status_label = None
                self.console_text = None
                self.command_entry = None

            def get_manifest(self):
                return PluginManifest(**metadata)

            def get_usage_info(self):
                return {
                    "auto_effect": f"OpenClaw 通道插件：{metadata.get('description', '')}。启动后可通过设置界面配置并启动服务。",
                    "commands": {
                        "login": "触发扫码登录流程，在控制台中显示二维码",
                        "logout": "登出当前账号",
                        "status": "查看通道连接状态"
                    }
                }

            def on_load(self, host_api: HostAPI):
                self.host_api = host_api

            def get_settings_ui(self, parent):
                import tkinter as tk
                from tkinter import scrolledtext

                # 创建一个独立的顶级窗口用于调试
                top = tk.Toplevel(parent)
                top.title("通道控制台 ")
                top.geometry("650x550")

                main_frame = tb.Frame(top)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                self.status_label = tb.Label(main_frame, text="状态: 未启动", font=("微软雅黑", 12, "bold"))
                self.status_label.pack(pady=5)

                btn_frame = tb.Frame(main_frame)
                btn_frame.pack(pady=5)

                def start_channel():
                    config = self.host_api.get_plugin_config()
                    if not self.bridge:
                        try:
                            from .node_bridge import NodeBridge
                        except ImportError as e:
                            self._append_console(f"导入失败: {e}", "error")
                            return
                        self.bridge = NodeBridge(adapter.plugin_path)
                        self.bridge.set_stdout_callback(self._append_console)
                        self.bridge.set_stderr_callback(lambda line: self._append_console(f"[stderr] {line}", "error"))
                        self.bridge.register_handler("channel.message", self._handle_channel_message)
                        self.bridge.register_handler("channel.event", self._handle_channel_event)
                    if self.bridge.start(config):
                        self.status_label.config(text="状态: 运行中", bootstyle="success")
                        self._append_console("通道已启动")
                    else:
                        self.status_label.config(text="状态: 启动失败", bootstyle="danger")

                def stop_channel():
                    if self.bridge:
                        self.bridge.stop()
                        self.bridge = None
                    self.status_label.config(text="状态: 已停止", bootstyle="secondary")
                    self._append_console("通道已停止")

                tb.Button(btn_frame, text="启动通道", command=start_channel, bootstyle="success").pack(side=tk.LEFT, padx=10)
                tb.Button(btn_frame, text="停止通道", command=stop_channel, bootstyle="danger").pack(side=tk.LEFT, padx=10)

                console_frame = tb.Frame(main_frame)
                console_frame.pack(fill=tk.BOTH, expand=True, pady=10)

                self.console_text = scrolledtext.ScrolledText(
                    console_frame,
                    wrap=tk.WORD,
                    height=12,
                    font=("Consolas", 9),
                    bg="#1e1e1e",
                    fg="#d4d4d4"
                )
                self.console_text.pack(fill=tk.BOTH, expand=True)

                input_frame = tb.Frame(main_frame)
                input_frame.pack(fill=tk.X, pady=5)

                tb.Label(input_frame, text="命令:").pack(side=tk.LEFT)
                self.command_entry = tb.Entry(input_frame)
                self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.command_entry.bind("<Return>", self._send_command)
                tb.Button(input_frame, text="发送", command=self._send_command, bootstyle="primary").pack(side=tk.LEFT)

                quick_frame = tb.Frame(main_frame)
                quick_frame.pack(fill=tk.X, pady=5)
                tb.Button(quick_frame, text="扫码登录", command=lambda: self._send_command_str("login"), bootstyle="info").pack(side=tk.LEFT, padx=2)
                tb.Button(quick_frame, text="查看状态", command=lambda: self._send_command_str("status"), bootstyle="secondary").pack(side=tk.LEFT, padx=2)
                tb.Button(quick_frame, text="登出", command=lambda: self._send_command_str("logout"), bootstyle="warning").pack(side=tk.LEFT, padx=2)

                # 返回一个简单的标签，表示控制台已在独立窗口打开
                return tb.Label(parent, text="✅ 通道控制台已在独立窗口中打开，请查看。", font=("微软雅黑", 10), bootstyle="success")

            def _append_console(self, text: str, tag: str = None):
                if not self.console_text:
                    return
                def _append():
                    self.console_text.insert(tk.END, text + "\n", tag)
                    self.console_text.see(tk.END)
                self.console_text.after(0, _append)

            def _clear_console(self):
                if self.console_text:
                    self.console_text.delete(1.0, tk.END)

            def _send_command(self, event=None):
                if not self.command_entry:
                    return
                cmd = self.command_entry.get().strip()
                if not cmd:
                    return
                self._send_command_str(cmd)
                self.command_entry.delete(0, tk.END)

            def _send_command_str(self, cmd: str):
                self._append_console(f"> {cmd}", "info")

                if cmd.lower() == "help":
                    self._append_console("可用命令:")
                    self._append_console("  login  - 触发扫码登录流程")
                    self._append_console("  logout - 登出当前账号")
                    self._append_console("  status - 查看通道连接状态")
                    self._append_console("  clear  - 清空控制台")
                    return
                elif cmd.lower() == "clear":
                    self._clear_console()
                    return
                elif cmd.lower() == "login":
                    if self.bridge:
                        self.bridge.notify("channel.command", {"command": "login"})
                    self._append_console("正在请求登录二维码，请稍候...")
                    return
                elif cmd.lower() == "logout":
                    if self.bridge:
                        self.bridge.notify("channel.command", {"command": "logout"})
                    self._append_console("正在登出...")
                    return
                elif cmd.lower() == "status":
                    if self.bridge:
                        self.bridge.notify("channel.command", {"command": "status"})
                    else:
                        self._append_console("通道未启动")
                    return

                if self.bridge:
                    self.bridge.send_stdin(cmd)
                else:
                    self._append_console("通道未启动，无法发送命令", "error")

            def _handle_channel_message(self, params):
                channel_id = params.get("channelId")
                message = params.get("message", {})
                content = message.get("content", "")
                sender = message.get("sender", "unknown")

                self._append_console(f"[{channel_id}] {sender}: {content}")

                prompt = f"[{channel_id}] {sender}: {content}"
                reply = self.host_api.agent.call_ai(prompt)
                if self.bridge:
                    self.bridge.notify("channel.send", {
                        "channelId": channel_id,
                        "recipient": sender,
                        "content": reply
                    })
                    self._append_console(f"[AI回复] {reply[:100]}...", "success")

            def _handle_channel_event(self, params):
                event_type = params.get("event", {}).get("type", "unknown")
                self._append_console(f"[事件] {event_type}: {params}", "info")

            def on_unload(self):
                if self.bridge:
                    self.bridge.stop()

        return OpenClawChannelPlugin()

    def generate_gui_config_panel(self, parent, config: Dict[str, Any], save_callback) -> Any:
        schema = self.metadata.get("configSchema", {})
        ui_hints = self.metadata.get("uiHints", {})
        properties = schema.get("properties", {})
        if not properties:
            return None

        frame = tb.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        row = 0
        entries = {}

        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            default_val = prop_schema.get("default", "")
            description = prop_schema.get("description", prop_name)
            hint = ui_hints.get(prop_name, {})
            label_text = hint.get("label", description)

            current_val = config.get(prop_name, default_val)

            label = tb.Label(frame, text=label_text, font=("微软雅黑", 9))
            label.grid(row=row, column=0, sticky=tk.W, pady=3, padx=5)

            if prop_type == "boolean":
                var = tk.BooleanVar(value=current_val)
                widget = tb.Checkbutton(frame, variable=var, bootstyle="primary-round-toggle")
            elif prop_type in ("integer", "number"):
                var = tk.StringVar(value=str(current_val))
                widget = tb.Entry(frame, textvariable=var, width=20)
            elif prop_type == "string":
                is_password = hint.get("secret", False) or "password" in prop_name.lower()
                var = tk.StringVar(value=current_val)
                widget = tb.Entry(frame, textvariable=var, width=30, show="*" if is_password else "")
            elif prop_type == "array":
                val_str = ",".join(current_val) if isinstance(current_val, list) else str(current_val)
                var = tk.StringVar(value=val_str)
                widget = tb.Entry(frame, textvariable=var, width=30)
            else:
                var = tk.StringVar(value=str(current_val))
                widget = tb.Entry(frame, textvariable=var, width=30)

            widget.grid(row=row, column=1, sticky=tk.W, pady=3, padx=5)
            entries[prop_name] = (var, prop_type)
            row += 1

        def on_save():
            new_config = {}
            for prop_name, (var, prop_type) in entries.items():
                val = var.get()
                if prop_type == "boolean":
                    new_config[prop_name] = val
                elif prop_type == "integer":
                    new_config[prop_name] = int(val) if val.isdigit() else 0
                elif prop_type == "number":
                    try:
                        new_config[prop_name] = float(val)
                    except:
                        new_config[prop_name] = 0.0
                elif prop_type == "array":
                    new_config[prop_name] = [v.strip() for v in val.split(",") if v.strip()]
                else:
                    new_config[prop_name] = val
            save_callback(new_config)
            from tkinter import messagebox
            messagebox.showinfo("保存成功", "配置已保存")

        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        tb.Button(btn_frame, text="保存配置", command=on_save, bootstyle="success").pack()

        return frame

    def get_conversion_prompt(self) -> str:
        metadata = self.metadata
        tools = metadata.get("tools", [])
        commands = metadata.get("commands", [])

        prompt = f"""
请将以下 OpenClaw 插件转换为 TG HELPER PluginV2 原生插件。

【插件信息】
名称: {metadata.get('name')}
描述: {metadata.get('description')}
工具列表: {json.dumps(tools, ensure_ascii=False, indent=2)}
命令列表: {json.dumps(commands, ensure_ascii=False, indent=2)}
配置 Schema: {json.dumps(metadata.get('configSchema', {}), ensure_ascii=False, indent=2)}

【要求】
1. 生成一个继承自 PluginV2 的 Python 类。
2. 实现 get_manifest(), on_load(host_api), get_usage_info() 方法。
3. 在 on_load 中使用 host_api.agent.register_tool 注册上述工具。
4. 通过 host_api.events.subscribe 监听 MESSAGE_RECEIVED 事件实现命令。
5. 使用 host_api.get_plugin_config() / save_plugin_config() 管理配置。
6. 提供 get_settings_ui 方法，根据配置 schema 动态生成 GUI 设置面板。
7. 输出完整的 Python 代码，不要省略。
"""
        return prompt

    def get_source_code(self) -> str:
        sources = []
        for root, dirs, files in os.walk(self.plugin_path):
            for file in files:
                if file.endswith(('.js', '.ts', '.py', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read(5000)
                            sources.append(f"--- {file} ---\n{content}")
                    except:
                        pass
        return "\n\n".join(sources)
