import discord
from discord.ext import commands

class CommunityRecognition(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="recognize")
    async def recognize(self, ctx, member: discord.Member, *, message="No description"):
        """Recognize a community member's contributions."""
        await ctx.send(f"👏 {ctx.author.mention} recognized {member.mention}: {message}")

async def setup(bot: commands.Bot):
    await bot.add_cog(CommunityRecognition(bot))
