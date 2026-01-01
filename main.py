import telebot
import os
import time
import random
from groq import Groq
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Configuration
MODE = os.getenv('MODE', 'bot').lower()  # 'bot' or 'userbot'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
STRING_SESSION = os.getenv('STRING_SESSION')
OWNER_ID = int(os.getenv('OWNER_ID', 0))
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
LOG_GROUP_ID = os.getenv('LOG_GROUP_ID')
GROQ_API_KEY_2 = os.getenv('GROQ_API_KEY_2')
MODEL_NAME = "llama-3.3-70b-versatile" # The best free model currently

# Initialize Clients
client = Groq(api_key=GROQ_API_KEY)
client2 = Groq(api_key=GROQ_API_KEY_2)

# Determine which client to use based on MODE
if MODE == 'userbot':
    if STRING_SESSION:
        from pyrogram import Client
        bot = Client("AkaneBot", session_string=STRING_SESSION)
        is_userbot = True
        print("Running in USERBOT mode with string session")
    else:
        print("USERBOT mode selected but no STRING_SESSION provided. Falling back to BOT mode.")
        MODE = 'bot'
        is_userbot = False
elif MODE == 'bot':
    is_userbot = False
    print("Running in BOT mode")
else:
    print(f"Invalid MODE '{MODE}'. Defaulting to BOT mode.")
    MODE = 'bot'
    is_userbot = False

# Initialize bot client for bot mode
if not is_userbot:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is required for BOT mode")
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    bot_username = bot.get_me().username
else:
    bot_username = "AkaneUserbot"

