"""Anthropic Claude API integration for natural language processing."""

import os
import re
from typing import Dict, Any, Optional
import json
from datetime import datetime, timedelta
import anthropic
from loguru import logger

class ClaudeClient:
    """Client for interacting with Anthropic's Claude API."""
    
    def __init__(self):
        """Initialize the Claude client with API key."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables")
            
        # Create the Anthropic client with the API key
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Define the model to use - using Claude 3 Haiku which is good for these tasks
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        logger.info(f"Claude client initialized with model {self.model}")
    
    async def analyze_work_entry(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to extract work entry information.
        
        Args:
            text: The text message from the user
            
        Returns:
            Dict containing extracted work information or empty if not a work entry
        """
        system_prompt = """
        You are an assistant that helps extract work information from text.
        The user is from the Netherlands and will often write in Dutch or a mix of Dutch and English.
        
        The spreadsheet has the following columns:
        - Datum (Date)
        - Klant (Client) 
        - Beschrijving (Description)
        - Uren (Hours - billable)
        - Uren onbetaald (Unbillable hours)
        - Omzet (Revenue)
        
        Important Dutch vocabulary to help you understand:
        - "uur" or "uren" = hours
        - "klant" = client
        - "vandaag" = today
        - "gisteren" = yesterday
        - "vorige week" = last week
        - "declarabel" or "facturabel" = billable
        - "niet declarabel" or "niet facturabel" = not billable
        - "onbetaald" = unpaid/unbillable
        
        Format your response as ONLY valid JSON with the following fields:
        {
            "is_work_entry": true/false,
            "client": "client name or null if not found",
            "hours": number of hours or null if not found,
            "billable": true/false,
            "date": "DD-MM-YYYY",
            "description": "description of the work",
            "hourly_rate": 85
        }
        """
        
        # Get current date for reference
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        user_prompt = f"""
        Analyze the following text and extract:
        
        1. If this is a work entry (description of work done)
        2. Client name (klant)
        3. Hours worked (uren)
        4. Whether the work is billable (facturabel) - default to true if unclear
        5. Date (datum) - use today if not specified, format as DD-MM-YYYY for Dutch format
        
        Important date references:
        - Today is {today.strftime('%d-%m-%Y')}
        - Tomorrow is {tomorrow.strftime('%d-%m-%Y')}
        - Yesterday is {yesterday.strftime('%d-%m-%Y')}
        
        For references like "morgen" (tomorrow) or "volgende week" (next week), calculate the actual date.
        
        6. Description of the work (beschrijving)
        
        User text: {text}
        """
        
        try:
            # Create a message with the Claude client using Messages API
            # Note: with newer versions of Anthropic client, this is not an async method
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract the response text
            response_text = response.content[0].text
            
            # Extract JSON from the response (in case there's additional text)
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                # If no valid JSON found, attempt to parse the whole response
                result = json.loads(response_text)
            
            # Set date to today if not provided
            if "date" not in result or not result["date"]:
                result["date"] = datetime.now().strftime("%d-%m-%Y")
            
            # Validate date format and fix if needed
            if "date" in result and result["date"]:
                try:
                    # Try to parse the date to ensure it's valid
                    date_str = result["date"]
                    
                    # Check if it's in the expected DD-MM-YYYY format
                    if re.match(r'\d{2}-\d{2}-\d{4}', date_str):
                        # Already in the correct format
                        pass
                    elif re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        # ISO format (YYYY-MM-DD), convert to DD-MM-YYYY
                        year, month, day = date_str.split('-')
                        result["date"] = f"{day}-{month}-{year}"
                    elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                        # US format (MM/DD/YYYY or DD/MM/YYYY), assuming DD/MM/YYYY
                        day, month, year = date_str.split('/')
                        result["date"] = f"{day.zfill(2)}-{month.zfill(2)}-{year}"
                    else:
                        # Unrecognized format, use today
                        logger.warning(f"Unrecognized date format: {date_str}, using today's date")
                        result["date"] = datetime.now().strftime("%d-%m-%Y")
                except Exception as e:
                    logger.error(f"Error validating date format: {e}, using today's date")
                    result["date"] = datetime.now().strftime("%d-%m-%Y")
                
            return result
                
        except Exception as e:
            logger.error(f"Error analyzing work entry: {e}")
            # Return empty result on error
            return {
                "is_work_entry": False
            }
    
    async def generate_response(self, message: str) -> str:
        """
        Generate a conversational response to a user message.
        
        Args:
            message: The user's message
            
        Returns:
            The assistant's response
        """
        try:
            system_prompt = """
            Je bent Bramify, een persoonlijke assistent gespecialiseerd in urenregistratie.
            Je helpt gebruikers hun werkuren bij te houden op een vriendelijke, conversationele manier.
            Wees beknopt, behulpzaam, en houd een professionele maar vriendelijke toon aan.
            Antwoord altijd in het Nederlands, ook als de gebruiker in het Engels schrijft.
            """
            
            # Create a message with the Claude client using Messages API
            # Note: with newer versions of Anthropic client, this is not an async method
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I'm having trouble generating a response right now. Please try again."