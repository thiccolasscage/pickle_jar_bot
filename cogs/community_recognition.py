import discord
from discord import app_commands
from discord.ext import commands
import datetime
from typing import Optional
import random
from utils.db_manager import db
from utils.logger import logger
from utils.config import config

class CommunityRecognition(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # Track recognition cooldowns
    
    async def get_recognition_count(self, guild_id, user_id):
        """Get the number of recognitions a user has received"""
        result = await db.fetch(
            """
            SELECT COUNT(*) as count FROM recognitions
            WHERE guild_id = $1 AND user_id = $2
            """,
            str(guild_id), str(user_id)
        )
        return result[0]['count'] if result else 0
    
    @commands.hybrid_command(name="recognize")
    @commands.guild_only()
    @app_commands.describe(
        member="The member to recognize",
        reason="Reason for recognition (optional)"
    )
    async def recognize(self, ctx, member: discord.Member, *, reason: Optional[str] = None):
        """Recognize a community member's contributions"""
        # Check if user is trying to recognize themselves
        if member.id == ctx.author.id:
            await ctx.send("You can't recognize yourself!")
            return
            
        # Check if the user is recognizing a bot
        if member.bot:
            await ctx.send("You can't recognize bots!")
            return
            
        # Check cooldown (prevent spam)
        cooldown_key = f"{ctx.guild.id}:{ctx.author.id}"
        current_time = datetime.datetime.now().timestamp()
        
        if cooldown_key in self.cooldowns:
            last_use = self.cooldowns[cooldown_key]
            if current_time - last_use < 300:  # 5 minute cooldown
                seconds_left = int(300 - (current_time - last_use))
                await ctx.send(f"You can recognize someone again in {seconds_left} seconds.")
                return
                
        # Update cooldown
        self.cooldowns[cooldown_key] = current_time
        
        # Format reason if provided
        formatted_reason = f": {reason}" if reason else ""
        
        # Save recognition to database
        await db.execute(
            """
            INSERT INTO recognitions (guild_id, user_id, recognized_by, reason)
            VALUES ($1, $2, $3, $4)
            """,
            str(ctx.guild.id), str(member.id), str(ctx.author.id), reason
        )
        
        # Get total recognitions for the user
        recognition_count = await self.get_recognition_count(ctx.guild.id, member.id)
        
        # Create and send embed
        embed = discord.Embed(
            title="🏆 Community Recognition",
            description=f"{ctx.author.mention} recognized {member.mention}{formatted_reason}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Total Recognitions", value=str(recognition_count), inline=False)
        
        # Add a special note for milestone recognitions
        if recognition_count in [1, 5, 10, 25, 50, 100, 250, 500, 1000]:
            embed.add_field(
                name="🎉 Milestone Reached!",
                value=f"Congratulations to {member.mention} for reaching {recognition_count} recognitions!",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
        # Optional: Add XP to user_levels table if it exists
        try:
            xp_gain = random.randint(15, 25)  # Random XP between 15-25 for being recognized
            await db.execute(
                """
                INSERT INTO user_levels (guild_id, user_id, xp, level)
                VALUES ($1, $2, $3, 0)
                ON CONFLICT (guild_id, user_id) 
                DO UPDATE SET xp = user_levels.xp + $3
                """,
                str(ctx.guild.id), str(member.id), xp_gain
            )
        except Exception as e:
            logger.log(f"Error adding XP for recognition: {e}", "error")
    
    @commands.hybrid_command(name="recognitions")
    @commands.guild_only()
    @app_commands.describe(
        member="The member to check recognitions for (default: yourself)"
    )
    async def recognitions(self, ctx, member: Optional[discord.Member] = None):
        """Check how many times a member has been recognized"""
        # Default to the command author if no member is specified
        target = member or ctx.author
        
        # Get recognition count
        recognition_count = await self.get_recognition_count(ctx.guild.id, target.id)
        
        # Get recent recognitions
        recent = await db.fetch(
            """
            SELECT recognized_by, reason, timestamp
            FROM recognitions
            WHERE guild_id = $1 AND user_id = $2
            ORDER BY timestamp DESC
            LIMIT 5
            """,
            str(ctx.guild.id), str(target.id)
        )
        
        # Create embed
        embed = discord.Embed(
            title=f"Recognitions for {target.display_name}",
            description=f"{target.mention} has received **{recognition_count}** recognitions",
            color=discord.Color.gold()
        )
        
        # Add recent recognitions if any
        if recent:
            recent_text = ""
            for i, rec in enumerate(recent, 1):
                recognizer = ctx.guild.get_member(int(rec['recognized_by']))
                recognizer_name = recognizer.display_name if recognizer else "Unknown User"
                
                reason = f": {rec['reason']}" if rec['reason'] else ""
                time = rec['timestamp'].strftime("%Y-%m-%d")
                
                recent_text += f"**{i}.** By {recognizer_name}{reason} • {time}\n"
                
            embed.add_field(name="Recent Recognitions", value=recent_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="leaderboard")
    @commands.guild_only()
    @app_commands.describe(
        range="Number of members to show (default: 10)"
    )
    async def recognition_leaderboard(self, ctx, range: Optional[int] = 10):
        """Show the top recognized members in the server"""
        if range < 1:
            await ctx.send("Please enter a positive number.")
            return
            
        if range > 25:
            range = 25  # Limit to 25 to avoid too long messages
            
        # Get top recognized members
        leaderboard = await db.fetch(
            """
            SELECT user_id, COUNT(*) as count
            FROM recognitions
            WHERE guild_id = $1
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT $2
            """,
            str(ctx.guild.id), range
        )
        
        if not leaderboard:
            await ctx.send("No recognitions have been given yet!")
            return
            
        # Create embed
        embed = discord.Embed(
            title="🏆 Recognition Leaderboard",
            description=f"Top {range} most recognized members",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        leaderboard_text = ""
        for i, entry in enumerate(leaderboard, 1):
            user_id = int(entry['user_id'])
            count = entry['count']
            
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
                
            leaderboard_text += f"**{i}.** {medal}{name} • {count} recognition{'s' if count != 1 else ''}\n"
            
        embed.description = leaderboard_text
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="thankers")
    @commands.guild_only()
    @app_commands.describe(
        range="Number of members to show (default: 10)"
    )
    async def top_recognizers(self, ctx, range: Optional[int] = 10):
        """Show members who have given the most recognitions"""
        if range < 1:
            await ctx.send("Please enter a positive number.")
            return
            
        if range > 25:
            range = 25  # Limit to 25 to avoid too long messages
            
        # Get top recognizers
        leaderboard = await db.fetch(
            """
            SELECT recognized_by, COUNT(*) as count
            FROM recognitions
            WHERE guild_id = $1
            GROUP BY recognized_by
            ORDER BY count DESC
            LIMIT $2
            """,
            str(ctx.guild.id), range
        )
        
        if not leaderboard:
            await ctx.send("No recognitions have been given yet!")
            return
            
        # Create embed
        embed = discord.Embed(
            title="👏 Top Recognizers",
            description=f"Members who recognize others the most",
            color=discord.Color.blue()
        )
        
        # Add leaderboard entries
        leaderboard_text = ""
        for i, entry in enumerate(leaderboard, 1):
            user_id = int(entry['recognized_by'])
            count = entry['count']
            
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
                
            leaderboard_text += f"**{i}.** {medal}{name} • {count} given\n"
            
        embed.description = leaderboard_text
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CommunityRecognition(bot))