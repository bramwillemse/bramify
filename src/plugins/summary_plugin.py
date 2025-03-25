"""Summary plugin for providing work summaries."""

from typing import Dict, Any, List, Optional
from telegram import Update
from telegram.ext import ContextTypes

from plugins.plugin_base import PluginBase
from integrations.google_sheets.client import GoogleSheetsClient
from integrations.telegram.utils import format_work_summary
from utils.date_utils import get_date_range_for_period

class SummaryPlugin(PluginBase):
    """Plugin for generating and displaying work summaries."""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        """
        Initialize the summary plugin.
        
        Args:
            sheets_client: Google Sheets client for accessing work data
        """
        super().__init__(
            name="Work Summary",
            description="Generate summaries of your work hours for different time periods"
        )
        self.sheets = sheets_client
    
    async def initialize(self) -> bool:
        """
        Initialize the plugin and register commands.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        # Register commands
        self.register_command("today", self.cmd_today, "Show today's work summary")
        self.register_command("yesterday", self.cmd_yesterday, "Show yesterday's work summary")
        self.register_command("week", self.cmd_week, "Show this week's work summary")
        self.register_command("month", self.cmd_month, "Show this month's work summary")
        self.register_command("summary", self.cmd_summary, "Show work summary for a specified period")
        
        return True
    
    async def cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /today command."""
        await self._show_summary(update, context, "today")
    
    async def cmd_yesterday(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /yesterday command."""
        await self._show_summary(update, context, "yesterday")
    
    async def cmd_week(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /week command."""
        await self._show_summary(update, context, "this week")
    
    async def cmd_month(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /month command."""
        await self._show_summary(update, context, "this month")
    
    async def cmd_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /summary command with optional period argument.
        
        Usage: /summary [period]
        where period can be: today, yesterday, week, month, last week, last month
        """
        # Get the period from arguments or default to "week"
        period = "week"
        if context.args and len(context.args) > 0:
            period = " ".join(context.args).lower()
            
        await self._show_summary(update, context, period)
    
    async def _show_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, period: str) -> None:
        """
        Show work summary for the specified period.
        
        Args:
            update: The Telegram update
            context: The callback context
            period: Time period for the summary
        """
        # Get date range for the period
        start_date, end_date = get_date_range_for_period(period)
        
        # Get work entries for the date range
        entries = self.sheets.get_work_entries(start_date, end_date)
        
        # Format the summary
        summary_text = format_work_summary(entries)
        
        # Add header based on the period
        header = f"*Work Summary: {period.title()}*\n"
        header += f"({start_date} to {end_date})\n\n"
        
        # Send the summary
        await update.message.reply_text(
            header + summary_text,
            parse_mode="Markdown"
        )
    
    async def on_shutdown(self) -> None:
        """Handle plugin shutdown."""
        pass
    
    def get_help(self) -> str:
        """
        Get help text for this plugin.
        
        Returns:
            Help text describing the plugin and its commands
        """
        help_text = super().get_help() + "\n\n"
        help_text += "*Commands:*\n"
        help_text += "/today - Show today's work summary\n"
        help_text += "/yesterday - Show yesterday's work summary\n"
        help_text += "/week - Show this week's work summary\n"
        help_text += "/month - Show this month's work summary\n"
        help_text += "/summary [period] - Show work summary for a specific period\n"
        
        return help_text