# Telegram ChatBot - Akane

A conversational AI Telegram bot named Akane (inspired by Oshi no Ko anime) that responds in Hinglish (mix of Hindi and English) and remembers chat history per user.

## Features

- **Hinglish Responses**: Casual mix of Hindi and English for relatable conversations
- **Session Memory**: Remembers conversation history for each user individually
- **Short & Casual**: Responses are kept concise and friendly
- **Commands**:
  - `/start`: Initialize and greet
  - `/clear`: Reset conversation history
- **Robust Polling**: Handles network issues with timeouts

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - Copy `sample.env` to `.env`
   - Fill in your actual API keys and tokens in the `.env` file:
     - `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather) on Telegram
     - `GROQ_API_KEY` & `GROQ_API_KEY_2`: Get from [Groq Console](https://console.groq.com/)
     - `LOG_GROUP_ID`: Create a private Telegram group, add your bot, and get the group ID
4. Run the bot: `python main.py` or double-click `start_bot.bat`

## APIs Used

- **Telegram Bot API**: For bot interactions
- **Groq API**: For AI responses using llama-3.3-70b-versatile model

## Notes

- Free Groq tier has higher limits than Gemini free tier
- Bot uses session management to isolate user conversations
- Downgraded httpx to 0.27.2 for compatibility

## License

MIT
