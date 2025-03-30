import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.db_manager import db
from utils.logger import logger
from utils.config import config

# Load environment variables first
load_dotenv()

def get_token(bot_name: str) -> str:
    """Get bot token safely with better error handling"""
    try:
        token_env = config.get("bots", {}).get(bot_name, {}).get("token_env")
        if not token_env:
            logger.log(f"Missing token_env configuration for {bot_name}", "error")
            return None
            
        token = os.getenv(token_env)
        if not token:
            logger.log(f"Missing environment variable: {token_env}", "error")
            return None
            
        return token
    except Exception as e:
        logger.log(f"Error getting token for {bot_name}: {str(e)}", "error")
        return None

bots = {}

async def load_cogs(bot: commands.Bot):
    """Load all cogs from the cogs directory"""
    cog_list = [
        "cogs.error_handler",
        "cogs.moderation",
        "cogs.community_recognition",
        "cogs.admin_tools",
        "cogs.pickle_tracking",
        "cogs.custom_commands"
    ]
    
    success_count = 0
    for cog in cog_list:
        try:
            await bot.load_extension(cog)
            logger.log(f"Loaded extension: {cog}")
            success_count += 1
        except Exception as e:
            logger.log(f"Failed to load extension {cog}: {e}", "error")
    
    if success_count == len(cog_list):
        logger.log("Successfully loaded all cogs!")
    else:
        logger.log(f"Failed to load {len(cog_list) - success_count} cogs", "error")

async def start_bot():
    """Start a single bot instance with all features"""
    bot = commands.Bot(
        command_prefix="!",
        description="PickleJar Bot - A Discord bot with pickle tracking and moderation features",
        intents=discord.Intents.all()
    )
    
    @bot.event
    async def on_ready():
        server_count = len(bot.guilds)
        logger.log(f"{bot.user} is online! Serving {server_count} servers.")
        try:
            synced = await bot.tree.sync()
            logger.log(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.log(f"Failed to sync commands: {e}", "error")

    # Load all cogs
    await load_cogs(bot)
    
    # Try to get token
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        token = os.getenv("DISCORD_PICKLE_BOT_TOKEN")  # Fallback to pickle bot token
    
    if not token:
        logger.log("No bot token found in environment variables. Please set DISCORD_BOT_TOKEN in .env file.", "error")
        return
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.log("Invalid token. Please check your bot token.", "error")
    except Exception as e:
        logger.log(f"Error starting bot: {str(e)}", "error")

async def main():
    """Main function to start the bot"""
    print(r"""
 ____  _      _    _        _               ____        _
|  _ \(_) ___| | _| | ___  | | __ _ _ __   | __ )  ___ | |_
| |_) | |/ __| |/ / |/ _ \ | |/ _` | '__|  |  _ \ / _ \| __|
|  __/| | (__|   <| |  __/ | | (_| | |     | |_) | (_) | |_
|_|   |_|\___|_|\_\_|\___| |_|\__,_|_|     |____/ \___/ \__|

Starting PickleJar Bot...
    """)

    # Connect to database but don't require it
    db_connected = await db.connect(required=False)
    if not db_connected:
        logger.log("Warning: Running without database connection. Some features will be unavailable.", "error")
    else:
        # Initialize database tables if connected successfully
        try:
            schema_created = await db.create_tables_from_schema("postgresql_schema_optimized.sql")
            if schema_created:
                logger.log("Database tables created successfully!")
            else:
                logger.log("Failed to create database tables. Some features may not work correctly.", "warning")
        except Exception as e:
            logger.log(f"Error creating database tables: {str(e)}", "error")
    
    # Start the bot
    await start_bot()