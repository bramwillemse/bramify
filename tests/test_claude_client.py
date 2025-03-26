"""Tests for the Claude client module."""

import pytest
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Import patch
from tests.patch_imports import patch_imports
patch_imports()

from src.integrations.claude.client import ClaudeClient


class MockAnthropicResponse:
    """Mock response from Anthropic API."""
    
    def __init__(self, content):
        """Initialize with content."""
        self.content = [{
            "text": content,
            "type": "text"
        }]


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = MagicMock()
    return mock_client


@pytest.fixture
def claude_client(mock_anthropic_client):
    """Create a ClaudeClient with mocked Anthropic client."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_api_key"}):
        with patch("anthropic.Anthropic", return_value=mock_anthropic_client):
            client = ClaudeClient()
            return client


@pytest.mark.asyncio
async def test_analyze_work_entry_valid(claude_client, mock_anthropic_client):
    """Test analyzing a valid work entry."""
    # Mock response
    mock_response = {
        "is_work_entry": True,
        "client": "Test Client",
        "hours": 3.5,
        "billable": True,
        "date": "25-03-2025",
        "description": "Test work",
        "hourly_rate": 85
    }
    
    mock_anthropic_client.messages.create.return_value = MockAnthropicResponse(json.dumps(mock_response))
    
    # Test
    result = await claude_client.analyze_work_entry("3.5 hours for Test Client: Test work")
    
    # Verify
    assert result["is_work_entry"] is True
    assert result["client"] == "Test Client"
    assert result["hours"] == 3.5
    assert result["billable"] is True
    assert result["date"] == "25-03-2025"
    assert result["description"] == "Test work"
    
    # Check that the API was called with the right parameters
    mock_anthropic_client.messages.create.assert_called_once()
    call_args = mock_anthropic_client.messages.create.call_args[1]
    assert call_args["model"] == claude_client.model
    assert "User text: 3.5 hours for Test Client: Test work" in call_args["messages"][0]["content"]


@pytest.mark.asyncio
async def test_analyze_work_entry_invalid_json(claude_client, mock_anthropic_client):
    """Test handling invalid JSON in response."""
    # Mock invalid JSON response
    mock_anthropic_client.messages.create.return_value = MockAnthropicResponse("Not valid JSON")
    
    # Test
    result = await claude_client.analyze_work_entry("Hello, how are you?")
    
    # Verify
    assert result["is_work_entry"] is False


@pytest.mark.asyncio
async def test_analyze_work_entry_exception(claude_client, mock_anthropic_client):
    """Test handling exception during API call."""
    # Mock exception
    mock_anthropic_client.messages.create.side_effect = Exception("API error")
    
    # Test
    result = await claude_client.analyze_work_entry("3.5 hours for Test Client")
    
    # Verify
    assert result["is_work_entry"] is False


@pytest.mark.asyncio
async def test_analyze_work_entry_no_date(claude_client, mock_anthropic_client):
    """Test analyzing a work entry with no date."""
    # Mock response with no date
    mock_response = {
        "is_work_entry": True,
        "client": "Test Client",
        "hours": 3.5,
        "billable": True,
        "date": None,
        "description": "Test work",
        "hourly_rate": 85
    }
    
    mock_anthropic_client.messages.create.return_value = MockAnthropicResponse(json.dumps(mock_response))
    
    # Test
    with patch("src.integrations.claude.client.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.strftime.return_value = "25-03-2025"
        mock_datetime.now.return_value = mock_now
        
        result = await claude_client.analyze_work_entry("3.5 hours for Test Client")
    
    # Verify
    assert result["date"] == "25-03-2025"  # Should default to today


@pytest.mark.asyncio
async def test_date_format_validation(claude_client, mock_anthropic_client):
    """Test validation and correction of different date formats."""
    date_test_cases = [
        # Input date format, expected output format
        ("2025-03-26", "26-03-2025"),  # ISO format
        ("26/03/2025", "26-03-2025"),  # European with slash
        ("3/26/2025", "26-03-2025"),   # US format with slash
        ("invalid-date", "25-03-2025"),  # Invalid format should default to today
        ("26-03-2025", "26-03-2025"),  # Already correct format
    ]
    
    for input_date, expected_date in date_test_cases:
        # Mock response with different date format
        mock_response = {
            "is_work_entry": True,
            "client": "Test Client",
            "hours": 3.5,
            "billable": True,
            "date": input_date,
            "description": f"Test work on {input_date}",
            "hourly_rate": 85
        }
        
        mock_anthropic_client.messages.create.return_value = MockAnthropicResponse(json.dumps(mock_response))
        
        # Test with mocked today's date
        with patch("src.integrations.claude.client.datetime") as mock_datetime:
            # For invalid date fallback
            mock_now = MagicMock()
            mock_now.strftime.return_value = "25-03-2025"
            mock_datetime.now.return_value = mock_now
            
            result = await claude_client.analyze_work_entry(f"3.5 hours on {input_date}")
        
        # Verify date format was corrected
        assert result["date"] == expected_date, f"Failed for input date: {input_date}"


@pytest.mark.asyncio
async def test_generate_response(claude_client, mock_anthropic_client):
    """Test generating a response."""
    # Mock response
    mock_anthropic_client.messages.create.return_value = MockAnthropicResponse("Test response")
    
    # Test
    result = await claude_client.generate_response("Test message")
    
    # Verify
    assert result == "Test response"
    
    # Check API call
    mock_anthropic_client.messages.create.assert_called_once()
    call_args = mock_anthropic_client.messages.create.call_args[1]
    assert call_args["model"] == claude_client.model
    assert call_args["messages"][0]["content"] == "Test message"


@pytest.mark.asyncio
async def test_generate_response_exception(claude_client, mock_anthropic_client):
    """Test handling exception in generate_response."""
    # Mock exception
    mock_anthropic_client.messages.create.side_effect = Exception("API error")
    
    # Test
    result = await claude_client.generate_response("Test message")
    
    # Verify
    assert "Sorry, I'm having trouble" in result