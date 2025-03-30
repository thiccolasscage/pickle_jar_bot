import discord
from discord.ext import commands
from utils.db_manager import db
from utils.logger import logger

class PickleTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Example words that trigger "pickle" rewards
        self.pickle_words = {"pickle", "dill", "gherkins"}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content_lower = message.content.lower()
        if any(word in content_lower for word in self.pickle_words):
            await message.channel.send(f"🥒 {message.author.mention} just got a pickle!")
            logger.log(f"{message.author} mentioned a pickle word.")

            # Optional: If you want to store in DB, adapt the code below:
            # user_id = str(message.author.id)
            # await db.execute(
            #     \"\"\"INSERT INTO pickle_counts(user_id, pickles)
            #         VALUES($1, 1)
            #         ON CONFLICT (user_id)
            #         DO UPDATE SET pickles = pickle_counts.pickles + 1\"\"\",
            #     user_id
            # )

async def setup(bot: commands.Bot):
    await bot.add_cog(PickleTracking(bot))
