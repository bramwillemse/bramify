#!/usr/bin/env python3
"""
Run Bramify locally without Docker.
This script will handle setting up the environment and launching the bot.
"""

import os
import sys
import subprocess
from pathlib import Path
import platform

def setup_environment():
    """Set up Python virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    
    # Check Python version
    python_version = platform.python_version()
    print(f"Using Python {python_version}")
    
    # Python 3.13 has compatibility issues with pydantic-core
    if python_version.startswith("3.13"):
        print("WARNING: Python 3.13 might have compatibility issues with some dependencies.")
        print("You might want to try with Python 3.11 instead.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            print("Setup aborted. Try using Python 3.11.")
            sys.exit(1)
    
    # Remove existing virtual environment if it exists
    if venv_path.exists():
        print("Recreating virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    # Create virtual environment
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Determine the pip path based on platform
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
    else:  # macOS/Linux
        pip_path = venv_path / "bin" / "pip"
    
    # Install essential packages first
    print("Installing essential packages...")
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(pip_path), "install", "wheel"], check=True)
    
    # Install a compatible version of pydantic
    print("Installing pydantic...")
    subprocess.run([str(pip_path), "install", "pydantic==2.0.3"], check=True)
    
    # Install specific packages that have issues with Python 3.13
    if python_version.startswith("3.13"):
        print("Installing specific dependency versions for Python 3.13...")
        subprocess.run([str(pip_path), "install", "python-telegram-bot==20.7"], check=True)
        subprocess.run([str(pip_path), "install", "anthropic==0.8.0"], check=True)
        subprocess.run([str(pip_path), "install", "google-auth==2.23.0"], check=True)
        subprocess.run([str(pip_path), "install", "google-auth-oauthlib==1.1.0"], check=True)
        subprocess.run([str(pip_path), "install", "google-auth-httplib2==0.1.1"], check=True)
        subprocess.run([str(pip_path), "install", "google-api-python-client==2.100.0"], check=True)
        subprocess.run([str(pip_path), "install", "python-dotenv==1.0.0"], check=True)
        subprocess.run([str(pip_path), "install", "loguru==0.7.2"], check=True)
    else:
        # Install all requirements
        print("Installing requirements...")
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)

def run_bot():
    """Run the Bramify bot."""
    print("Starting Bramify bot...")
    
    # Determine the python path based on platform
    if os.name == 'nt':  # Windows
        python_path = Path("venv") / "Scripts" / "python"
    else:  # macOS/Linux
        python_path = Path("venv") / "bin" / "python"
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Make sure .env file exists with the spreadsheet ID
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write("# Telegram\n")
            f.write(f"TELEGRAM_BOT_TOKEN={os.environ.get('TELEGRAM_BOT_TOKEN', '')}\n")
            f.write(f"TELEGRAM_ALLOWED_USER_IDS={os.environ.get('TELEGRAM_ALLOWED_USER_IDS', '')}\n\n")
            f.write("# Anthropic Claude\n")
            f.write(f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', '')}\n\n")
            f.write("# Google Sheets\n")
            f.write(f"GOOGLE_SHEETS_CREDENTIALS_FILE=config/service_account.json\n")
            f.write(f"GOOGLE_SHEETS_SPREADSHEET_ID={os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID', '')}\n")
    
    # Run the bot
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    subprocess.run([str(python_path), "src/main.py"], env=env)

def main():
    """Main function to run Bramify locally."""
    # Check if config/service_account.json and config/token.json exist
    if not Path("config/service_account.json").exists():
        print("Error: Service account file not found at config/service_account.json")
        print("Please run service_account_setup.py first")
        return False
    
    if not Path("config/token.json").exists():
        print("Error: Token file not found at config/token.json")
        print("Please run service_account_setup.py first")
        return False
    
    # Update the .env file with the spreadsheet ID if it's not there
    env_file = Path(".env")
    spreadsheet_id = ""
    
    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()
            
        if "GOOGLE_SHEETS_SPREADSHEET_ID=" in env_content:
            # Extract the spreadsheet ID from the .env file
            for line in env_content.split("\n"):
                if line.startswith("GOOGLE_SHEETS_SPREADSHEET_ID="):
                    spreadsheet_id = line.split("=", 1)[1].strip()
    
    if not spreadsheet_id:
        # Ask for the spreadsheet ID
        spreadsheet_id = input("Enter your Google Sheets spreadsheet ID: ")
        
        # Add it to the .env file
        with open(env_file, "a") as f:
            f.write(f"\nGOOGLE_SHEETS_SPREADSHEET_ID={spreadsheet_id}\n")
    
    # Setup the environment
    setup_environment()
    
    # Run the bot
    run_bot()
    
    return True

if __name__ == "__main__":
    main()