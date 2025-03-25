# Creating Plugins for Bramify

This guide explains how to create new plugins for Bramify to extend its functionality.

## Plugin System Overview

Bramify uses a plugin system that allows you to add new features without modifying the core code. Plugins can:

- Add new commands
- Process messages in custom ways
- Integrate with external services
- Add scheduled tasks

All plugins inherit from the `PluginBase` class and implement specific methods.

## Creating a New Plugin

### Step 1: Create a New Plugin File

Create a new Python file in the `src/plugins` directory. For example, `reminder_plugin.py`.

### Step 2: Import Required Components

```python
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from plugins.plugin_base import PluginBase
```

### Step 3: Create Your Plugin Class

```python
class ReminderPlugin(PluginBase):
    """Plugin for setting and managing reminders."""
    
    def __init__(self):
        """Initialize the reminder plugin."""
        super().__init__(
            name="Reminders",
            description="Set and manage reminders for future tasks"
        )
        self.reminders = {}  # Dictionary to store user reminders
    
    async def initialize(self) -> bool:
        """Initialize the plugin and register commands."""
        # Register commands
        self.register_command("remind", self.cmd_remind, "Set a reminder")
        self.register_command("list_reminders", self.cmd_list_reminders, "List all reminders")
        
        return True
    
    async def cmd_remind(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /remind command to set a reminder."""
        # Implementation goes here
        await update.message.reply_text("Reminder set!")
    
    async def cmd_list_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /list_reminders command to list all reminders."""
        # Implementation goes here
        await update.message.reply_text("Here are your reminders:")
    
    async def on_shutdown(self) -> None:
        """Handle plugin shutdown."""
        # Clean up any resources
        pass
```

### Step 4: Register Your Plugin

Open `src/core/plugin_manager.py` and add your plugin to the `load_plugins` method:

```python
async def load_plugins(self) -> None:
    """Load and initialize all available plugins."""
    # Import your plugin
    from plugins.summary_plugin import SummaryPlugin
    from plugins.reminder_plugin import ReminderPlugin  # Add this line
    from integrations.google_sheets.client import GoogleSheetsClient
    
    # Create instances of required dependencies
    sheets_client = GoogleSheetsClient()
    
    # Register plugin classes
    self.register_plugin_class("summary", SummaryPlugin, sheets_client)
    self.register_plugin_class("reminder", ReminderPlugin)  # Add this line
```

## Plugin Development Guidelines

### Command Handlers

To add a new command:

```python
self.register_command("command_name", self.handler_method, "Help text for command")
```

The handler method should have this signature:

```python
async def handler_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
```

### Message Handlers

To process messages:

```python
self.register_message_handler(self.message_handler, filters.TEXT & filters.Regex("specific pattern"))
```

The handler method should have this signature:

```python
async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
```

### Accessing Shared Resources

If your plugin needs access to shared resources like the Claude client or Google Sheets:

1. Add the required parameters to your plugin's constructor
2. Pass these dependencies when registering the plugin in `plugin_manager.py`

Example:

```python
def __init__(self, claude_client, sheets_client):
    super().__init__(name="MyPlugin", description="Description")
    self.claude = claude_client
    self.sheets = sheets_client
```

Then in `plugin_manager.py`:

```python
self.register_plugin_class("my_plugin", MyPlugin, claude_client, sheets_client)
```

## Best Practices

1. Keep plugins focused on a single responsibility
2. Use clear, descriptive command names
3. Provide helpful command descriptions
4. Handle errors gracefully
5. Clean up resources in the `on_shutdown` method
6. Use type hints for better code documentation
7. Add docstrings to all methods