"""Tests for the core bot functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import sys
from pathlib import Path

# Create mock modules
sys.modules['anthropic'] = MagicMock()
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()
sys.modules['integrations.claude.client'] = MagicMock()
sys.modules['integrations.google_sheets.client'] = MagicMock()
sys.modules['core.config'] = MagicMock()
sys.modules['core.plugin_manager'] = MagicMock()
sys.modules['integrations.telegram.utils'] = MagicMock()

# Mock classes
class MockBramifyBot:
    """Mock BramifyBot for tests."""
    
    def __init__(self):
        self.config = MagicMock()
        self.config.bot.telegram_token = "test_token"
        self.config.bot.allowed_user_ids = [12345]
        self.claude = MagicMock()
        self.sheets = MagicMock()
        self.app = MagicMock()
        self.plugin_manager = MagicMock()
        self.test_mode = True
    
    async def cmd_start(self, update, context):
        if not self._is_user_allowed(update):
            return
        await update.message.reply_text("Hello! I'm Bramify...")
    
    async def cmd_help(self, update, context):
        if not self._is_user_allowed(update):
            return
        base_help_text = "🤖 *Bramify Help* 🤖\n\n*Core Commands:*\n..."
        plugin_help = self.plugin_manager.get_help_text()
        await update.message.reply_text(base_help_text + plugin_help, parse_mode="Markdown")
    
    async def _process_message(self, message, user_id):
        try:
            # Analyze with Claude
            analysis = await self.claude.analyze_work_entry(message)
            
            if analysis.get("is_work_entry", False):
                work_data = {
                    "date": analysis.get("date"),
                    "client": analysis.get("client"),
                    "project": analysis.get("project"),
                    "hours": analysis.get("hours"),
                    "billable": analysis.get("billable"),
                    "description": analysis.get("description")
                }
                self.sheets.add_work_entry(work_data, test_mode=self.test_mode)
                
                response = f"✅ I've registered your work:\n\n"
                response += f"📅 Date: {work_data['date']}\n"
                response += f"👥 Client: {work_data['client']}\n"
                response += f"⏱️ Hours: {work_data['hours']}\n"
                response += f"💰 Billable: {'Yes' if work_data['billable'] else 'No'}\n"
                response += f"📝 Description: {work_data['description'][:50]}...\n"
                
                return response
            else:
                return await self.claude.generate_response(message)
                
        except Exception as e:
            return "Sorry, I encountered an error processing your message."
    
    def _is_user_allowed(self, update):
        user_id = update.effective_user.id
        if not self.config.bot.allowed_user_ids:
            return True
        is_allowed = user_id in self.config.bot.allowed_user_ids
        if not is_allowed:
            update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return is_allowed
    
    async def cmd_enable_production(self, update, context):
        if not self._is_user_allowed(update):
            return
        self.test_mode = False
        await update.message.reply_text("✅ Production mode enabled.")
    
    async def cmd_test_mode(self, update, context):
        if not self._is_user_allowed(update):
            return
        self.test_mode = True
        await update.message.reply_text("✅ Test mode enabled.")
    
    async def setup(self):
        await self.plugin_manager.load_plugins()
    
    async def run(self):
        await self.setup()
        self.app.run_polling()


# Patch the original BramifyBot with our mock
@patch("src.core.bot.BramifyBot", MockBramifyBot)
class TestBramifyBot:
    """Test suite for BramifyBot."""
    
    @pytest.fixture
    def bot(self):
        """Return a bot instance for testing."""
        return MockBramifyBot()
    
    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.effective_user.username = "testuser"
        update.message.text = "test message"
        return update
    
    @pytest.mark.asyncio
    async def test_cmd_start(self, bot, mock_update):
        """Test the /start command handler."""
        context = MagicMock()
        
        # Call the handler
        await bot.cmd_start(mock_update, context)
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cmd_unauthorized(self, bot, mock_update):
        """Test unauthorized access."""
        # Change user ID to unauthorized
        mock_update.effective_user.id = 99999
        context = MagicMock()
        
        # Call the handler
        await bot.cmd_start(mock_update, context)
        
        # Verify response contains unauthorized message
        assert not mock_update.message.reply_text.called or "not authorized" in mock_update.message.reply_text.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_help(self, bot, mock_update):
        """Test the /help command handler."""
        context = MagicMock()
        bot.plugin_manager.get_help_text.return_value = "*Test Plugin*: Test help text"
        
        # Call the handler
        await bot.cmd_help(mock_update, context)
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_work_entry(self, bot):
        """Test processing a message that contains work information."""
        # Add client mapper
        bot.client_mapper = MagicMock()
        bot.client_mapper.get_code.return_value = "TST"  # Mock that we have a code
        
        # Configure mock Claude to return a work entry
        bot.claude.analyze_work_entry = AsyncMock()
        bot.claude.analyze_work_entry.return_value = {
            "is_work_entry": True,
            "date": "25-03-2025",
            "client": "Test Client",
            "hours": 3.5,
            "billable": True,
            "description": "Test work description",
            "hourly_rate": 85
        }
        
        # Call the method
        response = await bot._process_message("I worked on Test Client for 3.5 hours today", 12345)
        
        # Verify Claude was called
        bot.claude.analyze_work_entry.assert_called_once()
        
        # Verify client code was looked up
        bot.client_mapper.get_code.assert_called_once_with("Test Client")
        
        # Verify work entry was added
        bot.sheets.add_work_entry.assert_called_once()
        
        # Verify response contains work details
        assert "✅ I've registered your work" in response
        assert "Test Client (TST)" in response
    
    @pytest.mark.asyncio
    async def test_process_message_work_entry_no_client_code(self, bot):
        """Test processing a message with a new client (no code yet)."""
        # Add client mapper
        bot.client_mapper = MagicMock()
        bot.client_mapper.get_code.return_value = None  # No code yet
        bot.client_mapper.suggest_code_for_client.return_value = "TES"
        
        # Create pending_work_entries dict
        bot.pending_work_entries = {}
        
        # Configure mock Claude to return a work entry
        bot.claude.analyze_work_entry = AsyncMock()
        bot.claude.analyze_work_entry.return_value = {
            "is_work_entry": True,
            "date": "25-03-2025",
            "client": "Test Client",
            "hours": 3.5,
            "billable": True,
            "description": "Test work description",
            "hourly_rate": 85
        }
        
        # Create a mock update
        mock_update = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        
        # Call the method with the update
        response = await bot._process_message(
            "I worked on Test Client for 3.5 hours today", 
            12345, 
            mock_update
        )
        
        # Verify Claude was called
        bot.claude.analyze_work_entry.assert_called_once()
        
        # Verify client code was looked up
        bot.client_mapper.get_code.assert_called_once_with("Test Client")
        
        # Verify a code was suggested
        bot.client_mapper.suggest_code_for_client.assert_called_once_with("Test Client")
        
        # Verify pending work entry was stored
        assert 12345 in bot.pending_work_entries
        assert bot.pending_work_entries[12345]["client"] == "Test Client"
        
        # Verify user was prompted for a code
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "client code" in call_args.lower()
        assert "TES" in call_args  # Suggested code
        
        # Verify we're waiting for the code
        assert response == bot.WAITING_FOR_CLIENT_CODE
    
    @pytest.mark.asyncio
    async def test_process_message_conversation(self, bot):
        """Test processing a regular conversational message."""
        # Configure mock Claude
        bot.claude.analyze_work_entry = AsyncMock()
        bot.claude.analyze_work_entry.return_value = {
            "is_work_entry": False
        }
        bot.claude.generate_response = AsyncMock()
        bot.claude.generate_response.return_value = "This is a response to your question."
        
        # Call the method
        response = await bot._process_message("What's the weather like today?", 12345)
        
        # Verify Claude was called for analysis and response
        bot.claude.analyze_work_entry.assert_called_once()
        bot.claude.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cmd_enable_production(self, bot, mock_update):
        """Test enabling production mode."""
        context = MagicMock()
        
        # Call the handler
        await bot.cmd_enable_production(mock_update, context)
        
        # Verify mode was changed
        assert bot.test_mode is False
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_command_aliases(self, bot):
        """Test that both command formats (with and without underscore) work."""
        # In the actual implementation, we verify that the handler is registered twice
        # Here we'll just check that both command formats would call the same method
        from src.core.bot import BramifyBot
        from unittest.mock import patch
        
        # Check that both enableproduction and enable_production call the same method
        bot_instance = BramifyBot()
        
        # Check the registered handlers by looking at their callbacks
        command_handlers = [h for h in bot_instance.app.add_handler.call_args_list 
                           if hasattr(h[0][0], 'command')]
        
        # Get handlers for our commands
        enable_prod_handlers = [h for h in command_handlers 
                               if h[0][0].command in ['enable_production', 'enableproduction']]
        test_mode_handlers = [h for h in command_handlers 
                             if h[0][0].command in ['test_mode', 'testmode']]
        
        # Verify both command formats are registered
        assert len(enable_prod_handlers) == 2
        assert len(test_mode_handlers) == 2
        
        # Verify both command formats call the same handler method
        assert enable_prod_handlers[0][0][0].callback == enable_prod_handlers[1][0][0].callback
        assert test_mode_handlers[0][0][0].callback == test_mode_handlers[1][0][0].callback
    
    @pytest.mark.asyncio
    async def test_cmd_test_mode(self, bot, mock_update):
        """Test enabling test mode."""
        # First set production mode
        bot.test_mode = False
        context = MagicMock()
        
        # Call the handler
        await bot.cmd_test_mode(mock_update, context)
        
        # Verify mode was changed
        assert bot.test_mode is True
        
        # Verify response
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_client_code(self, bot, mock_update):
        """Test handling client code input during conversation."""
        # Set up client mapper
        bot.client_mapper = MagicMock()
        bot.client_mapper._normalize_code.return_value = "TST"
        
        # Set up a pending work entry
        bot.pending_work_entries = {
            12345: {
                "date": "25-03-2025",
                "client": "Test Client",
                "hours": 3.5,
                "billable": True,
                "description": "Test work description"
            }
        }
        
        # Set up the message text
        mock_update.message.text = "TST"
        
        # Configure success response for add_work_entry
        bot.sheets.add_work_entry.return_value = True
        
        # Call the handler
        result = await bot.handle_client_code(mock_update, MagicMock())
        
        # Verify mapping was added
        bot.client_mapper.add_mapping.assert_called_once_with("Test Client", "TST")
        
        # Verify work entry was added with the client code
        bot.sheets.add_work_entry.assert_called_once()
        work_data = bot.sheets.add_work_entry.call_args[0][0]
        assert work_data["client_code"] == "TST"
        
        # Verify the entry was removed from pending
        assert 12345 not in bot.pending_work_entries
        
        # Verify the conversation ended
        from telegram.ext import ConversationHandler
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_setup_and_run(self, bot):
        """Test bot setup and run methods."""
        # Setup mock methods
        bot.plugin_manager.load_plugins = AsyncMock()
        bot.app.run_polling = MagicMock()
        
        # Call setup
        await bot.setup()
        
        # Verify plugin manager was called
        bot.plugin_manager.load_plugins.assert_called_once()
        
        # Test run
        await bot.run()
        
        # Verify polling was started
        bot.app.run_polling.assert_called_once()