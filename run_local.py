#!/usr/bin/env python3
"""
Run Bramify locally without Docker.
This script will handle setting up the environment and launching the bot.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_credentials():
    """Check if credentials.json and token.json exist."""
    credentials_path = Path("config/credentials.json")
    token_path = Path("config/token.json")
    
    missing = []
    if not credentials_path.exists():
        missing.append("credentials.json")
    if not token_path.exists():
        missing.append("token.json")
        
    return missing

def setup_environment():
    """Set up Python virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Determine the pip path based on platform
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
    else:  # macOS/Linux
        pip_path = venv_path / "bin" / "pip"
    
    # Install requirements
    print("Installing requirements...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)

def generate_token():
    """Generate a Google API token."""
    print("Generating Google API token...")
    
    # Determine the python path based on platform
    if os.name == 'nt':  # Windows
        python_path = Path("venv") / "Scripts" / "python"
    else:  # macOS/Linux
        python_path = Path("venv") / "bin" / "python"
    
    subprocess.run([str(python_path), "generate_token.py"], check=True)

def run_bot():
    """Run the Bramify bot."""
    print("Starting Bramify bot...")
    
    # Determine the python path based on platform
    if os.name == 'nt':  # Windows
        python_path = Path("venv") / "Scripts" / "python"
    else:  # macOS/Linux
        python_path = Path("venv") / "bin" / "python"
    
    subprocess.run([str(python_path), "src/main.py"])

def main():
    """Main function to run Bramify locally."""
    # Create necessary directories
    os.makedirs("config", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Check if credentials exist
    missing = check_credentials()
    
    if "credentials.json" in missing:
        # Try to find credentials in Downloads folder
        downloads_path = Path.home() / "Downloads"
        credentials_files = list(downloads_path.glob("client_secret_*.json"))
        
        if credentials_files:
            # Use the most recent credentials file
            latest_creds = max(credentials_files, key=lambda x: x.stat().st_mtime)
            os.makedirs("config", exist_ok=True)
            target_path = Path("config/credentials.json")
            
            print(f"Copying {latest_creds} to {target_path}")
            with open(latest_creds, "r") as src_file:
                with open(target_path, "w") as dst_file:
                    dst_file.write(src_file.read())
        else:
            print("Error: credentials.json not found. Please create it in the config directory.")
            print("You can download it from the Google Cloud Console.")
            return
    
    # Set up environment
    setup_environment()
    
    # Generate token if needed
    if "token.json" in missing:
        generate_token()
    
    # Run the bot
    run_bot()

if __name__ == "__main__":
    main()