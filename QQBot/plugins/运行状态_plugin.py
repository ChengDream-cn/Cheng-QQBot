import psutil
import time
import logging
from datetime import datetime

start_time = time.time()
process = psutil.Process()

def on_load():
    logging.info("运行状态插件已加载")

def on_unload():
    logging.info("运行状态插件已卸载")

def format_uptime(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    return f"{int(days)}天{int(hours)}小时{int(minutes)}分"

def get_system_status():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    load_avg = psutil.getloadavg()
    
    return (
        f"🕒 运行时间: {format_uptime(time.time() - start_time)}\n"
        f"💻 CPU使用率: {psutil.cpu_percent()}%\n"
        f"🧠 内存使用: {mem.used/1024/1024:.1f}MB / {mem.total/1024/1024:.1f}MB\n"
        f"💾 磁盘使用: {disk.used/1024/1024/1024:.1f}GB / {disk.total/1024/1024/1024:.1f}GB\n"
        f"📊 系统负载: {load_avg[0]:.2f} (1分钟), {load_avg[1]:.2f} (5分钟)"
    )

def handle_command(content, **kwargs):
    if content == '/运行状态':
        return get_system_status()
