import asyncio
import os
import time
import random
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from groq import Groq, RateLimitError
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Configuration
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
STRING_SESSION = os.getenv('PYROGRAM_STRING_SESSION')
LOG_GROUP_ID = os.getenv('LOG_GROUP_ID')
MODEL_NAME = "llama-3.3-70b-versatile"

# Load Groq API keys
groq_keys = []
for i in range(1, 8):
    key = os.getenv(f'GROQ_API_KEY_{i}')
    if key:
        groq_keys.append(key)

if not groq_keys:
    raise ValueError("At least one GROQ_API_KEY_1 is required")

# Validate required environment variables
if not all([API_ID, API_HASH]):
    raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH are required")

# Initialize Groq clients
clients = [Groq(api_key=key) for key in groq_keys]

# Initialize Userbot
app = Client("akane_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# Load system prompt from file
try:
    with open('../system_prompt.txt', 'r', encoding='utf-8') as f:
        system_content = f.read().strip()
    SYSTEM_PROMPT = {
        "role": "system",
        "content": system_content
    }
except FileNotFoundError:
    print("Error: system_prompt.txt not found in parent directory")
    SYSTEM_PROMPT = {
        "role": "system",
        "content": "You are a helpful assistant."
    }

# User sessions storage (Key: chat_id, Value: list of messages)
sessions = {}

# Processing flag to handle one message per chat at a time
processing_chats = {}

def process_ai_response(chat_id, user_text, message):
    """Process AI response and handle common logic"""
    # Initialize session if new user
    if chat_id not in sessions:
        sessions[chat_id] = [SYSTEM_PROMPT]

    # Add user message to history
    sessions[chat_id].append({"role": "user", "content": user_text})

    try:
        # Send typing action
        asyncio.create_task(send_typing_action(message))
        time.sleep(random.uniform(4, 5))  # Random delay to look more human

        # Try each client until success
        for i, client in enumerate(clients):
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=sessions[chat_id],
                    temperature=0.7,
                    max_tokens=256,
                )
                print(f"Used API key {i+1}")
                break  # Success, exit loop
            except RateLimitError:
                print(f"API key {i+1} rate limited, trying next...")
                if i == len(clients) - 1:
                    raise  # All keys rate limited
                continue

        ai_response = completion.choices[0].message.content

        # Add AI response to history to remember context
        sessions[chat_id].append({"role": "assistant", "content": ai_response})

        # Keep history short to save tokens (last 10 messages)
        if len(sessions[chat_id]) > 11:
            sessions[chat_id] = [SYSTEM_PROMPT] + sessions[chat_id][-10:]

        return ai_response

    except RateLimitError as e:
        print(f"All API keys rate limited: {e}")
        # Log rate limit error to logger group
        if LOG_GROUP_ID:
            try:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                chat_title = message.chat.title if hasattr(message.chat, 'title') and message.chat.title else "Private"
                group_info = f"Chat ID: {chat_id}, Title: {chat_title}"
                message_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{message.message_id}"
                log_text = f"All Groq API keys rate limited at {current_time}\nGroup Info: {group_info}\nMessage Link: {message_link}\nError: {str(e)}"
                asyncio.create_task(app.send_message(LOG_GROUP_ID, log_text))
            except:
                pass  # Ignore logging errors
        return None
    except Exception as e:
        print(f"Error: {e}")
        # Log error to logger group
        if LOG_GROUP_ID:
            try:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                chat_title = message.chat.title if hasattr(message.chat, 'title') and message.chat.title else "Private"
                group_info = f"Chat ID: {chat_id}, Title: {chat_title}"
                message_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{message.message_id}"
                log_text = f"Error occurred at {current_time}\nGroup Info: {group_info}\nMessage Link: {message_link}\nError: {str(e)}"
                asyncio.create_task(app.send_message(LOG_GROUP_ID, log_text))
            except:
                pass  # Ignore logging errors
        return None
    finally:
        if chat_id in processing_chats:
            processing_chats[chat_id] = False

async def send_typing_action(message):
    """Send typing action for more human-like interaction"""
    try:
        await app.send_chat_action(message.chat.id, "typing")
    except:
        pass

@app.on_message(filters.command("start") & filters.private)
async def start_private(client, message):
    sessions[message.chat.id] = [SYSTEM_PROMPT]
    await message.reply("Hey! I'm Akane, your friendly chatbot! What's up? 😊")

@app.on_message(filters.command("start") & ~filters.private)
async def start_group(client, message):
    sessions[message.chat.id] = [SYSTEM_PROMPT]
    await message.reply("Kya baat hai bolo yaar? 👋")

@app.on_message(filters.command("clear"))
async def clear(client, message):
    sessions[message.chat.id] = [SYSTEM_PROMPT]
    await message.reply("History clear kar di gayi hai! 🧹")

@app.on_message(filters.text & ~filters.bot & ~filters.command(["start", "clear"]))
async def handle_message(client, message):
    chat_id = message.chat.id

    # Check if bot is mentioned in groups (for userbot, respond to all messages)
    # Userbots can respond anywhere, but let's be respectful and only respond when mentioned or in private
    if not message.chat.type == "private" and not app.me.mention in message.text and message.reply_to_message_id:
        # Only respond if replying to bot's message
        if message.reply_to_message and message.reply_to_message.from_user.id != app.me.id:
            return

    # Prevent concurrent processing per chat
    if chat_id in processing_chats and processing_chats[chat_id]:
        return
    processing_chats[chat_id] = True

    user_name = message.from_user.first_name or message.from_user.username or "User"
    user_text = f"{user_name}: {message.text}"

    ai_response = process_ai_response(chat_id, user_text, message)
    if ai_response:
        try:
            await message.reply(ai_response)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply(ai_response)

if __name__ == "__main__":
    print("🤖 Akane Userbot is starting...")
    print("Make sure you have set up your .env file with API credentials!")

    app.run()
