# Handleiding voor Google Sheets Autorisatie

Dit document helpt je om handmatig een token te genereren voor toegang tot Google Sheets.

## Stap 1: Google Cloud Console configureren

1. Ga naar [Google Cloud Console](https://console.cloud.google.com/)
2. Selecteer je project "bramify-hour-registration" of maak een nieuw project
3. Ga naar "APIs & Services" → "Credentials"
4. Klik op de bestaande OAuth client ID of maak een nieuwe:
   - Kies "Desktop app" als type (niet "Web application")
   - Geef het een naam zoals "Bramify Desktop Client"
   - Klik op "Create"
5. Download het JSON-bestand (er verschijnt een download knop)
6. Hernoem het bestand naar `credentials.json` en plaats het in de `config` map

## Stap 2: Genereer een token

1. Open een terminal en ga naar je bramify directory
2. Voer de volgende commando's uit:

```bash
# Maak een virtual environment aan
python3 -m venv venv

# Activeer de virtual environment
source venv/bin/activate

# Installeer benodigde packages
pip install google-auth-oauthlib google-auth google-api-python-client

# Genereer een token
python3 -c "
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Pad naar credentials
CREDENTIALS_FILE = 'config/credentials.json'
TOKEN_FILE = 'config/token.json'

# Definieer scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Maak OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

# Vraag autorisatie
credentials = flow.run_local_server(port=0)

# Sla token op
os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
with open(TOKEN_FILE, 'w') as token:
    token.write(credentials.to_json())
    
print(f'Token opgeslagen in {TOKEN_FILE}')
"
```

## Stap 3: Controleer of het token is gegenereerd

1. Controleer of er een `token.json` bestand is aangemaakt in de `config` map
2. Als het bestand bestaat, is de autorisatie geslaagd

## Stap 4: Start de container

1. Start de Docker container:

```bash
docker compose up
```

2. De container zou nu moeten werken zonder OAuth fouten