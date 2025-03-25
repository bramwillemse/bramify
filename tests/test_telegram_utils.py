"""Tests for Telegram utilities."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from src.integrations.telegram.utils import format_work_summary, send_typing_action


class MockUpdate:
    """Mock for Telegram Update."""
    
    def __init__(self):
        self.message = MagicMock()
        self.message.chat = MagicMock()
        self.message.chat.send_action = AsyncMock()


@pytest.mark.asyncio
async def test_send_typing_action():
    """Test sending typing action."""
    # Setup
    update = MockUpdate()
    
    # Execute
    await send_typing_action(update)
    
    # Verify
    update.message.chat.send_action.assert_called_once_with(action="typing")


@pytest.mark.asyncio
async def test_send_typing_action_with_exception():
    """Test handling exceptions in send_typing_action."""
    # Setup
    update = MockUpdate()
    update.message.chat.send_action.side_effect = Exception("Test exception")
    
    # Execute (should not raise an exception)
    await send_typing_action(update)
    
    # Verify method was called despite the exception
    update.message.chat.send_action.assert_called_once_with(action="typing")


def test_format_work_summary_empty():
    """Test formatting with empty entries."""
    summary = format_work_summary([])
    assert summary == "Geen werkregistraties gevonden."


def test_format_work_summary_billable_hours():
    """Test formatting with billable hours."""
    entries = [
        {
            "Date": "25-03-2025",
            "Client": "Client A",
            "Description": "Development",
            "Hours": "3.5",
            "Unbillable Hours": "",
            "Revenue": "350"
        }
    ]
    
    summary = format_work_summary(entries)
    
    assert "Totale Uren: 3.5" in summary
    assert "Factureerbare Uren: 3.5" in summary
    assert "Niet-Factureerbare Uren: 0.0" in summary
    assert "*Client A*: 3.5 uren" in summary
    assert "Development: 3.5 uren" in summary


def test_format_work_summary_unbillable_hours():
    """Test formatting with unbillable hours."""
    entries = [
        {
            "Date": "25-03-2025",
            "Client": "Client A",
            "Description": "Admin",
            "Hours": "",
            "Unbillable Hours": "2.0",
            "Revenue": ""
        }
    ]
    
    summary = format_work_summary(entries)
    
    assert "Totale Uren: 2.0" in summary
    assert "Factureerbare Uren: 0.0" in summary
    assert "Niet-Factureerbare Uren: 2.0" in summary
    assert "*Client A*: 2.0 uren" in summary
    assert "Admin (niet-factureerbaar): 2.0 uren" in summary


def test_format_work_summary_mixed_hours():
    """Test formatting with mix of billable and unbillable hours."""
    entries = [
        {
            "Date": "25-03-2025",
            "Client": "Client A",
            "Description": "Development",
            "Hours": "3.5",
            "Unbillable Hours": "",
            "Revenue": "350"
        },
        {
            "Date": "25-03-2025",
            "Client": "Client A",
            "Description": "Admin",
            "Hours": "",
            "Unbillable Hours": "1.5",
            "Revenue": ""
        }
    ]
    
    summary = format_work_summary(entries)
    
    assert "Totale Uren: 5.0" in summary
    assert "Factureerbare Uren: 3.5" in summary
    assert "Niet-Factureerbare Uren: 1.5" in summary
    assert "*Client A*: 5.0 uren" in summary


def test_format_work_summary_with_period_info():
    """Test formatting with period information."""
    entries = [
        {
            "Date": "25-03-2025",
            "Client": "Client A",
            "Description": "Development",
            "Hours": "3.5",
            "Unbillable Hours": "",
            "Revenue": "350"
        }
    ]
    
    # Test day period
    day_summary = format_work_summary(entries, "day", 25)
    assert "📅" in day_summary
    
    # Test week period
    week_summary = format_work_summary(entries, "week", 12)
    assert "📆" in week_summary
    assert "Week 12" in week_summary
    
    # Test month period
    month_summary = format_work_summary(entries, "month", 3)
    assert "📋" in month_summary
    assert "Maart" in month_summary


def test_format_work_summary_deduplicate():
    """Test deduplication of entries."""
    # Create duplicate entries
    entries = [
        {
            "Date": "25-03-2025",
            "Client": "Client A",
            "Description": "Development",
            "Hours": "3.5",
            "Unbillable Hours": "",
            "Revenue": "350"
        },
        {
            "Date": "25-03-2025",
            "Client": "Client A",
            "Description": "Development",
            "Hours": "3.5",
            "Unbillable Hours": "",
            "Revenue": "350"
        }
    ]
    
    summary = format_work_summary(entries)
    
    # After deduplication, we should only have 3.5 hours total, not 7.0
    assert "Totale Uren: 3.5" in summary
    assert "*Client A*: 3.5 uren" in summary