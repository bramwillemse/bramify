"""Tests for the client mapper functionality."""

import pytest
import os
import json
from unittest.mock import patch, mock_open
from pathlib import Path

from src.integrations.client_mapper import ClientMapper


@pytest.fixture
def sample_mappings():
    """Return sample client-code mappings."""
    return {
        "acmeinc": "ACM",
        "globex": "GLB",
        "wayneenterprises": "WNT",
        "apeture": "APE"
    }


@pytest.fixture
def client_mapper(sample_mappings):
    """Create a ClientMapper with mocked file operations."""
    with patch("builtins.open", mock_open(read_data=json.dumps(sample_mappings))):
        with patch("os.path.exists", return_value=True):
            with patch("os.makedirs"):
                mapper = ClientMapper(config_file="mock_config.json")
                # Set the mappings directly to avoid file operations
                mapper.client_codes = sample_mappings
                return mapper


def test_get_code_exact_match(client_mapper):
    """Test getting a code with an exact match."""
    assert client_mapper.get_code("Acme Inc") == "ACM"
    assert client_mapper.get_code("GLOBEX") == "GLB"
    assert client_mapper.get_code("Wayne Enterprises") == "WNT"


def test_get_code_partial_match(client_mapper):
    """Test getting a code with a partial match."""
    assert client_mapper.get_code("Acme Corporation") == "ACM"
    assert client_mapper.get_code("Globex Corp") == "GLB"


def test_get_code_no_match(client_mapper):
    """Test getting a code with no match."""
    assert client_mapper.get_code("Unknown Client") is None
    assert client_mapper.get_code("") is None


def test_add_mapping(client_mapper):
    """Test adding a new mapping."""
    with patch.object(client_mapper, "_save_mappings"):
        client_mapper.add_mapping("Stark Industries", "STK")
        assert client_mapper.get_code("Stark Industries") == "STK"


def test_normalize_client_name(client_mapper):
    """Test normalizing client names."""
    assert client_mapper._normalize_client_name("Acme, Inc.") == "acmeinc"
    assert client_mapper._normalize_client_name("The Globex Corporation") == "globexcorporation"
    assert client_mapper._normalize_client_name("Wayne & Sons, LLC") == "waynesonsllc"


def test_normalize_code(client_mapper):
    """Test normalizing codes."""
    assert client_mapper._normalize_code("abc") == "ABC"
    assert client_mapper._normalize_code("a1b2c3") == "ABC"
    assert client_mapper._normalize_code("ab") == "ABX"
    assert client_mapper._normalize_code("abcd") == "ABC"


def test_suggest_code_single_word(client_mapper):
    """Test suggesting a code for a single-word client name."""
    assert client_mapper.suggest_code_for_client("Microsoft") == "MIC"
    assert client_mapper.suggest_code_for_client("IBM") == "IBM"
    assert client_mapper.suggest_code_for_client("A") == "AXX"


def test_suggest_code_multiple_words(client_mapper):
    """Test suggesting a code for a multi-word client name."""
    assert client_mapper.suggest_code_for_client("Apple Inc") == "AI"
    assert client_mapper.suggest_code_for_client("Google Cloud Platform") == "GCP"
    assert client_mapper.suggest_code_for_client("Amazon Web Services") == "AWS"


def test_find_existing_clients(client_mapper):
    """Test finding existing clients."""
    results = client_mapper.find_existing_clients("ac")
    assert len(results) == 1
    assert results[0][1] == "ACM"
    
    # Test empty search returns all clients
    all_results = client_mapper.find_existing_clients("")
    assert len(all_results) == len(client_mapper.client_codes)


def test_load_mappings_file_exists():
    """Test loading mappings when the file exists."""
    sample_data = {"testclient": "TST"}
    
    with patch("builtins.open", mock_open(read_data=json.dumps(sample_data))):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("os.makedirs"):
                mapper = ClientMapper(config_file="test_config.json")
                assert mapper.client_codes == sample_data


def test_load_mappings_file_does_not_exist():
    """Test loading mappings when the file doesn't exist."""
    with patch("builtins.open", mock_open()):
        with patch("pathlib.Path.exists", return_value=False):
            with patch("os.makedirs"):
                with patch("json.dump") as mock_dump:
                    mapper = ClientMapper(config_file="test_config.json")
                    assert mapper.client_codes == {}
                    mock_dump.assert_called_once()


def test_save_mappings():
    """Test saving mappings."""
    sample_data = {"testclient": "TST"}
    
    with patch("builtins.open", mock_open()):
        with patch("os.makedirs"):
            with patch("json.dump") as mock_dump:
                mapper = ClientMapper(config_file="test_config.json")
                mapper.client_codes = sample_data
                mapper._save_mappings()
                mock_dump.assert_called_once_with(sample_data, mock_open()(), indent=2)


def test_integration_with_google_sheets():
    """Test integration with GoogleSheetsClient."""
    # We'll mock the GoogleSheetsClient since we can't create a real one in tests
    from unittest.mock import patch, MagicMock
    from src.integrations.google_sheets.client import GoogleSheetsClient
    
    # Create a mock sheets client
    sheets_client = MagicMock(spec=GoogleSheetsClient)
    
    # Create work data with a client code
    work_data = {
        "date": "26-03-2025",
        "client": "Test Client",
        "client_code": "TST",
        "description": "Test work",
        "hours": 3.5,
        "billable": True
    }
    
    # Create a mock for _format_row_data method that we can inspect
    with patch.object(GoogleSheetsClient, "_format_row_data") as mock_format:
        # Call the formatter function to return a real row
        mock_format.side_effect = lambda data: ["26-03-2025", data.get("client_code") or data.get("client"), "Test work", "3.5", "", "297.5"]
        
        # Instantiate a real client and set up minimal mocks
        with patch.object(GoogleSheetsClient, "_setup_sheets_client"):
            with patch.object(GoogleSheetsClient, "_detect_sheet_structure"):
                with patch.object(GoogleSheetsClient, "_find_date_row", return_value=0):
                    client = GoogleSheetsClient()
                    client.column_mapping = {"date": 0, "client": 1, "description": 2, "hours": 3, "unbillable_hours": 4, "revenue": 5}
                    client.test_sheet = "Test-2025"
                    client.spreadsheet_id = "mock_id"
                    client.sheets = MagicMock()
                    
                    # Calls to find next empty row
                    mock_get = MagicMock()
                    mock_get.execute.return_value = {"values": [["header1"], ["row1"]]}
                    client.sheets.spreadsheets().values().get.return_value = mock_get
                    
                    # Call to update the spreadsheet
                    mock_update = MagicMock()
                    mock_update.execute.return_value = {}
                    client.sheets.spreadsheets().values().update.return_value = mock_update
                    
                    # Call the method with work data that has a client code
                    client.add_work_entry(work_data, test_mode=True)
                    
                    # Verify the update was called with expected data
                    client.sheets.spreadsheets().values().update.assert_called_once()
                    call_args = client.sheets.spreadsheets().values().update.call_args[1]
                    
                    # Check that the body contains our client code
                    assert call_args["body"]["values"][0][1] == "TST"  # Client column should be TST