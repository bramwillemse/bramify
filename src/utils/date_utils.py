"""Date and time utilities for Bramify."""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

def parse_date_text(text: str) -> Optional[str]:
    """
    Extract a date from natural language text.
    
    Args:
        text: Natural language text containing date references
        
    Returns:
        Date string in YYYY-MM-DD format or None if no date found
    """
    # Current date for reference
    today = datetime.now().date()
    
    # Check for common date expressions
    text_lower = text.lower()
    
    if "today" in text_lower:
        return today.strftime("%Y-%m-%d")
    
    if "yesterday" in text_lower:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if "tomorrow" in text_lower:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Check for day of week
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days):
        if day in text_lower:
            # Calculate the date of the most recent occurrence of this day
            today_weekday = today.weekday()
            days_diff = (today_weekday - i) % 7
            
            # If "last" appears before the day name, go back one more week
            if re.search(r'last\s+' + day, text_lower):
                days_diff += 7
                
            target_date = today - timedelta(days=days_diff)
            return target_date.strftime("%Y-%m-%d")
    
    # Check for dates in common formats
    date_patterns = [
        # ISO format: YYYY-MM-DD
        r'(\d{4}-\d{2}-\d{2})',
        # European format: DD-MM-YYYY or DD/MM/YYYY
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        # Short year: DD-MM-YY or DD/MM/YY
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if pattern == date_patterns[0]:  # ISO format
                    return match.group(1)
                elif pattern == date_patterns[1]:  # European format
                    day, month, year = map(int, match.groups())
                    return f"{year}-{month:02d}-{day:02d}"
                elif pattern == date_patterns[2]:  # Short year
                    day, month, year = map(int, match.groups())
                    # Assume 20xx for years less than 50, 19xx otherwise
                    year = 2000 + year if year < 50 else 1900 + year
                    return f"{year}-{month:02d}-{day:02d}"
            except ValueError:
                # Invalid date components
                continue
    
    # No date found
    return None

def get_date_range_for_period(period: str) -> Tuple[str, str]:
    """
    Get start and end dates for common time periods.
    
    Args:
        period: String like 'today', 'yesterday', 'this week', 'last month', etc.
        
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now().date()
    current_year = today.year
    current_month = today.month
    current_day = today.day
    
    # For easier logging
    from loguru import logger
    
    if period in ["today", "day"]:
        logger.info(f"Date range for today: {today.strftime('%Y-%m-%d')}")
        return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
    if period in ["yesterday"]:
        yesterday = today - timedelta(days=1)
        logger.info(f"Date range for yesterday: {yesterday.strftime('%Y-%m-%d')}")
        return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
    
    if period in ["this week", "week"]:
        # Get the start of the week (Monday)
        start = today - timedelta(days=today.weekday())
        end = today
        logger.info(f"Date range for this week: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    if period in ["last week"]:
        # Get the start of last week (Monday)
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        logger.info(f"Date range for last week: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    if period in ["this month", "month"]:
        # Get the start of the current month, ensuring current year
        start = today.replace(day=1)
        logger.info(f"Date range for this month (original): {start.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
        
        # Explicitly enforce current year and month
        start_str = f"{current_year}-{current_month:02d}-01"
        end_str = f"{current_year}-{current_month:02d}-{current_day:02d}"
        logger.info(f"Date range for this month (enforced): {start_str} to {end_str}")
        return start_str, end_str
    
    if period in ["last month"]:
        # Get the start of the last month
        if today.month == 1:
            start = today.replace(year=today.year - 1, month=12, day=1)
            end_month = 12
            end_year = today.year - 1
        else:
            start = today.replace(month=today.month - 1, day=1)
            end_month = today.month - 1
            end_year = today.year
        
        # Get the end of the last month
        if today.month == 1:
            end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            # Last day of previous month
            end = today.replace(day=1) - timedelta(days=1)
        
        logger.info(f"Date range for last month (original): {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
        
        # Explicitly enforce correct year and month
        start_str = f"{end_year}-{end_month:02d}-01"
        end_str = f"{end_year}-{end_month:02d}-{end.day:02d}"
        logger.info(f"Date range for last month (enforced): {start_str} to {end_str}")
        return start_str, end_str
    
    # Default to today
    logger.info(f"Default date range (today): {today.strftime('%Y-%m-%d')}")
    return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")