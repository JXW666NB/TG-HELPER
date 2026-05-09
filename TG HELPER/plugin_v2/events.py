# -*- coding: utf-8 -*-
"""
事件总线——发布-订阅模式实现

设计参考：
- OpenClaw 的 Hook 系统[reference:2]
- Python pluggy 的 hook 机制[reference:3]
- 支持优先级、异步处理、事件传播控制

事件是主程序与插件之间的核心通信机制。插件通过 HostAPI.events.subscribe 订阅事件，
主程序在关键位置通过 EventBus.emit 触发事件。
"""

import threading
import time
from typing import Dict, List, Set, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import total_ordering
import inspect


class EventPriority(Enum):
    """事件处理优先级"""
    HIGHEST = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    LOWEST = 4


@total_ordering
@dataclass
class EventHandler:
    """事件处理器包装"""
    callback: Callable
    priority: EventPriority = EventPriority.NORMAL
    plugin_id: str = ""
    once: bool = False  # 是否只执行一次
    filter_func: Optional[Callable] = None  # 事件过滤函数
    
    def __lt__(self, other):
        if not isinstance(other, EventHandler):
            return NotImplemented
        return self.priority.value < other.priority.value


@dataclass
class Event:
    """事件对象"""
    name: str                       # 事件名称，如 "message.received"
    data: Any = None                # 事件携带的数据
    source: str = ""                # 事件来源（插件ID或"system"）
    timestamp: float = field(default_factory=time.time)
    propagation_stopped: bool = False   # 是否停止传播
    prevent_default: bool = False       # 是否阻止默认行为
    
    def stop_propagation(self):
        """停止事件传播（后续处理器不再执行）"""
        self.propagation_stopped = True
    
    def prevent_default_action(self):
        """阻止默认行为"""
        self.prevent_default = True


class SystemEvents:
    """系统预定义事件"""
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ENABLED = "plugin.enabled"
    PLUGIN_DISABLED = "plugin.disabled"
    ALL_PLUGINS_LOADED = "plugins.all_loaded"
    AGENT_BEFORE_START = "agent.before_start"
    AGENT_AFTER_START = "agent.after_start"
    AGENT_BEFORE_STOP = "agent.before_stop"
    AGENT_AFTER_STOP = "agent.after_stop"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_BEFORE_SEND = "message.before_send"
    MESSAGE_AFTER_SEND = "message.after_send"
    AI_BEFORE_CALL = "ai.before_call"
    AI_AFTER_CALL = "ai.after_call"
    AI_BEFORE_PROMPT_BUILD = "ai.before_prompt_build"
    AI_AFTER_PROMPT_BUILD = "ai.after_prompt_build"
    TOOL_BEFORE_EXECUTE = "tool.before_execute"
    TOOL_AFTER_EXECUTE = "tool.after_execute"
    TOOL_EXECUTE_FAILED = "tool.execute_failed"
    MEMORY_BEFORE_ADD = "memory.before_add"
    MEMORY_AFTER_ADD = "memory.after_add"
    MEMORY_BEFORE_QUERY = "memory.before_query"
    MEMORY_AFTER_QUERY = "memory.after_query"
    UI_READY = "ui.ready"
    UI_BEFORE_RENDER = "ui.before_render"
    UI_AFTER_RENDER = "ui.after_render"
    UI_SETTINGS_TAB_REGISTER = "ui.settings_tab.register"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_CONFIG_CHANGED = "system.config_changed"


