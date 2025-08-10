import logging
import random
import asyncio
from typing import Optional, List
from threading import Thread

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import Channel


LOG_FILE = "bots.log"

logger = logging.getLogger("bots")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(stream_handler)

is_running = False
clients: List[TelegramClient] = []
_loop = None
_loop_thread = None


def start_event_loop():
    """Starts the asyncio event loop in a separate thread."""
    global _loop, _loop_thread
    if _loop_thread and _loop_thread.is_alive():
        return

    _loop = asyncio.new_event_loop()
    _loop_thread = Thread(target=_loop.run_forever, daemon=True)
    _loop_thread.start()
    logger.info("Asyncio event loop started in a background thread.")


async def send_code_request(phone, api_id, api_hash) -> Optional[str]:
    client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
    await client.connect()
    try:
        phone_code = await client.send_code_request(phone)
        return phone_code.phone_code_hash
    except Exception as e:
        raise e
    finally:
        await client.disconnect()


async def add_account(phone, code, phone_code_hash, api_id, api_hash, password=None) -> bool:
    client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            try:
                await client.sign_in(phone, code=code, phone_code_hash=phone_code_hash, password=password)
            except SessionPasswordNeededError:
                if password:
                    await client.sign_in(password=password)
                else:
                    raise SessionPasswordNeededError(request=None)
        return True
    except Exception as e:
        raise e
    finally:
        await client.disconnect()


async def start_commenting(phones: list, comments: list, api_id, api_hash):
    global is_running
    await stop_all_clients()

    @events.register(events.NewMessage)
    async def handler(event):
        if not (isinstance(event.chat, Channel) and not event.chat.megagroup):
            return

        if is_running:
            comment = random.choice(comments)
            active_client = event.client
            try:
                await active_client.send_message(event.message.chat_id, comment, comment_to=event)
                logger.info(f"Comment '{comment}' sent by {active_client._phone} in chat {event.chat.id}")
            except Exception as e:
                logger.error(f"Error sending comment from {active_client._phone} in chat {event.chat.id}: {e}")

    for phone in phones:
        client = TelegramClient(f'sessions/{phone}', api_id, api_hash, loop=_loop)
        client._phone = phone
        try:
            await client.start()
            if not await client.is_user_authorized():
                logger.error(f"Account {phone} is not authorized. Disconnecting.")
                await client.disconnect()
                continue
            
            client.add_event_handler(handler)
            clients.append(client)
            logger.info(f"Client for {phone} started.")
        except Exception as e:
            logger.error(f"Failed to start client for {phone}: {e}")
    
    if clients:
        is_running = True
        logger.info(f"Started {len(clients)} clients successfully.")
    else:
        is_running = False
        logger.warning("No clients were started.")


async def stop_client(phone):
    client_to_remove = next((c for c in clients if getattr(c, '_phone', None) == phone), None)
    if client_to_remove:
        await client_to_remove.disconnect()
        clients.remove(client_to_remove)
        logger.info(f"Client for {phone} stopped.")
        return True
    return False


async def stop_all_clients():
    global is_running
    for client in clients:
        try:
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting client {getattr(client, '_phone', 'N/A')}: {e}")
    clients.clear()
    is_running = False
    logger.info("All clients stopped.")


def stop_event_loop():
    if _loop:
        _loop.call_soon_threadsafe(_loop.stop)

def run_coroutine(coro):
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()
