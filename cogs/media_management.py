import discord
from discord import app_commands
from discord.ext import commands
from utils.db_manager import db  # Reuse your async PostgreSQL manager

class MediaContributions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="contribute", description="Submit a media link for approval.")
    @app_commands.describe(
        url="Direct link to the media (image, gif, etc.)",
        title="Optional title for the submission",
        description="Optional description",
        tags="Comma-separated tags (e.g., funny, dog, chill)"
    )
    async def contribute(self, interaction: discord.Interaction, url: str, title: str = None, description: str = None, tags: str = None):
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        await db.execute(
            """
            INSERT INTO media_submissions (url, title, description, tags, submitted_by)
            VALUES ($1, $2, $3, $4, $5)
            """,
            url, title, description, tag_list, str(interaction.user.id)
        )

        await interaction.response.send_message(
            f"✅ Thanks, {interaction.user.mention}! Your media has been submitted for review.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(MediaContributions(bot))