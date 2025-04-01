import discord
from discord.ext import commands
from utils.db_manager import db
from utils.logger import logger

class CustomCommands(commands.Cog):
    """Allows users to create and use custom commands"""

    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = {}
        # Instead of creating a task here, add a listener for on_ready
        self.bot.add_listener(self.on_ready_load_commands, "on_ready")

    async def on_ready_load_commands(self):
        """Load commands when the bot is ready"""
        await self.load_commands()

    async def load_commands(self):
        """Load custom commands from the database"""
        try:
            # Create the table if it doesn't exist
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS custom_commands (
                    guild_id VARCHAR(32),
                    command_name TEXT,
                    command_response TEXT,
                    created_by VARCHAR(32),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, command_name)
                )
                """
            )
            
            # Load all commands
            results = await db.fetch("SELECT guild_id, command_name, command_response FROM custom_commands")
            
            for record in results:
                guild_id = record['guild_id']
                command_name = record['command_name']
                command_response = record['command_response']
                
                if guild_id not in self.custom_commands:
                    self.custom_commands[guild_id] = {}
                    
                self.custom_commands[guild_id][command_name] = command_response
                
            logger.log(f"Loaded {len(results)} custom commands")
        except Exception as e:
            logger.log(f"Error loading custom commands: {str(e)}", "error")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for custom command invocations"""
        if message.author.bot:
            return
            
        # Only process in guilds
        if not message.guild:
            return
            
        # Check if message starts with ! (command prefix)
        if not message.content.startswith('!'):
            return
            
        guild_id = str(message.guild.id)
        
        # Extract command name (remove prefix and get first word)
        command_parts = message.content[1:].split()
        if not command_parts:
            return
            
        command_name = command_parts[0].lower()
        
        # Check if this is a custom command for this guild
        if (guild_id in self.custom_commands and 
            command_name in self.custom_commands[guild_id]):
            
            response = self.custom_commands[guild_id][command_name]
            await message.channel.send(response)
            logger.log(f"Custom command '{command_name}' used by {message.author}")

    @commands.command(name="addcmd")
    @commands.has_permissions(manage_messages=True)
    async def add_command(self, ctx, command_name: str, *, response: str):
        """Add a custom command"""
        # Validate command name
        if command_name in [c.name for c in self.bot.commands]:
            await ctx.send(f"'{command_name}' is already a built-in command!")
            return
            
        # Remove ! prefix if user included it
        if command_name.startswith('!'):
            command_name = command_name[1:]
            
        command_name = command_name.lower()
        guild_id = str(ctx.guild.id)
        
        try:
            # Store in database
            await db.execute(
                """
                INSERT INTO custom_commands(guild_id, command_name, command_response, created_by)
                VALUES($1, $2, $3, $4)
                ON CONFLICT (guild_id, command_name)
                DO UPDATE SET command_response = $3, created_by = $4
                """,
                guild_id, command_name, response, str(ctx.author.id)
            )
            
            # Update local cache
            if guild_id not in self.custom_commands:
                self.custom_commands[guild_id] = {}
                
            self.custom_commands[guild_id][command_name] = response
            
            await ctx.send(f"Custom command `!{command_name}` has been added!")
            logger.log(f"{ctx.author} added custom command '{command_name}'")
        except Exception as e:
            logger.log(f"Error adding custom command: {str(e)}", "error")
            await ctx.send("Failed to add the custom command.")

    @commands.command(name="delcmd")
    @commands.has_permissions(manage_messages=True)
    async def delete_command(self, ctx, command_name: str):
        """Delete a custom command"""
        # Remove ! prefix if user included it
        if command_name.startswith('!'):
            command_name = command_name[1:]
            
        command_name = command_name.lower()
        guild_id = str(ctx.guild.id)
        
        # Check if command exists
        if (guild_id not in self.custom_commands or 
            command_name not in self.custom_commands[guild_id]):
            await ctx.send(f"Custom command `!{command_name}` doesn't exist!")
            return
            
        try:
            # Remove from database
            await db.execute(
                "DELETE FROM custom_commands WHERE guild_id = $1 AND command_name = $2",
                guild_id, command_name
            )
            
            # Remove from local cache
            del self.custom_commands[guild_id][command_name]
            
            await ctx.send(f"Custom command `!{command_name}` has been deleted!")
            logger.log(f"{ctx.author} deleted custom command '{command_name}'")
        except Exception as e:
            logger.log(f"Error deleting custom command: {str(e)}", "error")
            await ctx.send("Failed to delete the custom command.")

    @commands.command(name="listcmds")
    async def list_commands(self, ctx):
        """List all custom commands in this server"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.custom_commands or not self.custom_commands[guild_id]:
            await ctx.send("This server doesn't have any custom commands yet!")
            return
            
        commands_list = sorted(self.custom_commands[guild_id].keys())
        
        # Create embed with command list
        embed = discord.Embed(
            title=f"Custom Commands in {ctx.guild.name}",
            description="Use these commands with the `!` prefix",
            color=discord.Color.blue()
        )
        
        # Split into chunks if too many commands
        chunks = [commands_list[i:i+15] for i in range(0, len(commands_list), 15)]
        
        for i, chunk in enumerate(chunks):
            commands_text = "\n".join([f"`!{cmd}`" for cmd in chunk])
            embed.add_field(
                name=f"Commands {i*15+1}-{i*15+len(chunk)}" if len(chunks) > 1 else "Commands",
                value=commands_text,
                inline=False
            )
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))