#!/bin/bash

# Telegram ChatBot - Akane Setup Script for Termux
# This script helps you set up the Akane Telegram bot on Termux (Android)

echo "========================================="
echo "  Akane Telegram Bot - Termux Setup"
echo "========================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update and upgrade Termux packages
echo "📦 Updating Termux packages..."
pkg update && pkg upgrade -y

# Install required packages
echo "📦 Installing required packages..."
pkg install -y python git nano

# Check if Python is installed
if command_exists python; then
    echo "✅ Python is installed: $(python --version)"
else
    echo "❌ Python installation failed"
    exit 1
fi

# Check if Git is installed
if command_exists git; then
    echo "✅ Git is installed: $(git --version)"
else
    echo "❌ Git installation failed"
    exit 1
fi

# Clone the repository (if not already cloned)
if [ ! -d ".git" ]; then
    echo "📥 Cloning the repository..."
    # Get the repository URL from git config if possible
    REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "https://github.com/XieosZ/TeleGram-ChatBot.git")

    # If we're not in a git repo, clone it
    if [ "$REPO_URL" = "https://github.com/XieosZ/TeleGram-ChatBot.git" ]; then
        git clone "$REPO_URL" temp_bot && cd temp_bot && mv * .. && mv .* .. 2>/dev/null && cd .. && rm -rf temp_bot
    fi
else
    echo "✅ Repository already cloned"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if virtual environment is needed (optional)
echo "🔧 Setting up virtual environment (optional)..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✅ Virtual environment created"
    echo "To activate: source venv/bin/activate"
    echo "To deactivate: deactivate"
fi

# Setup environment file
echo "🔧 Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f "sample.env" ]; then
        cp sample.env .env
        echo "✅ Copied sample.env to .env"
        echo ""
        echo "⚠️  IMPORTANT: You need to edit the .env file with your actual API keys!"
        echo ""
        echo "Required environment variables:"
        echo "- TELEGRAM_BOT_TOKEN: Get from @BotFather on Telegram"
        echo "- GROQ_API_KEY_1 to GROQ_API_KEY_7: Get from https://console.groq.com/"
        echo "- LOG_GROUP_ID: Create a private group and add your bot (optional)"
        echo ""
        echo "Opening .env file for editing..."
        nano .env
    else
        echo "❌ sample.env file not found!"
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

# Create a run script for convenience
echo "🔧 Creating run script..."
cat > run_bot.sh << 'EOF'
#!/bin/bash
# Run Akane Telegram Bot

echo "Starting Akane Telegram Bot..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated virtual environment"
fi

# Run the bot
python main.py
EOF

chmod +x run_bot.sh
echo "✅ Created run_bot.sh script"

# Final instructions
echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "🎉 Your Akane Telegram bot is ready to run!"
echo ""
echo "📝 Next steps:"
echo "1. Make sure your .env file has all the required API keys"
echo "2. Run the bot with: ./run_bot.sh"
echo "3. Or run directly: python main.py"
echo ""
echo "💡 Tips:"
echo "- Use 'tmux' or 'screen' to run the bot in background:"
echo "  pkg install tmux"
echo "  tmux new -s bot"
echo "  ./run_bot.sh"
echo "  Ctrl+B, D to detach"
echo "  tmux attach -t bot (to reattach)"
echo ""
echo "- To stop the bot: Ctrl+C"
echo "- Check logs in the terminal"
echo ""
echo "❓ Need help? Check the README.md file"
echo ""
echo "========================================="
