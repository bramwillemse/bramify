"""Core bot functionality for Bramify."""

import os
from typing import List, Dict, Any, Optional
from loguru import logger

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from core.config import load_config, AppConfig
from core.plugin_manager import PluginManager
from integrations.claude.client import ClaudeClient
from integrations.google_sheets.client import GoogleSheetsClient
from integrations.client_mapper import ClientMapper
from integrations.telegram.utils import send_typing_action

class BramifyBot:
    """Main bot class handling Telegram interactions."""
    
    # Define conversation states
    WAITING_FOR_CLIENT_CODE = 1
    
    def __init__(self):
        """Initialize the Bramify bot with required integrations."""
        # Load configuration
        self.config = load_config()
        
        if not self.config.bot.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")
        
        # Initialize integrations
        self.claude = ClaudeClient()
        self.sheets = GoogleSheetsClient()
        self.client_mapper = ClientMapper()
        
        # Conversation state tracking
        self.pending_work_entries = {}  # User ID -> pending work entry
        
        # Initialize Telegram application
        self.app = Application.builder().token(self.config.bot.telegram_token).build()
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager(self.app)
        
        # Register core handlers
        self._register_handlers()
        
        logger.info("BramifyBot initialized")
    
    def _register_handlers(self):
        """Register message and command handlers."""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("enable_production", self.cmd_enable_production))
        self.app.add_handler(CommandHandler("enableproduction", self.cmd_enable_production))  # Add alias without underscore
        self.app.add_handler(CommandHandler("test_mode", self.cmd_test_mode))
        self.app.add_handler(CommandHandler("testmode", self.cmd_test_mode))  # Add alias without underscore
        self.app.add_handler(CommandHandler("list_clients", self.cmd_list_clients))
        
        # Conversation handler for client code
        conv_handler = ConversationHandler(
            entry_points=[],  # This is handled by handle_message
            states={
                self.WAITING_FOR_CLIENT_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_client_code)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            name="client_code_conversation",
            persistent=False,
        )
        self.app.add_handler(conv_handler)
        
        # Message handler for text messages (lowest priority)
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message,
            # Lower number = higher priority, this should be lower priority than plugins
            1
        ))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        # Initialize test mode
        self.test_mode = True
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not self._is_user_allowed(update):
            return
        
        await update.message.reply_text(
            "Hello! I'm Bramify, your personal assistant for hour registration. "
            "How can I help you today?\n\n"
            "You can tell me about your work or use /help to see available commands."
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if not self._is_user_allowed(update):
            return
        
        base_help_text = (
            "🤖 *Bramify Help* 🤖\n\n"
            "*Core Commands:*\n"
            "/start - Start interacting with the bot\n"
            "/help - Show this help message\n"
            "/test_mode or /testmode - Write hours to test sheet only\n"
            "/enable_production or /enableproduction - Write hours to the actual sheet\n\n"
            
            "*Hour Registration:*\n"
            "Just tell me what you worked on today, and I'll register your hours. "
            "For example: 'Today I worked on Project X for Client Y for 4 hours.'\n\n"
            
            f"*Current Mode:* {'Test Mode (data goes to test sheet)' if self.test_mode else 'Production Mode (data goes to actual sheet)'}\n\n"
        )
        
        # Add plugin help text
        plugin_help = self.plugin_manager.get_help_text()
        
        await update.message.reply_text(
            base_help_text + plugin_help, 
            parse_mode="Markdown"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process incoming messages and respond appropriately."""
        if not self._is_user_allowed(update):
            return
        
        user_message = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        logger.info(f"Received message from {username} ({user_id}): {user_message}")
        
        # Show typing indicator
        await send_typing_action(update)
        
        # Process the message with Claude, passing the update object for conversation handling
        response = await self._process_message(user_message, user_id, update)
        
        # If it's a conversation state, don't respond here
        if response == ConversationHandler.WAITING_FOR_CLIENT_CODE:
            return self.WAITING_FOR_CLIENT_CODE
        
        # Otherwise, send the response
        await update.message.reply_text(response)
    
    async def _process_message(self, message: str, user_id: int, update: Optional[Update] = None) -> str:
        """Process a message using Claude and extract work information if applicable."""
        try:
            # Analyze the message with Claude
            analysis = await self.claude.analyze_work_entry(message)
            
            # If work information was detected, save it
            if analysis.get("is_work_entry", False):
                work_data = {
                    "date": analysis.get("date"),
                    "client": analysis.get("client"),
                    "project": analysis.get("project"),
                    "hours": analysis.get("hours"),
                    "billable": analysis.get("billable"),
                    "description": analysis.get("description")
                }
                
                # Check if we have a client code for this client
                client_name = work_data.get("client", "")
                client_code = None
                
                if client_name:
                    client_code = self.client_mapper.get_code(client_name)
                
                # If we have a client code, add it to the work data
                if client_code:
                    work_data["client_code"] = client_code
                    
                    # Use the bot's test_mode setting
                    success = self.sheets.add_work_entry(work_data, test_mode=self.test_mode)
                    
                    # Prepare response
                    response = f"✅ I've registered your work:\n\n"
                    response += f"📅 Date: {work_data['date']}\n"
                    response += f"👥 Client: {work_data['client']} ({client_code})\n"
                    response += f"⏱️ Hours: {work_data['hours']}\n"
                    response += f"💰 Billable: {'Yes' if work_data['billable'] else 'No'}\n"
                    response += f"📝 Description: {work_data['description'][:50]}...\n"
                    
                    # Show revenue for billable hours
                    if work_data.get('billable', True) and work_data.get('hours'):
                        hourly_rate = work_data.get('hourly_rate', 85)
                        revenue = float(work_data['hours']) * hourly_rate
                        response += f"💵 Revenue: €{revenue:.2f}\n\n"
                    else:
                        response += "\n"
                    
                    if self.test_mode:
                        response += f"🔍 Note: This entry was added to a test sheet for validation. "
                        response += f"Once you confirm it's working correctly, you can use the /enableproduction "
                        response += f"command to start writing to your actual sheet."
                    
                    return response
                elif update:
                    # We need a client code - store the work entry and ask for a code
                    self.pending_work_entries[user_id] = work_data
                    
                    # Suggest a code
                    suggested_code = self.client_mapper.suggest_code_for_client(client_name)
                    
                    # Ask for the client code
                    prompt = f"I need a 3-letter client code for '{client_name}'.\n\n"
                    prompt += f"Suggested code: {suggested_code}\n\n"
                    prompt += "Please enter a 3-letter code for this client (or use the suggestion):"
                    
                    await update.message.reply_text(prompt)
                    
                    # Return to conversation handler
                    return ConversationHandler.WAITING_FOR_CLIENT_CODE
                else:
                    # No update object, so we can't start a conversation
                    logger.error("No update object provided, can't request client code")
                    return "Sorry, I can't process this work entry without knowing the client code."
            else:
                # Generate a response for a regular conversation
                return await self.claude.generate_response(message)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message. Please try again."
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the Telegram bot."""
        logger.error(f"Error handling update: {context.error}")
    
    def _is_user_allowed(self, update: Update) -> bool:
        """Check if the user is allowed to use the bot."""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        if not self.config.bot.allowed_user_ids:
            # If no allowed users are specified, allow everyone (not recommended for production)
            logger.warning("No allowed users specified, allowing all users")
            return True
            
        is_allowed = user_id in self.config.bot.allowed_user_ids
        
        if not is_allowed:
            logger.warning(f"Unauthorized access attempt by {username} ({user_id})")
            update.message.reply_text("Sorry, you are not authorized to use this bot.")
            
        return is_allowed
    
    async def cmd_enable_production(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /enable_production command to switch to production mode."""
        if not self._is_user_allowed(update):
            return
            
        self.test_mode = False
        await update.message.reply_text(
            "✅ Production mode enabled. Your work hours will now be saved to the actual sheet. "
            "Use /test_mode to switch back to test mode if needed."
        )
        
    async def cmd_test_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test_mode command to switch to test mode."""
        if not self._is_user_allowed(update):
            return
            
        self.test_mode = True
        await update.message.reply_text(
            "✅ Test mode enabled. Your work hours will be saved to a test sheet for validation. "
            "Use /enable_production to switch to production mode when ready."
        )
        
    async def cmd_list_clients(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list_clients command to show existing client codes."""
        if not self._is_user_allowed(update):
            return
            
        # Get all client mappings
        mappings = self.client_mapper.get_all_mappings()
        
        if not mappings:
            await update.message.reply_text(
                "No client codes defined yet. Client codes will be created automatically when you log hours."
            )
            return
        
        # Format the list of clients
        response = "📋 **Client Codes**\n\n"
        for client_name, code in mappings.items():
            # Show the original name if possible
            response += f"• `{code}` - {client_name}\n"
        
        await update.message.reply_text(response, parse_mode="Markdown")
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the current conversation."""
        user_id = update.effective_user.id
        
        # Clear any pending work entries
        if user_id in self.pending_work_entries:
            del self.pending_work_entries[user_id]
        
        await update.message.reply_text(
            "Operation cancelled.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return ConversationHandler.END
    
    async def handle_client_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle client code input during conversation."""
        if not self._is_user_allowed(update):
            return ConversationHandler.END
        
        user_id = update.effective_user.id
        user_input = update.message.text.strip()
        
        # Check if we have a pending work entry for this user
        if user_id not in self.pending_work_entries:
            await update.message.reply_text(
                "No pending work entry found. Please start over."
            )
            return ConversationHandler.END
        
        # Get the pending work entry
        work_data = self.pending_work_entries[user_id]
        client_name = work_data.get("client", "Unknown")
        
        # Normalize and validate the client code
        if user_input and len(user_input) >= 1:
            # Add the mapping
            self.client_mapper.add_mapping(client_name, user_input)
            
            # Update the work entry with the client code
            normalized_code = self.client_mapper._normalize_code(user_input)
            work_data["client_code"] = normalized_code
            
            # Save the work entry
            success = self.sheets.add_work_entry(work_data, test_mode=self.test_mode)
            
            # Clear the pending entry
            del self.pending_work_entries[user_id]
            
            if success:
                # Prepare response message
                response = f"✅ Work entry saved with client code: {normalized_code}\n\n"
                response += f"📅 Date: {work_data['date']}\n"
                response += f"👥 Client: {work_data['client']} ({normalized_code})\n"
                response += f"⏱️ Hours: {work_data['hours']}\n"
                response += f"💰 Billable: {'Yes' if work_data['billable'] else 'No'}\n"
                response += f"📝 Description: {work_data['description'][:50]}...\n"
                
                if self.test_mode:
                    response += f"\n🔍 Note: This entry was added to a test sheet for validation. "
                    response += f"Use /enable_production to start writing to your actual sheet."
                
                await update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    "❌ Failed to save work entry. Please try again.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return ConversationHandler.END
        else:
            # Invalid input
            await update.message.reply_text(
                f"Invalid client code. Please enter a valid 3-letter code for {client_name}:"
            )
            return self.WAITING_FOR_CLIENT_CODE
    
    async def setup(self):
        """Set up the bot, including loading plugins."""
        logger.info("Setting up Bramify")
        await self.plugin_manager.load_plugins()
    
    async def run(self):
        """Run the bot with setup."""
        logger.info("Setting up Bramify")
        await self.setup()
        
        logger.info("Starting Telegram bot")
        self.app.run_polling()