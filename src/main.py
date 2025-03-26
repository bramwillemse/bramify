"""Bramify - Personal AI assistant for hour registration."""

import os
import asyncio
from dotenv import load_dotenv
from loguru import logger

from core.bot import BramifyBot

def main():
    """Initialize and run the Bramify application."""
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/bramify.log", rotation="10 MB", level="INFO")
    logger.info("Starting Bramify")
    
    # Initialize the bot
    bot = BramifyBot()
    
    # Setup the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run setup in the event loop
    loop.run_until_complete(bot.setup())
    
    # Let the application manage its own event loop
    # This works better with python-telegram-bot
    bot.app.run_polling(close_loop=False)
    
if __name__ == "__main__":
    main()