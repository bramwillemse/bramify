"""Tests for the config module."""

import pytest
import os
from unittest.mock import patch, MagicMock

# Import patch
from tests.patch_imports import patch_imports
patch_imports()

from src.core.config import load_config, AppConfig, BotConfig, ClaudeConfig, GoogleSheetsConfig


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    env_vars = {
        "TELEGRAM_BOT_TOKEN": "test_token",
        "TELEGRAM_ALLOWED_USER_IDS": "123,456,789",
        "ANTHROPIC_API_KEY": "test_api_key",
        "ANTHROPIC_MODEL": "claude-test-model",
        "GOOGLE_SHEETS_CREDENTIALS_FILE": "test_credentials.json",
        "GOOGLE_SHEETS_TOKEN_FILE": "test_token.json",
        "GOOGLE_SHEETS_SPREADSHEET_ID": "test_spreadsheet_id",
        "DEBUG": "true"
    }
    with patch.dict(os.environ, env_vars):
        yield


def test_load_config(mock_env_vars):
    """Test loading configuration from environment variables."""
    config = load_config()
    
    # Check if config is an AppConfig
    assert isinstance(config, AppConfig)
    
    # Check bot config
    assert config.bot.telegram_token == "test_token"
    assert config.bot.allowed_user_ids == [123, 456, 789]
    
    # Check Claude config
    assert config.claude.api_key == "test_api_key"
    assert config.claude.model == "claude-test-model"
    
    # Check Google Sheets config
    assert config.sheets.credentials_file == "test_credentials.json"
    assert config.sheets.token_file == "test_token.json"
    assert config.sheets.spreadsheet_id == "test_spreadsheet_id"
    
    # Check debug flag
    assert config.debug is True


def test_load_config_defaults():
    """Test loading configuration with default values when env vars are missing."""
    with patch.dict(os.environ, {}, clear=True):
        config = load_config()
        
        # Check default values
        assert config.bot.telegram_token == ""
        assert config.bot.allowed_user_ids == []
        assert config.claude.api_key == ""
        assert config.claude.model == "claude-3-opus-20240229"
        assert config.sheets.credentials_file == "credentials.json"
        assert config.sheets.token_file == "token.json"
        assert config.sheets.spreadsheet_id == ""
        assert config.debug is False


def test_debug_flag_values():
    """Test different values for DEBUG environment variable."""
    test_cases = [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("", False),
        ("anything_else", False)
    ]
    
    for value, expected in test_cases:
        with patch.dict(os.environ, {"DEBUG": value}):
            config = load_config()
            assert config.debug is expected, f"Failed for DEBUG={value}"


def test_empty_allowed_users():
    """Test handling of empty allowed users list."""
    with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": ""}):
        config = load_config()
        assert config.bot.allowed_user_ids == []
        
    with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USER_IDS": "  ,  ,  "}):
        config = load_config()
        assert config.bot.allowed_user_ids == []