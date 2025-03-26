# Handleiding voor Google Sheets Authenticatie

Dit document legt uit hoe je Bramify toegang kunt geven tot je Google Sheets.

## Optie 1: Service Account (Aanbevolen)

Een service account is de gemakkelijkste manier om Bramify toegang te geven tot je Google Sheets. Je hoeft maar één keer in te stellen en dan werkt het zonder browser authenticatie.

### Stap 1: Service Account aanmaken

1. Ga naar [Google Cloud Console](https://console.cloud.google.com/)
2. Selecteer of maak een project
3. Ga naar "APIs & Services" → "Credentials"
4. Klik op "+ CREATE CREDENTIALS" bovenaan en kies "Service account"
5. Geef het een naam (bijv. "Bramify Bot")
6. Klik op "CREATE AND CONTINUE"
7. Bij rollen kun je "Geen rol" kiezen (we geven alleen toegang tot je spreadsheet)
8. Klik op "CONTINUE" en dan "DONE"

### Stap 2: Sleutel downloaden

1. Klik op de zojuist gemaakte service account in de lijst
2. Ga naar de tab "KEYS"
3. Klik op "ADD KEY" → "Create new key"
4. Kies "JSON" en klik op "CREATE"
5. Het sleutelbestand wordt gedownload naar je Downloads map

### Stap 3: Google Sheet delen met Service Account

1. Kopieer het e-mailadres van de service account (ziet eruit als: `bramify@project-id.iam.gserviceaccount.com`)
2. Open je Google Sheet
3. Klik op de "Share" knop rechtsboven
4. Plak het e-mailadres van de service account
5. Geef het "Editor" rechten en klik op "Share"

### Stap 4: Service Account configureren voor Bramify

1. Run het volgende commando in je terminal:
```bash
./service_account_setup.py
```
2. Het script zal het sleutelbestand vinden en kopiëren naar de juiste locatie
3. Start Bramify:
```bash
./run_local.py
```

## Optie 2: OAuth Authentication (Alternatief)

Als je om een of andere reden geen service account wilt gebruiken, kun je ook OAuth authenticatie instellen.

### Stap 1: OAuth Credentials maken

1. Ga naar [Google Cloud Console](https://console.cloud.google.com/)
2. Selecteer of maak een project
3. Ga naar "APIs & Services" → "Credentials"
4. Klik op "+ CREATE CREDENTIALS" bovenaan en kies "OAuth client ID"
5. Bij application type kies "Desktop app"
6. Geef het een naam (bijv. "Bramify Desktop")
7. Klik op "CREATE"
8. Download het JSON bestand

### Stap 2: OAuth Flow doorlopen

1. Kopieer het gedownloade JSON bestand naar `config/credentials.json`
2. Run het script om een token te genereren:
```bash
python3 generate_token.py
```
3. Volg de instructies om de OAuth flow te doorlopen
4. Start Bramify:
```bash
./run_local.py
```