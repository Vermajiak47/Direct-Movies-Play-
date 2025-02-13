import asyncio
import logging
from info import *
from pyrogram import Client
from util.config_parser import TokenParser
from . import multi_clients, work_loads, DeendayalBot


async def initialize_clients():
    global MULTI_CLIENT  # Ensure the variable is defined globally
    MULTI_CLIENT = False  # Default value

    multi_clients[0] = DeendayalBot
    work_loads[0] = 0
    all_tokens = TokenParser().parse_from_env()

    if not all_tokens:
        print("No additional clients found, using default client")
        return
    
    async def start_client(client_id, token):
        try:
            print(f"Starting - Client {client_id}")
            if client_id == len(all_tokens):
                await asyncio.sleep(2)
                print("This will take some time, please wait...")

            client = Client(
                name=str(client_id),
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                sleep_threshold=SLEEP_THRESHOLD,
                no_updates=True,
                in_memory=True
            )
            await client.start()
            
            work_loads[client_id] = 0
            return client_id, client
        except Exception as e:
            logging.error(f"Failed to start Client {client_id}: {e}", exc_info=True)
            return None

    # Start clients and filter out None values
    clients = await asyncio.gather(*[start_client(i, token) for i, token in all_tokens.items()])
    clients = dict(filter(None, clients))  # Remove failed clients

    multi_clients.update(clients)

    if len(multi_clients) > 1:
        MULTI_CLIENT = True
        print("Multi-Client Mode Enabled")
    else:
        print("No additional clients were initialized, using default client")
