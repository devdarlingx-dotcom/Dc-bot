#!/usr/bin/env bash
# Destiny Kawaii Bot Run Script 🌸

cd "$(dirname "$0")"

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "🌸 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
echo "🌸 Checking dependencies..."
pip install -q -r requirements.txt

# Run Destiny Bot
echo "✨ Starting Destiny Kawaii Bot..."
python3 bot.py
