# -*- coding: utf-8 -*-
"""
Plugin V2 基类和 HostAPI 接口定义（完整版，包含扩展字段）
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    capabilities: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    min_host_version: str = "2.0.0"
    min_tg_helper_version: str = "2.0.0"
    config_schema: Dict[str, Any] = field(default_factory=dict)
    ui_hints: Dict[str, Any] = field(default_factory=dict)
    hooks: List[str] = field(default_factory=list)
    entry_point: str = "main.py"
    keywords: List[str] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    commands: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: str) -> "PluginManifest":
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 容错：将 min_tg_helper_version 映射为 min_host_version
        if 'min_tg_helper_version' in data:
            data['min_host_version'] = data.pop('min_tg_helper_version')
        return cls(**data)


# ==================== HostAPI 抽象接口（全面扩展） ====================

class UIHostAPI(ABC):
    """UI 宿主 API"""
    @abstractmethod
    def display_message(self, text: str, is_user: bool = False) -> None:
        pass

    @abstractmethod
    def add_settings_tab(self, name: str, frame_factory: Callable[[Any], Any]) -> None:
        pass

    @abstractmethod
    def add_toolbar_button(self, text: str, command: Callable, icon: str = "") -> None:
        pass

    @abstractmethod
    def create_panel(self, title: str, position: str = "right") -> Any:
        pass

    @abstractmethod
    def set_theme(self, theme_name: str) -> bool:
        pass

    @abstractmethod
    def get_current_theme(self) -> str:
        pass

    @abstractmethod
    def set_font(self, family: str, size: int) -> bool:
        pass

    @abstractmethod
    def apply_styles(self, styles: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def register_message_renderer(self, name: str, renderer: Callable[[str, bool], str]) -> None:
        pass


class MemoryHostAPI(ABC):
    """记忆宿主 API"""
    @abstractmethod
    def add_short_term(self, role: str, content: str) -> None:
        pass

    @abstractmethod
    def get_short_term(self, limit: int = 50) -> str:
        pass

    @abstractmethod
    def add_long_term(self, text: str) -> None:
        pass

    @abstractmethod
    def query_memory(self, query: str, limit: int = 10) -> List[str]:
        pass

    @abstractmethod
    def register_backend(self, name: str, backend: Any) -> None:
        pass

    @abstractmethod
    def get_all_memories(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def clear_short_term(self) -> None:
        pass

    @abstractmethod
    def set_memory_config(self, key: str, value: Any) -> None:
        pass


class AgentHostAPI(ABC):
    """Agent 宿主 API"""
    @abstractmethod
    def register_tool(self, tool_def: Dict[str, Any], handler: Callable) -> None:
        pass

    @abstractmethod
    def register_middleware(self, name: str, middleware: Callable) -> None:
        pass

    @abstractmethod
    def call_ai(self, prompt: str, system_prompt: str = "", tool_choice: str = "auto") -> str:
        pass

    @abstractmethod
    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def set_system_prompt_template(self, template: str) -> None:
        pass

    @abstractmethod
    def add_pre_prompt_hook(self, hook: Callable[[str], str]) -> None:
        pass

    @abstractmethod
    def add_post_response_hook(self, hook: Callable[[str], str]) -> None:
        pass


class EventsHostAPI(ABC):
    """事件宿主 API"""
    @abstractmethod
    def subscribe(self, event_name: str, callback: Callable, priority: int = 0, once: bool = False) -> str:
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        pass

    @abstractmethod
    def emit(self, event_name: str, data: Any = None) -> None:
        pass

    @abstractmethod
    def get_subscriber_count(self, event_name: str) -> int:
        pass


class ToolsHostAPI(ABC):
    """工具宿主 API"""
    @abstractmethod
    def call_tool(self, tool_name: str, **kwargs) -> str:
        pass

    @abstractmethod
    def list_tools(self) -> List[str]:
        pass

    @abstractmethod
    def override_tool(self, tool_name: str, handler: Callable) -> bool:
        pass


class FSHostAPI(ABC):
    """文件系统宿主 API"""
    @abstractmethod
    def read_file(self, path: str, max_chars: int = 8000) -> str:
        pass

    @abstractmethod
    def write_file(self, path: str, content: str) -> bool:
        pass

    @abstractmethod
    def get_plugin_data_dir(self) -> str:
        pass

    @abstractmethod
    def list_directory(self, path: str) -> List[str]:
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        pass


class SystemHostAPI(ABC):
    """系统宿主 API"""
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def get_version(self) -> str:
        pass

    @abstractmethod
    def get_all_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def register_shutdown_hook(self, hook: Callable[[], None]) -> None:
        pass


class HostAPI(ABC):
    """宿主 API 总入口"""
    @property
    @abstractmethod
    def ui(self) -> UIHostAPI:
        pass

    @property
    @abstractmethod
    def memory(self) -> MemoryHostAPI:
        pass

    @property
    @abstractmethod
    def agent(self) -> AgentHostAPI:
        pass

    @property
    @abstractmethod
    def events(self) -> EventsHostAPI:
        pass

    @property
    @abstractmethod
    def tools(self) -> ToolsHostAPI:
        pass

    @property
    @abstractmethod
    def fs(self) -> FSHostAPI:
        pass

    @property
    @abstractmethod
    def system(self) -> SystemHostAPI:
        pass

    @abstractmethod
    def get_plugin_config(self, plugin_id: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_plugin_config(self, config: Dict[str, Any], plugin_id: str = None) -> None:
        pass


# ==================== Hook 装饰器 ====================
class HookSpec(ABC):
    """钩子规范"""
    pass


class HookImpl:
    """钩子实现标记"""
    def __init__(self, hook_name: str, priority: int = 0):
        self.hook_name = hook_name
        self.priority = priority

    def __call__(self, func):
        func._hook_name = self.hook_name
        func._hook_priority = self.priority
        return func


# ==================== PluginV2 基类 ====================
class PluginV2(ABC):
    """TG HELPER Plugin V2 基类"""
    def __init__(self):
        self.manifest: Optional[PluginManifest] = None
        self.host_api: Optional[HostAPI] = None
        self._enabled: bool = True
        self._plugin_dir: str = ""

    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        pass

    @abstractmethod
    def on_load(self, host_api: HostAPI) -> None:
        pass

    def on_enable(self) -> None:
        self._enabled = True

    def on_disable(self) -> None:
        self._enabled = False

    def on_unload(self) -> None:
        pass

    def on_config_changed(self, new_config: Dict[str, Any]) -> None:
        pass

    def get_settings_ui(self, parent: Any) -> Optional[Any]:
        return None

    def get_usage_info(self) -> Optional[Dict[str, Any]]:
        return None

    def is_enabled(self) -> bool:
        return self._enabled

    def set_plugin_dir(self, path: str):
        self._plugin_dir = path

    def get_plugin_dir(self) -> str:
        return self._plugin_dir

    def get_hook_implementations(self) -> Dict[str, List[Callable]]:
        hooks: Dict[str, List[Callable]] = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_hook_name'):
                hook_name = getattr(attr, '_hook_name')
                priority = getattr(attr, '_hook_priority', 0)
                if hook_name not in hooks:
                    hooks[hook_name] = []
                hooks[hook_name].append((priority, attr))
        for hook_name in hooks:
            hooks[hook_name] = [h for _, h in sorted(hooks[hook_name], key=lambda x: x[0])]
        return hooks
