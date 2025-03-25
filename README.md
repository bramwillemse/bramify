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
   config/             # Configuration files
   docs/               # Documentation
   src/                # Source code
      core/           # Core application logic
      integrations/   # External service integrations
         telegram/   # Telegram bot integration
         claude/     # Anthropic Claude integration
         google_sheets/ # Google Sheets integration
      plugins/        # Modular functionality plugins
      utils/          # Utility functions
   tests/              # Test suite
```

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your API keys
6. Run the application: `python src/main.py`

## Docker Deployment

```bash
docker-compose up -d
```

## Development

- Install development dependencies: `pip install -r requirements-dev.txt`
- Run tests: `pytest`
- Run linting: `flake8 src tests`
- Run type checking: `mypy src`

## License

MIT