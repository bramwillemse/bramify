"""Core bot functionality for Bramify."""

import os
from typing import List, Dict, Any
from loguru import logger

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core.config import load_config, AppConfig
from core.plugin_manager import PluginManager
from integrations.claude.client import ClaudeClient
from integrations.google_sheets.client import GoogleSheetsClient
from integrations.telegram.utils import send_typing_action

class BramifyBot:
    """Main bot class handling Telegram interactions."""
    
    def __init__(self):
        """Initialize the Bramify bot with required integrations."""
        # Load configuration
        self.config = load_config()
        
        if not self.config.bot.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")
        
        # Initialize integrations
        self.claude = ClaudeClient()
        self.sheets = GoogleSheetsClient()
        
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
        
        # Message handler for text messages (lowest priority)
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message,
            # Lower number = higher priority, this should be lower priority than plugins
            1
        ))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
    
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
            "/help - Show this help message\n\n"
            
            "*Hour Registration:*\n"
            "Just tell me what you worked on today, and I'll register your hours. "
            "For example: 'Today I worked on Project X for Client Y for 4 hours.'\n\n"
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
        
        # Process the message with Claude
        response = await self._process_message(user_message, user_id)
        
        await update.message.reply_text(response)
    
    async def _process_message(self, message: str, user_id: int) -> str:
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
                
                # Save to Google Sheets
                self.sheets.add_work_entry(work_data)
                
                return (
                    f"✅ I've registered your work:\n\n"
                    f"📅 Date: {work_data['date']}\n"
                    f"👥 Client: {work_data['client']}\n"
                    f"📋 Project: {work_data['project']}\n"
                    f"⏱️ Hours: {work_data['hours']}\n"
                    f"💰 Billable: {'Yes' if work_data['billable'] else 'No'}\n"
                    f"📝 Description: {work_data['description'][:50]}..."
                )
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
    
    async def setup(self):
        """Set up the bot, including loading plugins."""
        logger.info("Setting up Bramify")
        await self.plugin_manager.load_plugins()
    
    async def run(self):
        """Run the bot."""
        logger.info("Setting up Bramify")
        await self.setup()
        
        logger.info("Starting Telegram bot")
        self.app.run_polling()