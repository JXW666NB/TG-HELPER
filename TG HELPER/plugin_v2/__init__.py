# -*- coding: utf-8 -*-
"""
TG HELPER Plugin V2 核心模块
"""
from .base import PluginV2, HostAPI, PluginManifest, HookSpec, HookImpl
from .manager import PluginManagerV2
from .host_api import HostAPIImpl
from .events import EventBus, Event, SystemEvents
from .capabilities import CapabilityManager, Capability

__all__ = [
    "PluginV2",
    "HostAPI",
    "PluginManifest",
    "Capability",
    "HookSpec",
    "HookImpl",
    "PluginManagerV2",
    "HostAPIImpl",
    "EventBus",
    "Event",
    "SystemEvents",
    "CapabilityManager",
]