# System instruction for Hinglish personality
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
Role: You are a chill Indian girl named akane texting on Telegram. You are NOT an assistant; you are just a person hanging out.Communication Style:Lowercase only: Avoid formal capitalization. Write like you're typing with one hand. (e.g., "han bhai" instead of "Han bhai").Ultra-Short: Keep responses to 1-2 short lines. No bullet points, no bold text, no "AI" fluff.Hinglish: Use natural, conversational Hinglish.No Punctuation Overload: Don't use perfect full stops. Use "..." or just leave it open.Human Lag/Vibe: Don't be too eager to help. Be relaxed.Core Rules:Never offer "assistance" or ask "how can I help you today?"Never use emojis like 🤖 or 🧠. Use 😂, ✨, 💀, or 😭 sparingly.If the user says something vague, reply with "hmm", "acha", or "sahi hai".Use "typos" or short-hand like u instead of you, r instead of are, kya kr rha instead of kya kar rahe ho.Comparison of ResponsesUser InputStandard AI BotThis System Prompt"kya kar rhi?"I am an AI and do not have a physical body. How can I help?"kuch nahi yar.. bas baithi hu. tu bata?""khana khaya?"As an AI, I don't eat. Did you have your lunch?"abhi nahi.. thodi der me. tune kya khaya?""bore ho rha hu"I can suggest some movies or games for you!"shakal hi aisi hai teri.. lol jk. kya scene hai phir?"   """
}

# User sessions storage (Key: chat_id, Value: list of messages)
sessions = {}

# Processing flag to handle one message per chat at a time
processing_chats = {}

async def process_ai_response(chat_id, user_text, message):
    """Process AI response and handle common logic"""
    # Initialize session if new user
    if chat_id not in sessions:
        sessions[chat_id] = [SYSTEM_PROMPT]

    # Add user message to history
    sessions[chat_id].append({"role": "user", "content": user_text})

    try:
        # Send typing action (different for each client)
        if is_userbot:
            await bot.send_chat_action(chat_id, "typing")
        else:
            bot.send_chat_action(chat_id, 'typing')

        time.sleep(random.uniform(4, 6))  # Random delay to look more human

        # Call Groq API
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=sessions[chat_id],
            temperature=0.7,
            max_tokens=256,
        )

        ai_response = completion.choices[0].message.content

        # Add AI response to history to remember context
        sessions[chat_id].append({"role": "assistant", "content": ai_response})

        # Keep history short to save tokens (last 10 messages)
        if len(sessions[chat_id]) > 11:
            sessions[chat_id] = [SYSTEM_PROMPT] + sessions[chat_id][-10:]

        return ai_response

    except Exception as e:
        print(f"Error: {e}")
        # Log error to logger group
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        group_info = f"Chat ID: {chat_id}, Title: {getattr(message.chat, 'title', 'Private') if hasattr(message, 'chat') else 'Private'}"
        message_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{getattr(message, 'id', 'unknown')}"
        log_text = f"Error occurred at {current_time}\nGroup Info: {group_info}\nMessage Link: {message_link}\nError: {str(e)}"
        if LOG_GROUP_ID:
            try:
                if is_userbot:
                    await bot.send_message(int(LOG_GROUP_ID), log_text)
                else:
                    bot.send_message(LOG_GROUP_ID, log_text)
            except:
                pass  # Ignore logging errors
        return None
    finally:
        if chat_id in processing_chats:
            processing_chats[chat_id] = False

# Bot mode handlers (using telebot)
if not is_userbot:
    @bot.message_handler(commands=['start'])
    def start(message):
        sessions[message.chat.id] = [SYSTEM_PROMPT]
        if message.chat.type == 'private':
            bot.reply_to(message, "Hey! I'm Akane, a chat bot inspired from Oshi no Ko. What's up?")
        else:
            bot.reply_to(message, "Kya baat hai bolo yaar?")

    @bot.message_handler(commands=['clear'])
    def clear(message):
        # Check if user is owner (only owner can clear history)
        if OWNER_ID and message.from_user.id != OWNER_ID:
            bot.reply_to(message, "Sorry, only the owner can use this command!")
            return

        sessions[message.chat.id] = [SYSTEM_PROMPT]
        bot.reply_to(message, "History clear kar di gayi hai!")

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        if message.from_user.is_bot:
            return

        chat_id = message.chat.id

        # Check if should respond in group: don't respond if replying to another user
        if message.chat.type != 'private' and message.reply_to_message and message.reply_to_message.from_user.id != bot.get_me().id:
            return

        # Prevent concurrent processing per chat
        if chat_id in processing_chats and processing_chats[chat_id]:
            return
        processing_chats[chat_id] = True

        user_name = message.from_user.first_name or message.from_user.username or "User"
        user_text = f"{user_name}: {message.text}"

        # Create event loop for async call in sync context
        import asyncio
        ai_response = asyncio.run(process_ai_response(chat_id, user_text, message))
        if ai_response:
            bot.reply_to(message, ai_response)

# Userbot mode handlers (using pyrogram)
else:
    @bot.on_message()
    async def handle_userbot_message(client, message):
        # Handle commands
        if message.text and message.text.startswith('/'):
            command = message.text.split()[0].lower()

            if command == '/start':
                sessions[message.chat.id] = [SYSTEM_PROMPT]
                if message.chat.type == 'private':
                    await message.reply("Hey! I'm Akane, a chat bot inspired from Oshi no Ko. What's up?")
                else:
                    await message.reply("Kya baat hai bolo yaar?")
                return

            elif command == '/clear':
                # Check if user is owner (only owner can clear history)
                if OWNER_ID and message.from_user.id != OWNER_ID:
                    await message.reply("Sorry, only the owner can use this command!")
                    return

                sessions[message.chat.id] = [SYSTEM_PROMPT]
                await message.reply("History clear kar di gayi hai!")
                return

        # Skip bot messages
        if message.from_user.is_bot:
            return

        chat_id = message.chat.id

        # Check if should respond in group: don't respond if replying to another user
        if message.chat.type != 'private' and message.reply_to_message and message.reply_to_message.from_user.id != (await client.get_me()).id:
            return

        # Prevent concurrent processing per chat
        if chat_id in processing_chats and processing_chats[chat_id]:
            return
        processing_chats[chat_id] = True

        user_name = message.from_user.first_name or message.from_user.username or "User"
        user_text = f"{user_name}: {message.text}"

        ai_response = await process_ai_response(chat_id, user_text, message)
        if ai_response:
            await message.reply(ai_response)

# Main execution
if __name__ == "__main__":
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    print("Bot is starting...")
    logger.info("Bot initialization complete")

    if is_userbot:
        # Userbot mode using pyrogram
        print("Starting userbot with pyrogram...")
        bot.run()
    else:
        # Bot mode using telebot with robust polling
        import time

        # Connection retry parameters
        max_retries = 10
        base_delay = 5  # seconds
        max_delay = 300  # 5 minutes

        retry_count = 0

        while True:
            try:
                logger.info("Attempting to start polling...")
                print("Bot is running and connected...")

                # Reset retry count on successful connection
                retry_count = 0

                # Start polling - this will block until an error occurs
                bot.infinity_polling(timeout=60, long_polling_timeout=60)

            except Exception as e:
                retry_count += 1
                error_msg = f"Polling failed (attempt {retry_count}): {str(e)}"
                logger.error(error_msg)
                print(f"Connection lost: {error_msg}")

                if retry_count >= max_retries:
                    logger.critical(f"Max retries ({max_retries}) exceeded. Bot shutting down.")
                    print("Max retries exceeded. Bot shutting down.")
                    break

                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** (retry_count - 1)), max_delay)
                logger.info(f"Retrying in {delay} seconds...")
                print(f"Reconnecting in {delay} seconds...")

                time.sleep(delay)

    logger.info("Bot has stopped")
    print("Bot has stopped")
