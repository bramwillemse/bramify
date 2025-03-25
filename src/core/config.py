"""Configuration management for Bramify."""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

class BotConfig(BaseModel):
    """Bot configuration model."""
    telegram_token: str
    allowed_user_ids: List[int]
    
class ClaudeConfig(BaseModel):
    """Claude API configuration model."""
    api_key: str
    model: str = "claude-3-opus-20240229"
    
class GoogleSheetsConfig(BaseModel):
    """Google Sheets configuration model."""
    credentials_file: str
    token_file: Optional[str] = None
    spreadsheet_id: str
    
class AppConfig(BaseModel):
    """Main application configuration model."""
    bot: BotConfig
    claude: ClaudeConfig
    sheets: GoogleSheetsConfig
    debug: bool = False

def load_config() -> AppConfig:
    """
    Load application configuration from environment variables.
    
    Returns:
        AppConfig object with all configuration values
    """
    # Make sure environment variables are loaded
    load_dotenv()
    
    # Parse allowed user IDs
    allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
    allowed_user_ids = [int(uid.strip()) for uid in allowed_users_str.split(",") if uid.strip()]
    
    # Create config objects
    bot_config = BotConfig(
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        allowed_user_ids=allowed_user_ids
    )
    
    claude_config = ClaudeConfig(
        api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    )
    
    sheets_config = GoogleSheetsConfig(
        credentials_file=os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json"),
        token_file=os.getenv("GOOGLE_SHEETS_TOKEN_FILE", "token.json"),
        spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    )
    
    # Create and return the main config
    return AppConfig(
        bot=bot_config,
        claude=claude_config,
        sheets=sheets_config,
        debug=os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    )