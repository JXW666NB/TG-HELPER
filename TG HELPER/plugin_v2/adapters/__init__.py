# -*- coding: utf-8 -*-
"""
适配器模块
"""
from .base_adapter import BaseAdapter
from .openclaw_adapter import OpenClawAdapter
from .xiaoli_adapter import XiaoliAdapter

__all__ = ["BaseAdapter", "OpenClawAdapter", "XiaoliAdapter"]