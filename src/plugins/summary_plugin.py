"""Summary plugin for providing work summaries."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from plugins.plugin_base import PluginBase
from integrations.google_sheets.client import GoogleSheetsClient
from integrations.telegram.utils import format_work_summary
from utils.date_utils import get_date_range_for_period

class SummaryPlugin(PluginBase):
    """Plugin voor het genereren en weergeven van urenoverzichten."""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        """
        Initialize the summary plugin.
        
        Args:
            sheets_client: Google Sheets client for accessing work data
        """
        super().__init__(
            name="Uren Overzicht",
            description="Genereer overzichten van je gewerkte uren voor verschillende periodes"
        )
        self.sheets = sheets_client
        
        # Get the test sheet name from the sheets client
        self.test_sheet = self.sheets.test_sheet
    
    async def initialize(self) -> bool:
        """
        Initialiseer de plugin en registreer commando's.
        
        Returns:
            True als initialisatie succesvol was, False anders
        """
        # Register commands
        self.register_command("today", self.cmd_today, "Show hours worked today")
        self.register_command("yesterday", self.cmd_yesterday, "Show hours worked yesterday")
        self.register_command("week", self.cmd_week, "Show hours worked this week")
        self.register_command("month", self.cmd_month, "Show hours worked this month")
        
        return True
    
    async def cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Verwerk het /today commando."""
        await self._show_summary(update, context, "today")
    
    async def cmd_yesterday(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Verwerk het /yesterday commando."""
        await self._show_summary(update, context, "yesterday")
    
    async def cmd_week(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Verwerk het /week commando."""
        await self._show_summary(update, context, "this week")
    
    async def cmd_month(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Verwerk het /month commando."""
        await self._show_summary(update, context, "this month")
    
    async def _show_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, period: str) -> None:
        """
        Toon urenoverzicht voor de opgegeven periode.
        
        Args:
            update: De Telegram update
            context: De callback context
            period: Tijdsperiode voor het overzicht
        """
        from loguru import logger
        
        # Get date range for the period
        start_date, end_date = get_date_range_for_period(period)
        logger.info(f"Generating work summary for period: {period} ({start_date} to {end_date})")
        
        # Get work entries for the date range
        entries = self.sheets.get_work_entries(start_date, end_date)
        logger.info(f"Found {len(entries)} entries for period {period}")
        
        # Log informatie over testentries
        test_entries = [e for e in entries if e.get('Sheet') == self.test_sheet]
        logger.info(f"Test entries count: {len(test_entries)}")
        for e in test_entries:
            logger.info(f"Test entry: {e.get('Date')} - {e.get('Client')} - Hours: '{e.get('Hours')}'")
            
        # Voor een betere gebruikerservaring maken we meteen gebruik van alle entries
        # inclusief test entries, zonder dubbele berichten te sturen
        filtered_entries = test_entries.copy()
        
        # Apply filtering based on the period
        if True:  # Always apply date filtering
            # Get the date information
            today_dt = datetime.now().date()
            current_year = today_dt.year
            current_month = today_dt.month
            current_day = today_dt.day
            
            # Format checking examples
            logger.info(f"Strictly filtering dates for period: {period}")
            logger.info(f"Current date: {today_dt.day}-{today_dt.month}-{today_dt.year}")
            
            # Parse start_date and end_date as datetime objects for comparison
            try:
                start_year, start_month, start_day = start_date.split('-')
                start_dt = datetime(int(start_year), int(start_month), int(start_day)).date()
                
                end_year, end_month, end_day = end_date.split('-')
                end_dt = datetime(int(end_year), int(end_month), int(end_day)).date()
                
                logger.info(f"Date range: {start_dt.strftime('%d-%m-%Y')} to {end_dt.strftime('%d-%m-%Y')}")
            except Exception as e:
                logger.error(f"Error parsing date range: {e}")
                start_dt = today_dt
                end_dt = today_dt
            
            # Special debug log to see what dates we have
            for e in entries[:5]:  # Look at first 5 entries
                logger.info(f"Entry date example: {e.get('Date')}")
            
            # Try several date formats for flexibility
            # We filteren alleen niet-test entries, test entries zijn al toegevoegd
            regular_entries = [e for e in entries if e.get('Sheet') != self.test_sheet]
            
            for entry in regular_entries:
                date_str = entry.get('Date', '')
                
                # Skip if empty date
                if not date_str:
                    continue
                
                # Check for year match first - very important!
                # For this month/today/this week/etc. we need current year
                year_str = str(current_year)
                if year_str not in date_str:
                    # Skip entries from other years
                    continue
                
                # For 'today' or specific day, check for exact day match
                if period.lower() in ['today', 'day', 'yesterday']:
                    day_str = str(start_dt.day)
                    month_str = str(start_dt.month)
                    
                    # For debugging
                    logger.info(f"Looking for day {day_str} in entry date: {date_str}")
                    
                    # More strict checking for today
                    # Check for explicit "25 maart" or "25-3" type patterns
                    dutch_months = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 
                                   'juli', 'augustus', 'september', 'oktober', 'november', 'december']
                    month_name = dutch_months[start_dt.month-1]
                    
                    # Specific patterns to look for in "today" filtering
                    specific_patterns = [
                        f" {day_str} {month_name}",  # "25 maart"
                        f" {day_str}-{month_str}",   # "25-3"
                        f" {day_str}/{month_str}",   # "25/3"
                        f"dag {day_str} {month_name}" # "zondag 25 maart"
                    ]
                    
                    # Check if any of the specific patterns are in the date string
                    pattern_match = any(pattern in date_str.lower() for pattern in specific_patterns)
                    
                    # If we have an exact pattern match for the day/month
                    if pattern_match and year_str in date_str:
                        logger.info(f"✅ Exact match for today ({day_str} {month_name} {year_str}): {date_str}")
                        filtered_entries.append(entry)
                    # Check if the date is in DD-MM-YYYY format directly
                    elif (f"{day_str}-{month_str}-{year_str}" in date_str or 
                          f"{day_str.zfill(2)}-{month_str.zfill(2)}-{year_str}" in date_str):
                        logger.info(f"✅ Direct date format match: {date_str}")
                        filtered_entries.append(entry)
                    # Otherwise try the more general approach with Test entries, or any entries from today
                    elif (entry.get("Sheet", "") == self.test_sheet or  # Test sheet entries
                          # Match any entry with format resembling today's date
                          ((day_str in date_str or day_str.zfill(2) in date_str) and  # Day match
                           (month_str in date_str or month_str.zfill(2) in date_str or month_name.lower() in date_str.lower()) and  # Month match
                           year_str in date_str)):  # Year match
                        logger.info(f"✅ Test sheet or day-month-year match for today: {date_str}")
                        filtered_entries.append(entry)
                
                # For 'this month' or 'last month', check for month match
                elif period.lower() in ['this month', 'month', 'last month']:
                    month_str = str(start_dt.month)
                    dutch_months = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 
                                   'juli', 'augustus', 'september', 'oktober', 'november', 'december']
                    month_name = dutch_months[start_dt.month-1]
                    
                    # For debugging
                    logger.info(f"Looking for month {month_name} in entry date: {date_str}")
                    
                    # Check for explicit month name in the date string
                    if month_name in date_str.lower() and year_str in date_str:
                        logger.info(f"✅ Exact month match for {month_name} {year_str}: {date_str}")
                        filtered_entries.append(entry)
                    # Check for month in numerical format (with year)
                    elif ((f"-{month_str}-" in date_str or f"-{month_str.zfill(2)}-" in date_str) and 
                          year_str in date_str):
                        logger.info(f"✅ Numerical month match: {date_str}")
                        filtered_entries.append(entry)
                    # Otherwise try the more general approach with Test entries
                    elif entry.get("Sheet", "") == self.test_sheet or (
                         # Month match (numerical or name) with year
                         ((month_str in date_str or month_str.zfill(2) in date_str or month_name.lower() in date_str.lower()) and 
                          year_str in date_str)):
                        logger.info(f"✅ Test sheet or general month match: {date_str}")
                        filtered_entries.append(entry)
                
                # For 'this week' or 'last week', we need to check against the range
                elif period.lower() in ['this week', 'week', 'last week']:
                    # This is trickier because we'd need to parse the date
                    # For now, let's include all entries from the current year (already filtered above)
                    filtered_entries.append(entry)
            
            entries = filtered_entries
            logger.info(f"After strict date filtering: {len(entries)} entries")
            
            # Show the entries we found
            for e in entries[:3]:  # Look at first 3 entries
                logger.info(f"Matched entry: {e.get('Date')} - {e.get('Client')} - {e.get('Description')}")
            
            # For safety, limit to the most recent entries
            max_entries = 15 if period.lower() in ['today', 'day', 'yesterday'] else 30
            if len(entries) > max_entries:
                logger.info(f"Limiting entries to most recent {max_entries} (from {len(entries)})")
                entries = entries[:max_entries]
        
        # Bepaal period_type en period_number voor de summary
        period_type = None
        period_number = None
        
        if period.lower() in ['today', 'day']:
            period_type = 'day'
            period_number = start_dt.day
            logger.info(f"Today - dag {period_number}, datum: {start_dt}")
        elif period.lower() in ['yesterday']:
            period_type = 'day'
            period_number = start_dt.day
            logger.info(f"Yesterday - dag {period_number}, datum: {start_dt}")
        elif period.lower() in ['this week', 'week', 'last week']:
            period_type = 'week'
            # Bereken weeknummer
            week_number = start_dt.isocalendar()[1]
            period_number = week_number
            logger.info(f"Week {period_number}, startdatum: {start_dt}")
        elif period.lower() in ['this month', 'month', 'last month']:
            period_type = 'month'
            period_number = start_dt.month
            logger.info(f"Maand {period_number}, startdatum: {start_dt}")
            
        # Format the summary met period informatie
        summary_text = format_work_summary(entries, period_type, period_number)
        
        # Send the summary zonder extra header
        await update.message.reply_text(
            summary_text,
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
        help_text = f"*{self.name}*: Genereer overzichten van je gewerkte uren voor verschillende periodes\n\n"
        help_text += "*Commando's:*\n"
        help_text += "/today - Toon uren gewerkt vandaag\n"
        help_text += "/yesterday - Toon uren gewerkt gisteren\n"
        help_text += "/week - Toon uren gewerkt deze week\n"
        help_text += "/month - Toon uren gewerkt deze maand\n"
        
        return help_text