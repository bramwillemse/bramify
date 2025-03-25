"""Tests for Claude API integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.integrations.claude.client import ClaudeClient

@pytest.fixture
def mock_anthropic():
    """Mock the Anthropic client and API response."""
    mock_client = MagicMock()
    mock_messages = AsyncMock()
    mock_client.messages.create = mock_messages
    
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="""
    {
        "is_work_entry": true,
        "client": "TestClient",
        "project": "TestProject",
        "hours": 4,
        "billable": true,
        "date": "2023-01-15",
        "description": "Working on the test feature"
    }
    """)]
    
    mock_messages.return_value = mock_response
    
    with patch('anthropic.Anthropic', return_value=mock_client):
        yield mock_client

@pytest.mark.asyncio
async def test_analyze_work_entry(mock_anthropic):
    """Test analyzing a work entry message."""
    client = ClaudeClient()
    message = "I worked 4 hours today on TestProject for TestClient"
    
    result = await client.analyze_work_entry(message)
    
    assert result["is_work_entry"] is True
    assert result["client"] == "TestClient"
    assert result["project"] == "TestProject"
    assert result["hours"] == 4
    assert result["billable"] is True
    assert "date" in result
    assert "description" in result

@pytest.mark.asyncio
async def test_generate_response(mock_anthropic):
    """Test generating a response to a user message."""
    client = ClaudeClient()
    message = "Can you help me with my hours?"
    
    # Configure the mock to return a text response
    mock_anthropic.messages.create.return_value.content[0].text = "I can help you track your hours. What did you work on today?"
    
    response = await client.generate_response(message)
    
    assert response == "I can help you track your hours. What did you work on today?"
    mock_anthropic.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_work_entry_error(mock_anthropic):
    """Test error handling in work entry analysis."""
    client = ClaudeClient()
    message = "I worked today"
    
    # Make the API call raise an exception
    mock_anthropic.messages.create.side_effect = Exception("API Error")
    
    result = await client.analyze_work_entry(message)
    
    # Should return a default response on error
    assert result["is_work_entry"] is False