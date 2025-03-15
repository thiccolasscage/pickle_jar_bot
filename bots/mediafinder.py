import discord
from discord.ext import commands
import aiohttp

class MediaFinder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="findmedia")
    async def find_media(self, ctx, *, query: str):
        """Fetch media from a hypothetical external API."""
        # Example: "cat videos" or "dog images"
        api_url = f"https://api.example.com/search?query={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "url" in data:
                        await ctx.send(data["url"])
                    else:
                        await ctx.send("No media URL found in response.")
                else:
                    await ctx.send("No media found or API error.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MediaFinder(bot))
