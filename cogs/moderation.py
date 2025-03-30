import discord
from discord.ext import commands
from utils.db_manager import db
from utils.logger import logger
from utils.config import config
import datetime

class Moderation(commands.Cog):
    """Commands for server moderation"""

    def __init__(self, bot):
        self.bot = bot
        self.default_warning_reason = config.get("moderation", {}).get(
            "default_warning_reason", "Breaking server rules"
        )
        self.warning_thresholds = config.get("moderation", {}).get("warning_thresholds", {
            "3": "mute",
            "5": "kick",
            "7": "ban"
        })
        self.auto_punish = config.get("moderation", {}).get("auto_punish", False)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a user from the server"""
        try:
            await member.ban(reason=reason)
            
            # Log the ban
            logger.log(f"{ctx.author} banned {member} for: {reason}")
            
            # Send confirmation
            embed = discord.Embed(
                title="User Banned",
                description=f"{member.mention} has been banned",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason)
            embed.set_footer(text=f"Banned by {ctx.author}")
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                embed = discord.Embed(
                    title=f"You've been banned from {ctx.guild.name}",
                    description=f"Reason: {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=embed)
            except discord.Forbidden:
                # Can't DM the user
                pass
                
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that user.")
        except Exception as e:
            logger.log(f"Error banning user: {str(e)}", "error")
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a user from the server"""
        try:
            await member.kick(reason=reason)
            
            # Log the kick
            logger.log(f"{ctx.author} kicked {member} for: {reason}")
            
            # Send confirmation
            embed = discord.Embed(
                title="User Kicked",
                description=f"{member.mention} has been kicked",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason)
            embed.set_footer(text=f"Kicked by {ctx.author}")
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                embed = discord.Embed(
                    title=f"You've been kicked from {ctx.guild.name}",
                    description=f"Reason: {reason}",
                    color=discord.Color.orange()
                )
                await member.send(embed=embed)
            except discord.Forbidden:
                # Can't DM the user
                pass
                
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that user.")
        except Exception as e:
            logger.log(f"Error kicking user: {str(e)}", "error")
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_user(self, ctx, member: discord.Member, *, reason=None):
        """Warn a user"""
        if reason is None:
            reason = self.default_warning_reason
            
        user_id = str(member.id)
        
        try:
            # Get current warning count
            current_warnings = await db.fetchval(
                "SELECT warnings FROM pickle_counts WHERE user_id = $1",
                user_id
            ) or 0
            
            # Increment warnings
            new_warnings = current_warnings + 1
            
            # Update in database
            await db.execute(
                """
                INSERT INTO pickle_counts(user_id, warnings)
                VALUES($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET warnings = $2
                """,
                user_id, new_warnings
            )
            
            # Log the warning
            logger.log(f"{ctx.author} warned {member} (Warning #{new_warnings}): {reason}")
            
            # Send confirmation
            embed = discord.Embed(
                title="User Warned",
                description=f"{member.mention} has been warned",
                color=discord.Color.gold()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Warning Count", value=str(new_warnings), inline=False)
            embed.set_footer(text=f"Warned by {ctx.author}")
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                embed = discord.Embed(
                    title=f"You've been warned in {ctx.guild.name}",
                    description=f"Reason: {reason}",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Warning Count", value=str(new_warnings), inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                # Can't DM the user
                pass
                
            # Check for auto-punishments if enabled
            if self.auto_punish:
                await self.check_auto_punish(ctx, member, new_warnings)
                
        except Exception as e:
            logger.log(f"Error warning user: {str(e)}", "error")
            await ctx.send(f"An error occurred: {str(e)}")

    async def check_auto_punish(self, ctx, member, warning_count):
        """Check if auto-punishment should be applied based on warning count"""
        warning_count_str = str(warning_count)
        
        # Check if this warning count triggers a punishment
        for threshold, action in self.warning_thresholds.items():
            if warning_count_str == threshold:
                if action == "mute":
                    # Example implementation - this requires a mute role to be set up
                    try:
                        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
                        if mute_role:
                            await member.add_roles(mute_role)
                            await ctx.send(f"{member.mention} has been automatically muted for reaching {warning_count} warnings.")
                    except Exception as e:
                        logger.log(f"Failed to auto-mute: {str(e)}", "error")
                
                elif action == "kick":
                    try:
                        await member.kick(reason=f"Automatic kick: Reached {warning_count} warnings")
                        await ctx.send(f"{member.mention} has been automatically kicked for reaching {warning_count} warnings.")
                    except Exception as e:
                        logger.log(f"Failed to auto-kick: {str(e)}", "error")
                
                elif action == "ban":
                    try:
                        await member.ban(reason=f"Automatic ban: Reached {warning_count} warnings")
                        await ctx.send(f"{member.mention} has been automatically banned for reaching {warning_count} warnings.")
                    except Exception as e:
                        logger.log(f"Failed to auto-ban: {str(e)}", "error")

    @commands.command(name="warnings")
    async def get_warnings(self, ctx, member: discord.Member = None):
        """Check warnings for a user"""
        target = member or ctx.author
        user_id = str(target.id)
        
        try:
            # Get warning count
            warnings = await db.fetchval(
                "SELECT warnings FROM pickle_counts WHERE user_id = $1",
                user_id
            ) or 0
            
            # Send response
            if warnings == 0:
                await ctx.send(f"{target.mention} has no warnings! 🎉")
            else:
                await ctx.send(f"{target.mention} has {warnings} warning(s).")
                
        except Exception as e:
            logger.log(f"Error retrieving warnings: {str(e)}", "error")
            await ctx.send("I couldn't retrieve warning information at this time.")

    @commands.command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear all warnings for a user"""
        user_id = str(member.id)
        
        try:
            # Update database
            await db.execute(
                """
                UPDATE pickle_counts
                SET warnings = 0
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Log action
            logger.log(f"{ctx.author} cleared all warnings for {member}")
            
            # Send confirmation
            await ctx.send(f"All warnings for {member.mention} have been cleared.")
                
        except Exception as e:
            logger.log(f"Error clearing warnings: {str(e)}", "error")
            await ctx.send("I couldn't clear the warnings at this time.")

    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute_user(self, ctx, member: discord.Member, duration: int = 10, *, reason="No reason provided"):
        """Mute a user for a specified number of minutes"""
        try:
            # Check for Muted role
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not muted_role:
                # Create role if it doesn't exist
                muted_role = await ctx.guild.create_role(name="Muted", reason="Mute command used but no Muted role existed")
                
                # Set permissions for the role
                for channel in ctx.guild.channels:
                    try:
                        await channel.set_permissions(muted_role, send_messages=False, speak=False)
                    except:
                        pass
            
            # Add role to user
            await member.add_roles(muted_role, reason=reason)
            
            # Log the mute
            logger.log(f"{ctx.author} muted {member} for {duration} minutes: {reason}")
            
            # Send confirmation
            embed = discord.Embed(
                title="User Muted",
                description=f"{member.mention} has been muted for {duration} minutes",
                color=discord.Color.dark_orange()
            )
            embed.add_field(name="Reason", value=reason)
            embed.set_footer(text=f"Muted by {ctx.author}")
            
            await ctx.send(embed=embed)
            
            # Schedule unmute
            if duration > 0:
                # Import needed here to avoid circular imports
                import asyncio
                await asyncio.sleep(duration * 60)
                # Check if still muted
                if muted_role in member.roles:
                    await member.remove_roles(muted_role, reason="Mute duration expired")
                    await ctx.send(f"{member.mention} has been unmuted (mute duration expired).")
                
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except Exception as e:
            logger.log(f"Error muting user: {str(e)}", "error")
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute_user(self, ctx, member: discord.Member, *, reason="Mute duration expired"):
        """Unmute a user"""
        try:
            # Check for Muted role
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not muted_role:
                await ctx.send("There is no Muted role set up!")
                return
                
            # Check if user is muted
            if muted_role not in member.roles:
                await ctx.send(f"{member.mention} is not currently muted!")
                return
                
            # Remove muted role
            await member.remove_roles(muted_role, reason=reason)
            
            # Log the unmute
            logger.log(f"{ctx.author} unmuted {member}: {reason}")
            
            # Send confirmation
            await ctx.send(f"{member.mention} has been unmuted.")
                
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except Exception as e:
            logger.log(f"Error unmuting user: {str(e)}", "error")
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
