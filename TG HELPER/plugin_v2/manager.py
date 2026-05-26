# -*- coding: utf-8 -*-
"""
Plugin V2 管理器（完整版）
支持原生 PluginV2、OpenClaw 适配器、小狸 CLI 适配器
"""
import os
import sys
import json
import importlib.util
import traceback
from typing import Dict, List, Optional, Any, Set, Callable

from .base import PluginV2, HostAPI, PluginManifest
from .host_api import HostAPIImpl
from .events import EventBus, SystemEvents
from .capabilities import CapabilityManager


class PluginManagerV2:
    _instance: Optional["PluginManagerV2"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._hooks: Dict[str, List[tuple]] = {}
        self._load_order: List[str] = []
        self._cap_manager = CapabilityManager()
        self._event_bus = EventBus()
        self._gui_instance = None
        self._memory_instance = None
        self._agent_instance = None
        self._tools_instance = None
        self._config_instance = None
        self._plugins_dirs: List[str] = ["./plugins", os.path.expanduser("~/.tg_helper/plugins")]
        self._hot_reload_enabled = True
        self._debug_mode = False

        # 适配器系统
        self._adapters = []
        self._load_adapters()

    def _load_adapters(self):
        """加载所有适配器"""
        try:
            from .adapters import OpenClawAdapter, XiaoliAdapter
            self._adapters = [OpenClawAdapter, XiaoliAdapter]
        except ImportError as e:
            print(f"[PluginManager] 适配器导入失败: {e}")
            self._adapters = []

    def set_gui_instance(self, gui: Any):
        self._gui_instance = gui

    def set_memory_instance(self, memory: Any):
        self._memory_instance = memory

    def set_agent_instance(self, agent: Any):
        self._agent_instance = agent

    def set_tools_instance(self, tools: Any):
        self._tools_instance = tools

    def set_config_instance(self, config: Any):
        self._config_instance = config

    def set_debug_mode(self, enabled: bool):
        self._debug_mode = enabled
        self._event_bus.set_debug_mode(enabled)

    def add_plugins_dir(self, path: str):
        if path not in self._plugins_dirs:
            self._plugins_dirs.append(path)

    def _find_adapter_for_path(self, plugin_path: str):
        """查找能处理该路径的适配器"""
        for adapter_cls in self._adapters:
            try:
                adapter = adapter_cls(plugin_path)
                if adapter.can_handle():
                    return adapter
            except Exception as e:
                print(f"[PluginManager] 适配器检测失败 {adapter_cls.__name__}: {e}")
        return None

    def discover_plugins(self) -> List[str]:
        """发现所有可能的插件路径（包括文件夹和单文件）"""
        discovered = []
        for search_dir in self._plugins_dirs:
            if not os.path.exists(search_dir):
                continue
            for item in os.listdir(search_dir):
                item_path = os.path.join(search_dir, item)

                # 1. 文件夹：检查 plugin.json 或适配器
                if os.path.isdir(item_path):
                    manifest_path = os.path.join(item_path, "plugin.json")
                    if os.path.exists(manifest_path):
                        discovered.append(item_path)
                    else:
                        adapter = self._find_adapter_for_path(item_path)
                        if adapter:
                            discovered.append(item_path)
                            print(f"[PluginManager] 发现适配器插件(目录): {item_path} (适配器: {type(adapter).__name__})")

                # 2. 单文件 .py：尝试适配器（主要是小狸）
                elif os.path.isfile(item_path) and item_path.endswith('.py') and not item.startswith('__'):
                    adapter = self._find_adapter_for_path(item_path)
                    if adapter:
                        discovered.append(item_path)
                        print(f"[PluginManager] 发现适配器插件(单文件): {item_path} (适配器: {type(adapter).__name__})")

        return discovered

    def load_plugin(self, plugin_path: str) -> Optional[str]:
        """加载插件（自动选择原生或适配器）"""
        # 如果是目录，检查 plugin.json
        if os.path.isdir(plugin_path):
            manifest_path = os.path.join(plugin_path, "plugin.json")
            if os.path.exists(manifest_path):
                return self._load_native_plugin(plugin_path, manifest_path)

        # 尝试适配器（目录或文件均可）
        adapter = self._find_adapter_for_path(plugin_path)
        if adapter:
            return self._load_adapter_plugin(adapter, plugin_path)

        print(f"[PluginManager] 无法识别插件格式: {plugin_path}")
        return None

    def _load_native_plugin(self, plugin_path: str, manifest_path: str) -> Optional[str]:
        """加载原生 PluginV2 插件"""
        try:
            manifest = PluginManifest.from_file(manifest_path)
            if manifest.id in self._plugins:
                return manifest.id

            entry_path = os.path.join(plugin_path, manifest.entry_point)
            if not os.path.exists(entry_path):
                print(f"[PluginManager] 入口文件不存在: {entry_path}")
                return None

            spec = importlib.util.spec_from_file_location(manifest.id, entry_path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[manifest.id] = module
            spec.loader.exec_module(module)

            plugin_instance = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PluginV2) and attr != PluginV2:
                    plugin_instance = attr()
                    break
            if plugin_instance is None:
                print(f"[PluginManager] 未找到 PluginV2 子类: {plugin_path}")
                return None

            plugin_instance.manifest = manifest
            plugin_instance.set_plugin_dir(plugin_path)

            host_api = HostAPIImpl(
                plugin_id=manifest.id,
                gui_instance=self._gui_instance,
                memory_instance=self._memory_instance,
                agent_instance=self._agent_instance,
                tools_instance=self._tools_instance,
                config_instance=self._config_instance,
                cap_manager=self._cap_manager,
                event_bus=self._event_bus
            )
            plugin_instance.host_api = host_api

            self._cap_manager.grant_permission(manifest.id, manifest.permissions)
            plugin_instance.on_load(host_api)
            self._register_plugin_hooks(plugin_instance, manifest)

            self._plugins[manifest.id] = {
                "instance": plugin_instance,
                "manifest": manifest,
                "module": module,
                "path": plugin_path,
                "enabled": True,
                "host_api": host_api
            }
            self._load_order.append(manifest.id)
            self._event_bus.emit(SystemEvents.PLUGIN_LOADED, {"plugin_id": manifest.id}, "system")
            print(f"[PluginManager] ✅ 原生插件 {manifest.id} 加载成功")
            return manifest.id

        except Exception as e:
            print(f"[PluginManager] 加载原生插件失败 {plugin_path}: {e}")
            traceback.print_exc()
            return None

    def _load_adapter_plugin(self, adapter, plugin_path: str) -> Optional[str]:
        """通过适配器加载插件"""
        try:
            metadata = adapter.load_metadata()
            plugin_id = metadata["id"]

            if plugin_id in self._plugins:
                return plugin_id

            host_api = HostAPIImpl(
                plugin_id=plugin_id,
                gui_instance=self._gui_instance,
                memory_instance=self._memory_instance,
                agent_instance=self._agent_instance,
                tools_instance=self._tools_instance,
                config_instance=self._config_instance,
                cap_manager=self._cap_manager,
                event_bus=self._event_bus
            )

            plugin_instance = adapter.create_plugin_instance(host_api)
            plugin_instance.manifest = PluginManifest(**metadata)
            plugin_instance.set_plugin_dir(plugin_path)
            plugin_instance.host_api = host_api

            self._cap_manager.grant_permission(plugin_id, metadata.get("permissions", []))
            plugin_instance.on_load(host_api)
            self._register_plugin_hooks(plugin_instance, plugin_instance.manifest)

            self._plugins[plugin_id] = {
                "instance": plugin_instance,
                "manifest": plugin_instance.manifest,
                "module": None,
                "path": plugin_path,
                "enabled": True,
                "host_api": host_api,
                "adapter": adapter,
                "adapter_type": type(adapter).__name__
            }
            self._load_order.append(plugin_id)
            self._event_bus.emit(SystemEvents.PLUGIN_LOADED, {"plugin_id": plugin_id, "adapter": True}, "system")
            print(f"[PluginManager] ✅ 适配器插件 {plugin_id} 加载成功 (来源: {type(adapter).__name__})")
            return plugin_id

        except Exception as e:
            print(f"[PluginManager] 适配器加载失败 {plugin_path}: {e}")
            traceback.print_exc()
            return None

    def _register_plugin_hooks(self, plugin_instance: PluginV2, manifest: PluginManifest):
        hook_impls = plugin_instance.get_hook_implementations()
        for hook_name, handlers in hook_impls.items():
            if hook_name not in self._hooks:
                self._hooks[hook_name] = []
            for handler in handlers:
                self._hooks[hook_name].append((0, handler, manifest.id))

    def load_all_plugins(self) -> List[str]:
        discovered = self.discover_plugins()
        loaded_ids = []
        for path in discovered:
            plugin_id = self.load_plugin(path)
            if plugin_id:
                loaded_ids.append(plugin_id)
        self._event_bus.emit(SystemEvents.ALL_PLUGINS_LOADED, {"count": len(loaded_ids)}, "system")
        return loaded_ids

    def unload_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            return False
        plugin_info = self._plugins[plugin_id]
        try:
            plugin_info["instance"].on_unload()
            self._event_bus.unsubscribe_all_plugin(plugin_id)
            for hook_name in list(self._hooks.keys()):
                self._hooks[hook_name] = [(p, h, pid) for p, h, pid in self._hooks[hook_name] if pid != plugin_id]
            if plugin_id in sys.modules:
                del sys.modules[plugin_id]
            del self._plugins[plugin_id]
            if plugin_id in self._load_order:
                self._load_order.remove(plugin_id)
            self._event_bus.emit(SystemEvents.PLUGIN_UNLOADED, {"plugin_id": plugin_id}, "system")
            return True
        except Exception as e:
            print(f"[PluginManager] 卸载插件失败 {plugin_id}: {e}")
            return False

    def enable_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            return False
        info = self._plugins[plugin_id]
        if info["enabled"]:
            return True
        info["instance"].on_enable()
        info["enabled"] = True
        self._event_bus.emit(SystemEvents.PLUGIN_ENABLED, {"plugin_id": plugin_id}, "system")
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            return False
        info = self._plugins[plugin_id]
        if not info["enabled"]:
            return True
        info["instance"].on_disable()
        info["enabled"] = False
        self._event_bus.emit(SystemEvents.PLUGIN_DISABLED, {"plugin_id": plugin_id}, "system")
        return True

    def reload_plugin(self, plugin_id: str) -> bool:
        if not self._hot_reload_enabled:
            print("[PluginManager] 热重载未启用")
            return False
        if plugin_id not in self._plugins:
            return False
        plugin_path = self._plugins[plugin_id]["path"]
        self.unload_plugin(plugin_id)
        return self.load_plugin(plugin_path) is not None

    def get_plugin(self, plugin_id: str) -> Optional[PluginV2]:
        info = self._plugins.get(plugin_id)
        return info["instance"] if info else None

    def get_all_plugins_info(self) -> List[Dict[str, Any]]:
        result = []
        for pid, info in self._plugins.items():
            if "adapter_type" in info:
                adapter_name = info["adapter_type"]
                if "OpenClaw" in adapter_name:
                    source = "OpenClaw"
                elif "Xiaoli" in adapter_name:
                    source = "小狸"
                else:
                    source = f"适配({adapter_name})"
            else:
                source = "TG HELPER"
            result.append({
                "id": pid,
                "name": info["manifest"].name,
                "version": info["manifest"].version,
                "description": info["manifest"].description,
                "enabled": info["enabled"],
                "instance": info["instance"],
                "manifest": info["manifest"],
                "source": source
            })
        return result

    def get_event_bus(self) -> EventBus:
        return self._event_bus

    def get_capability_manager(self) -> CapabilityManager:
        return self._cap_manager

    def get_hook_handlers(self, hook_name: str) -> List[Callable]:
        if hook_name in self._hooks:
            return [h for _, h, _ in self._hooks[hook_name]]
        return []

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        results = []
        if hook_name in self._hooks:
            for _, handler, pid in self._hooks[hook_name]:
                info = self._plugins.get(pid)
                if info and not info["enabled"]:
                    continue
                try:
                    result = handler(*args, **kwargs)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"[PluginManager] 钩子 {hook_name} 执行失败 ({pid}): {e}")
        return results

    def shutdown(self):
        # 先执行所有插件注册的 shutdown hooks
        for plugin_id, info in list(self._plugins.items()):
            host_api = info.get("host_api")
            if host_api and hasattr(host_api, '_system_api'):
                system_api = host_api._system_api
                if hasattr(system_api, '_shutdown_hooks'):
                    for hook in system_api._shutdown_hooks:
                        try:
                            hook()
                        except Exception as e:
                            print(f"[PluginManager] shutdown hook 执行失败 ({plugin_id}): {e}")
        for plugin_id in list(self._plugins.keys()):
            self.unload_plugin(plugin_id)
        self._event_bus.emit(SystemEvents.SYSTEM_SHUTDOWN, None, "system")
