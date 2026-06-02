"""
TG HELPER AI硬件模块
支持TG桌面机器人、TG智能眼镜等AI硬件设备
"""

from .robot_client import TGRobotClient
from .smart_glasses import TGSmartGlasses, SmartGlassesDiscovery

__all__ = ['TGRobotClient', 'TGSmartGlasses', 'SmartGlassesDiscovery']
