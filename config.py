import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Chat ID where feedback messages are forwarded. Can be your personal
# Telegram user ID (get it from @userinfobot) or a group chat ID
# (starts with -100...). The bot must be a member of the chat if it's a group.
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

DB_PATH = os.getenv("DB_PATH", "data/feedback.db")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set — add it to your .env file")

if not ADMIN_CHAT_ID:
    raise RuntimeError("ADMIN_CHAT_ID is not set — add it to your .env file")
