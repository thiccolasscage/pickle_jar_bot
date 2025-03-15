import os
import asyncio
import discord
from discord.ext import commands
from utils.db_manager import db
from utils.logger import logger
from utils.config import config

def get_token(bot_name: str) -> str:
    """
    Retrieves the environment variable token based on config.json settings.
    """
    token_env = config.get("bots")[bot_name]["token_env"]
    return os.getenv(token_env)

bots = {}

async def start_bot(bot_name: str):
    """
    Creates and starts a Bot instance for the specified bot_name.
    """
    prefix = config.get("bots")[bot_name]["prefix"]
    description = config.get("bots")[bot_name]["description"]

    bot = commands.Bot(command_prefix=prefix, description=description, intents=discord.Intents.all())

    @bot.event
    async def on_ready():
        logger.log(f"{bot.user} is online!", "info")

    bots[bot_name] = bot
    await bot.start(get_token(bot_name))

async def main():
    """
    Connects to the database and starts each bot in config.json concurrently.
    """
    await db.connect()

    # Start each bot as an async task
    for bot_name in config.get("bots"):
        asyncio.create_task(start_bot(bot_name))

    # Keep the event loop running indefinitely
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())