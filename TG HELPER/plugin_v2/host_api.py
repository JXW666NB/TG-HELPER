# -*- coding: utf-8 -*-
"""
HostAPI 实现（完整版）
"""
import os
import json
import threading
from typing import Dict, List, Optional, Any, Callable

from config import banben

# 插件配置写锁（所有插件共享，防止并发写损坏 JSON）
_PLUGIN_CONFIG_LOCK = threading.Lock()

from .base import (
    HostAPI, UIHostAPI, MemoryHostAPI, AgentHostAPI,
    EventsHostAPI, ToolsHostAPI, FSHostAPI, SystemHostAPI
)
from .events import EventBus, Event, SystemEvents
from .capabilities import CapabilityManager


class HostAPIImpl(HostAPI):
    def __init__(self, plugin_id: str, gui_instance: Any, memory_instance: Any,
                 agent_instance: Any, tools_instance: Any, config_instance: Any,
                 cap_manager: CapabilityManager, event_bus: EventBus):
        self._plugin_id = plugin_id
        self._gui = gui_instance
        self._memory = memory_instance
        self._agent = agent_instance
        self._tools = tools_instance
        self._config = config_instance
        self._cap_manager = cap_manager
        self._event_bus = event_bus

        self._ui_api = UIHostAPIImpl(plugin_id, gui_instance, cap_manager, event_bus)
        self._memory_api = MemoryHostAPIImpl(plugin_id, memory_instance, cap_manager, event_bus)
        self._agent_api = AgentHostAPIImpl(plugin_id, agent_instance, tools_instance, cap_manager, event_bus)
        self._events_api = EventsHostAPIImpl(plugin_id, event_bus, cap_manager)
        self._tools_api = ToolsHostAPIImpl(plugin_id, tools_instance, cap_manager)
        self._fs_api = FSHostAPIImpl(plugin_id, cap_manager)
        self._system_api = SystemHostAPIImpl(plugin_id, config_instance, cap_manager)

    @property
    def ui(self) -> UIHostAPI:
        return self._ui_api

    @property
    def memory(self) -> MemoryHostAPI:
        return self._memory_api

    @property
    def agent(self) -> AgentHostAPI:
        return self._agent_api

    @property
    def events(self) -> EventsHostAPI:
        return self._events_api

    @property
    def tools(self) -> ToolsHostAPI:
        return self._tools_api

    @property
    def fs(self) -> FSHostAPI:
        return self._fs_api

    @property
    def system(self) -> SystemHostAPI:
        return self._system_api

    def get_plugin_config(self, plugin_id: str = None) -> Dict[str, Any]:
        if plugin_id is None:
            plugin_id = self._plugin_id
        config_file = os.path.expanduser("~/.agent_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get("plugins", {}).get(plugin_id, {})
            except:
                pass
        return {}

    def save_plugin_config(self, config: Dict[str, Any], plugin_id: str = None) -> None:
        if plugin_id is None:
            plugin_id = self._plugin_id
        config_file = os.path.expanduser("~/.agent_config.json")
        with _PLUGIN_CONFIG_LOCK:
            all_config = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        all_config = json.load(f)
                except Exception:
                    all_config = {}
            if "plugins" not in all_config:
                all_config["plugins"] = {}
            all_config["plugins"][plugin_id] = config
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(all_config, f, indent=2, ensure_ascii=False)


class UIHostAPIImpl(UIHostAPI):
    def __init__(self, plugin_id: str, gui: Any, cap_manager: CapabilityManager, event_bus: EventBus):
        self._plugin_id = plugin_id
        self._gui = gui
        self._cap_manager = cap_manager
        self._event_bus = event_bus
        self._message_renderers = {}

    def _check_permission(self, capability: str) -> bool:
        if not self._cap_manager.check_permission(self._plugin_id, capability):
            print(f"[HostAPI] 插件 {self._plugin_id} 无权限执行 {capability}")
            return False
        return True

    def display_message(self, text: str, is_user: bool = False) -> None:
        if not self._check_permission("ui.display"):
            return
        def _display():
            if self._gui:
                if is_user:
                    self._gui.display_user_message(text)
                else:
                    self._gui.display_assistant_message(text)
        if threading.current_thread() is threading.main_thread():
            _display()
        else:
            if hasattr(self._gui, 'schedule_on_main'):
                self._gui.schedule_on_main(_display)

    def add_settings_tab(self, name: str, frame_factory: Callable[[Any], Any]) -> None:
        if not self._check_permission("ui.settings_tab"):
            return
        def _add():
            if self._gui and hasattr(self._gui, 'notebook'):
                frame = frame_factory(self._gui.notebook)
                self._gui.notebook.add(frame, text=name)
        if hasattr(self._gui, 'schedule_on_main'):
            self._gui.schedule_on_main(_add)

    def add_toolbar_button(self, text: str, command: Callable, icon: str = "") -> None:
        if not self._check_permission("ui.modify"):
            return
        print(f"[HostAPI] 插件 {self._plugin_id} 请求添加工具栏按钮: {text}")

    def create_panel(self, title: str, position: str = "right") -> Any:
        if not self._check_permission("ui.modify"):
            return None
        return None

    def set_theme(self, theme_name: str) -> bool:
        if not self._check_permission("ui.modify"):
            return False
        def _apply():
            if self._gui:
                self._gui.change_theme(theme_name)
        if hasattr(self._gui, 'schedule_on_main'):
            self._gui.schedule_on_main(_apply)
        return True

    def get_current_theme(self) -> str:
        if self._gui:
            return getattr(self._gui, 'current_theme', 'flatly')
        return 'flatly'

    def set_font(self, family: str, size: int) -> bool:
        if not self._check_permission("ui.modify"):
            return False
        print(f"[HostAPI] 字体设置请求: family={family}, size={size} (PyQt6 使用 QSS 管理字体，此请求已忽略)")
        return True

    def apply_styles(self, styles: Dict[str, Any]) -> bool:
        if not self._check_permission("ui.modify"):
            return False
        def _apply():
            if self._gui:
                if not hasattr(self._gui, '_plugin_styles'):
                    self._gui._plugin_styles = {}
                self._gui._plugin_styles.update(styles)
                self._event_bus.emit("ui.styles_changed", styles, self._plugin_id)
        if hasattr(self._gui, 'schedule_on_main'):
            self._gui.schedule_on_main(_apply)
        return True

    def register_message_renderer(self, name: str, renderer: Callable[[str, bool], str]) -> None:
        if not self._check_permission("ui.modify"):
            return
        self._message_renderers[name] = renderer


class MemoryHostAPIImpl(MemoryHostAPI):
    def __init__(self, plugin_id: str, memory: Any, cap_manager: CapabilityManager, event_bus: EventBus):
        self._plugin_id = plugin_id
        self._memory = memory
        self._cap_manager = cap_manager
        self._event_bus = event_bus
        self._custom_backends = {}

    def _check_permission(self, capability: str) -> bool:
        return self._cap_manager.check_permission(self._plugin_id, capability)

    def add_short_term(self, role: str, content: str) -> None:
        if not self._check_permission("memory.write"):
            return
        self._memory.add_short_term(role, content)

    def get_short_term(self, limit: int = 50) -> str:
        if not self._check_permission("memory.read"):
            return ""
        return self._memory.get_short_term(max_entries=limit)

    def add_long_term(self, text: str) -> None:
        if not self._check_permission("memory.write"):
            return
        self._memory.add_long_term(text)

    def query_memory(self, query: str, limit: int = 10) -> List[str]:
        if not self._check_permission("memory.read"):
            return []
        return self._memory.query_long_term(query, limit)

    def register_backend(self, name: str, backend: Any) -> None:
        if not self._check_permission("memory.modify"):
            return
        self._custom_backends[name] = backend

    def get_all_memories(self) -> Dict[str, Any]:
        if not self._check_permission("memory.read"):
            return {}
        return {
            "short_term": self._memory.get_short_term(),
            "long_term": self._memory.get_long_term(),
            "summaries": self._memory.get_summaries()
        }

    def clear_short_term(self) -> None:
        if not self._check_permission("memory.write"):
            return
        self._memory.clear_short_term()

    def set_memory_config(self, key: str, value: Any) -> None:
        if not self._check_permission("memory.modify"):
            return
        if hasattr(self._memory, 'config'):
            self._memory.config[key] = value


class AgentHostAPIImpl(AgentHostAPI):
    def __init__(self, plugin_id: str, agent: Any, tools: Any, cap_manager: CapabilityManager, event_bus: EventBus):
        self._plugin_id = plugin_id
        self._agent = agent
        self._tools = tools
        self._cap_manager = cap_manager
        self._event_bus = event_bus
        self._middlewares = []
        self._pre_prompt_hooks = []
        self._post_response_hooks = []

    def _check_permission(self, capability: str) -> bool:
        return self._cap_manager.check_permission(self._plugin_id, capability)

    # 不允许插件覆盖的核心工具列表
    _PROTECTED_TOOLS = {
        "execute_command", "run_command", "os", "sys", "eval", "exec",
        "__import__", "open", "subprocess", "shutil", "socket",
    }

    def register_tool(self, tool_def: Dict[str, Any], handler: Callable) -> None:
        if not self._check_permission("agent.tool_register"):
            return
        tool_name = tool_def.get("name")
        if not tool_name:
            return
        if tool_name in self._PROTECTED_TOOLS:
            print(f"[HostAPI] 拒绝注册受保护的工具名: {tool_name}")
            return
        # 避免覆盖已存在的核心方法
        if hasattr(self._tools, tool_name) and callable(getattr(self._tools, tool_name)):
            existing = getattr(self._tools, tool_name)
            if not hasattr(existing, '_is_plugin_tool'):
                print(f"[HostAPI] 警告: 工具 {tool_name} 已存在，将被插件版本覆盖")
        def wrapped_handler(**kwargs):
            try:
                return handler(kwargs)
            except Exception as e:
                return f"工具执行错误: {e}"
        wrapped_handler._is_plugin_tool = True
        wrapped_handler._plugin_id = self._plugin_id
        setattr(self._tools, tool_name, wrapped_handler)
        # 同时注册到 Tools._plugin_tools，供 AI 系统提示词动态发现
        if hasattr(self._tools, 'register_plugin_tool'):
            self._tools.register_plugin_tool(
                tool_name=tool_name,
                description=tool_def.get("description", ""),
                parameters=tool_def.get("parameters", {}),
                plugin_id=self._plugin_id,
            )

    def register_middleware(self, name: str, middleware: Callable) -> None:
        if not self._check_permission("agent.intercept"):
            return
        self._middlewares.append(middleware)

    def call_ai(self, prompt: str, system_prompt: str = "", tool_choice: str = "auto") -> str:
        if not self._check_permission("agent.intercept"):
            return "无权限调用 AI"
        for hook in self._pre_prompt_hooks:
            prompt = hook(prompt)
        # 实际调用由主程序处理，这里通过事件请求
        response = [None]
        event = threading.Event()
        def callback(resp):
            response[0] = resp
            event.set()
        self._event_bus.emit("agent.custom_call", {"prompt": prompt, "system_prompt": system_prompt, "callback": callback}, self._plugin_id)
        event.wait(timeout=60)
        if response[0] is None:
            return "AI 调用超时"
        for hook in self._post_response_hooks:
            response[0] = hook(response[0])
        return response[0]

    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, str]]:
        if not self._check_permission("memory.read"):
            return []
        return self._agent.shared_conversation_history[-limit:]

    def set_system_prompt_template(self, template: str) -> None:
        if not self._check_permission("agent.modify"):
            return
        self._agent._system_prompt_template = template

    def add_pre_prompt_hook(self, hook: Callable[[str], str]) -> None:
        self._pre_prompt_hooks.append(hook)

    def add_post_response_hook(self, hook: Callable[[str], str]) -> None:
        self._post_response_hooks.append(hook)


