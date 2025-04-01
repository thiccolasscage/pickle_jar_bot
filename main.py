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

# Define available cogs
AVAILABLE_COGS = [
    "cogs.error_handler",
    "cogs.moderation",
    "cogs.community_recognition",
    "cogs.admin_tools",
    "cogs.pickle_tracking",
    "cogs.custom_commands"
]

async def load_cogs(bot):
    """Load all cogs from the cogs directory"""
    success_count = 0
    for cog in AVAILABLE_COGS:
        try:
            await bot.load_extension(cog)
            logger.log(f"Loaded extension: {cog}")
            success_count += 1
        except Exception as e:
            logger.log(f"Failed to load extension {cog}: {e}", "error")
    
    if success_count == len(AVAILABLE_COGS):
        logger.log("Successfully loaded all cogs!")
    else:
        logger.log(f"Failed to load {len(AVAILABLE_COGS) - success_count} cogs", "error")

async def start_bot():
    """Start the bot with all features"""
    # Get bot token
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.log("No bot token found in environment variables. Please set DISCORD_BOT_TOKEN in .env file.", "error")
        return
    
    # Create bot instance
    intents = discord.Intents.all()
    bot = commands.Bot(
        command_prefix="!",
        description="PickleJar Bot - A Discord bot with pickle tracking and moderation features",
        intents=intents
    )
    
    @bot.event
    async def on_ready():
        """Called when the bot is ready"""
        server_count = len(bot.guilds)
        member_count = sum(guild.member_count for guild in bot.guilds)
        
        logger.log(f"PickleJar Bot is online!")
        logger.log(f"Bot ID: {bot.user.id}")
        logger.log(f"Serving {server_count} servers with {member_count} members")
        
        # Set activity status
        activity = discord.Activity(type=discord.ActivityType.watching, name="for pickles")
        await bot.change_presence(activity=activity)
        
        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.log(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.log(f"Failed to sync commands: {e}", "error")
    
    # Load all cogs
    await load_cogs(bot)
    
    # Start the bot
    try:
        logger.log("Starting bot...")
        await bot.start(token)
    except discord.LoginFailure:
        logger.log("Invalid token. Please check your DISCORD_BOT_TOKEN in .env file.", "error")
    except Exception as e:
        logger.log(f"Error starting bot: {str(e)}", "error")

# Create a simple web server for health checks
async def health_check(request):
    return web.Response(text="Bot is running!")

async def setup_web_server():
    """Set up a simple web server for health checks"""
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.log("Web server started on port 8080")

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

    # Start the web server for health checks
    web_server_task = asyncio.create_task(setup_web_server())
    
    # Connect to database but don't require it
    try:
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
    except Exception as e:
        logger.log(f"Database initialization error: {str(e)}", "error")
    
    # Start the bot
    await start_bot()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())