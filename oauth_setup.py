#!/usr/bin/env python3
"""
A simple script to generate a Google OAuth token for Bramify.
This uses a Desktop client credentials file to simplify the process.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pathlib import Path

# Configuration
CONFIG_DIR = Path("config")
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def convert_to_desktop_client():
    """Convert a web client to a desktop client if needed."""
    if not CREDENTIALS_FILE.exists():
        print(f"Error: Credentials file not found at {CREDENTIALS_FILE}")
        return False
        
    # Read the credentials file
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_data = json.load(f)
    
    # Check if it's already a desktop client
    if 'installed' in creds_data:
        print("Already using a desktop client configuration.")
        return True
        
    # If it's a web client, convert to desktop client format
    if 'web' in creds_data:
        print("Converting web client to desktop client format...")
        web_data = creds_data['web']
        desktop_data = {
            'installed': {
                'client_id': web_data['client_id'],
                'project_id': web_data['project_id'],
                'auth_uri': web_data['auth_uri'],
                'token_uri': web_data['token_uri'],
                'auth_provider_x509_cert_url': web_data['auth_provider_x509_cert_url'],
                'client_secret': web_data['client_secret'],
                'redirect_uris': ['http://localhost']
            }
        }
        
        # Backup original file
        backup_file = CREDENTIALS_FILE.with_suffix('.json.bak')
        with open(backup_file, 'w') as f:
            json.dump(creds_data, f, indent=4)
        print(f"Original credentials backed up to {backup_file}")
        
        # Write the new desktop client format
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(desktop_data, f, indent=4)
        print("Converted to desktop client format successfully.")
        return True
    
    print("Unknown credentials format.")
    return False

def create_token():
    """Create a token using the credentials file."""
    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        
        # Run the OAuth flow
        print("\nStarting OAuth flow. A browser window should open automatically.")
        print("Please authorize the application when prompted.")
        credentials = flow.run_local_server(port=0)
        
        # Save credentials to token.json
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())
            
        print(f"\nSuccess! Token saved to {TOKEN_FILE}")
        return True
        
    except Exception as e:
        print(f"\nError generating token: {e}")
        return False

def main():
    """Main function."""
    print("=== Bramify OAuth Setup ===\n")
    
    # Create config directory if it doesn't exist
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # Check if credentials file exists
    if not CREDENTIALS_FILE.exists():
        # Look for credentials in Downloads folder
        downloads = Path.home() / "Downloads"
        client_secrets = list(downloads.glob("client_secret_*.json"))
        
        if client_secrets:
            # Use the most recent client_secret file
            latest = max(client_secrets, key=lambda p: p.stat().st_mtime)
            print(f"Found credentials file: {latest}")
            print(f"Copying to {CREDENTIALS_FILE}")
            
            # Make sure the directory exists
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
            # Copy the file
            with open(latest, 'r') as src:
                with open(CREDENTIALS_FILE, 'w') as dst:
                    dst.write(src.read())
        else:
            print(f"Error: No credentials file found at {CREDENTIALS_FILE}")
            print("and no client_secret_*.json files found in Downloads folder.")
            print("\nPlease create a Desktop OAuth client in Google Cloud Console")
            print("and download the credentials file to config/credentials.json")
            return False
    
    # Convert to desktop client if needed
    if not convert_to_desktop_client():
        return False
    
    # Create token
    return create_token()

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSetup completed successfully!")
        print("You can now run Bramify with:")
        print("  ./run_local.py")
        print("  or")
        print("  docker compose up")
    else:
        print("\nSetup failed. Please check the error messages above.")