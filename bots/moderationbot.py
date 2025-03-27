import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a user."""
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} has been banned. Reason: {reason}")

    @commands.command(name="warn")
    async def warn_user(self, ctx, member: discord.Member, *, reason="Breaking rules"):
        """Warn a user."""
        await ctx.send(f"{member.mention} has been warned for: {reason}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
