"""Utilities for Telegram bot integration."""

from typing import Dict, Any, List, Optional
from telegram import Update
from loguru import logger

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
    
    # Debugging information
    from loguru import logger
    logger.info(f"Formatting summary for {len(entries)} entries")
    
    # Determine period emoji and text
    period_emoji = "📊"
    period_info = ""
    
    if period_type:
        if period_type == 'day':
            period_emoji = "📅"
            if period_number:
                # Gebruik dagnaam in plaats van nummer
                from datetime import datetime
                # Dagen in het Nederlands
                days = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
                
                # Bepaal welke dag het is (voor vandaag, gisteren, etc.)
                try:
                    # Maak een datetime met het huidige jaar, maand en de opgegeven dag
                    today = datetime.now()
                    date_with_day = datetime(today.year, today.month, period_number)
                    # Weekdag is 0-6 (maandag=0, zondag=6)
                    weekday = date_with_day.weekday()
                    day_name = days[weekday]
                    period_info = f" - {day_name}"
                except:
                    # Bij fouten, val terug op dagnummer
                    period_info = f" - Dag {period_number}"
        elif period_type == 'week':
            period_emoji = "📆"
            if period_number:
                period_info = f" - Week {period_number}"
        elif period_type == 'month':
            period_emoji = "📋"
            months = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 
                     'juli', 'augustus', 'september', 'oktober', 'november', 'december']
            if period_number and 1 <= period_number <= 12:
                period_info = f" - {months[period_number-1].capitalize()}"
    
    # Deduplicate entries based on client/date/description
    deduped_entries = []
    seen_entries = set()
    for entry in entries:
        # Create a key for deduplication
        client = entry.get("Client", "")
        date = entry.get("Date", "")
        desc = entry.get("Description", "")
        key = f"{client}|{date}|{desc}"
        
        if key not in seen_entries:
            seen_entries.add(key)
            deduped_entries.append(entry)
    
    if len(deduped_entries) < len(entries):
        logger.info(f"Removed {len(entries) - len(deduped_entries)} duplicate entries")
    
    entries = deduped_entries
    
    # Calculate total hours
    total_hours = 0
    billable_hours = 0
    unbillable_hours = 0
    
    for entry in entries:
        # Try to convert billable hours first
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
    
    # Group by client and description
    client_descriptions = {}
    for entry in entries:
        client = entry.get("Client", "Ongespecificeerd")
        description = entry.get("Description", "Ongespecificeerd")
        
        # Skip entirely empty descriptions
        if not description or description.strip() == "":
            continue
            
        # Parse hours (billable + unbillable)
        try:
            billable_str = entry.get("Hours", "0")
            unbillable_str = entry.get("Unbillable Hours", "0")
            
            billable_val = 0
            if billable_str and not isinstance(billable_str, bool):
                billable_str = str(billable_str).replace(',', '.')
                try:
                    billable_val = float(billable_str)
                except (ValueError, TypeError):
                    billable_val = 0
                
            unbillable_val = 0
            if unbillable_str and not isinstance(unbillable_str, bool):
                unbillable_str = str(unbillable_str).replace(',', '.')
                try:
                    unbillable_val = float(unbillable_str)
                except (ValueError, TypeError):
                    unbillable_val = 0
                
            # Skip entries met 0 uren (billable + unbillable)
            if billable_val == 0 and unbillable_val == 0:
                continue
                
            hours = billable_val + unbillable_val
        except Exception as e:
            from loguru import logger
            logger.error(f"Error parsing hours in format_work_summary: {e}")
            continue
        
        if client not in client_descriptions:
            client_descriptions[client] = {}
        
        # Don't include date in description anymore
        # Add prefix for unbillable hours if needed
        if unbillable_val > 0 and billable_val == 0:
            desc_key = f"{description} (niet-factureerbaar)"
        else:
            desc_key = description
        
        if desc_key not in client_descriptions[client]:
            client_descriptions[client][desc_key] = 0
            
        client_descriptions[client][desc_key] += hours
    
    # Format the summary
    summary = f"{period_emoji} *Werk Overzicht{period_info}*\n\n"
    summary += f"Totale Uren: {total_hours:.1f}\n"
    summary += f"Factureerbare Uren: {billable_hours:.1f}\n"
    summary += f"Niet-Factureerbare Uren: {unbillable_hours:.1f}\n\n"
    
    # Get only clients with hours > 0
    client_items = [(client, desc) for client, desc in client_descriptions.items() 
                   if sum(desc.values()) > 0]
    
    # Sort by hours (highest first)
    client_items = sorted(client_items, 
                          key=lambda x: sum(x[1].values()), 
                          reverse=True)
    
    # Show all clients with hours
    for client, descriptions in client_items:
        client_total = sum(descriptions.values())
        
        # Skip clients with 0 hours (shouldn't happen due to filtering above, but just in case)
        if client_total == 0:
            continue
            
        summary += f"*{client}*: {client_total:.1f} uren\n"
        
        # Sort descriptions by hours (highest first) and limit to top 3
        desc_items = sorted(descriptions.items(), key=lambda x: x[1], reverse=True)
        
        # Only show descriptions with hours > 0
        desc_items = [(desc, hours) for desc, hours in desc_items if hours > 0]
        
        # Show top 3
        for description, hours in desc_items[:3]:
            # Truncate description if it's too long
            short_desc = description[:40] + "..." if len(description) > 40 else description
            summary += f"  - {short_desc}: {hours:.1f} uren\n"
        
        # Add ellipsis if there are more descriptions
        if len(desc_items) > 3:
            summary += f"  - ... en {len(desc_items) - 3} meer activiteiten\n"
        
        summary += "\n"
    
    return summary