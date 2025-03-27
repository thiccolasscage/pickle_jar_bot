import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.db_manager import db
from utils.logger import logger
from utils.config import config

load_dotenv()  # Load .env variables

def get_token(bot_name: str) -> str:
    token_env = config.get("bots")[bot_name]["token_env"]
    token = os.getenv(token_env)
    if not token:
        raise ValueError(f"{token_env} is not set in your .env file.")
    return token

bots = {}

async def load_cogs(bot: commands.Bot, bot_name: str):
    cog_map = {
        "picklejar": ["cogs.pickle_tracking"],
        "mediafinder": ["cogs.media_management"]
    }
    for cog_path in cog_map.get(bot_name, []):
        try:
            await bot.load_extension(cog_path)
            logger.log(f"Loaded cog: {cog_path} for {bot_name}")
        except Exception as e:
            logger.log(f"Failed to load {cog_path} for {bot_name}: {e}", level="error")

async def start_bot(bot_name: str):
    prefix = config.get("bots")[bot_name]["prefix"]
    description = config.get("bots")[bot_name]["description"]

    bot = commands.Bot(command_prefix=prefix, description=description, intents=discord.Intents.all())
    bots[bot_name] = bot

    @bot.event
    async def on_ready():
        logger.log(f"{bot.user} is online as {bot_name}!", "info")
        try:
            synced = await bot.tree.sync()
            logger.log(f"Synced {len(synced)} slash commands for {bot_name}")
        except Exception as e:
            logger.log(f"Failed to sync commands for {bot_name}: {e}", level="error")

    await load_cogs(bot, bot_name)
    await bot.start(get_token(bot_name))

async def main():
    print(r"""

 ____  _      _    _        _               ____        _
|  _ \(_) ___| | _| | ___  | | __ _ _ __   | __ )  ___ | |_
| |_) | |/ __| |/ / |/ _ \ | |/ _` | '__|  |  _ \ / _ \| __|
|  __/| | (__|   <| |  __/ | | (_| | |     | |_) | (_) | |_
|_|   |_|\___|_|\_\_|\___| |_|\__,_|_|     |____/ \___/ \__|

Starting PickleJar Bot...
    """)

    await db.connect()

    tasks = []
    for bot_name in config.get("bots", {}):
        tasks.append(asyncio.create_task(start_bot(bot_name)))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
