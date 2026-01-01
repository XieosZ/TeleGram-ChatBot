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

# Initialize Groq clients
client = Groq(api_key=GROQ_API_KEY)
client2 = Groq(api_key=GROQ_API_KEY_2)

# Determine which client to use based on MODE
if MODE == 'userbot':
    if STRING_SESSION:
        # Userbot mode with string session
        from pyrogram import Client, filters
        from pyrogram.enums import ChatAction
        bot = Client("akane_userbot", session_string=STRING_SESSION)
        IS_USERBOT = True
        print("Running in USERBOT mode with string session")
    elif TELEGRAM_BOT_TOKEN:
        # Fallback to bot mode if no string session
        import telebot
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        IS_USERBOT = False
        print("String session not found, falling back to BOT mode")
    else:
        raise ValueError("MODE=userbot requires either STRING_SESSION or TELEGRAM_BOT_TOKEN")
elif MODE == 'bot':
    if TELEGRAM_BOT_TOKEN:
        # Bot mode
        import telebot
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        IS_USERBOT = False
        print("Running in BOT mode")
    else:
        raise ValueError("MODE=bot requires TELEGRAM_BOT_TOKEN")
else:
    raise ValueError("MODE must be either 'bot' or 'userbot'")

# Get bot username for bot mode
bot_username = None
if not IS_USERBOT:
    bot_username = bot.get_me().username

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

def handle_start(message):
    """Handle /start command"""
    chat_id = message.chat.id
    sessions[chat_id] = [SYSTEM_PROMPT]

    if IS_USERBOT:
        # Pyrogram message object
        is_private = message.chat.type == "private"
        response_text = "Hey! I'm Akane, a chat bot inspired from Oshi no Ko. What's up?" if is_private else "Kya baat hai bolo yaar?"
        bot.send_message(chat_id, response_text)
    else:
        # Telebot message object
        if message.chat.type == 'private':
            bot.reply_to(message, "Hey! I'm Akane, a chat bot inspired from Oshi no Ko. What's up?")
        else:
            bot.reply_to(message, "Kya baat hai bolo yaar?")

def handle_clear(message):
    """Handle /clear command - owner only"""
    user_id = message.from_user.id

    if OWNER_ID and user_id != OWNER_ID:
        response_text = "Sorry, only the owner can use this command."
        if IS_USERBOT:
            bot.send_message(message.chat.id, response_text)
        else:
            bot.reply_to(message, response_text)
        return

    chat_id = message.chat.id
    sessions[chat_id] = [SYSTEM_PROMPT]

    if IS_USERBOT:
        bot.send_message(chat_id, "History clear kar di gayi hai!")
    else:
        bot.reply_to(message, "History clear kar di gayi hai!")

def handle_message(message):
    """Handle regular messages"""
    if IS_USERBOT:
        # Pyrogram message object
        if message.from_user.is_bot:
            return

        chat_id = message.chat.id
        user = message.from_user

        # Check if should respond in group: don't respond if replying to another user
        if message.chat.type != "private" and message.reply_to_message and message.reply_to_message.from_user.id != bot.me.id:
            return
    else:
        # Telebot message object
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

    # Initialize session if new user
    if chat_id not in sessions:
        sessions[chat_id] = [SYSTEM_PROMPT]

    # Add user message to history
    sessions[chat_id].append({"role": "user", "content": user_text})

    try:
        # Send typing action
        if IS_USERBOT:
            bot.send_chat_action(chat_id, ChatAction.TYPING)
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

        # Send response
        if IS_USERBOT:
            bot.send_message(chat_id, ai_response)
        else:
            bot.reply_to(message, ai_response)

    except Exception as e:
        print(f"Error: {e}")
        # Log error to logger group
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if IS_USERBOT:
            group_info = f"Chat ID: {chat_id}, Title: {message.chat.title or 'Private'}"
            message_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{message.id}"
        else:
            group_info = f"Chat ID: {chat_id}, Title: {message.chat.title if hasattr(message.chat, 'title') and message.chat.title else 'Private'}"
            message_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{message.message_id}"
        log_text = f"Error occurred at {current_time}\nGroup Info: {group_info}\nMessage Link: {message_link}\nError: {str(e)}"
        if IS_USERBOT:
            bot.send_message(LOG_GROUP_ID, log_text)
        else:
            bot.send_message(LOG_GROUP_ID, log_text)
    finally:
        processing_chats[chat_id] = False

# Register handlers based on mode
if IS_USERBOT:
    # Pyrogram handlers
    @bot.on_message(filters.command("start"))
    async def pyrogram_start(client, message):
        handle_start(message)

    @bot.on_message(filters.command("clear"))
    async def pyrogram_clear(client, message):
        handle_clear(message)

    @bot.on_message(filters.text & ~filters.command(["start", "clear"]))
    async def pyrogram_message(client, message):
        handle_message(message)
else:
    # Telebot handlers
    @bot.message_handler(commands=['start'])
    def telebot_start(message):
        handle_start(message)

    @bot.message_handler(commands=['clear'])
    def telebot_clear(message):
        handle_clear(message)

    @bot.message_handler(func=lambda message: True)
    def telebot_message(message):
        handle_message(message)

# Start the bot based on mode
if __name__ == "__main__":
    import time
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    print("Bot is starting...")
    logger.info("Bot initialization complete")

    if IS_USERBOT:
        # Pyrogram userbot mode - uses asyncio
        import asyncio

        async def run_userbot():
            await bot.start()
            print("Userbot is running and connected...")
            logger.info("Userbot connected successfully")

            # Keep the bot running
            await bot.idle()

        # Run the userbot
        asyncio.run(run_userbot())

    else:
        # Telebot polling mode with network robustness
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
