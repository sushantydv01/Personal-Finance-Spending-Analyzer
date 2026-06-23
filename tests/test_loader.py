import pytest
import pandas as pd  # pyrefly: ignore [missing-import]
from utils.data_loader import clean_data, categorize_transaction

def test_date_parsing():
    """Tests that mixed date formats are parsed successfully and invalid dates are dropped."""
    data = {
        'Date': ['2026-06-01', '06/02/2026', '2026/06/03', 'invalid-date'],
        'Description': ['Uber', 'Spotify', 'Target', 'McDonalds'],
        'Amount': [10.0, -15.0, 50.0, -5.0]
    }
    df = pd.DataFrame(data)
    cleaned = clean_data(df)
    
    # The invalid row should have been dropped
    assert len(cleaned) == 3
    # Check if 'Date' column contains datetime types
    assert pd.api.types.is_datetime64_any_dtype(cleaned['Date'])
    assert cleaned['Date'].iloc[0] == pd.Timestamp('2026-06-01')
    assert cleaned['Date'].iloc[1] == pd.Timestamp('2026-06-02')
    assert cleaned['Date'].iloc[2] == pd.Timestamp('2026-06-03')


def test_categorization():
    """Tests the keyword-based classification rule mappings."""
    assert categorize_transaction("Uber Eats order") == "Food"
    assert categorize_transaction("Uber trip") == "Transport"
    assert categorize_transaction("Spotify music") == "Entertainment"
    assert categorize_transaction("Target store") == "Shopping"
    assert categorize_transaction("Comcast internet") == "Utilities"
    assert categorize_transaction("Monthly Salary deposit") == "Salary"
    assert categorize_transaction("Apartment Rent payment") == "Rent"
    assert categorize_transaction("Venmo transfer") == "Transfer"
    assert categorize_transaction("CVS pharmacy medicine") == "Healthcare"
    assert categorize_transaction("Some random purchase") == "Other"
    assert categorize_transaction("") == "Other"
    assert categorize_transaction(None) == "Other"


def test_missing_value_handling():
    """Tests parsing raw messy values (currency formatting, missing descriptions/amounts)."""
    data = {
        'Date': ['2026-06-01', '2026-06-02', '2026-06-03'],
        'Description': [None, 'Uber', 'Netflix'],
        'Amount': [None, '$1,234.56', '($45.00)'],
        'Balance': [None, '$5,000.00', '']
    }
    df = pd.DataFrame(data)
    cleaned = clean_data(df)
    
    # Missing description should default to 'Unknown'
    assert cleaned['Description'].iloc[0] == 'Unknown'
    
    # Numerical validation of formatted values
    assert cleaned['Amount'].iloc[0] == 0.0
    assert cleaned['Amount'].iloc[1] == 1234.56
    assert cleaned['Amount'].iloc[2] == -45.00
    
    # Validation of balance cleaning
    assert cleaned['Balance'].iloc[0] == 0.0
    assert cleaned['Balance'].iloc[1] == 5000.00
    assert cleaned['Balance'].iloc[2] == 0.0
