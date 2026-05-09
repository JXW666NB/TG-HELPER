# -*- coding: utf-8 -*-
"""
小狸 CLI 插件适配器（支持单文件）
"""
import os
import sys
import importlib.util
import json
from typing import Dict, Any, Optional
from .base_adapter import BaseAdapter
from ..base import PluginV2, HostAPI, PluginManifest


class XiaoliAdapter(BaseAdapter):
    """小狸 CLI 插件适配器"""
    
    def can_handle(self) -> bool:
        # 如果是目录，检查是否包含典型的小狸插件文件
        if os.path.isdir(self.plugin_path):
            for f in os.listdir(self.plugin_path):
                if f.endswith('.py') and f != '__init__.py':
                    file_path = os.path.join(self.plugin_path, f)
                    if self._contains_plugin_class(file_path):
                        return True
        # 如果是单个 .py 文件
        elif os.path.isfile(self.plugin_path) and self.plugin_path.endswith('.py'):
            return self._contains_plugin_class(self.plugin_path)
        return False
    
    def _contains_plugin_class(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'class Plugin' in content and 'def get_tool_info' in content
        except:
            return False
    
    def load_metadata(self) -> Dict[str, Any]:
        plugin_file = self._find_plugin_file()
        if not plugin_file:
            raise ValueError("未找到小狸插件文件")
        
        # 动态加载模块以获取元数据
        spec = importlib.util.spec_from_file_location("xiaoli_temp", plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, 'Plugin'):
            raise ValueError("插件未包含 Plugin 类")
        
        plugin_instance = module.Plugin()
        tool_info = plugin_instance.get_tool_info()
        
        # 使用文件名作为插件ID的一部分
        base_name = os.path.splitext(os.path.basename(plugin_file))[0]
        self.plugin_id = f"xiaoli.{tool_info.get('name', base_name)}"
        self.plugin_name = tool_info.get('name', self.plugin_id)
        self._plugin_instance = plugin_instance
        self._tool_info = tool_info
        self._module = module
        self._plugin_file = plugin_file
        
        return {
            "id": self.plugin_id,
            "name": self.plugin_name,
            "version": "1.0.0",
            "description": tool_info.get('description', ''),
            "capabilities": ["agent.tool_register", "ui.display"],
            "permissions": ["agent.tool_register", "ui.display"],
            "entry_point": os.path.basename(plugin_file),
            "keywords": tool_info.get('keywords', []),
        }
    
    def _find_plugin_file(self) -> Optional[str]:
        # 如果是单文件，直接返回
        if os.path.isfile(self.plugin_path) and self.plugin_path.endswith('.py'):
            return self.plugin_path
        # 如果是目录，查找包含 Plugin 类的文件
        for f in os.listdir(self.plugin_path):
            if f.endswith('.py') and f != '__init__.py':
                file_path = os.path.join(self.plugin_path, f)
                if self._contains_plugin_class(file_path):
                    return file_path
        return None
    
    def create_plugin_instance(self, host_api):
        metadata = self.load_metadata()
        plugin_instance = self._plugin_instance
        tool_info = self._tool_info
        
        class XiaoliRuntimePlugin(PluginV2):
            def get_manifest(self):
                return PluginManifest(**metadata)
            
            def get_usage_info(self):
                return {
                    "tools": [{"name": tool_info['name'], "description": tool_info['description']}],
                    "auto_effect": f"小狸插件：{tool_info['description']}"
                }
            
            def on_load(self, host_api: HostAPI):
                tool_name = tool_info['name']
                
                def handler(params):
                    # 将字典参数转换为空格分隔的字符串（小狸插件期望字符串）
                    # 简单处理：将 values 拼接成字符串
                    args_list = []
                    for k, v in params.items():
                        args_list.append(str(v))
                    args_str = " ".join(args_list)
                    try:
                        result = plugin_instance.handle(args_str)
                        return result
                    except Exception as e:
                        return f"小狸插件执行错误: {e}"
                
                host_api.agent.register_tool(
                    {
                        "name": tool_name,
                        "description": tool_info['description'],
                        "parameters": {"type": "object", "properties": {}, "additionalProperties": True}
                    },
                    handler
                )
        
        return XiaoliRuntimePlugin()
    
    def get_conversion_prompt(self) -> str:
        tool_info = self._tool_info
        source = self.get_source_code()
        return f"""
请将以下小狸 CLI 插件转换为 TG HELPER PluginV2 原生插件。

【插件信息】
名称: {tool_info.get('name')}
描述: {tool_info.get('description')}
关键词: {tool_info.get('keywords', [])}

【原始代码】
{source}

【要求】
1. 生成一个继承自 PluginV2 的 Python 类。
2. 实现 get_manifest(), on_load(host_api), get_usage_info() 方法。
3. 在 on_load 中使用 host_api.agent.register_tool 注册工具，工具名与原插件一致。
4. 处理函数需将接收到的字典参数转换为原插件期望的字符串格式（空格分隔）。
5. 保留原插件的核心逻辑，适配为 PluginV2 风格。
6. 输出完整 Python 代码。
"""
    
    def get_source_code(self) -> str:
        plugin_file = self._find_plugin_file()
        if plugin_file:
            with open(plugin_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
