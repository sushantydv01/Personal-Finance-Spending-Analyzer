import os
from typing import Union, Optional
import pandas as pd  # pyrefly: ignore [missing-import]

def load_data(file_path: str) -> pd.DataFrame:
    """
    Safely loads a transaction CSV file into a pandas DataFrame.
    
    Tries decoding with UTF-8 first, then falls back to Latin-1.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: The raw transaction data loaded from the file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or cannot be read.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The transaction file was not found: '{file_path}'")
        
    # Attempt to load the CSV using UTF-8, falling back to Latin-1 if needed
    for encoding in ['utf-8', 'latin-1']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if df.empty:
                raise ValueError(f"The file is empty: '{file_path}'")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")
            
    raise ValueError(f"Could not parse encoding for file: '{file_path}'")


def _clean_numeric_value(val: Union[str, int, float]) -> float:
    """
    Helper function to clean currency strings and parse them to float.
    Handles formats like '$1,234.56', '($45.00)', and '-$45.00'.
    """
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
        
    val_str = str(val).strip()
    if not val_str:
        return 0.0
        
    # Check for parenthesis format indicating a negative amount (e.g. (100.00))
    is_negative = False
    if val_str.startswith('(') and val_str.endswith(')'):
        is_negative = True
        val_str = val_str[1:-1]
        
    # Remove common currency symbols and formatting commas
    val_str = val_str.replace('$', '').replace(',', '').replace(' ', '')
    
    try:
        parsed_val = float(val_str)
        return -parsed_val if is_negative else parsed_val
    except ValueError:
        return 0.0


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans transaction data by normalizing column names, parsing dates,
    formatting currency fields, and handling missing values.
    
    Args:
        df (pd.DataFrame): The raw input DataFrame.
        
    Returns:
        pd.DataFrame: A cleaned DataFrame.
    """
    # Create a copy to prevent side effects on the original DataFrame
    cleaned_df = df.copy()
    
    # Normalize column names to lowercase for robust mapping matching
    original_cols = cleaned_df.columns.str.strip().str.lower()
    cleaned_df.columns = original_cols
    
    # Flexible column mapping to avoid rigid schemas
    column_mapping = {}
    for col in cleaned_df.columns:
        if 'date' in col:
            column_mapping[col] = 'Date'
        elif any(kw in col for kw in ['desc', 'merchant', 'details', 'name']):
            column_mapping[col] = 'Description'
        elif any(kw in col for kw in ['amount', 'val', 'cost', 'price']):
            column_mapping[col] = 'Amount'
        elif 'balance' in col:
            column_mapping[col] = 'Balance'
            
    cleaned_df = cleaned_df.rename(columns=column_mapping)
    
    # Ensure mandatory columns exist; if not, initialize them as defaults
    if 'Date' not in cleaned_df.columns:
        raise ValueError("Missing required column for Date mapping.")
    if 'Description' not in cleaned_df.columns:
        cleaned_df['Description'] = 'Unknown'
    if 'Amount' not in cleaned_df.columns:
        cleaned_df['Amount'] = 0.0
        
    # Clean date strings: pre-resolve letter 'O' instead of digit '0' typos
    date_col = cleaned_df['Date']
    if date_col.dtype == object or pd.api.types.is_string_dtype(date_col):
        cleaned_df['Date'] = (
            date_col.astype(str)
            .str.replace('O', '0', case=False)
            .str.strip()
        )
        
    # Strip whitespace from all string/object columns
    for col in cleaned_df.select_dtypes(include=['object', 'string']).columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
        
    # Parse mixed date formats safely
    try:
        cleaned_df['Date'] = pd.to_datetime(
            cleaned_df['Date'], errors='coerce', format='mixed'
        )
    except (ValueError, TypeError):
        cleaned_df['Date'] = pd.to_datetime(cleaned_df['Date'], errors='coerce')
        
    # Drop rows that have missing or unparseable Dates
    cleaned_df = cleaned_df.dropna(subset=['Date'])
    
    # Fill missing descriptions with a default value
    cleaned_df['Description'] = (
        cleaned_df['Description']
        .fillna('Unknown')
        .replace({'nan': 'Unknown', '': 'Unknown'})
    )
    
    # Parse and clean numerical columns (Amount & Balance)
    cleaned_df['Amount'] = cleaned_df['Amount'].apply(_clean_numeric_value)
    if 'Balance' in cleaned_df.columns:
        cleaned_df['Balance'] = (
            cleaned_df['Balance'].apply(_clean_numeric_value)
        )
    else:
        cleaned_df['Balance'] = 0.0
        
    return cleaned_df