class EventsHostAPIImpl(EventsHostAPI):
    def __init__(self, plugin_id: str, event_bus: EventBus, cap_manager: CapabilityManager):
        self._plugin_id = plugin_id
        self._event_bus = event_bus
        self._cap_manager = cap_manager

    def subscribe(self, event_name: str, callback: Callable, priority: int = 0, once: bool = False) -> str:
        from .events import EventPriority
        prio_map = {-2: EventPriority.LOWEST, -1: EventPriority.LOW, 0: EventPriority.NORMAL, 1: EventPriority.HIGH, 2: EventPriority.HIGHEST}
        priority_enum = prio_map.get(priority, EventPriority.NORMAL)
        return self._event_bus.subscribe(event_name=event_name, callback=callback, priority=priority_enum, plugin_id=self._plugin_id, once=once)

    def unsubscribe(self, subscription_id: str) -> bool:
        return self._event_bus.unsubscribe(subscription_id)

    def emit(self, event_name: str, data: Any = None) -> None:
        self._event_bus.emit(event_name, data, self._plugin_id)

    def get_subscriber_count(self, event_name: str) -> int:
        return self._event_bus.get_subscriber_count(event_name)


class ToolsHostAPIImpl(ToolsHostAPI):
    def __init__(self, plugin_id: str, tools: Any, cap_manager: CapabilityManager):
        self._plugin_id = plugin_id
        self._tools = tools
        self._cap_manager = cap_manager

    def call_tool(self, tool_name: str, **kwargs) -> str:
        tool_method = getattr(self._tools, tool_name, None)
        if tool_method is None:
            return f"错误：未知工具 {tool_name}"
        try:
            return tool_method(**kwargs)
        except Exception as e:
            return f"工具执行异常：{str(e)}"

    def list_tools(self) -> List[str]:
        tools = []
        for attr in dir(self._tools):
            if callable(getattr(self._tools, attr)) and not attr.startswith('_'):
                tools.append(attr)
        return tools

    def override_tool(self, tool_name: str, handler: Callable) -> bool:
        if not self._check_permission("agent.modify"):
            return False
        if tool_name in self._PROTECTED_TOOLS:
            print(f"[HostAPI] 拒绝覆盖受保护的工具: {tool_name}")
            return False
        if not hasattr(self._tools, tool_name):
            return False
        setattr(self._tools, tool_name, handler)
        return True


