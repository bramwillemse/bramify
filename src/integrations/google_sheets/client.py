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
from google.oauth2 import service_account
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
        """Set up the Google Sheets API client using OAuth or Service Account."""
        try:
            credentials = None
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            
            # Check if we have a token file
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as token:
                    try:
                        creds_data = json.load(token)
                        
                        # Check if this is a service account reference
                        if creds_data.get('type') == 'service_account_reference':
                            # Use service account instead of OAuth
                            service_account_file = creds_data.get('service_account_file')
                            logger.info(f"Using service account from {service_account_file}")
                            
                            if not os.path.exists(service_account_file):
                                logger.error(f"Service account file not found at {service_account_file}")
                                raise ValueError(f"Service account file not found at {service_account_file}")
                            
                            from google.oauth2 import service_account
                            credentials = service_account.Credentials.from_service_account_file(
                                service_account_file, scopes=scopes
                            )
                            logger.info("Successfully loaded service account credentials")
                        else:
                            # Regular OAuth credentials
                            credentials = Credentials.from_authorized_user_info(creds_data, scopes)
                            logger.info("Successfully loaded OAuth token")
                    except Exception as e:
                        logger.error(f"Error loading token file: {e}")
            else:
                logger.error(f"Token file not found at {self.token_file}")
            
            # If using OAuth and credentials need refresh
            if credentials and not isinstance(credentials, service_account.Credentials) and not credentials.valid:
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    logger.info("OAuth credentials refreshed")
                else:
                    logger.error("Invalid credentials and can't refresh")
            
            # If no credentials, try service account file directly
            if not credentials and os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    try:
                        creds_data = json.load(f)
                        logger.info(f"Trying service account at {self.credentials_file}")
                        
                        # If this is a service account credentials file
                        if creds_data.get('type') == 'service_account':
                            credentials = service_account.Credentials.from_service_account_file(
                                self.credentials_file, scopes=scopes
                            )
                            logger.info("Switched to service account authentication")
                        else:
                            logger.warning("Credentials file is not a service account JSON")
                    except Exception as e:
                        logger.error(f"Error reading credentials file: {e}")
            
            # If still no credentials, prompt for OAuth
            if not credentials:
                logger.error("No valid credentials found. Please authenticate manually.")
                raise ValueError("Authentication required")
            
            # Create the Sheets API service
            self.sheets = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets client: {e}")
            raise
    
    def _detect_sheet_structure(self):
        """Detect existing sheets and column structure."""
        try:
            # Get all sheet names
            try:
                sheet_metadata = self.sheets.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()
            except Exception as e:
                logger.error(f"Error getting spreadsheet metadata: {e}")
                sheet_metadata = {"sheets": []}
            
            sheets = [sheet['properties']['title'] for sheet in sheet_metadata.get('sheets', [])]
            logger.info(f"Found sheets: {sheets}")
            
            # Ensure the needed sheets exist
            if self.work_hours_sheet not in sheets:
                logger.warning(f"Sheet '{self.work_hours_sheet}' not found. Will create it if needed.")
            
            # Create test sheet if it doesn't exist
            if self.test_sheet not in sheets:
                logger.info(f"Creating test sheet '{self.test_sheet}'")
                try:
                    self.sheets.spreadsheets().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body={
                            "requests": [
                                {
                                    "addSheet": {
                                        "properties": {
                                            "title": self.test_sheet
                                        }
                                    }
                                }
                            ]
                        }
                    ).execute()
                except Exception as e:
                    logger.error(f"Error creating test sheet: {e}")
                
                # Copy headers from work sheet if it exists
                if self.work_hours_sheet in sheets:
                    # Get headers from work sheet
                    try:
                        result = self.sheets.spreadsheets().values().get(
                            spreadsheetId=self.spreadsheet_id,
                            range=f"{self.work_hours_sheet}!A1:G1"
                        ).execute()
                    except Exception as e:
                        logger.error(f"Error getting headers from work sheet: {e}")
                        result = {"values": [['Datum', 'Klant', 'Beschrijving', 'Uren', 'Uren onbetaald', 'Omzet']]}
                    
                    headers = result.get('values', [['Datum', 'Klant', 'Beschrijving', 'Uren', 'Uren onbetaald', 'Omzet']])
                    
                    # Copy headers to test sheet
                    try:
                        self.sheets.spreadsheets().values().update(
                            spreadsheetId=self.spreadsheet_id,
                            range=f"{self.test_sheet}!A1:G1",
                            valueInputOption="RAW",
                            body={
                                "values": headers
                            }
                        ).execute()
                    except Exception as e:
                        logger.error(f"Error copying headers to test sheet: {e}")
            
            # Detect column structure
            self._detect_columns()
            
        except Exception as e:
            logger.error(f"Error detecting sheet structure: {e}")
    
    def _detect_columns(self):
        """Detect column mapping in the work hours sheet."""
        try:
            # Try to get headers from the current year sheet
            try:
                result = self.sheets.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.work_hours_sheet}!1:1"
                ).execute()
            except Exception as e:
                logger.error(f"Error getting headers: {e}")
                return
            
            values = result.get('values', [])
            if not values:
                logger.warning(f"No headers found in sheet {self.work_hours_sheet}")
                return
            
            headers = values[0]
            logger.info(f"Detected headers: {headers}")
            
            # Default column mapping (expected structure)
            # 0 = Date, 1 = Client, 2 = Description, 3 = Hours, 4 = Unbillable hours, 5 = Revenue
            self.column_mapping = {
                'date': 0,
                'client': 1,
                'description': 2,
                'hours': 3,
                'unbillable_hours': 4,
                'revenue': 5
            }
            
            # Try to map headers
            for i, header in enumerate(headers):
                header_lower = header.lower()
                
                if 'datum' in header_lower or 'date' in header_lower:
                    self.column_mapping['date'] = i
                elif 'klant' in header_lower or 'client' in header_lower:
                    self.column_mapping['client'] = i
                elif 'beschrijving' in header_lower or 'description' in header_lower:
                    self.column_mapping['description'] = i
                elif 'uren' in header_lower and 'onbetaald' not in header_lower and 'unbillable' not in header_lower:
                    self.column_mapping['hours'] = i
                elif ('onbetaald' in header_lower or 'unbillable' in header_lower) and 'uren' in header_lower:
                    self.column_mapping['unbillable_hours'] = i
                elif 'omzet' in header_lower or 'revenue' in header_lower:
                    self.column_mapping['revenue'] = i
            
            logger.info(f"Column mapping: {self.column_mapping}")
            
        except Exception as e:
            logger.error(f"Error detecting columns: {e}")
    
    def add_work_entry(self, work_data: Dict[str, Any], test_mode: bool = True) -> bool:
        """
        Add a work entry to the spreadsheet.
        
        Args:
            work_data: Dictionary containing work data
            test_mode: Whether to add to the test sheet instead of the real one
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine target sheet
            target_sheet = self.test_sheet if test_mode else self.work_hours_sheet
            
            # Format the data for insertion
            row = [""] * (max(self.column_mapping.values()) + 2)  # +2 for possible timestamp column
            
            # Add date
            row[self.column_mapping["date"]] = work_data.get("date", datetime.now().strftime("%d-%m-%Y"))
            
            # Add client
            row[self.column_mapping["client"]] = work_data.get("client", "")
            
            # Add description
            row[self.column_mapping["description"]] = work_data.get("description", "")
            
            # Handle hours - billable vs unbillable
            hours = work_data.get("hours")
            is_billable = work_data.get("billable", True)
            
            if is_billable:
                row[self.column_mapping["hours"]] = hours
                row[self.column_mapping["unbillable_hours"]] = ""
            else:
                row[self.column_mapping["hours"]] = ""
                row[self.column_mapping["unbillable_hours"]] = hours
                
            # Calculate revenue (hourly rate × hours) if billable
            hourly_rate = work_data.get("hourly_rate", 85)  # Default €85/hour
            if is_billable and hours:
                row[self.column_mapping["revenue"]] = float(hours) * hourly_rate
            else:
                row[self.column_mapping["revenue"]] = ""
            
            # Add timestamp if there's room
            timestamp_col = max(self.column_mapping.values()) + 1
            row[timestamp_col] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            # Find the next empty row
            try:
                result = self.sheets.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{target_sheet}!A:A"
                ).execute()
            except Exception as e:
                logger.error(f"Error getting values for next row: {e}")
                result = {"values": []}
            
            values = result.get('values', [])
            next_row = len(values) + 1
            
            # Add the data
            try:
                self.sheets.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{target_sheet}!A{next_row}:{chr(65 + len(row))}{next_row}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [row]}
                ).execute()
            except Exception as e:
                logger.error(f"Error updating sheet with new row: {e}")
                return False
            
            logger.info(f"Added work entry for {work_data.get('client')} to {target_sheet}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding work entry to Google Sheets: {e}")
            return False
    
    def get_work_entries(self, start_date: str = None, end_date: str = None, include_test: bool = True) -> List[Dict[str, Any]]:
        """
        Get work entries from the spreadsheet, optionally filtered by date range.
        
        Args:
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            include_test: Whether to include entries from the test sheet
            
        Returns:
            List of work entry dictionaries
        """
        try:
            entries = []
            
            # Convert start_date and end_date to datetime objects for comparison
            start_dt = None
            end_dt = None
            if start_date:
                try:
                    start_year, start_month, start_day = start_date.split('-')
                    start_dt = datetime(int(start_year), int(start_month), int(start_day))
                    logger.info(f"Filtering entries from {start_dt.strftime('%d-%m-%Y')}")
                except Exception as e:
                    logger.error(f"Error parsing start date {start_date}: {e}")
            
            if end_date:
                try:
                    end_year, end_month, end_day = end_date.split('-')
                    end_dt = datetime(int(end_year), int(end_month), int(end_day), 23, 59, 59)
                    logger.info(f"Filtering entries until {end_dt.strftime('%d-%m-%Y')}")
                except Exception as e:
                    logger.error(f"Error parsing end date {end_date}: {e}")
            
            # Determine which sheets to check
            sheets_to_check = [self.work_hours_sheet]
            if include_test:
                sheets_to_check.append(self.test_sheet)
                
            logger.info(f"Checking sheets: {sheets_to_check}")
            
            # Process each sheet
            for sheet_name in sheets_to_check:
                try:
                    # Get all data from the sheet
                    try:
                        result = self.sheets.spreadsheets().values().get(
                            spreadsheetId=self.spreadsheet_id,
                            range=f"{sheet_name}!A:G"
                        ).execute()
                        
                        values = result.get('values', [])
                    except Exception as e:
                        logger.error(f"Error getting values from sheet {sheet_name}: {e}")
                        values = []
                    
                    if not values:
                        logger.info(f"No data found in sheet {sheet_name}")
                        continue
                    
                    # Extract headers and data
                    headers = values[0]
                    data_rows = values[1:]
                    
                    logger.info(f"Found {len(data_rows)} rows in sheet {sheet_name}")
                    
                    # Map the Dutch headers to English equivalents for consistency
                    header_mapping = {
                        'Datum': 'Date',
                        'Klant': 'Client', 
                        'Beschrijving': 'Description',
                        'Uren': 'Hours',
                        'Uren onbetaald': 'Unbillable Hours',
                        'Omzet': 'Revenue'
                    }
                    
                    mapped_headers = [header_mapping.get(h, h) for h in headers]
                    
                    # Track how many rows pass the date filter
                    filtered_count = 0
                    
                    # Convert to list of dictionaries
                    for row in data_rows:
                        # Skip empty rows
                        if not row or not ''.join(row).strip():
                            continue
                            
                        # Pad row with empty strings if it's shorter than headers
                        padded_row = row + [''] * (len(headers) - len(row))
                        
                        # Create entry with English header names
                        entry = dict(zip(mapped_headers, padded_row))
                        
                        # Add source sheet info
                        entry['Sheet'] = sheet_name
                        
                        # Apply date filtering
                        should_include = True
                        
                        # Convert Dutch date to datetime for comparison
                        if 'Date' in entry and entry['Date']:
                            date_str = entry['Date']
                            entry_dt = None
                            
                            try:
                                if '-' in date_str:
                                    # Handle DD-MM-YYYY format
                                    day, month, year = date_str.split('-')
                                    if len(year) == 4:  # Ensure it's a 4-digit year
                                        entry_dt = datetime(int(year), int(month), int(day))
                                    
                                # Apply date filtering if we have a valid date
                                if entry_dt:
                                    if start_dt and entry_dt < start_dt:
                                        should_include = False
                                    if end_dt and entry_dt > end_dt:
                                        should_include = False
                            except Exception as e:
                                logger.warning(f"Error parsing date '{date_str}': {e}")
                        
                        # Add entry if it passes the filter
                        if should_include:
                            entries.append(entry)
                            filtered_count += 1
                    
                    logger.info(f"Included {filtered_count} entries from sheet {sheet_name} after date filtering")
                        
                except Exception as e:
                    logger.warning(f"Error processing sheet {sheet_name}: {e}")
                    continue
            
            # Sort entries by date (most recent first)
            entries.sort(key=lambda entry: entry.get('Date', ''), reverse=True)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting work entries: {e}")
            return []