import discord
from discord.ext import commands
import traceback
import sys
from utils.logger import logger

class ErrorHandler(commands.Cog):
    """A cog for global error handling."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""
        
        # This prevents any commands with local handlers from being handled here
        if hasattr(ctx.command, 'on_error'):
            return

        # Get the original exception
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            # Optional: you can send a message or simply ignore unknown commands
            return

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f'`{ctx.command}` has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'`{ctx.command}` cannot be used in Private Messages.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.BadArgument):
            await ctx.send('Bad argument provided. Please check your input and try again.')

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Missing required argument: {error.param.name}')

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(f'You lack the required permissions to use this command.')

        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f'I lack the required permissions to execute this command.')

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is on cooldown. Please try again in {error.retry_after:.1f} seconds.')
        
        else:
            # All other Errors not returned come here
            error_message = f'Ignoring exception in command {ctx.command}: {error}'
            logger.log(error_message, "error")
            logger.log(traceback.format_exception(type(error), error, error.__traceback__), "error")
            
            # Send a message to the user
            await ctx.send(f'An error occurred: {str(error)}')

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
