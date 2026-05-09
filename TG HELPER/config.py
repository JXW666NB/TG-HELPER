import os
from config_manager import load_config, CONFIG_FILE

class AgentConfig:
    def __init__(self):
        user_config = load_config()
        self.ai_api_key = user_config.get("ai_api_key", "")
        self.ai_base_url = user_config.get("ai_base_url", "https://api.moonshot.cn/v1")
        self.ai_model = user_config.get("ai_model", "kimi-k2.5")
        self.multimodal_model = user_config.get("multimodal_model", self.ai_model)
        self.max_tokens = user_config.get("max_tokens", 2000)
        self.temperature = user_config.get("temperature", 1.0)
        # 多模态备用模型配置
        self.multimodal_enabled = user_config.get("multimodal_enabled", False)
        self.multimodal_api_key = user_config.get("multimodal_api_key", "")
        self.multimodal_base_url = user_config.get("multimodal_base_url", "")
        self.multimodal_model = user_config.get("multimodal_model", "")
        self.multimodal_max_tokens = user_config.get("multimodal_max_tokens", 2000)
        self.multimodal_temperature = user_config.get("multimodal_temperature", 1.0)
        # 可选配置
        self.email_smtp_server = user_config.get("email_smtp_server")
        self.email_port = user_config.get("email_port", 587)
        self.email_user = user_config.get("email_user")
        self.email_password = user_config.get("email_password")
        self.google_api_key = user_config.get("google_api_key")
        self.google_cse_id = user_config.get("google_cse_id")

        # QQ 对接配置（WebSocket）
        self.qq_websocket_url = user_config.get("qq_websocket_url", "ws://127.0.0.1:6099")
        self.qq_bot_uin = user_config.get("qq_bot_uin", "")
        self.qq_whitelist = user_config.get("qq_whitelist", "")
        self.qq_enabled = user_config.get("qq_enabled", False)
        # 白名单总开关
        self.whitelist_enabled = user_config.get("whitelist_enabled", True)

        # NapCat HTTP 配置
        self.napcat_http_url = user_config.get("napcat_http_url", "http://127.0.0.1:6099")
        self.napcat_access_token = user_config.get("napcat_access_token", "")

        # 调试模式
        self.debug_mode = user_config.get("debug_mode", False)

        # 安全配置：每个工具是否需要确认（默认需要）
        default_confirm_tools = [
            "delete_file", "move_file", "copy_file", "execute_code",
            "click", "type_text", "move_mouse", "install_python_package"
        ]
        self.tool_confirmation = user_config.get("tool_confirmation", {})
        self.browser_safe_mode = user_config.get("browser_safe_mode", True)
        # 确保所有默认工具都有配置
        for tool in default_confirm_tools:
            if tool not in self.tool_confirmation:
                self.tool_confirmation[tool] = True  # 默认开启确认

        # 其他
        self.memory_dir = user_config.get("memory_dir", "./memory")
        self.require_confirmation = user_config.get("require_confirmation", True)  # 可能不再使用，但保留兼容
        self.command_whitelist = user_config.get("command_whitelist")
        # 在AgentConfig类的__init__中添加：
        self.skills_dirs = user_config.get("skills_dirs", ["./skills"])
        self.multi_agent_enabled = user_config.get("multi_agent_enabled", False)
        self.worker_count = user_config.get("worker_count", 2)
        self.tasks_dir = user_config.get("tasks_dir", "./config")
        self.auto_backup_short_term = user_config.get("auto_backup_short_term", False)
        # 人格设置
        self.current_personality = user_config.get("current_personality", "TGAI")
        self.personality_dir = user_config.get("personality_dir", "./AI人格")
        self.fun_mode_enabled = user_config.get("fun_mode_enabled", False)
         # 群聊陪伴模式
        self.group_companion_enabled = user_config.get("group_companion_enabled", False)
        self.group_companion_group_id = user_config.get("group_companion_group_id", "")
        self.group_companion_probability = user_config.get("group_companion_probability", 60)
        self.group_companion_voice = user_config.get("group_companion_voice", False)
        self.main_model_type = user_config.get("main_model_type", "cloud")
        self.sub_model_type = user_config.get("sub_model_type", "cloud")
        self.local_model = user_config.get("local_model", "")
        # ==== 新增：IoT设备管理配置 ====
        self.iot_config_dir = user_config.get("iot_config_dir", "./device_configs")
        self.iot_mqtt_broker = user_config.get("iot_mqtt_broker", "localhost")
        self.iot_mqtt_port = user_config.get("iot_mqtt_port", 1883)
        self.gui_theme = user_config.get("gui_theme", "darkly")
        self.inspector_enabled = user_config.get("inspector_enabled", False)
        self.inspector_interval = user_config.get("inspector_interval", 3600)
# 新增：浏览器有头/无头模式，默认无头（False=不显示窗口）
        self.browser_headful = user_config.get("browser_headful", False)
        # 多Agent模式
        self.multi_agent_enabled = user_config.get("multi_agent_enabled", False)
        self.multi_agent_planner_persona = user_config.get("multi_agent_planner_persona", "TGAI")
        self.multi_agent_worker_persona = user_config.get("multi_agent_worker_persona", "艾依")
        self.multi_agent_reviewer_persona = user_config.get("multi_agent_reviewer_persona", "塔戈")
config = AgentConfig()
