# pickle_# Pickle Jar Bot

A Discord bot that rewards users for mentioning pickle-related words, with moderation, community recognition, and custom command features.

## Features

- **Pickle Tracking:** Reward users when they mention pickle-related words
- **Community Recognition:** Allow users to recognize others' contributions
- **Moderation Tools:** Comprehensive warning system, temp mutes, temp bans
- **Custom Commands:** Create server-specific commands with variables
- **Media Search:** (Optional) Search for GIFs, videos, and memes
- **Admin Tools:** Server management, role setup, welcome messages, and more

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- A Discord Bot Token (from the [Discord Developer Portal](https://discord.com/developers/applications))
- PostgreSQL database (optional, but recommended for production)

### Installation

1. **Clone the repository**
   ```
   git clone https://github.com/yourusername/pickle_jar_bot.git
   cd pickle_jar_bot
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Create a `.env` file in the root directory based on the `.env.example` template
   - Add your Discord Bot Token and Database URL

4. **Initialize the database**
   - The bot will automatically create required tables on first run
   - For PostgreSQL, make sure your database is created before running the bot

5. **Run the bot**
   ```
   python main.py
   ```

### Environment Variables

Create a `.env` file with the following:

```
DISCORD_PICKLE_BOT_TOKEN=your_discord_bot_token_here
DATABASE_URL=postgresql://username:password@localhost:5432/pickle_bot
```

### Configuration

The `config.json` file contains settings for your bot:

- Bot prefix and description
- Pickle trigger words and cooldowns
- Moderation settings
- Feature toggles

## Commands

### Pickle System
- `/pickles [user]` - Check pickle count
- `/pickleboard` - Display pickle leaderboard
- `/pickle_words` - List trigger words
- `/add_pickle_word` - Add a new trigger word (Admin only)
- `/remove_pickle_word` - Remove a trigger word (Admin only)

### Moderation
- `/warn <user> [reason]` - Warn a user
- `/warnings <user>` - Check a user's warnings
- `/clearwarn <warning_id>` - Clear a specific warning
- `/kick <user> [reason]` - Kick a user
- `/ban <user> [reason]` - Ban a user permanently
- `/tempban <user> <duration> [reason]` - Ban a user temporarily
- `/unban <user_id> [reason]` - Unban a user
- `/tempmute <user> <duration> [reason]` - Temporarily mute a user
- `/unmute <user> [reason]` - Unmute a user

### Recognition
- `/recognize <user> [reason]` - Recognize a user's contributions
- `/recognitions [user]` - Check recognitions for a user
- `/leaderboard` - View the recognition leaderboard
- `/thankers` - See who has given the most recognitions

### Custom Commands
- `/custom add <command> <response>` - Add a custom command
- `/custom remove <command>` - Remove a custom command
- `/custom list` - List all custom commands
- `/custom info <command>` - View details about a command

### Server Settings
- `/settings` - View current server settings
- `/settings prefix <prefix>` - Set custom command prefix
- `/settings mod_role <role>` - Set moderator role
- `/settings admin_role <role>` - Set admin role
- `/settings welcome_channel <channel>` - Set welcome channel
- `/settings welcome_message <message>` - Set welcome message
- `/settings log_channel <channel>` - Set logging channel
- `/settings mute_role <role>` - Set mute role
- `/settings auto_role <role>` - Set auto-role for new members

## Troubleshooting

### Database Connection Issues

If you're having trouble connecting to PostgreSQL:

1. Make sure PostgreSQL is installed and running
2. Verify your DATABASE_URL is correct
3. Try using SQLite instead for testing:
   ```
   DATABASE_URL=sqlite:///database.sqlite
   ```

### Bot Token Issues

If your bot won't connect:

1. Ensure your token is correct in the `.env` file
2. Check that you've enabled the required Privileged Gateway Intents in the Discord Developer Portal
3. Make sure the bot has been invited to your server with the correct permissions

## License

This project is licensed under the MIT License - see the LICENSE file for details.jar_bot