import asyncio
import websockets
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from message_processor import process_message, handle_event
from fetch_access_token import fetch_access_token

logging.getLogger().setLevel(logging.INFO)
executor = ThreadPoolExecutor(max_workers=10)

async def websocket_listener(uri):
    logging.info(f"Connecting to WebSocket server at {uri}...")
    async with websockets.connect(uri) as websocket:
        logging.info("Connected to WebSocket server.")
        while True:
            try:
                message = await websocket.recv()
                loop = asyncio.get_event_loop()
                loop.run_in_executor(
                    executor, 
                    lambda: asyncio.run_coroutine_threadsafe(
                        process_message_wrapper(message), 
                        loop
                    )
                )
            except websockets.exceptions.ConnectionClosedOK:
                logging.info("Connection closed normally.")
                break
            except Exception as e:
                logging.error(f"WebSocket error: {e}", exc_info=True)
                break

async def process_message_wrapper(message):
    try:
        data = json.loads(message)
        logging.debug(f"Raw message data: {data}")
        
        if data['op'] == 0:
            event_type = data['t']
            access_token = await fetch_access_token()
            
            if event_type in ['GROUP_ADD_ROBOT', 'GROUP_DEL_ROBOT', 'FRIEND_ADD', 'FRIEND_DEL']:
                await handle_event(data)
            else:
                await process_message(data, access_token)
                
    except Exception as e:
        logging.error(f"Message processing failed: {e}", exc_info=True)