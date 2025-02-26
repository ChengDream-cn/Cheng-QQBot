import os
import sys
import importlib.util
import logging
import time
from threading import Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.lock = Lock()
        self.observer = Observer()
        self.plugin_dir = "plugins"
        self._init_plugins()
        self._start_watching()

    def _init_plugins(self):
        """初始化加载所有插件"""
        with self.lock:
            for filename in os.listdir(self.plugin_dir):
                if filename.endswith(".py") and filename != "__init__.py":
                    self._load_plugin(filename)

    def _load_plugin(self, filename: str):
        """加载单个插件"""
        module_name = filename[:-3]
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, 
                os.path.join(self.plugin_dir, filename)
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 初始化插件
            if hasattr(module, "on_load"):
                try:
                    module.on_load()
                except Exception as e:
                    logging.error(f"插件初始化失败 {module_name}: {str(e)}")

            self.plugins[module_name] = module
            logging.info(f"✅ 成功加载插件: {module_name}")

        except Exception as e:
            logging.error(f"❌ 加载插件失败 {filename}: {str(e)}", exc_info=True)

    def _unload_plugin(self, module_name: str):
        """卸载单个插件"""
        with self.lock:
            if module_name in self.plugins:
                try:
                    # 执行卸载回调
                    if hasattr(self.plugins[module_name], "on_unload"):
                        self.plugins[module_name].on_unload()

                    # 清理模块引用
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    del self.plugins[module_name]
                    logging.info(f"♻️ 成功卸载插件: {module_name}")

                except Exception as e:
                    logging.error(f"❌ 卸载插件失败 {module_name}: {str(e)}")

    class PluginWatcher(FileSystemEventHandler):
        """文件系统监视器"""
        def __init__(self, manager):
            self.manager = manager
            self.last_modified = 0  # 防抖处理

        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                current_time = time.time()
                if current_time - self.last_modified > 1:  # 1秒防抖
                    self.last_modified = current_time
                    self._handle_plugin_change(event)

        def _handle_plugin_change(self, event):
            filename = os.path.basename(event.src_path)
            if filename == "__init__.py":
                return

            module_name = filename[:-3]
            logging.info(f"🔄 检测到插件变更: {filename}")
            
            try:
                self.manager._unload_plugin(module_name)
                self.manager._load_plugin(filename)
                logging.info(f"🔄 成功热更新插件: {module_name}")
            except Exception as e:
                logging.error(f"热更新失败: {str(e)}", exc_info=True)

    def _start_watching(self):
        """启动文件监视"""
        self.observer.schedule(
            self.PluginWatcher(self),
            self.plugin_dir,
            recursive=False
        )
        self.observer.start()

    def shutdown(self):
        """关闭插件系统"""
        self.observer.stop()
        self.observer.join()
        for module_name in list(self.plugins.keys()):
            self._unload_plugin(module_name)

def load_plugins():
    return PluginManager().plugins
