"""Anthropic Claude API integration for natural language processing."""

import os
from typing import Dict, Any, Optional
import json
from datetime import datetime
import anthropic
from loguru import logger

class ClaudeClient:
    """Client for interacting with Anthropic's Claude API."""
    
    def __init__(self):
        """Initialize the Claude client with API key."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables")
            
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"  # Use the latest model
        
        logger.info("Claude client initialized")
    
    async def analyze_work_entry(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to extract work entry information.
        
        Args:
            text: The text message from the user
            
        Returns:
            Dict containing extracted work information or empty if not a work entry
        """
        prompt = f"""
        You are an assistant that helps extract work information from text.
        Analyze the following text and extract:
        
        1. If this is a work entry (description of work done)
        2. Client name
        3. Project name
        4. Hours worked
        5. Whether the work is billable (default to true if unclear)
        6. Date (use today if not specified)
        7. Brief description of the work
        
        Format your response as JSON with the following fields:
        {{
            "is_work_entry": true/false,
            "client": "client name or null if not found",
            "project": "project name or null if not found",
            "hours": number of hours or null if not found,
            "billable": true/false,
            "date": "YYYY-MM-DD",
            "description": "brief description of the work"
        }}
        
        User text: {text}
        """
        
        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response as JSON
            response_text = message.content[0].text
            
            # Extract JSON from the response (in case there's additional text)
            json_start = response_text.find("{{")
            json_end = response_text.rfind("}}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                # If no valid JSON found, attempt to parse the whole response
                result = json.loads(response_text)
            
            # Set date to today if not provided
            if "date" not in result or not result["date"]:
                result["date"] = datetime.now().strftime("%Y-%m-%d")
                
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
            You are Bramify, a personal assistant specialized in hour registration.
            You help users track their work hours in a friendly, conversational manner.
            Be concise, helpful, and maintain a professional but friendly tone.
            """
            
            response = await self.client.messages.create(
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