"""Tests for date utilities."""

import pytest
from datetime import datetime, timedelta
from src.utils.date_utils import parse_date_text, get_date_range_for_period

def test_parse_date_today():
    """Test parsing 'today' from text."""
    today = datetime.now().date().strftime("%Y-%m-%d")
    assert parse_date_text("Today I worked on Project X") == today
    assert parse_date_text("I worked today on Project X") == today

def test_parse_date_yesterday():
    """Test parsing 'yesterday' from text."""
    yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert parse_date_text("Yesterday I worked on Project X") == yesterday
    assert parse_date_text("I worked yesterday on Project X") == yesterday

def test_parse_date_formats():
    """Test parsing various date formats."""
    # ISO format
    assert parse_date_text("On 2023-01-15 I worked on Project X") == "2023-01-15"
    
    # European format
    assert parse_date_text("On 15-01-2023 I worked on Project X") == "2023-01-15"
    assert parse_date_text("On 15/01/2023 I worked on Project X") == "2023-01-15"
    
    # American format
    assert parse_date_text("On 01/15/2023 I worked on Project X") == "2023-01-15"

def test_get_date_range_today():
    """Test getting date range for 'today'."""
    today = datetime.now().date().strftime("%Y-%m-%d")
    start, end = get_date_range_for_period("today")
    assert start == today
    assert end == today
    
    # Test alias
    start, end = get_date_range_for_period("day")
    assert start == today
    assert end == today

def test_get_date_range_this_week():
    """Test getting date range for 'this week'."""
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    
    start, end = get_date_range_for_period("this week")
    assert start == monday.strftime("%Y-%m-%d")
    assert end == today.strftime("%Y-%m-%d")
    
    # Test alias
    start, end = get_date_range_for_period("week")
    assert start == monday.strftime("%Y-%m-%d")
    assert end == today.strftime("%Y-%m-%d")

def test_get_date_range_this_month():
    """Test getting date range for 'this month'."""
    today = datetime.now().date()
    first_day = today.replace(day=1)
    
    start, end = get_date_range_for_period("this month")
    assert start == first_day.strftime("%Y-%m-%d")
    assert end == today.strftime("%Y-%m-%d")
    
    # Test alias
    start, end = get_date_range_for_period("month")
    assert start == first_day.strftime("%Y-%m-%d")
    assert end == today.strftime("%Y-%m-%d")