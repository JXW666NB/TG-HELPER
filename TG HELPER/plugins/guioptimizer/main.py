from plugin_v2 import PluginV2, HostAPI, SystemEvents

class GUIOptimizerPlugin(PluginV2):
    def get_manifest(self):
        return {
            "id": "com.tghelper.guioptimizer",
            "name": "GUI美化优化器",
            "version": "1.0.0",
            "description": "提供GUI界面美化和优化功能。命令：/theme <主题名> 切换主题（dark/light/eye-care/blue），/font <字体> <大小> 设置字体，/style 查看当前样式，/reset-ui 重置默认。工具：set_ui_theme, set_ui_font, apply_custom_style。支持自定义消息气泡颜色和实时预览。",
            "capabilities": ["ui.modify", "ui.display", "agent.tool_register", "system.config"],
            "permissions": ["ui.modify", "ui.display", "agent.tool_register", "system.config"],
            "entry_point": "main.py"
        }

    def get_usage_info(self):
        return {
            "commands": {
                "/theme": "切换主题，用法：/theme <dark|light|eye-care|blue>",
                "/font": "设置字体，用法：/font <字体名> <大小>",
                "/style": "查看当前UI样式配置",
                "/reset-ui": "重置为默认UI设置"
            },
            "tools": [
                {"name": "set_ui_theme", "description": "设置UI主题，参数：theme_name（字符串，可选值：dark, light, eye-care, blue）"},
                {"name": "set_ui_font", "description": "设置全局字体，参数：family（字符串）, size（整数）"},
                {"name": "apply_custom_style", "description": "应用自定义样式，参数：styles（对象，包含bg_color, text_color, user_bubble, ai_bubble等）"}
            ]
        }

    def on_load(self, host_api: HostAPI):
        self.host = host_api
        self.config = host_api.get_plugin_config() or {}
        
        # 预定义主题配置
        self.themes = {
            "dark": {
                "bg_color": "#1e1e1e",
                "text_color": "#ffffff",
                "user_bubble": "#2b5278",
                "ai_bubble": "#3a3a3a",
                "accent_color": "#7289da",
                "border_color": "#40444b"
            },
            "light": {
                "bg_color": "#ffffff",
                "text_color": "#000000",
                "user_bubble": "#dcf8c6",
                "ai_bubble": "#f0f0f0",
                "accent_color": "#007bff",
                "border_color": "#e0e0e0"
            },
            "eye-care": {
                "bg_color": "#c7edcc",
                "text_color": "#2c3e50",
                "user_bubble": "#a8d5ba",
                "ai_bubble": "#dcedc8",
                "accent_color": "#558b2f",
                "border_color": "#aed581"
            },
            "blue": {
                "bg_color": "#0f172a",
                "text_color": "#e2e8f0",
                "user_bubble": "#1e40af",
                "ai_bubble": "#334155",
                "accent_color": "#60a5fa",
                "border_color": "#1e293b"
            }
        }

        # 处理用户命令
        def handle_commands(event):
            content = event.data.get("content", "").strip()
            
            if content.startswith("/theme "):
                theme_name = content[7:].strip().lower()
                self._apply_theme(theme_name)
                event.stop_propagation()
                
            elif content.startswith("/font "):
                parts = content.split()
                if len(parts) >= 3:
                    family = parts[1]
                    try:
                        size = int(parts[2])
                        self._set_font(family, size)
                    except ValueError:
                        host_api.ui.display_message("错误：字体大小必须是数字", is_user=False)
                else:
                    host_api.ui.display_message("用法：/font <字体名> <大小>，例如：/font Microsoft 16", is_user=False)
                event.stop_propagation()
                
            elif content == "/style":
                info = self._get_style_info()
                host_api.ui.display_message(info, is_user=False)
                event.stop_propagation()
                
            elif content == "/reset-ui":
                self._reset_ui()
                host_api.ui.display_message("✅ UI已重置为默认设置", is_user=False)
                event.stop_propagation()

        host_api.events.subscribe(SystemEvents.MESSAGE_RECEIVED, handle_commands)

        # UI就绪后恢复上次设置
        def on_ui_ready(event):
            saved_theme = self.config.get("theme")
            saved_font = self.config.get("font", {"family": "Arial", "size": 14})
            
            if saved_theme and saved_theme in self.themes:
                host_api.ui.apply_styles(self.themes[saved_theme])
            if saved_font:
                host_api.ui.set_font(saved_font.get("family", "Arial"), saved_font.get("size", 14))
                
        host_api.events.subscribe(SystemEvents.UI_READY, on_ui_ready)

        # 注册工具：AI设置主题
        def tool_set_theme(params):
            theme_name = params.get("theme_name", "light")
            if theme_name in self.themes:
                self._apply_theme(theme_name)
                return {"success": True, "message": f"主题已切换为 {theme_name} 模式", "applied_styles": self.themes[theme_name]}
            else:
                available = ", ".join(self.themes.keys())
                return {"success": False, "error": f"未知主题 '{theme_name}'，可用主题：{available}"}

        host_api.agent.register_tool({
            "name": "set_ui_theme",
            "description": "设置UI主题，支持深色模式、浅色模式、护眼模式和深蓝模式",
            "parameters": {
                "type": "object",
                "properties": {
                    "theme_name": {
                        "type": "string",
                        "enum": ["dark", "light", "eye-care", "blue"],
                        "description": "主题名称：dark(深色), light(浅色), eye-care(护眼绿), blue(深蓝科技)"
                    }
                },
                "required": ["theme_name"]
            }
        }, tool_set_theme)

        # 注册工具：AI设置字体
        def tool_set_font(params):
            family = params.get("family", "Arial")
            size = params.get("size", 14)
            try:
                size = int(size)
                if size < 8 or size > 32:
                    return {"success": False, "error": "字体大小必须在8-32之间"}
                self._set_font(family, size)
                return {"success": True, "message": f"字体已设置为 {family} {size}px"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        host_api.agent.register_tool({
            "name": "set_ui_font",
            "description": "设置全局UI字体，影响聊天界面和菜单显示",
            "parameters": {
                "type": "object",
                "properties": {
                    "family": {
                        "type": "string", 
                        "description": "字体家族名称，如 Arial, Microsoft YaHei, Consolas, serif"
                    },
                    "size": {
                        "type": "integer", 
                        "description": "字体大小（像素），推荐范围：12-18"
                    }
                },
                "required": ["family", "size"]
            }
        }, tool_set_font)

        # 注册工具：AI应用自定义样式
        def tool_apply_custom_style(params):
            styles = params.get("styles", {})
            try:
                host_api.ui.apply_styles(styles)
                # 保存到配置
                custom_styles = self.config.get("custom_styles", {})
                custom_styles.update(styles)
                self.config["custom_styles"] = custom_styles
                host_api.save_plugin_config(self.config)
                return {"success": True, "message": "自定义样式已应用并保存"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        host_api.agent.register_tool({
            "name": "apply_custom_style",
            "description": "应用自定义CSS样式对象，可精细控制UI外观。支持：bg_color(背景色), text_color(文字色), user_bubble(用户气泡色), ai_bubble(AI气泡色), accent_color(强调色), border_color(边框色)",
            "parameters": {
                "type": "object",
                "properties": {
                    "styles": {
                        "type": "object",
                        "description": "样式字典，例如：{\"bg_color\": \"#1a1a1a\", \"user_bubble\": \"#2d5a27\"}"
                    }
                },
                "required": ["styles"]
            }
        }, tool_apply_custom_style)

        # 添加设置页面到系统设置
        def create_settings_tab():
            # 返回配置字典供Host渲染
            return {
                "type": "form",
                "title": "界面美化设置",
                "description": "自定义TG Helper的界面外观",
                "fields": [
                    {
                        "name": "theme",
                        "type": "select",
                        "label": "预设主题",
                        "options": [
                            {"value": "light", "label": "浅色模式"},
                            {"value": "dark", "label": "深色模式"},
                            {"value": "eye-care", "label": "护眼模式"},
                            {"value": "blue", "label": "深蓝科技"}
                        ],
                        "default": self.config.get("theme", "light")
                    },
                    {
                        "name": "font_family",
                        "type": "text",
                        "label": "字体名称",
                        "default": self.config.get("font", {}).get("family", "Arial"),
                        "placeholder": "例如：Microsoft YaHei"
                    },
                    {
                        "name": "font_size",
                        "type": "number",
                        "label": "字体大小",
                        "min": 8,
                        "max": 32,
                        "default": self.config.get("font", {}).get("size", 14)
                    }
                ],
                "on_save": self._on_settings_save
            }
        
        host_api.ui.add_settings_tab("UI美化", create_settings_tab)

    def _apply_theme(self, theme_name):
        if theme_name in self.themes:
            theme_data = self.themes[theme_name]
            self.host.ui.apply_styles(theme_data)
            self.config["theme"] = theme_name
            self.host.save_plugin_config(self.config)
            self.host.ui.display_message(f"🎨 已切换到 {theme_name} 主题", is_user=False)
        else:
            available = ", ".join(self.themes.keys())
            self.host.ui.display_message(f"❌ 未知主题。可用主题：{available}", is_user=False)

    def _set_font(self, family, size):
        try:
            self.host.ui.set_font(family, size)
            self.config["font"] = {"family": family, "size": size}
            self.host.save_plugin_config(self.config)
            self.host.ui.display_message(f"🔤 字体已设置为 {family} {size}px", is_user=False)
        except Exception as e:
            self.host.ui.display_message(f"❌ 设置字体失败：{str(e)}", is_user=False)

    def _get_style_info(self):
        theme = self.config.get("theme", "default (未设置)")
        font = self.config.get("font", {})
        custom = self.config.get("custom_styles", {})
        
        info = f"📊 当前UI配置：\n主题：{theme}\n字体：{font.get('family', 'Arial')} {font.get('size', 14)}px"
        if custom:
            info += f"\n自定义样式项：{len(custom)}个"
        return info

    def _reset_ui(self):
        self.config = {}
        self.host.save_plugin_config(self.config)
        self.host.ui.set_theme("default")
        self.host.ui.set_font("Arial", 14)
        self.host.ui.apply_styles({
            "bg_color": "#ffffff",
            "text_color": "#000000",
            "user_bubble": "#dcf8c6",
            "ai_bubble": "#f0f0f0"
        })

    def _on_settings_save(self, settings_data):
        theme = settings_data.get("theme")
        font_family = settings_data.get("font_family", "Arial")
        font_size = settings_data.get("font_size", 14)
        
        if theme in self.themes:
            self._apply_theme(theme)
        self._set_font(font_family, font_size)
        return {"success": True, "message": "设置已保存并应用"}