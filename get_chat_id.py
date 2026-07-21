"""
One-time helper: run this after messaging your bot on Telegram at least once,
and it will print the chat_id you need to put in .env as TELEGRAM_CHAT_ID.

Usage:
    1. Create a bot via @BotFather, get the token.
    2. Put the token in .env as TELEGRAM_BOT_TOKEN.
    3. Open a DM with your bot and send it any message (e.g. "hi").
    4. Run: python get_chat_id.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not token or token.startswith("your_"):
    print("Set TELEGRAM_BOT_TOKEN in your .env file first.")
    raise SystemExit(1)

resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=15)
resp.raise_for_status()
data = resp.json()

if not data.get("result"):
    print("No messages found yet. Send your bot a message on Telegram, then rerun this.")
    raise SystemExit(0)

seen = set()
for update in data["result"]:
    msg = update.get("message") or update.get("channel_post")
    if not msg:
        continue
    chat = msg["chat"]
    key = (chat["id"], chat.get("type"), chat.get("title") or chat.get("username") or chat.get("first_name"))
    if key in seen:
        continue
    seen.add(key)
    print(f"chat_id: {chat['id']}   type: {chat.get('type')}   name: {key[2]}")
