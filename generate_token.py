#!/usr/bin/env python3
"""
Generate a Google Sheets API token from OAuth credentials.
Run this locally (not in Docker) to create a token.json file.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# Credentials file path
CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "config/credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_SHEETS_TOKEN_FILE", "config/token.json")

def generate_token():
    """Generate a token.json file from OAuth credentials."""
    print(f"Using credentials file: {CREDENTIALS_FILE}")
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: Credentials file {CREDENTIALS_FILE} not found!")
        return False
        
    # Define the scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        
        # Run the OAuth flow
        credentials = flow.run_local_server(port=0)
        
        # Save credentials to token.json
        token_dir = os.path.dirname(TOKEN_FILE)
        os.makedirs(token_dir, exist_ok=True)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())
            
        print(f"Success! Token saved to {TOKEN_FILE}")
        return True
        
    except Exception as e:
        print(f"Error generating token: {e}")
        return False

if __name__ == "__main__":
    generate_token()