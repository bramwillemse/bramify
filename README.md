# Bramify

A personal AI assistant for hour registration and task management, built with Python, Telegram, Anthropic Claude, and Google Sheets.

## Features

- Conversational hour registration through Telegram
- Natural language processing with Anthropic Claude
- Structured data storage in Google Sheets
- Modular architecture for easy extension

## Project Structure

```
bramify/
├── config/             # Configuration files
├── docs/               # Documentation
├── src/                # Source code
│   ├── core/           # Core application logic
│   ├── integrations/   # External service integrations
│   │   ├── telegram/   # Telegram bot integration
│   │   ├── claude/     # Anthropic Claude integration
│   │   └── google_sheets/ # Google Sheets integration
│   ├── plugins/        # Modular functionality plugins
│   └── utils/          # Utility functions
└── tests/              # Test suite
```

## Setup

### 1. Prerequisites

- Docker (recommended) or Python 3.11+
- Telegram bot token (from BotFather)
- Anthropic Claude API key
- Google OAuth credentials (web application type)

### 2. Quick Setup

The quickest way to get started is using the setup script:

```bash
./setup.sh
```

This will:
1. Copy Google credentials if found in your Downloads folder
2. Create a virtual environment
3. Install necessary dependencies
4. Generate a Google OAuth token
5. Prepare everything for Docker

### 3. Manual Setup

If you prefer to set up manually:

1. Create necessary directories:
   ```
   mkdir -p config logs
   ```

2. Place your Google OAuth credentials in `config/credentials.json`

3. Generate the OAuth token:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install google-auth-oauthlib python-dotenv
   python generate_token.py
   ```

4. Configure environment variables in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_ALLOWED_USER_IDS=your_telegram_id
   ANTHROPIC_API_KEY=your_anthropic_api_key
   GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
   ```

### 4. Run with Docker

```bash
docker compose up
```

## Using the Bot

After the bot is running, you can:

1. Start a conversation with your bot in Telegram
2. Use `/start` to begin
3. Track hours by simply telling the bot what you worked on
4. Use `/help` to see all available commands
5. Try `/test_mode` and `/enable_production` to switch between test and production modes

## Development

- Install development dependencies: `pip install -r requirements-dev.txt`
- Run tests: `pytest`
- Run linting: `flake8 src tests`
- Run type checking: `mypy src`

## License

MIT