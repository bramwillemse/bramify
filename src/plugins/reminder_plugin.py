"""Reminder plugin for scheduling and managing reminders."""

import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
from telegram import Update
from telegram.ext import ContextTypes, filters
from loguru import logger

from plugins.plugin_base import PluginBase
from utils.date_utils import parse_date_text

class ReminderPlugin(PluginBase):
    """Plugin for setting and managing reminders."""
    
    def __init__(self):
        """Initialize the reminder plugin."""
        super().__init__(
            name="Reminders",
            description="Set and manage reminders for future tasks"
        )
        self.reminders = {}  # Dictionary to store user reminders - user_id -> list of reminders
        self.reminder_task = None
        self.storage_path = "config/reminders.json"
        
        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize the plugin and register commands."""
        # Register commands
        self.register_command("remind", self.cmd_remind, "Set a reminder")
        self.register_command("reminders", self.cmd_list_reminders, "List all reminders")
        self.register_command("clear_reminders", self.cmd_clear_reminders, "Clear all reminders")
        
        # Register message handler for natural language reminder setting
        self.register_message_handler(
            self.handle_reminder_message, 
            filters.TEXT & filters.Regex(r"(?i)remind\s+me\s+")
        )
        
        # Load existing reminders
        self._load_reminders()
        
        # Start the reminder checking task
        self.reminder_task = asyncio.create_task(self._check_reminders())
        
        return True
    
    def _load_reminders(self):
        """Load reminders from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r") as f:
                    stored_reminders = json.load(f)
                    
                    # Convert string keys (user_ids) back to integers
                    self.reminders = {int(k): v for k, v in stored_reminders.items()}
                    
                    logger.info(f"Loaded {sum(len(v) for v in self.reminders.values())} reminders")
        except Exception as e:
            logger.error(f"Error loading reminders: {e}")
            self.reminders = {}
    
    def _save_reminders(self):
        """Save reminders to storage."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.reminders, f)
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")
    
    async def cmd_remind(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /remind command to set a reminder.
        
        Usage: /remind [time] [message]
        Examples:
        /remind tomorrow at 9am Submit the report
        /remind in 2 hours Check the server status
        /remind Friday Call the client
        """
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /remind [time] [message]\n"
                "Examples:\n"
                "/remind tomorrow at 9am Submit the report\n"
                "/remind in 2 hours Check the server status\n"
                "/remind Friday Call the client"
            )
            return
        
        # Get the full text after the command
        reminder_text = " ".join(context.args)
        
        # Process the reminder
        success, response = await self._process_reminder(update.effective_user.id, reminder_text)
        
        await update.message.reply_text(response)
    
    async def handle_reminder_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle natural language reminder messages."""
        message = update.message.text
        
        # Check if it's a reminder message
        if re.search(r"(?i)remind\s+me\s+", message):
            # Process the reminder
            success, response = await self._process_reminder(update.effective_user.id, message)
            
            await update.message.reply_text(response)
    
    async def _process_reminder(self, user_id: int, text: str) -> Tuple[bool, str]:
        """
        Process a reminder request and extract time and message.
        
        Args:
            user_id: The Telegram user ID
            text: The reminder text
            
        Returns:
            Tuple of (success, response message)
        """
        # Various time patterns to match
        patterns = [
            # "in X hours/minutes/days"
            (r"in\s+(\d+)\s+(hour|hours|hr|hrs)", self._parse_relative_time),
            (r"in\s+(\d+)\s+(minute|minutes|min|mins)", self._parse_relative_time),
            (r"in\s+(\d+)\s+(day|days)", self._parse_relative_time),
            
            # specific time "at X:XX"
            (r"at\s+(\d{1,2}):(\d{2})(?:\s*(am|pm))?", self._parse_time),
            (r"at\s+(\d{1,2})(?:\s*(am|pm))?", self._parse_time),
            
            # specific day "on Monday", "next Friday"
            (r"(?:on|next)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", self._parse_weekday),
            
            # tomorrow, day after tomorrow
            (r"tomorrow", self._parse_tomorrow),
            (r"day\s+after\s+tomorrow", self._parse_day_after_tomorrow),
        ]
        
        reminder_time = None
        reminder_message = text
        
        # Try each pattern
        for pattern, parser in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reminder_time = parser(match)
                # Remove the time part from the message
                span = match.span()
                reminder_message = text[:span[0]].strip() + " " + text[span[1]:].strip()
                break
        
        if not reminder_time:
            # Try to extract a date
            date_text = parse_date_text(text)
            if date_text:
                try:
                    reminder_date = datetime.strptime(date_text, "%Y-%m-%d")
                    reminder_time = reminder_date.replace(
                        hour=9, minute=0, second=0  # Default to 9 AM
                    )
                except ValueError:
                    pass
        
        if not reminder_time:
            return False, "I couldn't understand when to remind you. Please try again with a clearer time."
        
        # Clean up the message 
        reminder_message = re.sub(r"(?i)remind\s+me\s+", "", reminder_message).strip()
        
        if not reminder_message:
            return False, "Please specify what to remind you about."
        
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
    
    def _parse_relative_time(self, match) -> datetime:
        """Parse relative time like 'in X hours'."""
        amount = int(match.group(1))
        unit = match.group(2).lower()
        
        now = datetime.now()
        
        if unit.startswith("hour"):
            return now + timedelta(hours=amount)
        elif unit.startswith("minute"):
            return now + timedelta(minutes=amount)
        elif unit.startswith("day"):
            return now + timedelta(days=amount)
        
        return now
    
    def _parse_time(self, match) -> datetime:
        """Parse specific time like 'at 3:30pm'."""
        now = datetime.now()
        
        hour = int(match.group(1))
        
        # Check if minutes are provided
        if len(match.groups()) > 1 and match.group(2) and match.group(2).isdigit():
            minute = int(match.group(2))
        else:
            minute = 0
            
        # Check for AM/PM
        am_pm = None
        if len(match.groups()) > 2:
            am_pm = match.group(3)
        
        # Adjust for PM
        if am_pm and am_pm.lower() == "pm" and hour < 12:
            hour += 12
            
        # Adjust for AM
        if am_pm and am_pm.lower() == "am" and hour == 12:
            hour = 0
            
        # Create the reminder time
        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the time is in the past, assume tomorrow
        if reminder_time < now:
            reminder_time += timedelta(days=1)
            
        return reminder_time
    
    def _parse_weekday(self, match) -> datetime:
        """Parse weekday like 'on Monday'."""
        weekday_name = match.group(1).lower()
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        weekday_num = weekdays.get(weekday_name)
        now = datetime.now()
        current_weekday = now.weekday()
        
        # Calculate days until the target weekday
        days_until = (weekday_num - current_weekday) % 7
        
        # If it's the same day and "next" is specified, add a week
        if days_until == 0 and "next" in match.group(0).lower():
            days_until = 7
            
        # If it's the same day without "next", but it's already past noon, add a week
        if days_until == 0 and now.hour >= 12 and "next" not in match.group(0).lower():
            days_until = 7
            
        # Default to 9 AM
        return (now + timedelta(days=days_until)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
    
    def _parse_tomorrow(self, match) -> datetime:
        """Parse 'tomorrow'."""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        # Default to 9 AM
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def _parse_day_after_tomorrow(self, match) -> datetime:
        """Parse 'day after tomorrow'."""
        now = datetime.now()
        day_after = now + timedelta(days=2)
        
        # Default to 9 AM
        return day_after.replace(hour=9, minute=0, second=0, microsecond=0)
    
    async def cmd_list_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /reminders command to list all reminders."""
        user_id = update.effective_user.id
        
        if user_id not in self.reminders or not self.reminders[user_id]:
            await update.message.reply_text("You don't have any reminders set.")
            return
        
        # Format and send the list of reminders
        reminders = self.reminders[user_id]
        now = datetime.now()
        
        response = "📝 *Your Reminders:*\n\n"
        
        for i, reminder in enumerate(sorted(reminders, key=lambda r: r["time"])):
            reminder_time = datetime.fromtimestamp(reminder["time"])
            time_diff = reminder_time - now
            
            if time_diff.total_seconds() < 0:
                time_status = "Overdue"
            elif time_diff.days > 0:
                time_status = f"in {time_diff.days} days"
            elif time_diff.seconds // 3600 > 0:
                time_status = f"in {time_diff.seconds // 3600} hours"
            else:
                time_status = f"in {time_diff.seconds // 60} minutes"
                
            response += f"{i+1}. {reminder['message']}\n"
            response += f"   📅 {reminder_time.strftime('%A, %B %d at %I:%M %p')} ({time_status})\n\n"
        
        await update.message.reply_text(response, parse_mode="Markdown")
    
    async def cmd_clear_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear_reminders command to clear all reminders."""
        user_id = update.effective_user.id
        
        if user_id in self.reminders:
            self.reminders[user_id] = []
            self._save_reminders()
            
        await update.message.reply_text("All your reminders have been cleared.")
    
    async def _check_reminders(self):
        """Background task to check for due reminders."""
        try:
            while True:
                now = datetime.now()
                now_ts = now.timestamp()
                
                # Check each user's reminders
                for user_id, reminders in list(self.reminders.items()):
                    # Find due reminders
                    due_reminders = [r for r in reminders if r["time"] <= now_ts]
                    
                    if due_reminders:
                        # Remove due reminders from the list
                        self.reminders[user_id] = [r for r in reminders if r["time"] > now_ts]
                        self._save_reminders()
                        
                        # Send notifications for each due reminder
                        for reminder in due_reminders:
                            await self._send_reminder(user_id, reminder)
                
                # Sleep for a minute before checking again
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info("Reminder checking task cancelled")
        except Exception as e:
            logger.error(f"Error in reminder checking task: {e}")
    
    async def _send_reminder(self, user_id: int, reminder: Dict[str, Any]):
        """
        Send a reminder to the user.
        
        Args:
            user_id: The Telegram user ID
            reminder: The reminder data
        """
        try:
            from telegram.bot import Bot
            from telegram import ParseMode
            
            # Get the bot instance from the application
            bot = Bot(token=self.telegram_app.bot.token)
            
            # Format the reminder message
            reminder_time = datetime.fromtimestamp(reminder["time"])
            message = (
                f"⏰ *Reminder!* ⏰\n\n"
                f"{reminder['message']}\n\n"
                f"(Set for {reminder_time.strftime('%A, %B %d at %I:%M %p')})"
            )
            
            # Send the reminder
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Sent reminder to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending reminder to user {user_id}: {e}")
    
    async def on_shutdown(self) -> None:
        """Handle plugin shutdown."""
        # Cancel the reminder checking task
        if self.reminder_task:
            self.reminder_task.cancel()
            
        # Save reminders
        self._save_reminders()
    
    def get_help(self) -> str:
        """
        Get help text for this plugin.
        
        Returns:
            Help text describing the plugin and its commands
        """
        help_text = super().get_help() + "\n\n"
        help_text += "*Commands:*\n"
        help_text += "/remind [time] [message] - Set a reminder\n"
        help_text += "/reminders - List all your reminders\n"
        help_text += "/clear_reminders - Clear all your reminders\n\n"
        help_text += "*Examples:*\n"
        help_text += "- /remind tomorrow at 9am Submit the report\n"
        help_text += "- /remind in 2 hours Check the server status\n"
        help_text += "- You can also say: \"Remind me tomorrow to call John\"\n"
        
        return help_text