FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create directories
RUN mkdir -p logs config

# Set environment variables (these will be overridden by docker-compose)
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_ALLOWED_USER_IDS=""
ENV ANTHROPIC_API_KEY=""
ENV GOOGLE_SHEETS_CREDENTIALS_FILE="config/credentials.json"
ENV GOOGLE_SHEETS_SPREADSHEET_ID=""

# Run the application
CMD ["python", "src/main.py"]