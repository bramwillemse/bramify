# Bramify Setup Guide

This guide will help you set up Bramify, a personal AI assistant for hour registration.

## Prerequisites

- Python 3.10 or higher
- A Telegram account
- Anthropic API key (for Claude)
- Google account with Google Sheets API enabled

## Step 1: Create a Telegram Bot

1. Open Telegram and search for the BotFather (@BotFather)
2. Start a chat with BotFather and send the command `/newbot`
3. Follow the instructions to create your bot
4. When finished, BotFather will give you a token. Save this as your `TELEGRAM_BOT_TOKEN`
5. Customize your bot with `/mybots` (optional)

## Step 2: Get an Anthropic API Key

1. Visit [Anthropic's website](https://www.anthropic.com)
2. Sign up for an API key
3. Save this as your `ANTHROPIC_API_KEY`

## Step 3: Set Up Google Sheets

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Sheets API
4. Create credentials (Service Account)
5. Download the credentials JSON file and save it as `credentials.json` in the config directory
6. Create a new Google Sheet and share it with the email address in your service account
7. Copy the spreadsheet ID from the URL (the long string between /d/ and /edit) and save it

## Step 4: Configure Environment Variables

1. Copy `.env.example` to `.env`
2. Fill in the following values:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_ALLOWED_USER_IDS`: Your Telegram user ID (you can find this using @userinfobot)
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `GOOGLE_SHEETS_CREDENTIALS_FILE`: Path to your credentials.json file (e.g., config/credentials.json)
   - `GOOGLE_SHEETS_SPREADSHEET_ID`: Your Google Sheets spreadsheet ID

## Step 5: Run the Bot

### Local Development

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python src/main.py
```

### Docker Deployment

```bash
# Build and run the Docker container
docker-compose up -d

# View logs
docker-compose logs -f
```

## Step 6: Start Using Your Bot

1. Open Telegram and search for your bot by username
2. Start a conversation with your bot
3. Send the `/start` command
4. Begin logging your hours by simply telling the bot what you worked on

## Troubleshooting

- Check the logs in the `logs` directory for error messages
- Ensure all API keys and credentials are correct
- Verify that the Google Sheet is shared with the service account email
- Make sure your Telegram user ID is in the allowed users list