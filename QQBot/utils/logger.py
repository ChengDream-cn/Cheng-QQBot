import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Any

def setup_logging(config: Dict[str, Any] = None):
    """配置多级日志系统"""
    config = config or {
        'log_dir': 'logs',
        'debug_keep_days': 7,
        'error_keep_weeks': 4,
        'console_level': 'INFO'
    }

    if not os.path.exists(config['log_dir']):
        os.makedirs(config['log_dir'])

    # 调试日志（按天轮转）
    debug_handler = TimedRotatingFileHandler(
        filename=os.path.join(config['log_dir'], 'debug.log'),
        when='midnight',
        backupCount=config['debug_keep_days'],
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.addFilter(lambda record: record.levelno <= logging.INFO)

    # 错误日志（按周轮转）
    error_handler = TimedRotatingFileHandler(
        filename=os.path.join(config['log_dir'], 'error.log'),
        when='W0',  # 每周一
        backupCount=config['error_keep_weeks'],
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config['console_level'])

    # 统一格式化
    formatter = logging.Formatter(
        '%(asctime)s [%(threadName)s] %(name)s - %(levelname)s - %(message)s'
    )
    for handler in [debug_handler, error_handler, console_handler]:
        handler.setFormatter(formatter)

    # 配置根日志
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[debug_handler, error_handler, console_handler],
        force=True
    )

    # 设置第三方库日志级别
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
