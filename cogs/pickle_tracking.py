import discord
from discord import app_commands
from discord.ext import commands
import datetime
import random
from typing import Optional, List
from utils.db_manager import db
from utils.logger import logger
from utils.config import config

class PickleTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pickle_words = set(config.get("pickle_rewards", {}).get("words", ["pickle", "dill", "gherkins"]))
        self.cooldown_seconds = config.get("pickle_rewards", {}).get("cooldown_seconds", 300)
        self.reward_messages = config.get("pickle_rewards", {}).get("reward_messages", ["🥒 {user} just got a pickle!"])
        self.user_cooldowns = {}  # Track user cooldowns
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages containing pickle words"""
        # Ignore messages from bots
        if message.author.bot:
            return
            
        # Check if the message contains a pickle word
        content_lower = message.content.lower()
        if not any(word in content_lower for word in self.pickle_words):
            return
            
        # Check if the user is on cooldown
        user_id = str(message.author.id)
        guild_id = str(message.guild.id) if message.guild else "DM"
        
        cooldown_key = f"{guild_id}:{user_id}"
        current_time = datetime.datetime.now().timestamp()
        
        if cooldown_key in self.user_cooldowns:
            last_pickle = self.user_cooldowns[cooldown_key]
            if current_time - last_pickle < self.cooldown_seconds:
                # User is on cooldown, don't reward
                return
        
        # User is not on cooldown, update cooldown time
        self.user_cooldowns[cooldown_key] = current_time
        
        # Insert or update pickle count in database
        query = """
        INSERT INTO pickle_counts(user_id, pickles, last_pickle_at)
        VALUES($1, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id)
        DO UPDATE SET 
            pickles = pickle_counts.pickles + 1,
            last_pickle_at = CURRENT_TIMESTAMP
        """
        
        try:
            await db.execute(query, user_id)
            logger.log(f"{message.author} mentioned a pickle word and received a pickle.")
            
            # Get random reward message
            reward_message = random.choice(self.reward_messages)
            formatted_message = reward_message.format(user=message.author.mention)
            
            # Send reward message
            await message.channel.send(formatted_message)
            
            # Add XP to user_levels if it exists
            try:
                xp_gain = random.randint(1, 5)  # Small random XP for pickle mentions
                await db.execute(
                    """
                    INSERT INTO user_levels (guild_id, user_id, xp, level)
                    VALUES ($1, $2, $3, 0)
                    ON CONFLICT (guild_id, user_id) 
                    DO UPDATE SET xp = user_levels.xp + $3
                    """,
                    guild_id, user_id, xp_gain
                )
            except Exception as e:
                # Silently fail if user_levels table doesn't exist
                pass
                
        except Exception as e:
            logger.log(f"Error updating pickle count: {str(e)}", "error")
    
    @commands.hybrid_command(name="pickles")
    @app_commands.describe(
        member="The member to check pickle count for (default: yourself)"
    )
    async def check_pickles(self, ctx, member: Optional[discord.Member] = None):
        """Check how many pickles a member has"""
        target = member or ctx.author
        user_id = str(target.id)
        
        # Query database for pickle count
        query = "SELECT pickles, last_pickle_at FROM pickle_counts WHERE user_id = $1"
        result = await db.fetchrow(query, user_id)
        
        if result:
            pickles = result['pickles']
            last_pickle = result['last_pickle_at']
            
            # Create embed
            embed = discord.Embed(
                title="🥒 Pickle Jar",
                description=f"{target.mention}'s pickle count",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Pickles Collected",
                value=str(pickles),
                inline=False
            )
            
            # Format last pickle time
            embed.add_field(
                name="Last Pickle",
                value=f"<t:{int(last_pickle.timestamp())}:R>",
                inline=False
            )
            
            # Add pickle jar visualization
            jar_fill = min(pickles / 100, 1.0)  # Cap at 100 pickles for a full jar
            jar_segments = 10
            filled_segments = int(jar_fill * jar_segments)
            
            jar_visual = "🫙 |"
            jar_visual += "🥒" * filled_segments
            jar_visual += "  " * (jar_segments - filled_segments)
            jar_visual += "|"
            
            embed.add_field(
                name="Pickle Jar",
                value=jar_visual,
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{target.display_name} hasn't collected any pickles yet!")
    
    @commands.hybrid_command(name="pickleboard")
    @app_commands.describe(
        limit="Number of members to show (default: 10)"
    )
    async def pickle_leaderboard(self, ctx, limit: Optional[int] = 10):
        """Show the pickle leaderboard"""
        if limit < 1:
            await ctx.send("Please enter a positive number.")
            return
            
        if limit > 25:
            limit = 25  # Limit to 25 to avoid too long messages
            
        # Query database for top pickle collectors
        query = """
        SELECT user_id, pickles
        FROM pickle_counts
        ORDER BY pickles DESC
        LIMIT $1
        """
        
        results = await db.fetch(query, limit)
        
        if not results:
            await ctx.send("No one has collected any pickles yet!")
            return
            
        # Create embed
        embed = discord.Embed(
            title="🥒 Pickle Leaderboard",
            description=f"Top {limit} pickle collectors",
            color=discord.Color.green()
        )
        
        # Add leaderboard entries
        entries = []
        
        for i, entry in enumerate(results, 1):
            user_id = int(entry['user_id'])
            pickles = entry['pickles']
            
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            
            # Add medal emoji for top 3
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
                
            entries.append(f"**{i}.** {medal}{name} • {pickles} pickle{'s' if pickles != 1 else ''}")
            
        embed.description = "\n".join(entries)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="add_pickle_word")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        word="The word to add to pickle triggers"
    )
    async def add_pickle_word(self, ctx, *, word: str):
        """Add a new word that triggers pickle rewards (Admin only)"""
        # Convert to lowercase for case-insensitive matching
        word = word.lower().strip()
        
        if word in self.pickle_words:
            await ctx.send(f"`{word}` is already a pickle trigger word.")
            return
            
        # Add word to the set
        self.pickle_words.add(word)
        
        # Update config
        current_words = config.get("pickle_rewards", {}).get("words", [])
        current_words.append(word)
        
        # TODO: Save to config file if needed
        
        await ctx.send(f"✅ Added `{word}` to pickle trigger words.")
        logger.log(f"{ctx.author} added '{word}' to pickle trigger words.")
    
    @commands.hybrid_command(name="remove_pickle_word")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        word="The word to remove from pickle triggers"
    )
    async def remove_pickle_word(self, ctx, *, word: str):
        """Remove a word from pickle triggers (Admin only)"""
        # Convert to lowercase for case-insensitive matching
        word = word.lower().strip()
        
        if word not in self.pickle_words:
            await ctx.send(f"`{word}` is not a pickle trigger word.")
            return
            
        # Remove word from the set
        self.pickle_words.remove(word)
        
        # Update config
        current_words = config.get("pickle_rewards", {}).get("words", [])
        if word in current_words:
            current_words.remove(word)
        
        # TODO: Save to config file if needed
        
        await ctx.send(f"✅ Removed `{word}` from pickle trigger words.")
        logger.log(f"{ctx.author} removed '{word}' from pickle trigger words.")
    
    @commands.hybrid_command(name="pickle_words")
    @app_commands.describe()
    async def list_pickle_words(self, ctx):
        """List all words that trigger pickle rewards"""
        if not self.pickle_words:
            await ctx.send("There are no pickle trigger words configured.")
            return
            
        # Create embed
        embed = discord.Embed(
            title="🥒 Pickle Trigger Words",
            description="Mentioning these words will give you a pickle (subject to cooldown):",
            color=discord.Color.green()
        )
        
        # Format word list
        word_list = "• " + "\n• ".join(sorted(self.pickle_words))
        embed.add_field(name="Words", value=word_list, inline=False)
        
        # Add cooldown info
        minutes = self.cooldown_seconds // 60
        seconds = self.cooldown_seconds % 60
        time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        if seconds:
            time_str += f" and {seconds} second{'s' if seconds != 1 else ''}"
            
        embed.add_field(
            name="Cooldown",
            value=f"You can get a new pickle every {time_str}.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="give_pickle")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        member="The member to give a pickle to",
        amount="Number of pickles to give (default: 1)"
    )
    async def give_pickle(self, ctx, member: discord.Member, amount: Optional[int] = 1):
        """Give pickles to a member (Admin only)"""
        if amount <= 0:
            await ctx.send("Please specify a positive number of pickles.")
            return
            
        if amount > 100:
            await ctx.send("You can give at most 100 pickles at once.")
            return
            
        user_id = str(member.id)
        
        # Update pickle count in database
        query = """
        INSERT INTO pickle_counts(user_id, pickles, last_pickle_at)
        VALUES($1, $2, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id)
        DO UPDATE SET 
            pickles = pickle_counts.pickles + $2,
            last_pickle_at = CURRENT_TIMESTAMP
        """
        
        try:
            await db.execute(query, user_id, amount)
            
            # Send confirmation
            pickle_word = "pickle" if amount == 1 else "pickles"
            await ctx.send(f"✅ Gave {amount} {pickle_word} to {member.mention}.")
            logger.log(f"{ctx.author} gave {amount} pickles to {member}.")
            
        except Exception as e:
            logger.log(f"Error giving pickles: {str(e)}", "error")
            await ctx.send("Error giving pickles. Please check the logs.")

async def setup(bot):
    await bot.add_cog(PickleTracking(bot))