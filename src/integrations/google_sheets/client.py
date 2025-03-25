"""Google Sheets API integration for storing work hours data."""

import os
import json
import pickle
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from loguru import logger

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleSheetsClient:
    """Client for interacting with the Google Sheets API."""
    
    def __init__(self):
        """Initialize the Google Sheets client with credentials."""
        # Get configuration from environment variables
        self.credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
        self.token_file = os.getenv("GOOGLE_SHEETS_TOKEN_FILE", "config/token.json")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        
        if not self.credentials_file or not self.spreadsheet_id:
            raise ValueError("Google Sheets configuration not complete. Check environment variables.")
        
        # Configure the sheets client
        self._setup_sheets_client()
        
        # Get the current year for the sheet name
        self.current_year = str(datetime.now().year)
        self.test_sheet = f"Test-{self.current_year}"
        self.work_hours_sheet = self.current_year
        
        # Attempt to detect existing sheet structure
        self._detect_sheet_structure()
        
        logger.info("Google Sheets client initialized")
    
    def _setup_sheets_client(self):
        """Set up the Google Sheets API client using OAuth."""
        try:
            credentials = None
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            
            # Check if we have a token file
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as token:
                    try:
                        creds_data = json.load(token)
                        credentials = Credentials.from_authorized_user_info(creds_data, scopes)
                    except Exception as e:
                        logger.error(f"Error loading token file: {e}")
            
            # If credentials don't exist or are invalid, get new ones
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, scopes)
                    credentials = flow.run_local_server(port=0)
                
                # Save the credentials
                token_dir = os.path.dirname(self.token_file)
                os.makedirs(token_dir, exist_ok=True)
                with open(self.token_file, 'w') as token:
                    token.write(credentials.to_json())
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=credentials)
            self.sheets = self.service.spreadsheets()
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets client: {e}")
            raise
    
    def _detect_sheet_structure(self):
        """Detect the existing sheet structure and adapt accordingly."""
        try:
            # Get spreadsheet metadata
            metadata = self.sheets.get(spreadsheetId=self.spreadsheet_id).execute()
            existing_sheets = [sheet['properties']['title'] for sheet in metadata['sheets']]
            
            logger.info(f"Found sheets: {existing_sheets}")
            
            # Check if current year sheet exists
            self.sheet_exists = self.work_hours_sheet in existing_sheets
            
            # Create test sheet if it doesn't exist
            if self.test_sheet not in existing_sheets:
                self._create_test_sheet()
            
            # If current year sheet exists, detect its structure
            if self.sheet_exists:
                self._detect_columns()
            else:
                logger.warning(f"Sheet for current year ({self.work_hours_sheet}) not found")
                # Use default column mapping
                self.column_mapping = {
                    "date": 0,         # A
                    "client": 1,       # B
                    "project": 2,      # C
                    "hours": 3,        # D
                    "billable": 4,     # E
                    "description": 5,  # F
                }
                
        except Exception as e:
            logger.error(f"Error detecting sheet structure: {e}")
            # Use default column mapping as fallback
            self.column_mapping = {
                "date": 0,
                "client": 1,
                "project": 2,
                "hours": 3,
                "billable": 4,
                "description": 5,
            }
    
    def _detect_columns(self):
        """Detect column headers in the current year sheet."""
        try:
            # Get the first row (headers)
            result = self.sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.work_hours_sheet}!1:1"
            ).execute()
            
            if 'values' not in result:
                logger.warning(f"No headers found in {self.work_hours_sheet} sheet")
                return
                
            headers = result['values'][0]
            logger.info(f"Detected headers: {headers}")
            
            # Initialize column mapping with fallback values
            self.column_mapping = {
                "date": 0,
                "client": 1,
                "project": 2,
                "hours": 3,
                "billable": 4,
                "description": 5,
            }
            
            # Map common header names to our fields
            header_mappings = {
                "date": ["date", "datum", "dag", "day"],
                "client": ["client", "klant", "klanten", "customer", "opdrachtgever"],
                "project": ["project", "opdracht", "task"],
                "hours": ["hours", "uren", "tijd", "time", "duur", "duration"],
                "billable": ["billable", "facturabel", "declarabel", "facturable"],
                "description": ["description", "beschrijving", "omschrijving", "notes", "notities"]
            }
            
            # Try to match headers to our fields
            for field, possible_headers in header_mappings.items():
                for i, header in enumerate(headers):
                    header_lower = header.lower()
                    if any(possible_name in header_lower for possible_name in possible_headers):
                        self.column_mapping[field] = i
                        break
            
            logger.info(f"Column mapping: {self.column_mapping}")
            
        except Exception as e:
            logger.error(f"Error detecting column headers: {e}")
    
    def _create_test_sheet(self):
        """Create a test sheet based on the current year sheet structure."""
        try:
            # Create the test sheet
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': self.test_sheet
                        }
                    }
                }]
            }
            self.sheets.batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # If the current year sheet exists, copy its headers
            if self.sheet_exists:
                # Get the first row (headers)
                result = self.sheets.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.work_hours_sheet}!1:1"
                ).execute()
                
                if 'values' in result:
                    headers = result['values'][0]
                    # Copy headers to test sheet
                    self.sheets.values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{self.test_sheet}!1:1",
                        valueInputOption="RAW",
                        body={"values": [headers]}
                    ).execute()
                    logger.info(f"Copied headers from {self.work_hours_sheet} to {self.test_sheet}")
                    return
            
            # If no current year sheet or headers, create default headers
            headers = [
                "Datum", "Klant", "Project", "Uren", "Facturabel", 
                "Beschrijving", "Tijdstip Ingevoerd"
            ]
            
            self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.test_sheet}!A1:G1",
                valueInputOption="RAW",
                body={"values": [headers]}
            ).execute()
            
            logger.info(f"Created {self.test_sheet} sheet with default headers")
            
        except Exception as e:
            logger.error(f"Error creating test sheet: {e}")
    
    def add_work_entry(self, work_data: Dict[str, Any], test_mode: bool = False) -> bool:
        """
        Add a work entry to the spreadsheet.
        
        Args:
            work_data: Dictionary containing work entry information
            test_mode: If True, add to test sheet instead of current year sheet
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Select the appropriate sheet
            target_sheet = self.test_sheet if test_mode else self.work_hours_sheet
            
            # If the target sheet doesn't exist and we're not in test mode, use test mode
            if not self.sheet_exists and not test_mode:
                logger.warning(f"Sheet {self.work_hours_sheet} doesn't exist, using test sheet")
                target_sheet = self.test_sheet
                test_mode = True
            
            # Convert work_data to a row based on the column mapping
            row = [""] * (max(self.column_mapping.values()) + 2)  # +2 for potential timestamp and safety
            
            # Fill in the data
            row[self.column_mapping["date"]] = work_data.get("date", datetime.now().strftime("%d-%m-%Y"))
            row[self.column_mapping["client"]] = work_data.get("client", "")
            row[self.column_mapping["project"]] = work_data.get("project", "")
            row[self.column_mapping["hours"]] = work_data.get("hours", 0)
            
            # Handle billable field - adapt to different formats
            billable_value = work_data.get("billable", True)
            if isinstance(billable_value, bool):
                row[self.column_mapping["billable"]] = "Ja" if billable_value else "Nee"
            else:
                row[self.column_mapping["billable"]] = billable_value
                
            row[self.column_mapping["description"]] = work_data.get("description", "")
            
            # Add timestamp if there's room
            timestamp_col = max(self.column_mapping.values()) + 1
            row[timestamp_col] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            # Find the next empty row
            result = self.sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{target_sheet}!A:A"
            ).execute()
            
            values = result.get('values', [])
            next_row = len(values) + 1
            
            # Add the data
            self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{target_sheet}!A{next_row}:{chr(65 + len(row))}{next_row}",
                valueInputOption="USER_ENTERED",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Added work entry for {work_data.get('client')} to {target_sheet}")
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