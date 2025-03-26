"""Client name to code mapping functionality."""

import os
import json
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import re
from loguru import logger

class ClientMapper:
    """Maps client names to their 3-letter codes."""
    
    def __init__(self, config_file: str = "config/client_codes.json"):
        """
        Initialize the client mapper.
        
        Args:
            config_file: Path to the JSON file containing client code mappings
        """
        self.config_file = config_file
        self.client_codes = {}
        self._load_mappings()
    
    def _load_mappings(self) -> None:
        """Load client-code mappings from the config file."""
        try:
            config_path = Path(self.config_file)
            
            # Create directory if it doesn't exist
            os.makedirs(config_path.parent, exist_ok=True)
            
            # If the file exists, load it
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.client_codes = json.load(f)
                logger.info(f"Loaded {len(self.client_codes)} client codes from {self.config_file}")
            else:
                # Create a new file with empty mappings
                self.client_codes = {}
                with open(config_path, 'w') as f:
                    json.dump(self.client_codes, f, indent=2)
                logger.info(f"Created new client codes file at {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading client codes: {e}")
            # Use empty mappings if there's an error
            self.client_codes = {}
    
    def _save_mappings(self) -> None:
        """Save client-code mappings to the config file."""
        try:
            config_path = Path(self.config_file)
            
            # Create directory if it doesn't exist
            os.makedirs(config_path.parent, exist_ok=True)
            
            # Save mappings
            with open(config_path, 'w') as f:
                json.dump(self.client_codes, f, indent=2)
            logger.info(f"Saved {len(self.client_codes)} client codes to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving client codes: {e}")
    
    def get_code(self, client_name: str) -> Optional[str]:
        """
        Get the code for a client name.
        
        Args:
            client_name: The client name to look up
            
        Returns:
            The 3-letter code or None if not found
        """
        # Normalize client name for lookup
        normalized_name = self._normalize_client_name(client_name)
        
        # Look for exact match
        if normalized_name in self.client_codes:
            return self.client_codes[normalized_name]
        
        # Look for partial match with any existing client name
        for existing_name, code in self.client_codes.items():
            if (normalized_name in existing_name or 
                existing_name in normalized_name):
                return code
        
        # No match found
        return None
    
    def add_mapping(self, client_name: str, code: str) -> None:
        """
        Add a new client-code mapping.
        
        Args:
            client_name: The client name
            code: The 3-letter code
        """
        # Normalize client name and code
        normalized_name = self._normalize_client_name(client_name)
        normalized_code = self._normalize_code(code)
        
        # Add the mapping
        self.client_codes[normalized_name] = normalized_code
        
        # Save to file
        self._save_mappings()
        
        logger.info(f"Added client code mapping: {normalized_name} -> {normalized_code}")
    
    def get_all_mappings(self) -> Dict[str, str]:
        """
        Get all client-code mappings.
        
        Returns:
            Dictionary of client names to codes
        """
        return dict(self.client_codes)
    
    def _normalize_client_name(self, client_name: str) -> str:
        """
        Normalize a client name for consistent lookup.
        
        Args:
            client_name: The client name to normalize
            
        Returns:
            Normalized client name
        """
        if not client_name:
            return ""
        
        # Convert to lowercase
        normalized = client_name.lower()
        
        # Remove common prefixes/suffixes that don't add to uniqueness
        prefixes_to_remove = ["the ", "company ", "client "]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        # Remove non-alphanumeric characters
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        return normalized
    
    def _normalize_code(self, code: str) -> str:
        """
        Normalize a client code.
        
        Args:
            code: The code to normalize
            
        Returns:
            Normalized 3-letter code
        """
        if not code:
            return ""
        
        # Convert to uppercase
        normalized = code.upper()
        
        # Keep only letters
        normalized = re.sub(r'[^A-Z]', '', normalized)
        
        # Ensure it's exactly 3 letters
        if len(normalized) > 3:
            normalized = normalized[:3]
        elif len(normalized) < 3:
            # Pad with 'X' if shorter than 3 letters
            normalized = normalized + 'X' * (3 - len(normalized))
        
        return normalized
    
    def suggest_code_for_client(self, client_name: str) -> str:
        """
        Suggest a 3-letter code for a new client.
        
        Args:
            client_name: The client name
            
        Returns:
            A suggested 3-letter code
        """
        if not client_name:
            return "UNK"  # Unknown
        
        # Split into words
        words = re.findall(r'\b\w+\b', client_name.upper())
        
        if not words:
            return "UNK"
        
        if len(words) == 1:
            # Single word: take first 3 letters
            word = words[0]
            if len(word) >= 3:
                return word[:3]
            else:
                return word + 'X' * (3 - len(word))
        
        # Multiple words: take first letter of first 3 words
        code = ''.join(word[0] for word in words[:3])
        
        # If we still don't have 3 letters, add first letter of first word repeatedly
        if len(code) < 3:
            code = code + words[0][0] * (3 - len(code))
        
        return code
    
    def find_existing_clients(self, partial_name: str) -> List[Tuple[str, str]]:
        """
        Find existing clients that match a partial name.
        
        Args:
            partial_name: Partial client name to search for
            
        Returns:
            List of tuples containing (client_name, code)
        """
        if not partial_name:
            return list(self.client_codes.items())
        
        normalized_partial = self._normalize_client_name(partial_name)
        
        # Find all clients that contain the partial name
        matching_clients = []
        for client_name, code in self.client_codes.items():
            if normalized_partial in client_name:
                # Find the original client name (before normalization)
                # This is a workaround since we don't store the original names
                matching_clients.append((client_name, code))
        
        return matching_clients