# plugin_base.py
import threading
import queue
class BasePlugin:
    """插件基类，所有插件必须继承此类并实现相应方法"""
    def __init__(self, gui, tools, config):
        self.gui = gui          # AgentGUI 实例
        self.tools = tools      # Tools 实例
        self.config = config    # 全局配置对象
        self.name = "BasePlugin"
        self.version = "1.0.0"
        self._ai_queue = queue.Queue()
        self._original_callback = None
        self._commands = {}      # 命令注册表 {"command": handler}

    def on_load(self):
        """插件加载时调用，可以在这里初始化资源、启动后台线程、注册命令等"""
        pass

    def on_unload(self):
        """插件卸载时调用，应清理资源、停止线程等"""
        pass

    def get_settings_ui(self, parent):
        """返回设置界面的 Frame（或 None），用于在设置页添加自定义控件"""
        return None

    def register_command(self, command, handler):
        """
        注册一个命令，当用户在聊天框输入此命令时，会调用 handler 函数。
        handler 签名：def handler(args: list) -> str 或 None，返回的字符串会显示在聊天框。
        如果返回 None，则不显示额外消息。
        """
        self._commands[command] = handler

    def get_commands(self):
        """返回所有注册的命令（供主程序调用）"""
        return self._commands

    def call_ai(self, message, timeout=30):
        """向聊天框发送消息并等待 AI 回复（阻塞）"""
        result_queue = queue.Queue()

        def on_reply(reply):
            result_queue.put(reply)

        # 临时替换回调
        original_callback = self.gui.agent.output_callback
        self.gui.agent.output_callback = on_reply

        # 发送消息（模拟用户输入）
        self.gui.memory.add_short_term("user", message)
        threading.Thread(target=self.gui.run_agent, args=(message,), daemon=True).start()

        try:
            reply = result_queue.get(timeout=timeout)
            return reply
        except queue.Empty:
            return "AI 未及时回复"
        finally:
            self.gui.agent.output_callback = original_callback

    def get_tools_list(self):
        """
        返回所有可用工具的名称和简短描述（用于生成插件时参考）
        """
        tools = []
        for attr in dir(self.tools):
            if callable(getattr(self.tools, attr)) and not attr.startswith('_'):
                doc = getattr(self.tools, attr).__doc__
                desc = doc.split('\n')[0] if doc else ""
                tools.append({"name": attr, "description": desc})
        return tools
