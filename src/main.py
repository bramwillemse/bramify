"""Bramify - Personal AI assistant for hour registration."""

import os
import asyncio
from dotenv import load_dotenv
from loguru import logger

from core.bot import BramifyBot

async def main():
    """Initialize and run the Bramify application."""
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/bramify.log", rotation="10 MB", level="INFO")
    logger.info("Starting Bramify")
    
    # Initialize and run the bot
    bot = BramifyBot()
    await bot.run()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())