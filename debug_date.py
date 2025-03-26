"""Debug script voor date_utils."""

from src.utils.date_utils import parse_date_text

# Test Amerikaanse datumnotatie
result = parse_date_text("On 01/15/2023 I worked on Project X")
print(f"Result for American date format: {result}")