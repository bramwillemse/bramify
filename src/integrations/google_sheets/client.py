"""Google Sheets API integration for storing work hours data."""

import os
import json
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class GoogleSheetsClient:
    """Client for interacting with the Google Sheets API."""
    
    def __init__(self):
        """Initialize the Google Sheets client with credentials."""
        # Get configuration from environment variables
        self.credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        
        if not self.credentials_file or not self.spreadsheet_id:
            raise ValueError("Google Sheets configuration not complete. Check environment variables.")
        
        # Configure the sheets client
        self._setup_sheets_client()
        
        # Define sheet names and structure
        self.work_hours_sheet = "WorkHours"
        self._ensure_sheet_exists()
        
        logger.info("Google Sheets client initialized")
    
    def _setup_sheets_client(self):
        """Set up the Google Sheets API client."""
        try:
            # Load credentials
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=credentials)
            self.sheets = self.service.spreadsheets()
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets client: {e}")
            raise
    
    def _ensure_sheet_exists(self):
        """Ensure that the required sheets exist, creating them if necessary."""
        try:
            # Get the spreadsheet metadata
            metadata = self.sheets.get(spreadsheetId=self.spreadsheet_id).execute()
            
            # Check if our sheets exist
            existing_sheets = [sheet['properties']['title'] for sheet in metadata['sheets']]
            
            # Create the work hours sheet if it doesn't exist
            if self.work_hours_sheet not in existing_sheets:
                self._create_work_hours_sheet()
                
        except Exception as e:
            logger.error(f"Error ensuring sheets exist: {e}")
    
    def _create_work_hours_sheet(self):
        """Create the work hours tracking sheet with headers."""
        try:
            # Create the sheet
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': self.work_hours_sheet
                        }
                    }
                }]
            }
            self.sheets.batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Add headers
            headers = [
                "Date", "Client", "Project", "Hours", "Billable", 
                "Description", "Timestamp"
            ]
            
            self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.work_hours_sheet}!A1:G1",
                valueInputOption="RAW",
                body={"values": [headers]}
            ).execute()
            
            logger.info(f"Created {self.work_hours_sheet} sheet with headers")
            
        except Exception as e:
            logger.error(f"Error creating work hours sheet: {e}")
    
    def add_work_entry(self, work_data: Dict[str, Any]) -> bool:
        """
        Add a work entry to the spreadsheet.
        
        Args:
            work_data: Dictionary containing work entry information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare the data row
            row = [
                work_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                work_data.get("client", ""),
                work_data.get("project", ""),
                work_data.get("hours", 0),
                "Yes" if work_data.get("billable", True) else "No",
                work_data.get("description", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            
            # Find the next empty row
            result = self.sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.work_hours_sheet}!A:A"
            ).execute()
            
            values = result.get('values', [])
            next_row = len(values) + 1
            
            # Add the data
            self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.work_hours_sheet}!A{next_row}:G{next_row}",
                valueInputOption="USER_ENTERED",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Added work entry for {work_data.get('client')} to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error adding work entry to Google Sheets: {e}")
            return False
    
    def get_work_entries(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Get work entries from the spreadsheet, optionally filtered by date range.
        
        Args:
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            
        Returns:
            List of work entry dictionaries
        """
        try:
            # Get all data from the sheet
            result = self.sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.work_hours_sheet}!A:G"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # Extract headers and data
            headers = values[0]
            data_rows = values[1:]
            
            # Convert to list of dictionaries
            entries = []
            for row in data_rows:
                # Pad row with empty strings if it's shorter than headers
                padded_row = row + [''] * (len(headers) - len(row))
                
                entry = dict(zip(headers, padded_row))
                
                # Filter by date range if provided
                entry_date = entry.get('Date', '')
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                    
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting work entries: {e}")
            return []