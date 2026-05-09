# -*- coding: utf-8 -*-
"""
旧版插件适配器——让 BasePlugin 兼容 PluginV2

旧版 BasePlugin 接口：
- on_load(self)
- on_unload(self)
- register_command(self, cmd, handler)
- call_ai(self, message)
- get_settings_ui(self, parent)
"""

from typing import Dict, List, Any, Callable, Optional

from ..base import PluginV2, HostAPI, PluginManifest, HookImpl
from ..events import SystemEvents


class LegacyPluginAdapter(PluginV2):
    """旧版 BasePlugin 的适配器包装"""
    
    def __init__(self, legacy_plugin: Any, plugin_id: str, plugin_path: str):
        super().__init__()
        self._legacy = legacy_plugin
        self._plugin_id = plugin_id
        self._plugin_path = plugin_path
        self._commands: Dict[str, Callable] = {}
        
        # 构建 Manifest
        self._manifest = PluginManifest(
            id=plugin_id,
            name=getattr(legacy_plugin, 'name', plugin_id),
            version=getattr(legacy_plugin, 'version', '1.0.0'),
            description=f"Legacy plugin: {plugin_id}",
            capabilities=["ui.display", "agent.tool_register"],  # 旧版插件默认权限
            permissions=["ui.display", "agent.tool_register"],
            entry_point="__legacy__"
        )
    
    def get_manifest(self) -> PluginManifest:
        return self._manifest
    
    def on_load(self, host_api: HostAPI) -> None:
        """加载旧版插件"""
        # 将 HostAPI 的部分能力注入到旧版插件
        self._legacy.gui = host_api.ui
        self._legacy.tools = host_api.tools
        self._legacy.config = host_api.system
        
        # 重写 call_ai 方法，使其通过 HostAPI
        original_call_ai = getattr(self._legacy, 'call_ai', None)
        if original_call_ai:
            def wrapped_call_ai(message, timeout=30):
                return host_api.agent.call_ai(message)
            self._legacy.call_ai = wrapped_call_ai
        
        # 调用旧版的 on_load
        if hasattr(self._legacy, 'on_load'):
            self._legacy.on_load()
        
        # 注册旧版命令
        if hasattr(self._legacy, '_commands'):
            for cmd, handler in self._legacy._commands.items():
                self._register_legacy_command(cmd, handler)
        
        print(f"[LegacyAdapter] 旧版插件 {self._plugin_id} 已适配加载")
    
    def _register_legacy_command(self, cmd: str, handler: Callable):
        """将旧版命令转换为事件订阅"""
        def on_command(event):
            data = event.data
            if data and data.get("command") == cmd:
                args = data.get("args", [])
                result = handler(args)
                if result:
                    self.host_api.ui.display_message(result)
                event.stop_propagation()
        
        self.host_api.events.subscribe("command.execute", on_command, plugin_id=self._plugin_id)
    
    def on_unload(self) -> None:
        """卸载旧版插件"""
        if hasattr(self._legacy, 'on_unload'):
            self._legacy.on_unload()
    
    @HookImpl("ui.settings_tab.register")
    def register_settings_tab(self, notebook: Any) -> Optional[Any]:
        """注册设置标签页"""
        if hasattr(self._legacy, 'get_settings_ui'):
            return self._legacy.get_settings_ui(notebook)
        return None