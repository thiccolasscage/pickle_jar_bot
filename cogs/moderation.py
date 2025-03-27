import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import asyncio
from typing import Optional, Literal
from utils.db_manager import db
from utils.logger import logger
from utils.config import config

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_expired_punishments.start()
        
    def cog_unload(self):
        self.check_expired_punishments.cancel()
    
    async def get_guild_settings(self, guild_id):
        """Retrieve guild settings from database"""
        settings = await db.fetchrow(
            "SELECT * FROM guild_settings WHERE guild_id = $1",
            str(guild_id)
        )
        return settings or {}
    
    async def has_mod_permissions(self, ctx):
        """Check if user has moderation permissions"""
        if ctx.author.guild_permissions.administrator:
            return True
            
        settings = await self.get_guild_settings(ctx.guild.id)
        mod_role_id = settings.get('mod_role_id')
        
        if mod_role_id:
            mod_role = ctx.guild.get_role(int(mod_role_id))
            if mod_role and mod_role in ctx.author.roles:
                return True
                
        return False
    
    @tasks.loop(minutes=5)
    async def check_expired_punishments(self):
        """Check and remove expired punishments"""
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Fetch expired punishments
        expired = await db.fetch(
            """
            SELECT * FROM timed_punishments 
            WHERE expires_at < $1 AND active = TRUE
            """,
            now
        )
        
        for record in expired:
            guild_id = int(record['guild_id'])
            user_id = int(record['user_id'])
            punishment_type = record['punishment_type']
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
                
            if punishment_type == 'mute':
                # Handle expired mute
                settings = await self.get_guild_settings(guild_id)
                mute_role_id = settings.get('mute_role_id')
                
                if mute_role_id:
                    mute_role = guild.get_role(int(mute_role_id))
                    member = guild.get_member(user_id)
                    
                    if member and mute_role and mute_role in member.roles:
                        try:
                            await member.remove_roles(mute_role, reason="Mute duration expired")
                            logger.log(f"Removed expired mute for {member} in {guild}")
                        except discord.HTTPException as e:
                            logger.log(f"Failed to remove mute role: {e}", "error")
            
            elif punishment_type == 'ban':
                # Handle expired ban
                try:
                    await guild.unban(discord.Object(user_id), reason="Ban duration expired")
                    logger.log(f"Removed expired ban for user {user_id} in {guild}")
                except discord.HTTPException as e:
                    logger.log(f"Failed to unban user {user_id}: {e}", "error")
            
            # Mark punishment as inactive
            await db.execute(
                """
                UPDATE timed_punishments
                SET active = FALSE
                WHERE id = $1
                """,
                record['id']
            )
    
    @check_expired_punishments.before_loop
    async def before_check_punishments(self):
        await self.bot.wait_until_ready()
    
    @commands.hybrid_command(name="warn")
    @commands.guild_only()
    @app_commands.describe(
        member="The member to warn",
        reason="The reason for the warning"
    )
    async def warn_user(self, ctx, member: discord.Member, *, reason: str = None):
        """Warn a user for breaking rules"""
        if not await self.has_mod_permissions(ctx):
            await ctx.send("You don't have permission to use this command.")
            return
            
        if reason is None:
            reason = config.get("moderation", {}).get("default_warning_reason", "No reason provided")
        
        # Store warning in database
        await db.execute(
            """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES ($1, $2, $3, $4)
            """,
            str(ctx.guild.id), str(member.id), str(ctx.author.id), reason
        )
        
        # Get warning count
        warnings = await db.fetch(
            """
            SELECT COUNT(*) as count FROM warnings
            WHERE guild_id = $1 AND user_id = $2 AND active = TRUE
            """,
            str(ctx.guild.id), str(member.id)
        )
        warning_count = warnings[0]['count'] if warnings else 0
        
        # Create embed for warning
        embed = discord.Embed(
            title="⚠️ Warning",
            description=f"{member.mention} has been warned by {ctx.author.mention}",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Warning Count", value=str(warning_count), inline=False)
        embed.set_footer(text=f"ID: {member.id}")
        
        await ctx.send(embed=embed)
        
        # Send DM to warned user
        try:
            user_embed = discord.Embed(
                title=f"You've been warned in {ctx.guild.name}",
                description=f"**Reason:** {reason}",
                color=discord.Color.yellow()
            )
            user_embed.add_field(name="Warning Count", value=str(warning_count), inline=False)
            user_embed.set_footer(text=f"If you believe this was in error, please contact a server moderator.")
            
            await member.send(embed=user_embed)
        except discord.HTTPException:
            await ctx.send(f"Note: Could not send DM to {member.mention}")
        
        # Check for auto-punishments
        if config.get("moderation", {}).get("auto_punish", False):
            thresholds = config.get("moderation", {}).get("warning_thresholds", {})
            
            for threshold_str, action in thresholds.items():
                threshold = int(threshold_str)
                if warning_count == threshold:
                    if action == "mute":
                        await self.tempmute.invoke(ctx)
                    elif action == "kick":
                        await self.kick_user.invoke(ctx)
                    elif action == "ban":
                        await self.tempban.invoke(ctx)
                    break
    
    @commands.hybrid_command(name="warnings")
    @commands.guild_only()
    @app_commands.describe(
        member="The member to check warnings for"
    )
    async def list_warnings(self, ctx, member: discord.Member):
        """List all warnings for a user"""
        # Anyone can view warnings
        warnings = await db.fetch(
            """
            SELECT id, moderator_id, reason, timestamp, active
            FROM warnings
            WHERE guild_id = $1 AND user_id = $2
            ORDER BY timestamp DESC
            """,
            str(ctx.guild.id), str(member.id)
        )
        
        if not warnings:
            await ctx.send(f"{member.display_name} has no warnings.")
            return
            
        active_warnings = [w for w in warnings if w['active']]
        
        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            description=f"Active warnings: {len(active_warnings)}\nTotal warnings: {len(warnings)}",
            color=discord.Color.orange()
        )
        
        for i, warning in enumerate(warnings[:10], 1):
            moderator = ctx.guild.get_member(int(warning['moderator_id']))
            mod_name = moderator.display_name if moderator else "Unknown Moderator"
            
            status = "Active" if warning['active'] else "Cleared"
            time = warning['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            
            embed.add_field(
                name=f"Warning #{i} ({status})",
                value=f"**Reason:** {warning['reason']}\n" \
                      f"**Moderator:** {mod_name}\n" \
                      f"**Date:** {time}\n" \
                      f"**ID:** {warning['id']}",
                inline=False
            )
        
        if len(warnings) > 10:
            embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings")
            
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clearwarn")
    @commands.guild_only()
    @app_commands.describe(
        warning_id="ID of the warning to clear"
    )
    async def clear_warning(self, ctx, warning_id: int):
        """Clear a specific warning by its ID"""
        if not await self.has_mod_permissions(ctx):
            await ctx.send("You don't have permission to use this command.")
            return
            
        # Verify the warning exists and belongs to this guild
        warning = await db.fetchrow(
            """
            SELECT user_id, active
            FROM warnings
            WHERE id = $1 AND guild_id = $2
            """,
            warning_id, str(ctx.guild.id)
        )
        
        if not warning:
            await ctx.send("Warning not found or not from this server.")
            return
            
        if not warning['active']:
            await ctx.send("This warning is already cleared.")
            return
            
        # Clear the warning
        await db.execute(
            """
            UPDATE warnings
            SET active = FALSE
            WHERE id = $1
            """,
            warning_id
        )
        
        user_id = warning['user_id']
        member = ctx.guild.get_member(int(user_id))
        member_name = member.display_name if member else f"User ID: {user_id}"
        
        await ctx.send(f"✅ Cleared warning #{warning_id} for {member_name}.")
    
    @commands.hybrid_command(name="kick")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(
        member="The member to kick",
        reason="The reason for kicking"
    )
    async def kick_user(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot kick a member with a role higher than or equal to yours.")
            return
            
        # Log the kick
        await db.execute(
            """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES ($1, $2, $3, $4 || ' (Kicked)')
            """,
            str(ctx.guild.id), str(member.id), str(ctx.author.id), reason
        )
        
        try:
            # Try to DM the user before kicking
            embed = discord.Embed(
                title=f"You've been kicked from {ctx.guild.name}",
                description=f"**Reason:** {reason}",
                color=discord.Color.red()
            )
            try:
                await member.send(embed=embed)
            except:
                pass  # Can't DM them, continue with kick
                
            await member.kick(reason=reason)
            
            # Confirmation message
            confirm_embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked by {ctx.author.mention}",
                color=discord.Color.red()
            )
            confirm_embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to kick member: {e}")
    
    @commands.hybrid_command(name="ban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member="The member to ban",
        delete_days="Number of days of message history to delete (0-7)",
        reason="Reason for the ban"
    )
    async def ban_user(self, ctx, member: discord.Member, delete_days: Optional[int] = 1, *, reason: str = "No reason provided"):
        """Permanently ban a member from the server"""
        if delete_days < 0 or delete_days > 7:
            await ctx.send("Message deletion days must be between 0 and 7.")
            return
            
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot ban a member with a role higher than or equal to yours.")
            return
            
        # Log the ban
        await db.execute(
            """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES ($1, $2, $3, $4 || ' (Banned)')
            """,
            str(ctx.guild.id), str(member.id), str(ctx.author.id), reason
        )
        
        try:
            # Try to DM the user before banning
            embed = discord.Embed(
                title=f"You've been banned from {ctx.guild.name}",
                description=f"**Reason:** {reason}",
                color=discord.Color.dark_red()
            )
            try:
                await member.send(embed=embed)
            except:
                pass  # Can't DM them, continue with ban
                
            await member.ban(delete_message_days=delete_days, reason=reason)
            
            # Confirmation message
            confirm_embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned by {ctx.author.mention}",
                color=discord.Color.dark_red()
            )
            confirm_embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to ban member: {e}")
    
    @commands.hybrid_command(name="tempmute")
    @commands.guild_only()
    @app_commands.describe(
        member="The member to mute",
        duration="Duration (e.g. 1h, 30m, 1d)",
        reason="Reason for the mute"
    )
    async def tempmute(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        """Temporarily mute a member"""
        if not await self.has_mod_permissions(ctx):
            await ctx.send("You don't have permission to use this command.")
            return
            
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot mute a member with a role higher than or equal to yours.")
            return
            
        # Get the mute role
        settings = await self.get_guild_settings(ctx.guild.id)
        mute_role_id = settings.get('mute_role_id')
        
        if not mute_role_id:
            await ctx.send("Mute role not configured. Please set one with `/settings mute_role`.")
            return
            
        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            await ctx.send("Mute role not found. It may have been deleted.")
            return
        
        # Parse duration
        duration_seconds = 0
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        try:
            time_str = ''
            for char in duration:
                if char.isdigit() or char == '.':
                    time_str += char
                elif char.lower() in time_units:
                    duration_seconds += float(time_str) * time_units[char.lower()]
                    time_str = ''
                else:
                    raise ValueError
                    
            if time_str:  # If there's leftover numbers with no unit, assume seconds
                duration_seconds += float(time_str)
                
            if duration_seconds <= 0:
                raise ValueError
                
        except ValueError:
            await ctx.send("Invalid duration format. Please use combinations like '30s', '5m', '1h', '1d'.")
            return
        
        # Calculate expiry time
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=duration_seconds)
        
        # Format readable duration
        readable_duration = ""
        days, remainder = divmod(duration_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            readable_duration += f"{int(days)} day{'s' if days != 1 else ''} "
        if hours > 0:
            readable_duration += f"{int(hours)} hour{'s' if hours != 1 else ''} "
        if minutes > 0:
            readable_duration += f"{int(minutes)} minute{'s' if minutes != 1 else ''} "
        if seconds > 0 and days == 0 and hours == 0:  # Only show seconds for short durations
            readable_duration += f"{int(seconds)} second{'s' if seconds != 1 else ''} "
            
        readable_duration = readable_duration.strip()
        
        try:
            # Add mute role
            await member.add_roles(mute_role, reason=f"Muted for {readable_duration}: {reason}")
            
            # Store in database
            await db.execute(
                """
                INSERT INTO timed_punishments 
                (guild_id, user_id, moderator_id, punishment_type, reason, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                str(ctx.guild.id), str(member.id), str(ctx.author.id), 'mute', reason, expires_at
            )
            
            # Also add a warning
            await db.execute(
                """
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES ($1, $2, $3, $4 || ' (Muted for ' || $5 || ')')
                """,
                str(ctx.guild.id), str(member.id), str(ctx.author.id), reason, readable_duration
            )
            
            # Send confirmation
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"{member.mention} has been muted by {ctx.author.mention}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Duration", value=readable_duration, inline=True)
            embed.add_field(name="Expires", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                user_embed = discord.Embed(
                    title=f"You've been muted in {ctx.guild.name}",
                    description=f"**Duration:** {readable_duration}\n**Expires:** <t:{int(expires_at.timestamp())}:R>\n**Reason:** {reason}",
                    color=discord.Color.orange()
                )
                await member.send(embed=user_embed)
            except:
                pass  # Can't DM them
                
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute that member.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to mute member: {e}")
    
    @commands.hybrid_command(name="unmute")
    @commands.guild_only()
    @app_commands.describe(
        member="The member to unmute",
        reason="Reason for unmuting"
    )
    async def unmute(self, ctx, member: discord.Member, *, reason: str = "Mute duration complete"):
        """Unmute a previously muted member"""
        if not await self.has_mod_permissions(ctx):
            await ctx.send("You don't have permission to use this command.")
            return
            
        # Get mute role
        settings = await self.get_guild_settings(ctx.guild.id)
        mute_role_id = settings.get('mute_role_id')
        
        if not mute_role_id:
            await ctx.send("Mute role not configured.")
            return
            
        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            await ctx.send("Mute role not found. It may have been deleted.")
            return
            
        if mute_role not in member.roles:
            await ctx.send(f"{member.display_name} is not muted.")
            return
            
        try:
            # Remove mute role
            await member.remove_roles(mute_role, reason=reason)
            
            # Update database
            await db.execute(
                """
                UPDATE timed_punishments
                SET active = FALSE
                WHERE guild_id = $1 AND user_id = $2 AND punishment_type = 'mute' AND active = TRUE
                """,
                str(ctx.guild.id), str(member.id)
            )
            
            # Send confirmation
            await ctx.send(f"✅ {member.mention} has been unmuted. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute that member.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to unmute member: {e}")
            
    @commands.hybrid_command(name="tempban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member="The member to temporarily ban",
        duration="Duration (e.g. 1h, 30m, 1d)",
        delete_days="Number of days of message history to delete (0-7)",
        reason="Reason for the ban"
    )
    async def tempban(self, ctx, member: discord.Member, duration: str, 
                      delete_days: Optional[int] = 1, *, reason: str = "No reason provided"):
        """Temporarily ban a member from the server"""
        if delete_days < 0 or delete_days > 7:
            await ctx.send("Message deletion days must be between 0 and 7.")
            return
            
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot ban a member with a role higher than or equal to yours.")
            return
            
        # Parse duration similarly to tempmute
        duration_seconds = 0
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        try:
            time_str = ''
            for char in duration:
                if char.isdigit() or char == '.':
                    time_str += char
                elif char.lower() in time_units:
                    duration_seconds += float(time_str) * time_units[char.lower()]
                    time_str = ''
                else:
                    raise ValueError
                    
            if time_str:  # If there's leftover numbers with no unit, assume seconds
                duration_seconds += float(time_str)
                
            if duration_seconds <= 0:
                raise ValueError
                
        except ValueError:
            await ctx.send("Invalid duration format. Please use combinations like '30s', '5m', '1h', '1d'.")
            return
        
        # Calculate expiry time
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=duration_seconds)
        
        # Format readable duration
        readable_duration = ""
        days, remainder = divmod(duration_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            readable_duration += f"{int(days)} day{'s' if days != 1 else ''} "
        if hours > 0:
            readable_duration += f"{int(hours)} hour{'s' if hours != 1 else ''} "
        if minutes > 0:
            readable_duration += f"{int(minutes)} minute{'s' if minutes != 1 else ''} "
        if seconds > 0 and days == 0 and hours == 0:
            readable_duration += f"{int(seconds)} second{'s' if seconds != 1 else ''} "
            
        readable_duration = readable_duration.strip()
        
        try:
            # Try to DM the user before banning
            embed = discord.Embed(
                title=f"You've been temporarily banned from {ctx.guild.name}",
                description=f"**Duration:** {readable_duration}\n**Expires:** <t:{int(expires_at.timestamp())}:R>\n**Reason:** {reason}",
                color=discord.Color.dark_red()
            )
            try:
                await member.send(embed=embed)
            except:
                pass  # Can't DM them, continue with ban
                
            # Ban the member
            await member.ban(delete_message_days=delete_days, reason=f"Temp ban for {readable_duration}: {reason}")
            
            # Store in database
            await db.execute(
                """
                INSERT INTO timed_punishments 
                (guild_id, user_id, moderator_id, punishment_type, reason, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                str(ctx.guild.id), str(member.id), str(ctx.author.id), 'ban', reason, expires_at
            )
            
            # Also add a warning
            await db.execute(
                """
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES ($1, $2, $3, $4 || ' (Banned for ' || $5 || ')')
                """,
                str(ctx.guild.id), str(member.id), str(ctx.author.id), reason, readable_duration
            )
            
            # Send confirmation
            confirm_embed = discord.Embed(
                title="⏱️ Temporary Ban",
                description=f"{member.mention} has been banned by {ctx.author.mention}",
                color=discord.Color.dark_red()
            )
            confirm_embed.add_field(name="Duration", value=readable_duration, inline=True)
            confirm_embed.add_field(name="Expires", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)
            confirm_embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to ban member: {e}")

    @commands.hybrid_command(name="unban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        user_id="The ID of the user to unban",
        reason="Reason for the unban"
    )
    async def unban_user(self, ctx, user_id: str, *, reason: str = "Ban appeal approved"):
        """Unban a user by their ID"""
        try:
            user_id = int(user_id)
        except ValueError:
            await ctx.send("Invalid user ID. Please provide a valid numeric ID.")
            return
            
        try:
            # Fetch ban entry
            bans = [ban_entry for ban_entry in await ctx.guild.bans()]
            user = discord.Object(id=user_id)
            
            # Unban user
            await ctx.guild.unban(user, reason=reason)
            
            # Update database
            await db.execute(
                """
                UPDATE timed_punishments
                SET active = FALSE
                WHERE guild_id = $1 AND user_id = $2 AND punishment_type = 'ban' AND active = TRUE
                """,
                str(ctx.guild.id), str(user_id)
            )
            
            # Send confirmation
            await ctx.send(f"✅ User with ID `{user_id}` has been unbanned. Reason: {reason}")
            
        except discord.NotFound:
            await ctx.send("This user is not banned or the ID is invalid.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban members.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to unban user: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))