import json
import random
import logging
from message_sender import send_group_message_async, send_user_message_async
from utils.plugin_loader import load_plugins

# 初始化插件
plugins = load_plugins()

async def process_message(data: dict, access_token: str):
    """处理消息主逻辑"""
    try:
        event_type = data['t']
        content = data['d']['content'].strip()
        msg_id = data['d']['id']
        
        # 获取上下文信息
        group_openid = data['d'].get('group_openid')
        member_openid = data['d']['author'].get('member_openid')
        user_openid = data['d']['author'].get('user_openid')

        response_content = None
        for plugin_name, plugin in plugins.items():
            try:
                response_content = plugin.handle_command(
                    content,
                    group_openid=group_openid,
                    member_openid=member_openid,
                    user_openid=user_openid
                )
                if response_content:
                    logging.info(f"插件 {plugin_name} 处理了消息")
                    break
            except Exception as e:
                logging.error(f"插件 {plugin_name} 处理异常: {str(e)}", exc_info=True)

        # 发送回复
        if response_content:
            if event_type == 'GROUP_AT_MESSAGE_CREATE':
                await send_group_message_async(
                    access_token, 
                    group_openid, 
                    response_content, 
                    msg_id, 
                    str(random.randint(1, 1000))
                )
            elif event_type == 'C2C_MESSAGE_CREATE':
                await send_user_message_async(
                    access_token,
                    user_openid,
                    response_content,
                    msg_id,
                    str(random.randint(1, 1000))
                )

    except Exception as e:
        logging.error(f"消息处理失败: {str(e)}", exc_info=True)

async def handle_event(data: dict):
    """处理事件消息（新增函数）"""
    try:
        event_type = data['t']
        event_data = data['d']
        
        # 调用插件的 handle_event 方法
        for plugin in plugins.values():
            if hasattr(plugin, 'handle_event'):
                try:
                    plugin.handle_event(event_type, event_data)
                except Exception as e:
                    logging.error(f"插件事件处理失败: {str(e)}", exc_info=True)
                    
    except KeyError as e:
        logging.error(f"事件数据格式错误: {str(e)}")
    except Exception as e:
        logging.error(f"事件处理异常: {str(e)}", exc_info=True)
