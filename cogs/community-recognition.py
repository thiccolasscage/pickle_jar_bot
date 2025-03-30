import discord
from discord.ext import commands
from utils.db_manager import db
from utils.logger import logger
import datetime

class CommunityRecognition(commands.Cog):
    """Commands for recognizing community members"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="recognize", aliases=["thank", "thanks"])
    async def recognize(self, ctx, member: discord.Member, *, message="No description"):
        """Recognize a community member's contributions"""
        # Prevent self-recognition
        if member.id == ctx.author.id:
            await ctx.send("You can't recognize yourself! Try recognizing someone else.")
            return
            
        # Prevent recognizing bots
        if member.bot:
            await ctx.send("Bots don't need recognition - they're just doing their job! Try recognizing a human instead.")
            return
            
        recognition_message = f"👏 {ctx.author.mention} recognized {member.mention}: {message}"
        await ctx.send(recognition_message)
        
        logger.log(f"{ctx.author} recognized {member}: {message}")
        
        try:
            # Store recognition in database
            await self.store_recognition(ctx.author.id, member.id, message)
            
            # Update recognition count
            await self.update_recognition_count(member.id)
        except Exception as e:
            logger.log(f"Error storing recognition: {str(e)}", "error")

    async def store_recognition(self, from_id, to_id, message):
        """Store recognition details in database"""
        try:
            # Ensure table exists
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS recognitions (
                    id SERIAL PRIMARY KEY,
                    from_user VARCHAR(32) NOT NULL,
                    to_user VARCHAR(32) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            
            # Insert recognition
            await db.execute(
                """
                INSERT INTO recognitions(from_user, to_user, message, created_at)
                VALUES($1, $2, $3, $4)
                """,
                str(from_id), str(to_id), message, datetime.datetime.now()
            )
        except Exception as e:
            logger.log(f"Error in store_recognition: {str(e)}", "error")
            raise

    async def update_recognition_count(self, user_id):
        """Update recognition count for a user"""
        try:
            # Create table if it doesn't exist
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS recognition_counts (
                    user_id VARCHAR(32) PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
                """
            )
            
            # Update count
            await db.execute(
                """
                INSERT INTO recognition_counts(user_id, count)
                VALUES($1, 1)
                ON CONFLICT (user_id)
                DO UPDATE SET count = recognition_counts.count + 1
                """,
                str(user_id)
            )
        except Exception as e:
            logger.log(f"Error in update_recognition_count: {str(e)}", "error")
            raise

    @commands.command(name="recognitions", aliases=["thanks_received"])
    async def recognition_count(self, ctx, member: discord.Member = None):
        """See how many times someone has been recognized"""
        target = member or ctx.author
        user_id = str(target.id)
        
        try:
            # Get recognition count
            count = await db.fetchval(
                "SELECT count FROM recognition_counts WHERE user_id = $1",
                user_id
            ) or 0
            
            if count == 0:
                await ctx.send(f"{target.mention} hasn't been recognized yet.")
            else:
                times = "time" if count == 1 else "times"
                await ctx.send(f"🏆 {target.mention} has been recognized {count} {times}!")
        except Exception as e:
            logger.log(f"Error retrieving recognition count: {str(e)}", "error")
            await ctx.send("I couldn't retrieve the recognition count at this time.")

    @commands.command(name="recognition_leaderboard", aliases=["top_recognized"])
    async def recognition_leaderboard(self, ctx):
        """Show the most recognized community members"""
        try:
            # Ensure table exists
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS recognition_counts (
                    user_id VARCHAR(32) PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
                """
            )
            
            # Get top 10 recognized users
            results = await db.fetch(
                "SELECT user_id, count FROM recognition_counts ORDER BY count DESC LIMIT 10"
            )
            
            if not results:
                await ctx.send("No one has been recognized yet!")
                return
                
            embed = discord.Embed(
                title="🏆 Recognition Leaderboard",
                description="Most recognized community members",
                color=discord.Color.gold()
            )
            
            for i, record in enumerate(results, 1):
                user_id = record["user_id"]
                count = record["count"]
                
                # Try to get user
                user = self.bot.get_user(int(user_id))
                name = user.name if user else f"User {user_id}"
                
                # Add medal emoji for top 3
                medal = ""
                if i == 1:
                    medal = "🥇 "
                elif i == 2:
                    medal = "🥈 "
                elif i == 3:
                    medal = "🥉 "
                
                # Format count
                times = "time" if count == 1 else "times"
                
                embed.add_field(
                    name=f"{medal}{i}. {name}",
                    value=f"Recognized {count} {times}",
                    inline=False
                )
                
            await ctx.send(embed=embed)
        except Exception as e:
            logger.log(f"Error retrieving recognition leaderboard: {str(e)}", "error")
            await ctx.send("I couldn't retrieve the recognition leaderboard at this time.")

async def setup(bot):
    await bot.add_cog(CommunityRecognition(bot))
