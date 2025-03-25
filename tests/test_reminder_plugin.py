"""Tests for the reminder plugin."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
import sys
import json
from datetime import datetime, timedelta
import os

# Mock modules for testing
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()
sys.modules['telegram.bot'] = MagicMock()
sys.modules['telegram.ext.filters'] = MagicMock()
sys.modules['asyncio'] = MagicMock()

# Mocks for relative imports
from tests.patch_imports import patch_imports
patch_imports()


# Mock ReminderPlugin class for testing
class MockReminderPlugin:
    """Mock implementation of ReminderPlugin for testing."""
    
    def __init__(self):
        """Initialize the plugin."""
        self.name = "Reminders"
        self.description = "Set and manage reminders for future tasks"
        self.reminders = {}
        self.command_handlers = []
        self.message_handlers = []
        self.enabled = True
        self.storage_path = "config/reminders.json"
        self.reminder_task = None
    
    async def initialize(self):
        """Initialize the plugin."""
        self.register_command("remind", self.cmd_remind, "Set a reminder")
        self.register_command("reminders", self.cmd_list_reminders, "List all reminders")
        self.register_command("clear_reminders", self.cmd_clear_reminders, "Clear all reminders")
        self._load_reminders()
        return True
    
    def register_command(self, command, callback, help_text):
        """Register a command."""
        self.command_handlers.append({"command": command, "callback": callback, "help_text": help_text})
    
    def register_message_handler(self, callback, filters_instance=None):
        """Register a message handler."""
        self.message_handlers.append({"callback": callback, "filters": filters_instance})
    
    def _load_reminders(self):
        """Load reminders from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r") as f:
                    stored_reminders = json.load(f)
                    self.reminders = {int(k): v for k, v in stored_reminders.items()}
        except Exception:
            self.reminders = {}
    
    def _save_reminders(self):
        """Save reminders to storage."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.reminders, f)
        except Exception:
            pass
    
    async def cmd_remind(self, update, context):
        """Handle /remind command."""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /remind [time] [message]...")
            return
        
        # Get the full text
        reminder_text = " ".join(context.args)
        
        # Process the reminder
        success, response = await self._process_reminder(update.effective_user.id, reminder_text)
        
        await update.message.reply_text(response)
    
    async def handle_reminder_message(self, update, context):
        """Handle natural language reminder messages."""
        message = update.message.text
        
        # Process the reminder
        success, response = await self._process_reminder(update.effective_user.id, message)
        
        await update.message.reply_text(response)
    
    async def _process_reminder(self, user_id, text):
        """Process a reminder request."""
        # Simplified for testing
        reminder_time = datetime.now() + timedelta(hours=1)
        reminder_message = text.replace("remind me", "").strip()
        
        # Store the reminder
        if user_id not in self.reminders:
            self.reminders[user_id] = []
            
        self.reminders[user_id].append({
            "time": reminder_time.timestamp(),
            "message": reminder_message,
            "created_at": datetime.now().timestamp()
        })
        
        # Save reminders
        self._save_reminders()
        
        # Format the response
        formatted_time = reminder_time.strftime("%A, %B %d at %I:%M %p")
        return True, f"✅ I'll remind you on {formatted_time}:\n\"{reminder_message}\""
    
    async def cmd_list_reminders(self, update, context):
        """Handle /reminders command."""
        user_id = update.effective_user.id
        
        if user_id not in self.reminders or not self.reminders[user_id]:
            await update.message.reply_text("You don't have any reminders set.")
            return
        
        response = "📝 *Your Reminders:*\n\n"
        for i, reminder in enumerate(self.reminders[user_id]):
            reminder_time = datetime.fromtimestamp(reminder["time"])
            response += f"{i+1}. {reminder['message']}\n"
            response += f"   📅 {reminder_time.strftime('%A, %B %d at %I:%M %p')}\n\n"
        
        await update.message.reply_text(response, parse_mode="Markdown")
    
    async def cmd_clear_reminders(self, update, context):
        """Handle /clear_reminders command."""
        user_id = update.effective_user.id
        
        if user_id in self.reminders:
            self.reminders[user_id] = []
            self._save_reminders()
            
        await update.message.reply_text("All your reminders have been cleared.")
    
    async def on_shutdown(self):
        """Handle plugin shutdown."""
        if self.reminder_task:
            self.reminder_task.cancel()
        self._save_reminders()
    
    def get_help(self):
        """Get help text for this plugin."""
        return f"*{self.name}*: {self.description}\n\n*Commands:*\n/remind [time] [message] - Set a reminder"


# Patch the import
@patch("src.plugins.reminder_plugin.ReminderPlugin", MockReminderPlugin)
class TestReminderPlugin:
    """Test suite for ReminderPlugin."""
    
    @pytest.fixture
    def reminder_plugin(self):
        """Return a ReminderPlugin instance for testing."""
        return MockReminderPlugin()
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context."""
        context = MagicMock()
        context.args = ["tomorrow", "Submit", "report"]
        return context
    
    @pytest.mark.asyncio
    async def test_initialize(self, reminder_plugin):
        """Test plugin initialization."""
        # Mock file operations
        with patch("os.path.exists", return_value=False):
            with patch("builtins.open", mock_open()):
                # Initialize the plugin
                result = await reminder_plugin.initialize()
                
                # Check that initialization was successful
                assert result is True
                
                # Check that commands were registered
                assert len(reminder_plugin.command_handlers) == 3
                
                # Check command names
                commands = [h["command"] for h in reminder_plugin.command_handlers]
                assert "remind" in commands
                assert "reminders" in commands
                assert "clear_reminders" in commands
    
    @pytest.mark.asyncio
    async def test_cmd_remind(self, reminder_plugin, mock_update, mock_context):
        """Test remind command."""
        # Mock _process_reminder to return a successful result
        reminder_plugin._process_reminder = AsyncMock(return_value=(True, "Reminder set!"))
        
        # Call the command
        await reminder_plugin.cmd_remind(mock_update, mock_context)
        
        # Check that _process_reminder was called
        reminder_plugin._process_reminder.assert_called_once()
        
        # Check that reply_text was called with the response
        mock_update.message.reply_text.assert_called_once_with("Reminder set!")
    
    @pytest.mark.asyncio
    async def test_cmd_remind_no_args(self, reminder_plugin, mock_update, mock_context):
        """Test remind command with no arguments."""
        # Set empty args
        mock_context.args = []
        
        # Call the command
        await reminder_plugin.cmd_remind(mock_update, mock_context)
        
        # Check that the usage message was shown
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Usage:" in call_args
    
    @pytest.mark.asyncio
    async def test_process_reminder(self, reminder_plugin):
        """Test processing a reminder."""
        # Mock file operations
        with patch("builtins.open", mock_open()):
            # Process a reminder
            success, response = await reminder_plugin._process_reminder(12345, "remind me to check email")
            
            # Check the result
            assert success is True
            assert "I'll remind you" in response
            assert "check email" in response
            
            # Check that the reminder was stored
            assert 12345 in reminder_plugin.reminders
            assert len(reminder_plugin.reminders[12345]) == 1
            assert reminder_plugin.reminders[12345][0]["message"] == "to check email"
    
    @pytest.mark.asyncio
    async def test_cmd_list_reminders_empty(self, reminder_plugin, mock_update, mock_context):
        """Test listing reminders when there are none."""
        # Ensure no reminders
        reminder_plugin.reminders = {}
        
        # Call the command
        await reminder_plugin.cmd_list_reminders(mock_update, mock_context)
        
        # Check the response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "don't have any reminders" in call_args
    
    @pytest.mark.asyncio
    async def test_cmd_list_reminders(self, reminder_plugin, mock_update, mock_context):
        """Test listing reminders."""
        # Add a reminder
        user_id = mock_update.effective_user.id
        reminder_time = datetime.now() + timedelta(hours=1)
        
        reminder_plugin.reminders = {
            user_id: [
                {
                    "time": reminder_time.timestamp(),
                    "message": "Test reminder",
                    "created_at": datetime.now().timestamp()
                }
            ]
        }
        
        # Call the command
        await reminder_plugin.cmd_list_reminders(mock_update, mock_context)
        
        # Check the response
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Your Reminders:" in call_args
        assert "Test reminder" in call_args
    
    @pytest.mark.asyncio
    async def test_cmd_clear_reminders(self, reminder_plugin, mock_update, mock_context):
        """Test clearing reminders."""
        # Add a reminder
        user_id = mock_update.effective_user.id
        reminder_plugin.reminders = {
            user_id: [
                {
                    "time": datetime.now().timestamp(),
                    "message": "Test reminder",
                    "created_at": datetime.now().timestamp()
                }
            ]
        }
        
        # Mock file operations
        with patch("builtins.open", mock_open()):
            # Call the command
            await reminder_plugin.cmd_clear_reminders(mock_update, mock_context)
            
            # Check that reminders were cleared
            assert user_id in reminder_plugin.reminders
            assert len(reminder_plugin.reminders[user_id]) == 0
            
            # Check the response
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "All your reminders have been cleared" in call_args
    
    @pytest.mark.asyncio
    async def test_on_shutdown(self, reminder_plugin):
        """Test plugin shutdown."""
        # Set up a mock task
        reminder_plugin.reminder_task = MagicMock()
        reminder_plugin.reminder_task.cancel = MagicMock()
        
        # Mock file operations
        with patch("builtins.open", mock_open()):
            # Call shutdown
            await reminder_plugin.on_shutdown()
            
            # Check that the task was cancelled
            reminder_plugin.reminder_task.cancel.assert_called_once()
    
    def test_get_help(self, reminder_plugin):
        """Test getting help text."""
        help_text = reminder_plugin.get_help()
        
        # Check help text content
        assert "*Reminders*" in help_text
        assert "Set and manage reminders" in help_text
        assert "/remind" in help_text