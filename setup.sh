#!/bin/bash
# Setup script for Bramify

# Make sure directories exist
mkdir -p config logs

# Check if credentials.json exists
if [ ! -f "config/credentials.json" ]; then
    # Check if we can copy from Downloads
    CLIENT_SECRET=$(find ~/Downloads -name "client_secret_*" -type f -print -quit)
    if [ ! -z "$CLIENT_SECRET" ]; then
        echo "Found client_secret file: $CLIENT_SECRET"
        echo "Copying to config/credentials.json..."
        cp "$CLIENT_SECRET" "config/credentials.json"
    else
        echo "ERROR: No credentials.json file found in config/ and no client_secret file found in Downloads."
        echo "Please place your Google OAuth credentials in config/credentials.json before continuing."
        exit 1
    fi
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Set up virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install google-auth-oauthlib python-dotenv

# Generate token
echo "Generating OAuth token..."
python3 generate_token.py

# Check if token generation was successful
if [ -f "config/token.json" ]; then
    echo "Setup complete! You can now run Bramify with Docker:"
    echo "docker compose up"
else
    echo "Failed to generate token. Please check errors above."
    exit 1
fi