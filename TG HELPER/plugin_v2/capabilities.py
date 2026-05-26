# -*- coding: utf-8 -*-
"""
权限能力定义与校验模块

设计参考：
- OpenClaw 的 plugin manifest 中声明 capabilities 和 permissions[reference:0]
- 能力分为核心能力（Core Capabilities）和扩展能力（Extended Capabilities）
- 运行时根据声明进行权限校验
"""

from enum import Enum
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field


class CapabilityScope(Enum):
    """能力作用范围"""
    GLOBAL = "global"           # 全局能力（如读写任意文件）
    USER = "user"               # 用户级别能力（如读写用户目录）
    SANDBOX = "sandbox"         # 沙箱能力（仅限插件自己的数据目录）


@dataclass
class Capability:
    """能力定义"""
    name: str                           # 能力名称，如 "memory.write"
    description: str                    # 能力描述
    scope: CapabilityScope = CapabilityScope.SANDBOX
    requires_confirmation: bool = False  # 是否需要用户确认
    dangerous: bool = False             # 是否危险操作


# 预定义能力列表（参考 OpenClaw 的能力模型[reference:1]）
PREDEFINED_CAPABILITIES: Dict[str, Capability] = {
    # === UI 相关能力 ===
    "ui.display": Capability(
        name="ui.display",
        description="向主界面显示消息",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=False,
        dangerous=False
    ),
    "ui.modify": Capability(
        name="ui.modify",
        description="修改主界面布局、添加面板或控件",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=True,
        dangerous=True
    ),
    "ui.settings_tab": Capability(
        name="ui.settings_tab",
        description="在设置页添加自定义标签页",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=False,
        dangerous=False
    ),
    
    # === 记忆相关能力 ===
    "memory.read": Capability(
        name="memory.read",
        description="读取短期和长期记忆",
        scope=CapabilityScope.USER,
        requires_confirmation=False,
        dangerous=False
    ),
    "memory.write": Capability(
        name="memory.write",
        description="写入短期和长期记忆",
        scope=CapabilityScope.USER,
        requires_confirmation=False,
        dangerous=False
    ),
    "memory.modify": Capability(
        name="memory.modify",
        description="修改记忆系统的行为逻辑",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=True,
        dangerous=True
    ),
    
    # === Agent 相关能力 ===
    "agent.intercept": Capability(
        name="agent.intercept",
        description="拦截和修改 Agent 的输入输出",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=True,
        dangerous=True
    ),
    "agent.modify": Capability(
        name="agent.modify",
        description="修改 Agent 的决策逻辑",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=True,
        dangerous=True
    ),
    "agent.tool_register": Capability(
        name="agent.tool_register",
        description="向 Agent 注册新的工具",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=False,
        dangerous=False
    ),
    
    # === 文件系统能力 ===
    "fs.read": Capability(
        name="fs.read",
        description="读取文件",
        scope=CapabilityScope.USER,
        requires_confirmation=False,
        dangerous=False
    ),
    "fs.write": Capability(
        name="fs.write",
        description="写入文件",
        scope=CapabilityScope.USER,
        requires_confirmation=True,
        dangerous=True
    ),
    "fs.execute": Capability(
        name="fs.execute",
        description="执行系统命令或脚本",
        scope=CapabilityScope.SANDBOX,
        requires_confirmation=True,
        dangerous=True
    ),
    
    # === 网络能力 ===
    "network.http": Capability(
        name="network.http",
        description="发起 HTTP 请求",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=False,
        dangerous=False
    ),
    "network.websocket": Capability(
        name="network.websocket",
        description="建立 WebSocket 连接",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=True,
        dangerous=False
    ),
    
    # === 系统能力 ===
    "system.info": Capability(
        name="system.info",
        description="读取系统信息",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=False,
        dangerous=False
    ),
    "system.config": Capability(
        name="system.config",
        description="读取和修改系统配置",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=True,
        dangerous=True
    ),
    
    # === 插件管理能力（保留给核心系统） ===
    "plugin.manage": Capability(
        name="plugin.manage",
        description="管理其他插件的加载/卸载",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=True,
        dangerous=True
    ),
    # 能力别名（方便 AI 生成时使用）
    "tools.register": Capability(
        name="tools.register",
        description="向 Agent 注册新的工具（同 agent.tool_register）",
        scope=CapabilityScope.GLOBAL,
        requires_confirmation=False,
        dangerous=False
    ),
}


class CapabilityManager:
    """能力管理器——负责权限校验"""
    
    def __init__(self):
        self._capabilities: Dict[str, Capability] = PREDEFINED_CAPABILITIES.copy()
        self._plugin_permissions: Dict[str, Set[str]] = {}  # plugin_id -> set of granted caps
        self._global_deny_list: Set[str] = set()  # 全局禁用的能力
    
    def register_capability(self, cap: Capability) -> None:
        """注册新能力（供后续扩展）"""
        self._capabilities[cap.name] = cap
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """获取能力定义"""
        return self._capabilities.get(name)
    
    def grant_permission(self, plugin_id: str, capabilities: List[str]) -> None:
        """授予插件权限"""
        if plugin_id not in self._plugin_permissions:
            self._plugin_permissions[plugin_id] = set()
        self._plugin_permissions[plugin_id].update(capabilities)
    
    def revoke_permission(self, plugin_id: str, capability: str) -> None:
        """撤销插件权限"""
        if plugin_id in self._plugin_permissions:
            self._plugin_permissions[plugin_id].discard(capability)
    
    # 别名映射表
    _capability_aliases = {
        "tools.register": "agent.tool_register",
        "config.read": "system.config",
        "config.write": "system.config",
        "memory.write": "memory.write",
    }

    def check_permission(self, plugin_id: str, capability: str) -> bool:
        """检查插件是否有某项权限（支持别名映射）"""
        actual_cap = self._capability_aliases.get(capability, capability)
        if actual_cap in self._global_deny_list:
            return False
        if plugin_id not in self._plugin_permissions:
            return False
        return actual_cap in self._plugin_permissions[plugin_id]

    def check_permissions(self, plugin_id: str, capabilities: List[str]) -> Dict[str, bool]:
        """批量检查权限"""
        return {cap: self.check_permission(plugin_id, cap) for cap in capabilities}

    def get_plugin_permissions(self, plugin_id: str) -> Set[str]:
        """获取插件已授予的所有权限"""
        return self._plugin_permissions.get(plugin_id, set()).copy()

    def get_capabilities(self) -> List[Capability]:
        """获取所有已定义的能力"""
        return list(self._capabilities.values())

    def deny_global(self, capability: str) -> None:
        """全局禁用某项能力"""
        self._global_deny_list.add(capability)

    def allow_global(self, capability: str) -> None:
        """取消全局禁用"""
        self._global_deny_list.discard(capability)

    def needs_confirmation(self, plugin_id: str, capability: str) -> bool:
        """判断某个操作是否需要用户确认"""
        actual_cap = self._capability_aliases.get(capability, capability)
        cap = self.get_capability(actual_cap)
        if cap is None:
            return True
        return cap.requires_confirmation

    def is_dangerous(self, capability: str) -> bool:
        """判断是否是危险操作"""
        actual_cap = self._capability_aliases.get(capability, capability)
        cap = self.get_capability(actual_cap)
        if cap is None:
            return True
        return cap.dangerous
