#!/usr/bin/env python3
"""
Test script to verify date format detection in Google Sheets template.
This will test if the code can find dates in various formats.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Import our GoogleSheetsClient
from src.integrations.google_sheets.client import GoogleSheetsClient

def add_work_entry_with_date(sheets_client, date_str, client="Test client"):
    """Add a work entry with the specified date."""
    work_data = {
        "date": date_str,
        "client": client,
        "description": f"Test entry with date: {date_str}",
        "hours": 1,
        "billable": True
    }
    
    # Always use test mode for safety
    success = sheets_client.add_work_entry(work_data, test_mode=True)
    return success

def test_date_formats():
    """Test the date format detection with various formats."""
    # Load environment variables
    load_dotenv()
    
    # Create the sheets client
    try:
        sheets_client = GoogleSheetsClient()
        print("✅ Successfully initialized GoogleSheetsClient")
    except Exception as e:
        print(f"❌ Failed to initialize GoogleSheetsClient: {e}")
        return
    
    # Access internal method to test date row finding directly
    find_date_row = sheets_client._find_date_row
    target_sheet = sheets_client.test_sheet
    
    # Test standard format (DD-MM-YYYY)
    standard_date = "26-03-2025"
    row = find_date_row(target_sheet, standard_date)
    print(f"\nStandard date {standard_date}: {'Found' if row > 0 else 'Not found'} at row {row}")
    
    # Test English format (Wednesday 26 March 2025)
    english_date = datetime(2025, 3, 26).strftime("%A %d %B %Y")
    row = find_date_row(target_sheet, "26-03-2025")  # We pass standard format but it should find English format
    print(f"English date ({english_date}): {'Found' if row > 0 else 'Not found'} at row {row}")
    
    # Test Dutch format (Woensdag 26 maart 2025)
    date_obj = datetime(2025, 3, 26)
    weekday = date_obj.strftime("%A")
    day = date_obj.day
    month = date_obj.strftime("%B")
    dutch_weekdays = {
        "Monday": "Maandag",
        "Tuesday": "Dinsdag",
        "Wednesday": "Woensdag",
        "Thursday": "Donderdag",
        "Friday": "Vrijdag",
        "Saturday": "Zaterdag",
        "Sunday": "Zondag"
    }
    dutch_months = {
        "January": "januari",
        "February": "februari",
        "March": "maart",
        "April": "april",
        "May": "mei",
        "June": "juni",
        "July": "juli",
        "August": "augustus",
        "September": "september",
        "October": "oktober",
        "November": "november",
        "December": "december"
    }
    dutch_date = f"{dutch_weekdays[weekday]} {day} {dutch_months[month]} 2025"
    row = find_date_row(target_sheet, "26-03-2025")  # We pass standard format but it should find Dutch format
    print(f"Dutch date ({dutch_date}): {'Found' if row > 0 else 'Not found'} at row {row}")
    
    # Test adding entries with different date formats
    print("\nTesting adding entries...")
    
    # Create a template row with just day and month in Dutch
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_day = tomorrow.day
    tomorrow_month = dutch_months[tomorrow.strftime("%B")]
    template_date = f"{tomorrow_day} {tomorrow_month}"
    
    # Add test entry to test sheet using the template date
    success = sheets_client.sheets.spreadsheets().values().update(
        spreadsheetId=sheets_client.spreadsheet_id,
        range=f"{target_sheet}!A15",
        valueInputOption="USER_ENTERED",
        body={"values": [[template_date]]}
    ).execute()
    
    print(f"Added template date row: {template_date} at row 15")
    
    # Now try to add work entry with standard date format
    tomorrow_str = tomorrow.strftime("%d-%m-%Y")
    success = add_work_entry_with_date(sheets_client, tomorrow_str)
    print(f"Add entry with standard date {tomorrow_str}: {'✅ Success' if success else '❌ Failed'}")
    
    print("\nTest completed. Please check your test sheet to verify the results.")

if __name__ == "__main__":
    # Set up logging to console
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    test_date_formats()