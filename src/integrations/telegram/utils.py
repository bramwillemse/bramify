"""Utilities for Telegram bot integration."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from telegram import Update
from loguru import logger
from collections import defaultdict

async def send_typing_action(update: Update):
    """
    Send typing action to indicate the bot is processing a message.
    
    Args:
        update: The Telegram update object
    """
    try:
        await update.message.chat.send_action(action="typing")
    except Exception as e:
        logger.error(f"Error sending typing action: {e}")

def format_work_summary(entries: List[Dict[str, Any]], period_type: str = None, period_number: int = None) -> str:
    """
    Format a list of work entries as a readable summary.
    
    Args:
        entries: List of work entry dictionaries
        period_type: Type of period ('day', 'week', 'month')
        period_number: Number identifier for period (day of month, week number, month number)
        
    Returns:
        Formatted summary text
    """
    if not entries:
        return "Geen werkregistraties gevonden."
    
    # Calculate totals
    total_hours = 0
    billable_hours = 0
    unbillable_hours = 0
    
    for entry in entries:
        # Try to convert billable hours
        try:
            hours_str = entry.get("Hours", "0")
            if hours_str and not isinstance(hours_str, bool):
                # Replace comma with dot for Dutch number format
                hours_str = str(hours_str).replace(',', '.')
                billable_hour = float(hours_str)
                billable_hours += billable_hour
                total_hours += billable_hour
        except (ValueError, TypeError):
            # Skip entries with invalid hour values
            pass
            
        # Try to convert unbillable hours
        try:
            unbill_str = entry.get("Unbillable Hours", "0")
            if unbill_str and not isinstance(unbill_str, bool):
                # Replace comma with dot for Dutch number format
                unbill_str = str(unbill_str).replace(',', '.')
                unbill_hour = float(unbill_str)
                unbillable_hours += unbill_hour
                total_hours += unbill_hour
        except (ValueError, TypeError):
            # Skip entries with invalid hour values
            pass
    
    # Format header based on period
    header = "📊 Gewerkte uren"
    
    if period_type == 'month':
        months = ["januari", "februari", "maart", "april", "mei", "juni", 
                 "juli", "augustus", "september", "oktober", "november", "december"]
        if 1 <= period_number <= 12:
            month_name = months[period_number - 1]
            current_year = datetime.now().year
            header = f"📋 **Gewerkte uren {month_name.capitalize()} {current_year}**"
    elif period_type == 'week':
        header = f"📋 **Gewerkte uren Week {period_number}**"
    elif period_type == 'day':
        # For a single day, we'll still use the template but with fewer entries
        if entries and 'Date' in entries[0]:
            date_str = entries[0].get('Date', '')
            try:
                if '-' in date_str:
                    day, month, year = date_str.split('-')
                    months = ["januari", "februari", "maart", "april", "mei", "juni", 
                             "juli", "augustus", "september", "oktober", "november", "december"]
                    if 1 <= int(month) <= 12:
                        month_name = months[int(month) - 1]
                        header = f"📋 **Gewerkte uren {int(day)} {month_name} {year}**"
            except:
                pass
    
    # Generate summary text
    summary = f"{header}\n"
    summary += f"*Totaal: {total_hours:.0f} | Declarabel: {billable_hours:.0f} | Niet-declarabel: {unbillable_hours:.0f}*\n\n"
    
    # Group entries by date and then by client
    date_client_entries = defaultdict(lambda: defaultdict(list))
    
    for entry in entries:
        date = entry.get('Date', 'Unknown Date')
        client = entry.get('Client', 'Unknown')
        
        # Skip entries with no hours
        try:
            billable = float(entry.get('Hours', 0) or 0)
            unbillable = float(entry.get('Unbillable Hours', 0) or 0)
            if billable == 0 and unbillable == 0:
                continue
        except:
            continue
            
        date_client_entries[date][client].append(entry)
    
    # Sort dates (most recent first if in DD-MM-YYYY format)
    sorted_dates = sorted(date_client_entries.keys(), 
                         key=lambda d: d.split('-')[::-1] if '-' in d and len(d.split('-')) == 3 else d, 
                         reverse=True)
    
    # For each date
    for date in sorted_dates:
        # Format date header
        date_header = date
        
        # Try to format date more nicely if it's in DD-MM-YYYY format
        if '-' in date:
            try:
                day, month, year = date.split('-')
                months = ["januari", "februari", "maart", "april", "mei", "juni", 
                         "juli", "augustus", "september", "oktober", "november", "december"]
                weekdays = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
                
                # Convert to date object to get weekday
                date_obj = datetime(int(year), int(month), int(day))
                weekday = weekdays[date_obj.weekday()]
                
                date_header = f"{weekday} {int(day)} {months[int(month)-1]} {year}"
            except (ValueError, IndexError):
                # Keep original if parsing fails
                pass
        
        summary += f"📅 **{date_header}**\n"
        
        # Sort clients by their code (alphabetically)
        for client in sorted(date_client_entries[date].keys()):
            summary += f"- {client}\n"
            
            # Group by description and sum hours
            description_hours = defaultdict(float)
            for entry in date_client_entries[date][client]:
                description = entry.get('Description', '').strip()
                if not description:
                    description = "(geen beschrijving)"
                
                billable = float(entry.get('Hours', 0) or 0)
                unbillable = float(entry.get('Unbillable Hours', 0) or 0)
                total_entry_hours = billable + unbillable
                
                if total_entry_hours > 0:
                    description_hours[description] += total_entry_hours
            
            # Add each description with hours
            for description, hours in description_hours.items():
                if hours > 0:
                    summary += f"    - {description} ({hours:.0f}u)\n"
                else:
                    summary += f"    - {description}\n"
        
        summary += "\n"
    
    return summary.strip()