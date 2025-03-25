"""Tests for plugin base functionality."""

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, Application

# Import patches for testing
from tests.patch_imports import patch_imports
patch_imports()

from src.plugins.plugin_base import PluginBase


class TestPlugin(PluginBase):
    """Test implementation of PluginBase."""
    
    def __init__(self, name="Test Plugin", description="Test plugin description"):
        """Initialize the test plugin."""
        super().__init__(name=name, description=description)
        self.commands = {}
        self.initialize_called = False
        self.shutdown_called = False
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.initialize_called = True
        return True
    
    async def on_shutdown(self) -> None:
        """Handle plugin shutdown."""
        self.shutdown_called = True
    
    # Override register_command to store for testing
    def register_command(self, command: str, callback, help_text: str) -> None:
        """Register a command with testing tracking."""
        super().register_command(command, callback, help_text)
        self.commands[command] = help_text


@pytest.fixture
def test_plugin():
    """Create a test plugin instance."""
    return TestPlugin()


def test_init():
    """Test plugin initialization."""
    plugin = TestPlugin("Custom Name", "Custom description")
    
    assert plugin.name == "Custom Name"
    assert plugin.description == "Custom description"
    assert plugin.enabled is True
    assert len(plugin.command_handlers) == 0
    assert len(plugin.message_handlers) == 0


def test_get_help(test_plugin):
    """Test getting help text."""
    help_text = test_plugin.get_help()
    
    assert "*Test Plugin*" in help_text
    assert "Test plugin description" in help_text


@pytest.mark.asyncio
async def test_initialize(test_plugin):
    """Test plugin initialization."""
    result = await test_plugin.initialize()
    
    assert result is True
    assert test_plugin.initialize_called is True


@pytest.mark.asyncio
async def test_on_shutdown(test_plugin):
    """Test plugin shutdown."""
    await test_plugin.on_shutdown()
    
    assert test_plugin.shutdown_called is True


def test_register_command(test_plugin):
    """Test registering a command."""
    async def dummy_callback(update, context):
        pass
    
    test_plugin.register_command("test", dummy_callback, "Test command help")
    
    assert len(test_plugin.command_handlers) == 1
    assert "test" in test_plugin.commands
    assert test_plugin.commands["test"] == "Test command help"
    assert isinstance(test_plugin.command_handlers[0], CommandHandler)


def test_register_message_handler(test_plugin):
    """Test registering a message handler."""
    async def dummy_callback(update, context):
        pass
    
    # Register with default filter
    test_plugin.register_message_handler(dummy_callback)
    
    assert len(test_plugin.message_handlers) == 1
    assert isinstance(test_plugin.message_handlers[0], MessageHandler)
    
    # Register with custom filter
    custom_filter = filters.TEXT & filters.COMMAND
    test_plugin.register_message_handler(dummy_callback, custom_filter)
    
    assert len(test_plugin.message_handlers) == 2


def test_register_handlers(test_plugin):
    """Test registering handlers with the application."""
    # Create mock application
    mock_app = MagicMock(spec=Application)
    
    # Register some handlers
    async def dummy_callback(update, context):
        pass
    
    test_plugin.register_command("test", dummy_callback, "Test command")
    test_plugin.register_message_handler(dummy_callback)
    
    # Register with application
    test_plugin.register_handlers(mock_app)
    
    # Verify app.add_handler was called twice
    assert mock_app.add_handler.call_count == 2