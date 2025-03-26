#!/usr/bin/env python3
"""
Test script to verify Google Sheets template date handling.
This will add test entries to your test sheet using the new template-aware code.
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

def test_template_handling():
    """Test the template handling with multiple date formats and clients."""
    # Load environment variables from the test file
    load_dotenv(".env.test")
    
    # Print the loaded spreadsheet ID
    print(f"Using spreadsheet ID: {os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID')}")
    
    # Create the sheets client
    sheets_client = GoogleSheetsClient()
    
    # Get today and yesterday's dates
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # Format dates in DD-MM-YYYY format
    today_str = today.strftime("%d-%m-%Y")
    yesterday_str = yesterday.strftime("%d-%m-%Y")
    
    print(f"Testing with dates: {today_str} and {yesterday_str}")
    
    # Test cases with different clients and dates
    test_cases = [
        {
            "date": today_str,
            "client": "Client A",
            "description": "Test entry for today - Client A",
            "hours": 2.5,
            "billable": True
        },
        {
            "date": today_str,
            "client": "Client B",
            "description": "Test entry for today - Client B",
            "hours": 1.5,
            "billable": True
        },
        {
            "date": yesterday_str,
            "client": "Client A",
            "description": "Test entry for yesterday - Client A",
            "hours": 3,
            "billable": False
        }
    ]
    
    # Add each test case to the test sheet
    for i, case in enumerate(test_cases):
        print(f"\nAdding test case {i+1}: {case['client']} on {case['date']}")
        success = sheets_client.add_work_entry(case, test_mode=True)
        
        if success:
            print(f"Successfully added test case {i+1}")
        else:
            print(f"Failed to add test case {i+1}")
    
    print("\nTest completed. Please check your test sheet to verify the results.")

if __name__ == "__main__":
    test_template_handling()