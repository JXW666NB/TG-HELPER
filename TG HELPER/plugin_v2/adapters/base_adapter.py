# -*- coding: utf-8 -*-
"""
适配器基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os


class BaseAdapter(ABC):
    """所有适配器的基类"""
    
    def __init__(self, plugin_path: str):
        self.plugin_path = plugin_path
        self.plugin_id: Optional[str] = None
        self.plugin_name: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    @abstractmethod
    def can_handle(self) -> bool:
        """检查该适配器是否能处理此插件路径"""
        pass
    
    @abstractmethod
    def load_metadata(self) -> Dict[str, Any]:
        """加载插件元数据，返回标准化的 PluginManifest 字典"""
        pass
    
    @abstractmethod
    def create_plugin_instance(self, host_api):
        """
        创建 TG HELPER PluginV2 实例（运行时适配）
        返回一个 PluginV2 子类的实例
        """
        pass
    
    @abstractmethod
    def get_conversion_prompt(self) -> str:
        """
        返回用于 AI 转换的提示词模板
        将外部插件源码描述转换为 TG HELPER PluginV2 代码
        """
        pass
    
    def get_source_code(self) -> str:
        """获取插件的主要源代码（供 AI 转换使用）"""
        return ""
    
    def generate_gui_config_panel(self, parent, config: Dict[str, Any], save_callback) -> Any:
        """
        根据外部插件的配置 schema 动态生成 GUI 配置面板。
        返回 PyQt6 Widget 对象。
        默认实现返回 None，子类可重写。
        """
        return None