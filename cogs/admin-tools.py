import discord
from discord.ext import commands
from utils.db_manager import db
from utils.logger import logger
import asyncio

class AdminTools(commands.Cog):
    """Administrative tools for server management"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! Bot latency: {latency}ms")

    @commands.command(name="stats")
    async def stats(self, ctx):
        """Display bot statistics"""
        server_count = len(self.bot.guilds)
        user_count = sum(guild.member_count for guild in self.bot.guilds)
        channel_count = sum(len(guild.channels) for guild in self.bot.guilds)
        
        embed = discord.Embed(
            title="PickleJar Bot Statistics",
            color=discord.Color.green()
        )
        embed.add_field(name="Servers", value=server_count, inline=True)
        embed.add_field(name="Users", value=user_count, inline=True)
        embed.add_field(name="Channels", value=channel_count, inline=True)
        embed.add_field(name="Bot Version", value="1.0.0", inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Clear a specified number of messages"""
        if amount <= 0:
            await ctx.send("Please specify a positive number of messages to delete.")
            return
            
        if amount > 100:
            await ctx.send("You can only delete up to 100 messages at once.")
            return
            
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        
        confirmation = await ctx.send(f"Deleted {len(deleted) - 1} messages.")
        await asyncio.sleep(3)  # Wait 3 seconds
        await confirmation.delete()  # Delete the confirmation message
        
        logger.log(f"{ctx.author} cleared {len(deleted) - 1} messages in {ctx.channel}")

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx, *, cog: str):
        """Reload a specific cog (owner only)"""
        try:
            await self.bot.reload_extension(cog)
            await ctx.send(f"Successfully reloaded `{cog}`")
            logger.log(f"Cog reloaded: {cog}")
        except Exception as e:
            await ctx.send(f"Failed to reload `{cog}`: {str(e)}")
            logger.log(f"Failed to reload cog {cog}: {str(e)}", "error")

    @commands.command(name="announce")
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send an announcement to a specific channel"""
        embed = discord.Embed(
            title="Announcement",
            description=message,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Announced by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        try:
            await channel.send(embed=embed)
            await ctx.send(f"Announcement sent to {channel.mention}")
            logger.log(f"{ctx.author} sent an announcement to {channel}")
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to send messages in {channel.mention}")
        except Exception as e:
            await ctx.send(f"Failed to send announcement: {str(e)}")

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup_server(self, ctx):
        """Initial server setup for PickleJar Bot"""
        await ctx.send("Starting server setup...")
        
        # Example: Create roles
        try:
            roles_to_create = ["Pickle Enthusiast", "Pickle Master", "Pickle King"]
            created_roles = []
            
            for role_name in roles_to_create:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                if not role:
                    await ctx.guild.create_role(name=role_name)
                    created_roles.append(role_name)
            
            if created_roles:
                await ctx.send(f"Created roles: {', '.join(created_roles)}")
            else:
                await ctx.send("All required roles already exist.")
            
            await ctx.send("Server setup completed successfully!")
        except Exception as e:
            await ctx.send(f"Error during server setup: {str(e)}")

async def setup(bot):
    await bot.add_cog(AdminTools(bot))
