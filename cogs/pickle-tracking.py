import discord
from discord.ext import commands
import random
import time
from utils.db_manager import db
from utils.logger import logger
from utils.config import config

class PickleTracking(commands.Cog):
    """Tracks pickle references and rewards users"""

    def __init__(self, bot):
        self.bot = bot
        # Load pickle words from config
        self.pickle_words = set(config.get("pickle_rewards", {}).get("words", 
            ["pickle", "dill", "gherkin", "gherkins", "pickled"]
        ))
        self.reward_messages = config.get("pickle_rewards", {}).get("reward_messages", [
            "🥒 {user} just got a pickle!",
            "Congrats {user}! You earned a pickle!",
            "One fresh pickle for {user}! 🥒",
            "Pickle acquired! {user} adds one to their collection!"
        ])
        self.cooldown_seconds = config.get("pickle_rewards", {}).get("cooldown_seconds", 300)
        # Track user cooldowns
        self.user_cooldowns = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor messages for pickle-related words and reward users"""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if the message contains any pickle words
        content_lower = message.content.lower()
        if any(word in content_lower for word in self.pickle_words):
            # Check if user is on cooldown
            user_id = str(message.author.id)
            current_time = time.time()
            
            # Check cooldown
            if user_id in self.user_cooldowns:
                last_reward_time = self.user_cooldowns[user_id]
                time_passed = current_time - last_reward_time
                
                if time_passed < self.cooldown_seconds:
                    # User is on cooldown, don't reward
                    remaining = self.cooldown_seconds - time_passed
                    logger.log(f"{message.author} mentioned a pickle word but is on cooldown ({remaining:.0f}s remaining)")
                    return
            
            # User is not on cooldown, reward them
            self.user_cooldowns[user_id] = current_time
            
            # Select a random reward message
            reward_message = random.choice(self.reward_messages)
            formatted_message = reward_message.format(user=message.author.mention)
            
            await message.channel.send(formatted_message)
            logger.log(f"{message.author} mentioned a pickle word and was rewarded")

            # Store in database if connected
            try:
                await db.execute(
                    """
                    INSERT INTO pickle_counts(user_id, count)
                    VALUES($1, 1)
                    ON CONFLICT (user_id)
                    DO UPDATE SET count = pickle_counts.count + 1
                    """,
                    user_id
                )
                logger.log(f"Updated pickle count for {message.author}")
            except Exception as e:
                logger.log(f"Failed to update database for {message.author}: {str(e)}", "error")

    @commands.command(name="pickles")
    async def pickle_count(self, ctx, member: discord.Member = None):
        """Check how many pickles a user has collected"""
        target = member or ctx.author
        user_id = str(target.id)
        
        try:
            result = await db.fetchrow(
                "SELECT count, coins FROM pickle_counts WHERE user_id = $1",
                user_id
            )
            
            if result:
                pickle_count = result['count']
                coin_count = result['coins']
                
                embed = discord.Embed(
                    title="🥒 Pickle Stats",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
                embed.add_field(name="User", value=target.mention, inline=False)
                embed.add_field(name="Pickles Collected", value=f"{pickle_count} 🥒", inline=True)
                embed.add_field(name="Pickle Coins", value=f"{coin_count} 🪙", inline=True)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"{target.mention} hasn't collected any pickles yet! 🥒")
        except Exception as e:
            logger.log(f"Error retrieving pickle count: {str(e)}", "error")
            await ctx.send("I couldn't retrieve the pickle count at this time.")

    @commands.command(name="leaderboard", aliases=["top"])
    async def pickle_leaderboard(self, ctx):
        """Display the pickle leaderboard"""
        try:
            results = await db.fetch(
                "SELECT user_id, count FROM pickle_counts ORDER BY count DESC LIMIT 10"
            )
            
            if not results:
                await ctx.send("No one has collected any pickles yet!")
                return
                
            embed = discord.Embed(
                title="🥒 Pickle Leaderboard",
                description="Top pickle collectors",
                color=discord.Color.green()
            )
            
            for i, record in enumerate(results, 1):
                user_id = record['user_id']
                count = record['count']
                
                # Try to get user information
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
                
                embed.add_field(
                    name=f"{medal}{i}. {name}",
                    value=f"{count} pickles 🥒",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.log(f"Error retrieving leaderboard: {str(e)}", "error")
            await ctx.send("I couldn't retrieve the leaderboard at this time.")

    @commands.command(name="daily")
    async def daily_reward(self, ctx):
        """Claim your daily pickle coins"""
        user_id = str(ctx.author.id)
        
        try:
            # Check if user has already claimed today
            last_claim = await db.fetchval(
                "SELECT last_daily FROM pickle_counts WHERE user_id = $1",
                user_id
            )
            
            import datetime
            now = datetime.datetime.now()
            
            if last_claim:
                # Convert to datetime if it's not already
                if isinstance(last_claim, str):
                    last_claim = datetime.datetime.fromisoformat(last_claim)
                
                # Check if 24 hours have passed
                time_passed = now - last_claim
                if time_passed.total_seconds() < 86400:  # 24 hours in seconds
                    next_claim = last_claim + datetime.timedelta(days=1)
                    time_until = next_claim - now
                    hours, remainder = divmod(int(time_until.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    await ctx.send(f"You've already claimed your daily reward! Next claim available in {hours}h {minutes}m.")
                    return
            
            # Give the reward
            daily_amount = 50  # 50 coins daily reward
            
            await db.execute(
                """
                INSERT INTO pickle_counts(user_id, coins, last_daily)
                VALUES($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET coins = pickle_counts.coins + $2, last_daily = $3
                """,
                user_id, daily_amount, now
            )
            
            await ctx.send(f"🎉 You claimed your daily reward of {daily_amount} pickle coins! 🪙")
            logger.log(f"{ctx.author} claimed their daily reward")
        except Exception as e:
            logger.log(f"Error processing daily claim: {str(e)}", "error")
            await ctx.send("I couldn't process your daily claim at this time.")

async def setup(bot):
    await bot.add_cog(PickleTracking(bot))
