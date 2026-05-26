# plugin_manager.py
import os
import sys
import importlib
import threading
import time
import traceback
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

class PluginManager:
    def __init__(self, gui, tools, config, plugins_dir="./plugins"):
        self.gui = gui
        self.tools = tools
        self.config = config
        self.plugins_dir = os.path.abspath(plugins_dir)
        self.plugins = {}  # {module_name: {'module': module, 'instance': plugin_instance, 'file_path': path}}
        self.loaded = False
        self.observer = None
        self._lock = threading.Lock()

    def load_all_plugins(self):
        """扫描并加载所有插件（仅旧版 .py 单文件插件）"""
        with self._lock:
            os.makedirs(self.plugins_dir, exist_ok=True)
            existing_names = set(self.plugins.keys())
            # 只加载单文件 .py 插件，跳过文件夹形式的新版插件
            plugin_files = [f for f in os.listdir(self.plugins_dir) 
                           if f.endswith('.py') and not f.startswith('__')]

            for f in plugin_files:
                module_name = f[:-3]
                file_path = os.path.join(self.plugins_dir, f)
                if module_name in existing_names:
                    continue
                # 额外检查：跳过包含 PluginV2 代码的文件（简单启发式）
                try:
                    with open(file_path, 'r', encoding='utf-8') as check_f:
                        content = check_f.read(500)
                        if 'PluginV2' in content or 'from plugin_v2 import' in content:
                            print(f"[插件] 跳过 V2 插件文件: {f}")
                            continue
                except:
                    pass
                self._load_plugin(module_name, file_path)

    def _load_plugin(self, module_name, file_path):
        """加载单个插件"""
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, 'Plugin'):
                raise Exception("插件必须包含一个名为 Plugin 的类")
            plugin_class = getattr(module, 'Plugin')
            plugin_instance = plugin_class(self.gui, self.tools, self.config)
            plugin_instance.name = module_name
            plugin_instance.on_load()

            self.plugins[module_name] = {
                'module': module,
                'instance': plugin_instance,
                'file_path': file_path
            }
            print(f"[插件] 已加载: {module_name}")
            return True
        except Exception as e:
            print(f"[插件] 加载失败 {module_name}: {e}")
            traceback.print_exc()
            return False

    def _unload_plugin(self, module_name):
        """卸载插件"""
        if module_name not in self.plugins:
            return
        plugin = self.plugins[module_name]
        try:
            plugin['instance'].on_unload()
        except Exception as e:
            print(f"[插件] 卸载 {module_name} 时出错: {e}")
        del self.plugins[module_name]
        print(f"[插件] 已卸载: {module_name}")

    def reload_plugin(self, module_name):
        """热重载指定插件"""
        if module_name not in self.plugins:
            return False
        file_path = self.plugins[module_name]['file_path']
        self._unload_plugin(module_name)
        return self._load_plugin(module_name, file_path)

    def reload_all(self):
        """重新加载所有插件"""
        with self._lock:
            current = set(self.plugins.keys())
            plugin_files = [f for f in os.listdir(self.plugins_dir) if f.endswith('.py') and not f.startswith('__')]
            new_names = set(f[:-3] for f in plugin_files)

            for name in current - new_names:
                self._unload_plugin(name)

            for f in plugin_files:
                name = f[:-3]
                if name in current:
                    self.reload_plugin(name)
                else:
                    file_path = os.path.join(self.plugins_dir, f)
                    self._load_plugin(name, file_path)

    def start_watchdog(self):
        """启动文件监控，实现热加载"""
        if not WATCHDOG_AVAILABLE:
            print("[插件] watchdog 未安装，热加载功能不可用。可执行 pip install watchdog")
            return

        class PluginFileHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith('.py'):
                    threading.Timer(0.5, lambda: self.manager.reload_all()).start()
            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith('.py'):
                    threading.Timer(0.5, lambda: self.manager.reload_all()).start()
            def on_deleted(self, event):
                if not event.is_directory and event.src_path.endswith('.py'):
                    threading.Timer(0.5, lambda: self.manager.reload_all()).start()

        self.observer = Observer()
        self.observer.schedule(PluginFileHandler(self), self.plugins_dir, recursive=False)
        self.observer.start()
        print("[插件] 文件监控已启动")

    def stop_watchdog(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def get_plugins_settings_frames(self, parent):
        """返回所有插件的设置界面"""
        frames = []
        for name, info in self.plugins.items():
            try:
                frame = info['instance'].get_settings_ui(parent)
                if frame:
                    frames.append((name, frame))
            except Exception as e:
                print(f"[插件] 获取 {name} 设置界面时出错: {e}")
        return frames
