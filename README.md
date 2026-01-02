# Telegram ChatBot - Akane

A conversational AI Telegram bot named Akane (inspired by Oshi no Ko anime) that responds in Hinglish (mix of Hindi and English) and remembers chat history per user.

## Features

- **Hinglish Responses**: Casual mix of Hindi and English for relatable conversations
- **Session Memory**: Remembers conversation history for each user individually (keeps last 10 messages to save tokens)
- **Short & Casual**: Responses are kept concise and friendly, mimicking human texting style
- **Rate Limit Handling**: Cycles through multiple Groq API keys to handle rate limits automatically
- **Error Logging**: Logs errors and rate limit issues to a designated Telegram group
- **Connection Resilience**: Automatic reconnection with exponential backoff on network failures
- **Commands**:
  - `/start`: Initialize and greet the bot
  - `/clear`: Reset conversation history for the chat
- **Group Support**: Responds only when mentioned or replied to in groups to avoid spam
- **Typing Indicators**: Shows typing action for more human-like interaction

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - Copy `sample.env` to `.env`
   - Fill in your actual API keys and tokens in the `.env` file:
     - `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather) on Telegram
     - `GROQ_API_KEY_1` to `GROQ_API_KEY_7`: Get from [Groq Console](https://console.groq.com/) (create multiple accounts for higher rate limits)
     - `LOG_GROUP_ID`: Create a private Telegram group, add your bot, and get the group ID (optional, for error logging)
4. Run the bot: `python main.py` or double-click `start_bot.bat`

### Termux (Android) Setup

For Android devices using Termux:

1. Install Termux from F-Droid or Google Play Store
2. Open Termux and run the setup script:
   ```bash
   git clone https://github.com/XieosZ/TeleGram-ChatBot.git
   cd TeleGram-ChatBot
   chmod +x setup.sh
   ./setup.sh
   ```
3. Follow the on-screen instructions to configure your API keys
4. Run the bot: `./run_bot.sh`

The setup script will automatically install all dependencies and create the necessary files.

## APIs Used

- **Telegram Bot API**: For bot interactions
- **Groq API**: For AI responses using llama-3.3-70b-versatile model

## Notes

- Free Groq tier provides higher rate limits than other free AI services
- Bot uses session management to isolate user conversations and maintain context
- Supports up to 7 Groq API keys for maximum rate limit handling
- Uses httpx 0.24.1 for HTTP requests compatibility
- Bot only responds in private chats or when directly replied to in groups

## License

MIT