def categorize_transaction(description: Optional[str]) -> str:
    """
    Classifies a transaction description into a category using keyword matching.
    
    Args:
        description (str): The description or merchant name of the transaction.
        
    Returns:
        str: The matched category name (e.g., Food, Transport, Rent, or Other).
    """
    if not isinstance(description, str) or not description.strip():
        return "Other"
        
    desc_lower = description.lower().strip()
    
    # Category keyword mapping setup matching common global/local merchants
    # Wrapped to comply with standard PEP8 line length recommendations
    category_map = {
        "Food": [
            "uber eats", "mcdonalds", "mcdonald's", "starbucks", "starbux",
            "supermarket", "grocery", "restaurant", "walmart", "subway",
            "pizza", "dunkin", "kroger", "whole foods", "cafe", "diner",
            "swiggy", "blinkit", "zepto", "dmart", "bigbasket", "kfc", "domino"
        ],
        "Transport": [
            "uber", "lyft", "gas", "fuel", "subway", "metro", "transit",
            "train", "bus", "shell", "chevron", "mobil", "bp", "exxon",
            "amtrak", "ola"
        ],
        "Entertainment": [
            "netflix", "spotify", "hulu", "disney", "cinema", "movie",
            "steam", "nintendo", "playstation", "xbox", "hbo", "ticketmaster",
            "pvr", "bookmyshow"
        ],
        "Shopping": [
            "amazon", "amzn", "target", "nike", "ebay", "clothing", "mall",
            "best buy", "nordstrom", "sephora", "macys", "zara", "h&m",
            "flipkart", "fk*", "ajio", "myntra", "nykaa"
        ],
        "Utilities": [
            "electric", "water", "gas bill", "internet", "comcast", "at&t",
            "verizon", "phone", "trash", "power", "utility", "sewer",
            "bescom", "jio", "fiber"
        ],
        "Salary": [
            "salary", "paycheck", "payroll", "direct deposit", "income",
            "employer"
        ],
        "Rent": [
            "rent", "mortgage", "landlord", "apartment", "housing", "lease"
        ],
        "Transfer": [
            "venmo", "zelle", "wire", "paypal", "transfer", "cash app",
            "upi", "gpay", "phonepe", "paytm", "zerodha", "atm"
        ],
        "Healthcare": [
            "cvs", "walgreens", "pharmacy", "hospital", "clinic", "medical",
            "doctor", "dentist", "insurance", "care", "prescription",
            "pharmeasy", "apollo"
        ]
    }
    
    for category, keywords in category_map.items():
        if any(keyword in desc_lower for keyword in keywords):
            return category
            
    return "Other"


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Appends extra derived fields to support financial calculations and visualizations.
    
    Derived columns: Month, Weekday, Day, Year, IsExpense, AbsoluteAmount, Category.
    
    Args:
        df (pd.DataFrame): Cleaned DataFrame containing 'Date' and 'Amount' columns.
        
    Returns:
        pd.DataFrame: DataFrame with the new derived columns added.
    """
    df_derived = df.copy()
    
    # Extract date parts using capitalized names
    df_derived['Month'] = df_derived['Date'].dt.month  # type: ignore
    df_derived['Weekday'] = df_derived['Date'].dt.day_name()  # type: ignore
    df_derived['Day'] = df_derived['Date'].dt.day  # type: ignore
    df_derived['Year'] = df_derived['Date'].dt.year  # type: ignore

    
    # Calculate derived logical and magnitude indicators
    df_derived['IsExpense'] = df_derived['Amount'] < 0
    df_derived['AbsoluteAmount'] = df_derived['Amount'].abs()
    
    # Add categorization mapping column
    df_derived['Category'] = (
        df_derived['Description'].apply(categorize_transaction)
    )
    
    return df_derived


def process_data(file_path: str) -> pd.DataFrame:
    """
    Full pipeline execution: loads, cleans, categorizes, and derives columns
    for a transaction dataset.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: Cleaned and structured transaction DataFrame.
    """
    raw_df = load_data(file_path)
    cleaned_df = clean_data(raw_df)
    final_df = add_derived_columns(cleaned_df)
    return final_df


if __name__ == "__main__":
    # Create a small sample CSV to demonstrate pipeline execution
    temp_csv = "temp_transactions.csv"
    sample_data = """Date,Description,Amount,Balance
2026-06-01,Salary Employer,$5000.00,$5000.00
06/02/2026,Uber,($15.50),$4984.50
2026-06-03,Starbucks,-$4.75,$4979.75
2026-06-04,Netflix,,$4979.75
"""
    try:
        with open(temp_csv, "w") as f:
            f.write(sample_data)
            
        print("Executing full data pipeline on sample data...")
        df = process_data(temp_csv)
        print("\nProcessed DataFrame:")
        print(df.to_string())
        
    finally:
        # Cleanup
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
