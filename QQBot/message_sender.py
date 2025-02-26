import aiohttp
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SEND_GROUP_MESSAGE_API_URL = 'https://api.sgroup.qq.com/v2/groups/{}/messages'
SEND_USER_MESSAGE_API_URL = 'https://api.sgroup.qq.com/v2/users/{}/messages'

async def send_group_message_async(access_token, group_openid, content, msg_id, msg_seq):
    logging.info(f"Sending message to group {group_openid}: {content}")
    headers = {
        "Authorization": f"QQBot {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "content": content,
        "msg_type": 0,  # 文本消息类型
        "msg_id": msg_id,
        "msg_seq": msg_seq
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(SEND_GROUP_MESSAGE_API_URL.format(group_openid), headers=headers, json=data) as response:
            if response.status != 200:
                text = await response.text()
                logging.error(f"Failed to send message: {text}")
            else:
                logging.info("Message sent successfully.")

async def send_user_message_async(access_token, user_openid, content, msg_id, msg_seq):
    logging.info(f"Sending message to user {user_openid}: {content}")
    headers = {
        "Authorization": f"QQBot {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "content": content,
        "msg_type": 0,  # 文本消息类型
        "msg_id": msg_id,
        "msg_seq": msg_seq
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(SEND_USER_MESSAGE_API_URL.format(user_openid), headers=headers, json=data) as response:
            if response.status != 200:
                text = await response.text()
                logging.error(f"Failed to send message: {text}")
            else:
                logging.info("Message sent successfully.")