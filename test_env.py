from dotenv import load_dotenv
import os

load_dotenv()

print("✅ DATABASE_URL =", os.getenv("DATABASE_URL"))
print("✅ PICKLE TOKEN =", os.getenv("DISCORD_PICKLE_BOT_TOKEN"))
print("✅ MEDIA TOKEN  =", os.getenv("DISCORD_MEDIA_BOT_TOKEN"))