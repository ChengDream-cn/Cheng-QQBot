import requests
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_ID = 'APPID'
CLIENT_SECRET = '秘钥'
BOT_API_URL = 'https://bots.qq.com/app/getAppAccessToken'

# 全局变量存储 access_token 和过期时间
current_access_token = None
token_expiration_time = 0

async def fetch_access_token():
    global current_access_token, token_expiration_time
    
    # 检查当前 access_token 是否即将过期（剩余60秒内）
    if time.time() >= token_expiration_time - 60:
        logging.info("Current access token is about to expire. Fetching a new one...")
        payload = {
            "appId": APP_ID,
            "clientSecret": CLIENT_SECRET
        }
        response = requests.post(BOT_API_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            current_access_token = data.get('access_token')
            expires_in = data.get('expires_in', 7200)  # 默认有效期为7200秒
            token_expiration_time = time.time() + int(expires_in)  # 确保 expires_in 是整数
            logging.info(f"New access token fetched successfully. Expires in {expires_in} seconds.")
        else:
            logging.error(f"Failed to get access token: {response.text}")
            raise Exception(f"Failed to get access token: {response.text}")
    
    return current_access_token