class EventBus:
    """事件总线——单例模式"""
    
    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []  # 匹配所有事件的处理器
        self._emit_lock = threading.RLock()
        self._debug_mode = False
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式（打印事件日志）"""
        self._debug_mode = enabled
    
    def subscribe(self,
                  event_name: str,
                  callback: Callable,
                  priority: EventPriority = EventPriority.NORMAL,
                  plugin_id: str = "",
                  once: bool = False,
                  filter_func: Optional[Callable] = None) -> str:
        """
        订阅事件
        
        Args:
            event_name: 事件名称，支持 "*" 通配符匹配所有事件
            callback: 回调函数，接收一个 Event 参数
            priority: 处理优先级
            plugin_id: 插件 ID
            once: 是否只执行一次
            filter_func: 事件过滤函数
            
        Returns:
            订阅 ID（可用于取消订阅）
        """
        handler = EventHandler(
            callback=callback,
            priority=priority,
            plugin_id=plugin_id,
            once=once,
            filter_func=filter_func
        )
        
        with self._emit_lock:
            if event_name == "*":
                self._wildcard_handlers.append(handler)
                self._wildcard_handlers.sort()
            else:
                if event_name not in self._handlers:
                    self._handlers[event_name] = []
                self._handlers[event_name].append(handler)
                self._handlers[event_name].sort()
        
        # 返回订阅 ID（使用 callback 的内存地址）
        return f"{event_name}:{id(callback)}"
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        with self._emit_lock:
            parts = subscription_id.split(":", 1)
            if len(parts) != 2:
                return False
            event_name, callback_id = parts
            
            if event_name == "*":
                for i, h in enumerate(self._wildcard_handlers):
                    if str(id(h.callback)) == callback_id:
                        self._wildcard_handlers.pop(i)
                        return True
            elif event_name in self._handlers:
                for i, h in enumerate(self._handlers[event_name]):
                    if str(id(h.callback)) == callback_id:
                        self._handlers[event_name].pop(i)
                        return True
        return False
    
    def unsubscribe_all_plugin(self, plugin_id: str):
        """取消插件的所有订阅"""
        with self._emit_lock:
            # 清理普通事件订阅
            for event_name in list(self._handlers.keys()):
                self._handlers[event_name] = [
                    h for h in self._handlers[event_name]
                    if h.plugin_id != plugin_id
                ]
            # 清理通配符订阅
            self._wildcard_handlers = [
                h for h in self._wildcard_handlers
                if h.plugin_id != plugin_id
            ]
    
    def emit(self,
             event_name: str,
             data: Any = None,
             source: str = "system",
             async_mode: bool = False) -> Event:
        """
        触发事件
        
        Args:
            event_name: 事件名称
            data: 事件携带的数据
            source: 事件来源
            async_mode: 是否异步执行（暂未实现，预留）
            
        Returns:
            触发后的事件对象（可能被处理器修改）
        """
        event = Event(name=event_name, data=data, source=source)
        
        if self._debug_mode:
            print(f"[EventBus] Emit: {event_name} from {source}")
        
        # 收集所有需要执行的处理器
        handlers_to_run: List[EventHandler] = []
        
        with self._emit_lock:
            # 添加通配符处理器
            handlers_to_run.extend(self._wildcard_handlers)
            # 添加特定事件处理器
            if event_name in self._handlers:
                handlers_to_run.extend(self._handlers[event_name])
        
        # 按优先级排序
        handlers_to_run.sort()
        
        # 执行处理器
        once_handlers_to_remove = []
        
        for handler in handlers_to_run:
            if event.propagation_stopped:
                break
            
            # 检查过滤器
            if handler.filter_func and not handler.filter_func(event):
                continue
            
            try:
                handler.callback(event)
            except Exception as e:
                print(f"[EventBus] Error in handler for {event_name}: {e}")
                import traceback
                traceback.print_exc()
            
            if handler.once:
                once_handlers_to_remove.append(handler)
        
        # 清理 once 处理器
        if once_handlers_to_remove:
            with self._emit_lock:
                for handler in once_handlers_to_remove:
                    if event_name == "*":
                        if handler in self._wildcard_handlers:
                            self._wildcard_handlers.remove(handler)
                    elif event_name in self._handlers:
                        if handler in self._handlers[event_name]:
                            self._handlers[event_name].remove(handler)
        
        return event
    
    def get_subscriber_count(self, event_name: str) -> int:
        """获取某事件的订阅者数量"""
        count = 0
        with self._emit_lock:
            if event_name in self._handlers:
                count += len(self._handlers[event_name])
            count += len(self._wildcard_handlers)
        return count
    
    def list_events(self) -> List[str]:
        """列出所有有订阅的事件"""
        with self._emit_lock:
            return list(self._handlers.keys())
    
    def clear(self):
        """清空所有订阅（慎用）"""
        with self._emit_lock:
            self._handlers.clear()
            self._wildcard_handlers.clear()
