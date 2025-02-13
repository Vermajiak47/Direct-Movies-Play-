import logging
import logging.config

# Configure logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logging.getLogger().setLevel(logging.INFO)

# Suppress less relevant logs
for lib in ["pyrogram", "imdbpy", "aiohttp", "aiohttp.web"]:
    logging.getLogger(lib).setLevel(logging.ERROR)

from pyrogram import Client, types
from database.ia_filterdb import Media
from utils import temp
from aiohttp import web
from typing import Union, Optional, AsyncGenerator
from info import *


class DeendayalXBot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def iter_messages(
        self, chat_id: Union[int, str], limit: int, offset_id: int = 0
    ) -> AsyncGenerator[types.Message, None]:
        """
        Iterates through messages in a chat sequentially.
        
        :param chat_id: Chat ID or username.
        :param limit: Max number of messages to fetch.
        :param offset_id: Start fetching from this message ID.
        :return: Async generator yielding messages.
        """
        fetched_count = 0
        last_message_id = offset_id

        while fetched_count < limit:
            batch_size = min(200, limit - fetched_count)
            messages = await self.get_messages(chat_id, range(last_message_id + 1, last_message_id + batch_size + 1))

            if not messages:
                break  # No more messages to fetch
            
            for message in messages:
                yield message
                last_message_id = message.message_id  # Update offset
                fetched_count += 1


# Initialize bot
DeendayalBot = DeendayalXBot()

# Dictionary for multi-client support
multi_clients = {}
work_loads = {}
