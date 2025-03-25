"""Base plugin system for Bramify."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, Application
from telegram.ext import ContextTypes

class PluginBase(ABC):
    """Base class for all Bramify plugins."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the plugin.
        
        Args:
            name: The name of the plugin
            description: A short description of what the plugin does
        """
        self.name = name
        self.description = description
        self.command_handlers = []
        self.message_handlers = []
        self.enabled = True
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin. This is called when the plugin is loaded.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    def register_handlers(self, application: Application) -> None:
        """
        Register all command and message handlers with the Telegram application.
        
        Args:
            application: The Telegram application instance
        """
        for handler in self.command_handlers:
            application.add_handler(handler)
            
        for handler in self.message_handlers:
            application.add_handler(handler)
    
    def register_command(self, command: str, callback: Callable, help_text: str) -> None:
        """
        Register a command handler.
        
        Args:
            command: The command to register (without leading slash)
            callback: The callback function to handle the command
            help_text: Help text for the command
        """
        self.command_handlers.append(CommandHandler(command, callback))
    
    def register_message_handler(
        self, 
        callback: Callable, 
        filters_instance: Optional[filters.BaseFilter] = None
    ) -> None:
        """
        Register a message handler.
        
        Args:
            callback: The callback function to handle messages
            filters_instance: Optional filter to apply to messages
        """
        if filters_instance is None:
            filters_instance = filters.TEXT & ~filters.COMMAND
            
        self.message_handlers.append(MessageHandler(filters_instance, callback))
    
    @abstractmethod
    async def on_shutdown(self) -> None:
        """Handle plugin shutdown. Clean up resources."""
        pass
    
    def get_help(self) -> str:
        """
        Get help text for this plugin.
        
        Returns:
            Help text describing the plugin and its commands
        """
        return f"*{self.name}*: {self.description}"