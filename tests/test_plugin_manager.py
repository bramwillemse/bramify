"""Tests for the plugin manager."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
from pathlib import Path

# Import patch
from tests.patch_imports import patch_imports
patch_imports()

from src.core.plugin_manager import PluginManager
from src.plugins.plugin_base import PluginBase


class MockPlugin(PluginBase):
    """Mock plugin for testing."""
    
    def __init__(self, name="Test Plugin", description="Test Description"):
        """Initialize the mock plugin."""
        super().__init__(name=name, description=description)
        self.initialize_called = False
        self.shutdown_called = False
        self.initialize_return_value = True
        
    async def initialize(self) -> bool:
        """Mock initialize method."""
        self.initialize_called = True
        return self.initialize_return_value
        
    async def on_shutdown(self) -> None:
        """Mock shutdown method."""
        self.shutdown_called = True


@pytest.fixture
def mock_telegram_app():
    """Create a mock Telegram application."""
    app = MagicMock()
    app.add_handler = MagicMock()
    return app


@pytest.fixture
def plugin_manager(mock_telegram_app):
    """Create a PluginManager instance for testing."""
    return PluginManager(mock_telegram_app)


@pytest.mark.asyncio
async def test_register_plugin_class(plugin_manager):
    """Test registering a plugin class."""
    plugin_manager.register_plugin_class("test", MockPlugin)
    
    # Check if the plugin was registered
    assert "test" in plugin_manager.plugin_classes
    plugin_class, args = plugin_manager.plugin_classes["test"]
    assert plugin_class == MockPlugin
    assert args == ()


@pytest.mark.asyncio
async def test_initialize_plugin(plugin_manager):
    """Test initializing a plugin."""
    # Register the plugin class
    plugin_manager.register_plugin_class("test", MockPlugin, "arg1", "arg2")
    
    # Initialize with different constructor to test args
    with patch("tests.test_plugin_manager.MockPlugin") as mock_plugin_class:
        mock_plugin = MockPlugin()
        mock_plugin_class.return_value = mock_plugin
        
        # Initialize the plugin
        result = await plugin_manager.initialize_plugin("test", MockPlugin, "arg1", "arg2")
        
        # Check results
        assert result is True
        assert "test" in plugin_manager.plugins
        assert mock_plugin_class.call_args[0] == ("arg1", "arg2")  # Constructor args


@pytest.mark.asyncio
async def test_initialize_plugin_failure(plugin_manager):
    """Test initializing a plugin that fails."""
    mock_plugin = MockPlugin()
    mock_plugin.initialize_return_value = False
    
    with patch("tests.test_plugin_manager.MockPlugin", return_value=mock_plugin):
        # Initialize the plugin
        result = await plugin_manager.initialize_plugin("test", MockPlugin)
        
        # Check results
        assert result is False
        assert "test" not in plugin_manager.plugins


@pytest.mark.asyncio
async def test_initialize_plugin_exception(plugin_manager):
    """Test initializing a plugin that raises an exception."""
    with patch("tests.test_plugin_manager.MockPlugin", side_effect=Exception("Test error")):
        # Initialize the plugin
        result = await plugin_manager.initialize_plugin("test", MockPlugin)
        
        # Check results
        assert result is False
        assert "test" not in plugin_manager.plugins


@pytest.mark.asyncio
async def test_get_plugin(plugin_manager):
    """Test getting a plugin by ID."""
    # Add a plugin
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    # Get the plugin
    plugin = plugin_manager.get_plugin("test")
    assert plugin is mock_plugin
    
    # Try to get a non-existent plugin
    plugin = plugin_manager.get_plugin("nonexistent")
    assert plugin is None


@pytest.mark.asyncio
async def test_get_all_plugins(plugin_manager):
    """Test getting all plugins."""
    # Add plugins
    plugin1 = MockPlugin(name="Plugin 1")
    plugin2 = MockPlugin(name="Plugin 2")
    plugin_manager.plugins["test1"] = plugin1
    plugin_manager.plugins["test2"] = plugin2
    
    # Get all plugins
    plugins = plugin_manager.get_all_plugins()
    assert len(plugins) == 2
    assert plugin1 in plugins
    assert plugin2 in plugins


@pytest.mark.asyncio
async def test_disable_enable_plugin(plugin_manager):
    """Test disabling and enabling a plugin."""
    # Add a plugin
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    # Disable the plugin
    result = plugin_manager.disable_plugin("test")
    assert result is True
    assert mock_plugin.enabled is False
    
    # Enable the plugin
    result = plugin_manager.enable_plugin("test")
    assert result is True
    assert mock_plugin.enabled is True
    
    # Try to disable a non-existent plugin
    result = plugin_manager.disable_plugin("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_shutdown_plugins(plugin_manager):
    """Test shutting down all plugins."""
    # Add plugins
    plugin1 = MockPlugin(name="Plugin 1")
    plugin2 = MockPlugin(name="Plugin 2")
    plugin_manager.plugins["test1"] = plugin1
    plugin_manager.plugins["test2"] = plugin2
    
    # Shutdown all plugins
    await plugin_manager.shutdown_plugins()
    
    # Check that shutdown was called on all plugins
    assert plugin1.shutdown_called is True
    assert plugin2.shutdown_called is True


@pytest.mark.asyncio
async def test_get_help_text(plugin_manager):
    """Test getting help text from all plugins."""
    # Add plugins
    plugin1 = MockPlugin(name="Plugin 1", description="Description 1")
    plugin2 = MockPlugin(name="Plugin 2", description="Description 2")
    plugin_manager.plugins["test1"] = plugin1
    plugin_manager.plugins["test2"] = plugin2
    
    # Disable one plugin
    plugin2.enabled = False
    
    # Get help text
    help_text = plugin_manager.get_help_text()
    
    # Check that only enabled plugins are included
    assert "*Plugin 1*: Description 1" in help_text
    assert "*Plugin 2*: Description 2" not in help_text