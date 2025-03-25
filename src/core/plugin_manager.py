"""Plugin management system for Bramify."""

import os
import importlib
from typing import Dict, List, Type, Optional
from loguru import logger

from telegram.ext import Application
from plugins.plugin_base import PluginBase

class PluginManager:
    """Manager for loading, enabling, and disabling plugins."""
    
    def __init__(self, telegram_app: Application):
        """
        Initialize the plugin manager.
        
        Args:
            telegram_app: The Telegram application instance
        """
        self.telegram_app = telegram_app
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_classes: Dict[str, Type[PluginBase]] = {}
        
    async def load_plugins(self) -> None:
        """Load and initialize all available plugins."""
        # This could be expanded to scan a directory or load from configuration
        from plugins.summary_plugin import SummaryPlugin
        from integrations.google_sheets.client import GoogleSheetsClient
        
        # Create instances of required dependencies
        sheets_client = GoogleSheetsClient()
        
        # Register plugin classes
        self.register_plugin_class("summary", SummaryPlugin, sheets_client)
        
        # Initialize all registered plugins
        for plugin_id, (plugin_class, args) in self.plugin_classes.items():
            await self.initialize_plugin(plugin_id, plugin_class, *args)
    
    def register_plugin_class(
        self, 
        plugin_id: str, 
        plugin_class: Type[PluginBase], 
        *args
    ) -> None:
        """
        Register a plugin class for later initialization.
        
        Args:
            plugin_id: Unique identifier for the plugin
            plugin_class: The plugin class
            *args: Arguments to pass to the plugin constructor
        """
        self.plugin_classes[plugin_id] = (plugin_class, args)
        logger.info(f"Registered plugin class: {plugin_id}")
    
    async def initialize_plugin(
        self, 
        plugin_id: str, 
        plugin_class: Type[PluginBase], 
        *args
    ) -> bool:
        """
        Initialize a plugin instance.
        
        Args:
            plugin_id: Unique identifier for the plugin
            plugin_class: The plugin class
            *args: Arguments to pass to the plugin constructor
            
        Returns:
            True if the plugin was initialized successfully, False otherwise
        """
        try:
            # Create the plugin instance
            plugin = plugin_class(*args)
            
            # Initialize the plugin
            success = await plugin.initialize()
            
            if success:
                # Register the plugin's handlers with the Telegram application
                plugin.register_handlers(self.telegram_app)
                
                # Store the plugin instance
                self.plugins[plugin_id] = plugin
                
                logger.info(f"Initialized plugin: {plugin.name}")
                return True
            else:
                logger.error(f"Failed to initialize plugin: {plugin_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_id}: {e}")
            return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """
        Get a plugin instance by ID.
        
        Args:
            plugin_id: The plugin ID
            
        Returns:
            The plugin instance, or None if not found
        """
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> List[PluginBase]:
        """
        Get all loaded plugin instances.
        
        Returns:
            List of plugin instances
        """
        return list(self.plugins.values())
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin_id: The plugin ID
            
        Returns:
            True if the plugin was disabled, False if not found
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.enabled = False
            logger.info(f"Disabled plugin: {plugin.name}")
            return True
        return False
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin_id: The plugin ID
            
        Returns:
            True if the plugin was enabled, False if not found
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.enabled = True
            logger.info(f"Enabled plugin: {plugin.name}")
            return True
        return False
    
    async def shutdown_plugins(self) -> None:
        """Shut down all plugins."""
        for plugin_id, plugin in self.plugins.items():
            try:
                await plugin.on_shutdown()
                logger.info(f"Shut down plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_id}: {e}")
    
    def get_help_text(self) -> str:
        """
        Get help text for all enabled plugins.
        
        Returns:
            Formatted help text
        """
        help_text = "*Available Plugins:*\n\n"
        
        for plugin in self.get_all_plugins():
            if plugin.enabled:
                help_text += f"{plugin.get_help()}\n\n"
                
        return help_text