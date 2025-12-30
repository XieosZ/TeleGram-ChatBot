import telebot
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MODEL_NAME = "llama-3.3-70b-versatile" # The best free model currently

# Initialize Clients
client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# System instruction for Hinglish personality
SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are Akane, a helpful Indian AI assistant from the anime Oshi no Ko. Always respond in Hinglish - mix Hindi and English casually. Keep responses very short and casual, like: 'Theek hai bhai!' or 'Kya baat hai?'. Be super casual and friendly."
}

# User sessions storage (Key: chat_id, Value: list of messages)
sessions = {}

@bot.message_handler(commands=['start'])
def start(message):
    sessions[message.chat.id] = [SYSTEM_PROMPT]
    bot.reply_to(message, "Namaste! Main Akane hoon, aapka AI assistant from Oshi no Ko. Kaise madad kar sakti hoon?")

@bot.message_handler(commands=['clear'])
def clear(message):
    sessions[message.chat.id] = [SYSTEM_PROMPT]
    bot.reply_to(message, "History clear kar di gayi hai!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.is_bot: return

    chat_id = message.chat.id
    user_text = message.text

    # Initialize session if new user
    if chat_id not in sessions:
        sessions[chat_id] = [SYSTEM_PROMPT]

    # Add user message to history
    sessions[chat_id].append({"role": "user", "content": user_text})

    try:
        bot.send_chat_action(chat_id, 'typing')

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

        bot.reply_to(message, ai_response)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Thoda issue ho gaya hai, please thodi der baad try karein.")

# Use robust polling to prevent the 'Read Timeout' errors you had before
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
