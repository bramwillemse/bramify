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
        # American format: MM/DD/YYYY
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
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
                elif pattern == date_patterns[2]:  # American format
                    month, day, year = map(int, match.groups())
                    return f"{year}-{month:02d}-{day:02d}"
                elif pattern == date_patterns[3]:  # Short year
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
    
    if period in ["today", "day"]:
        return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
    if period in ["yesterday"]:
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
    
    if period in ["this week", "week"]:
        # Get the start of the week (Monday)
        start = today - timedelta(days=today.weekday())
        end = today
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    if period in ["last week"]:
        # Get the start of last week (Monday)
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    if period in ["this month", "month"]:
        # Get the start of the current month
        start = today.replace(day=1)
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    
    if period in ["last month"]:
        # Get the start of the last month
        if today.month == 1:
            start = today.replace(year=today.year - 1, month=12, day=1)
        else:
            start = today.replace(month=today.month - 1, day=1)
        
        # Get the end of the last month
        if today.month == 1:
            end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            # Last day of previous month
            end = today.replace(day=1) - timedelta(days=1)
            
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    # Default to today
    return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")