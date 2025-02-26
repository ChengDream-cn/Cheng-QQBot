import asyncio
from websocket_handler import websocket_listener
from utils.logger import setup_logging
from utils.plugin_loader import PluginManager

def main():
    # 配置日志
    setup_logging({
        'log_dir': 'logs',
        'debug_keep_days': 7,
        'error_keep_weeks': 4,
        'console_level': 'INFO'
    })

    # 初始化插件系统
    plugin_manager = PluginManager()

    try:
        # 启动WebSocket监听
        uri = "wss://+连接地址+/ws/+秘钥"
        asyncio.run(websocket_listener(uri))
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在关闭...")
    finally:
        plugin_manager.shutdown()
        logging.info("系统已安全关闭")

if __name__ == "__main__":
    main()
