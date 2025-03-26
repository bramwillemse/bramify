#!/usr/bin/env python3
"""
This script creates a simple service account credentials file for Google Sheets.
This is much simpler than OAuth and avoids browser authentication issues.

Instructions:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new Service Account (not OAuth client)
3. Download the JSON key file
4. Place it in the config directory as service_account.json
5. Share your spreadsheet with the service account email address
"""

import os
import json
from pathlib import Path
import sys

# Configuration
CONFIG_DIR = Path("config")
SERVICE_ACCOUNT_FILE = CONFIG_DIR / "service_account.json"
TOKEN_FILE = CONFIG_DIR / "token.json"

def main():
    """Main function to set up service account credentials."""
    print("=== Bramify Service Account Setup ===\n")
    
    # Create config directory if it doesn't exist
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # Check if service account file exists
    if not SERVICE_ACCOUNT_FILE.exists():
        # Look for service account in Downloads folder
        downloads = Path.home() / "Downloads"
        service_account_files = list(downloads.glob("*-*.json"))
        
        if service_account_files:
            # Use the most recent service account file
            latest = max(service_account_files, key=lambda p: p.stat().st_mtime)
            print(f"Found potential service account file: {latest}")
            
            # Check if it looks like a service account file
            with open(latest, 'r') as f:
                try:
                    data = json.load(f)
                    if 'type' in data and data['type'] == 'service_account':
                        print(f"Confirmed service account file. Copying to {SERVICE_ACCOUNT_FILE}")
                        
                        # Copy the file
                        with open(SERVICE_ACCOUNT_FILE, 'w') as dst:
                            json.dump(data, f, indent=2)
                            
                        print(f"\nIMPORTANT: Share your Google Sheet with this email address:")
                        print(f"  {data.get('client_email', 'EMAIL NOT FOUND')}")
                        print("\nDon't skip this step or the service account won't have access!")
                    else:
                        print(f"The file doesn't appear to be a service account key file.")
                        print("Please download a service account key file from Google Cloud Console.")
                        return False
                except json.JSONDecodeError:
                    print(f"The file is not valid JSON. Please download a service account key file.")
                    return False
        else:
            print("\nNo service account file found.")
            print("\nPlease follow these steps:")
            print("1. Go to https://console.cloud.google.com/apis/credentials")
            print("2. Create a new Service Account (or use an existing one)")
            print("3. Add a new key to the service account (JSON format)")
            print("4. Download the JSON key file")
            print(f"5. Place it in {SERVICE_ACCOUNT_FILE}")
            print("6. Share your Google Sheet with the service account email address")
            return False
    else:
        # Verify the service account file
        try:
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                data = json.load(f)
                if 'type' in data and data['type'] == 'service_account':
                    print(f"Service account file found at {SERVICE_ACCOUNT_FILE}")
                    print(f"\nIMPORTANT: Make sure your Google Sheet is shared with:")
                    print(f"  {data.get('client_email', 'EMAIL NOT FOUND')}")
                else:
                    print(f"The file at {SERVICE_ACCOUNT_FILE} doesn't appear to be a valid service account key.")
                    print("Please download a proper service account key file.")
                    return False
        except (json.JSONDecodeError, IOError):
            print(f"Error reading {SERVICE_ACCOUNT_FILE}.")
            print("Please download a proper service account key file.")
            return False
    
    # Create a dummy token file that indicates we're using a service account
    token_data = {
        "type": "service_account_reference",
        "service_account_file": str(SERVICE_ACCOUNT_FILE)
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"\nCreated service account reference at {TOKEN_FILE}")
    print("\nSetup completed successfully!")
    
    # Update .env file with the correct token file path
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if "GOOGLE_SHEETS_TOKEN_FILE" not in env_content:
            with open(env_file, 'a') as f:
                f.write("\n# Using service account instead of OAuth\n")
                f.write(f"GOOGLE_SHEETS_CREDENTIALS_FILE={SERVICE_ACCOUNT_FILE}\n")
            print("Updated .env file with service account path.")
    
    return True

if __name__ == "__main__":
    if main():
        print("\nYou can now run Bramify with:")
        print("  ./run_local.py")
        print("  or")
        print("  docker compose up")
    else:
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1)