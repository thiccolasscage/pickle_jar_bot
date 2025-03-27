import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
token = os.getenv("DISCORD_PICKLE_BOT_TOKEN")

print("DATABASE_URL:", db_url)
print("TOKEN:", token)