class FSHostAPIImpl(FSHostAPI):
    def __init__(self, plugin_id: str, cap_manager: CapabilityManager):
        self._plugin_id = plugin_id
        self._cap_manager = cap_manager
        self._plugin_data_dir = os.path.join("./plugin_data", plugin_id)
        os.makedirs(self._plugin_data_dir, exist_ok=True)

    def _check_permission(self, capability: str) -> bool:
        return self._cap_manager.check_permission(self._plugin_id, capability)

    def _is_safe_path(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        if abs_path.startswith(os.path.abspath(self._plugin_data_dir)):
            return True
        if self._check_permission("fs.write"):
            user_dir = os.path.expanduser("~")
            if abs_path.startswith(user_dir):
                return True
        return False

    def read_file(self, path: str, max_chars: int = 8000) -> str:
        if not self._check_permission("fs.read"):
            return "错误：无文件读取权限"
        if not self._is_safe_path(path):
            return "错误：不允许访问该路径"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read(max_chars)
        except Exception as e:
            return f"读取文件失败：{e}"

    def write_file(self, path: str, content: str) -> bool:
        if not self._check_permission("fs.write"):
            return False
        if not self._is_safe_path(path):
            return False
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[HostAPI] 写入文件失败 ({path}): {e}")
            return False

    def get_plugin_data_dir(self) -> str:
        return self._plugin_data_dir

    def list_directory(self, path: str) -> List[str]:
        if not self._check_permission("fs.read"):
            return []
        if not self._is_safe_path(path):
            return []
        try:
            return os.listdir(path)
        except Exception as e:
            print(f"[HostAPI] 列出目录失败 ({path}): {e}")
            return []

    def delete_file(self, path: str) -> bool:
        if not self._check_permission("fs.write"):
            return False
        if not self._is_safe_path(path):
            return False
        try:
            os.remove(path)
            return True
        except Exception as e:
            print(f"[HostAPI] 删除文件失败 ({path}): {e}")
            return False


class SystemHostAPIImpl(SystemHostAPI):
    def __init__(self, plugin_id: str, config: Any, cap_manager: CapabilityManager):
        self._plugin_id = plugin_id
        self._config = config
        self._cap_manager = cap_manager
        self._shutdown_hooks = []

    def _check_permission(self, capability: str) -> bool:
        return self._cap_manager.check_permission(self._plugin_id, capability)

    def get_config(self, key: str, default: Any = None) -> Any:
        return getattr(self._config, key, default)

    def set_config(self, key: str, value: Any) -> None:
        if not self._check_permission("system.config"):
            return
        setattr(self._config, key, value)

    def get_version(self) -> str:
        return banben

    def get_all_config(self) -> Dict[str, Any]:
        if not self._check_permission("system.config"):
            return {}
        return {k: v for k, v in self._config.__dict__.items() if not k.startswith('_')}

    def register_shutdown_hook(self, hook: Callable[[], None]) -> None:
        self._shutdown_hooks.append(hook)
