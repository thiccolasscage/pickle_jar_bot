# 🚀 PickleJar Bot Pre-Deployment Checklist

Use this checklist to ensure your bot is ready for deployment:

## 🔑 Environment Variables
- [ ] Set `DISCORD_BOT_TOKEN` in `.env` file with your actual bot token
- [ ] Set `DATABASE_URL` in `.env` file with your PostgreSQL connection string
- [ ] If deploying to Railway, add these as environment variables in the Railway dashboard

## 🗄️ Database
- [ ] Ensure PostgreSQL is set up (local or Railway)
- [ ] Verify that `postgresql_schema_optimized.sql` is in the project root

## 📁 Project Structure
- [ ] Confirm all needed files are present:
  - [ ] `main.py`
  - [ ] `/cogs` directory with all cog files
  - [ ] `/utils` directory with utility files
  - [ ] `requirements.txt`
  - [ ] `railway.json` (if deploying to Railway)
- [ ] Remove any redundant or old files:
  - [ ] Any duplicate `main.py` files
  - [ ] Old bot files in `/bots` directory that have been moved to `/cogs`

## ✅ Configuration
- [ ] Update `config.json` with your preferred settings:
  - [ ] Pickle reward words and messages
  - [ ] Moderation settings and thresholds
- [ ] Check that command prefix is set as desired in `main.py`

## 🔒 Permissions
- [ ] Ensure your bot application has the necessary intents enabled in the Discord Developer Portal:
  - [ ] SERVER MEMBERS INTENT
  - [ ] MESSAGE CONTENT INTENT
  - [ ] PRESENCE INTENT
- [ ] Generate an invite link with proper permissions:
  - Administrator (for full functionality)
  - Or specific permissions:
    - Manage Roles
    - Manage Channels
    - Kick Members
    - Ban Members
    - Manage Messages
    - Read Messages/View Channels
    - Send Messages
    - Add Reactions

## 🧪 Testing
- [ ] Test the bot locally before deployment:
  - [ ] Run `python main.py` and ensure it starts without errors
  - [ ] Check that it connects to the database successfully
  - [ ] Test basic commands like `!ping`

## 📝 Documentation
- [ ] Update README.md with any custom configurations
- [ ] Add any additional commands or features to the documentation

## 🚢 Deployment (Railway)
- [ ] Initialize Git repository (if not already done):
  ```bash
  git init
  git add .
  git commit -m "Initial commit ready for deployment"
  ```
- [ ] Link to your GitHub repository:
  ```bash
  git remote add origin https://github.com/yourusername/pickle_jar_bot.git
  git push -u origin master
  ```
- [ ] Connect repository to Railway
- [ ] Add PostgreSQL plugin
- [ ] Set environment variables
- [ ] Deploy application

---

## 📋 Last Minute Checks
- [ ] Bot token is not hardcoded anywhere in the files
- [ ] All print statements are replaced with proper logging
- [ ] No debugging code left in production files
- [ ] Database schema matches the queries in your code
- [ ] All cogs listed in `main.py` exist and load properly
