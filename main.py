import telebot
import os
import time
import random
from groq import Groq, RateLimitError
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LOG_GROUP_ID = os.getenv('LOG_GROUP_ID')
MODEL_NAME = "llama-3.3-70b-versatile"  # The best free model currently

# Load Groq API keys
groq_keys = []
for i in range(1, 8):
    key = os.getenv(f'GROQ_API_KEY_{i}')
    if key:
        groq_keys.append(key)

if not groq_keys:
    raise ValueError("At least one GROQ_API_KEY_1 is required")

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

# Initialize Groq clients
clients = [Groq(api_key=key) for key in groq_keys]

# Initialize Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
bot_username = bot.get_me().username

print(f"Bot initialized successfully with {len(clients)} Groq API keys")

# Load system prompt from file
try:
    with open('system_prompt.txt', 'r', encoding='utf-8') as f:
        system_content = f.read().strip()
    SYSTEM_PROMPT = {
        "role": "system",
        "content": system_content
    }
except FileNotFoundError:
    print("Error: system_prompt.txt not found")
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
        bot.send_chat_action(chat_id, 'typing')
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
                bot.send_message(LOG_GROUP_ID, log_text)
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
                bot.send_message(LOG_GROUP_ID, log_text)
            except:
                pass  # Ignore logging errors
        return None
    finally:
        if chat_id in processing_chats:
            processing_chats[chat_id] = False

@bot.message_handler(commands=['start'])
def start(message):
    sessions[message.chat.id] = [SYSTEM_PROMPT]
    if message.chat.type == 'private':
        bot.reply_to(message, "Hey! I'm Akane, a chat bot inspired from Oshi no Ko. What's up?")
    else:
        bot.reply_to(message, "Kya baat hai bolo yaar?")

@bot.message_handler(commands=['clear'])
def clear(message):
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

    ai_response = process_ai_response(chat_id, user_text, message)
    if ai_response:
        bot.reply_to(message, ai_response)

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
