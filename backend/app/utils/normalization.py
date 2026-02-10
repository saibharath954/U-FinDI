import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Any

def normalize_date(date_str: str) -> str:
    """
    Normalize date string to ISO format (YYYY-MM-DD)
    """
    if not date_str or not isinstance(date_str, str):
        return date_str or ""
    
    # Remove whitespace
    date_str = date_str.strip()
    
    # Common date patterns
    patterns = [
        (r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})", "%d/%m/%Y"),  # DD/MM/YYYY or DD-MM-YYYY
        (r"(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})", "%Y-%m-%d"),    # YYYY-MM-DD
        (r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})", "%d %b %Y"),  # 01 Jan 2023
        (r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})", "%b %d %Y"), # Jan 01, 2023
    ]
    
    for pattern, date_format in patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                # Handle 2-digit years
                if date_format == "%d/%m/%Y":
                    day, month, year = match.groups()
                    if len(year) == 2:
                        year = f"20{year}"  # Assume 21st century
                    normalized = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    return normalized
                
                # For other formats, try to parse
                date_obj = datetime.strptime(match.group(), date_format)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
    
    # If no pattern matched, return original
    return date_str

def normalize_currency(amount_str: str) -> str:
    """
    Normalize currency string to standard format
    """
    if not amount_str or not isinstance(amount_str, str):
        return amount_str or ""
    
    # Remove currency symbols and commas
    cleaned = re.sub(r'[^\d\.\-]', '', amount_str)
    
    try:
        # Convert to float and format
        amount = float(cleaned)
        return f"{amount:.2f}"
    except ValueError:
        return amount_str

def normalize_amount(amount: Any) -> float:
    """
    Normalize any amount to float
    """
    if amount is None:
        return 0.0
    
    if isinstance(amount, (int, float)):
        return float(amount)
    
    if isinstance(amount, str):
        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[^\d\.\-]', '', amount.strip())
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    try:
        return float(amount)
    except (ValueError, TypeError):
        return 0.0

def normalize_name(name_str: str) -> str:
    """
    Normalize name string
    """
    if not name_str:
        return ""
    
    # Title case and remove extra whitespace
    normalized = ' '.join(name_str.strip().split())
    
    # Remove special characters except spaces and hyphens
    normalized = re.sub(r'[^A-Za-z\s\-\.]', '', normalized)
    
    # Title case each word
    words = normalized.split()
    words = [word.capitalize() for word in words]
    
    return ' '.join(words)

def normalize_account_number(account_str: str) -> str:
    """
    Normalize account number
    """
    if not account_str:
        return ""
    
    # Remove all non-numeric characters
    cleaned = re.sub(r'\D', '', account_str)
    
    return cleaned

def normalize_phone_number(phone_str: str) -> str:
    """
    Normalize phone number to international format
    """
    if not phone_str:
        return ""
    
    # Remove all non-numeric characters except plus
    cleaned = re.sub(r'[^\d\+]', '', phone_str.strip())
    
    # Add country code if missing
    if cleaned.startswith('0'):
        cleaned = '+44' + cleaned[1:]  # Default to UK
    
    return cleaned

def normalize_percentage(percentage_str: str) -> float:
    """
    Normalize percentage to float (0-1)
    """
    if not percentage_str:
        return 0.0
    
    if isinstance(percentage_str, (int, float)):
        return float(percentage_str) / 100.0
    
    # Remove percentage sign and whitespace
    cleaned = re.sub(r'[^\d\.\-]', '', str(percentage_str).strip())
    
    try:
        value = float(cleaned)
        return value / 100.0
    except ValueError:
        return 0.0

def normalize_boolean(value: Any) -> bool:
    """
    Normalize any value to boolean
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        lower_val = value.lower().strip()
        true_values = ['true', 'yes', 'y', '1', 't']
        false_values = ['false', 'no', 'n', '0', 'f']
        
        if lower_val in true_values:
            return True
        elif lower_val in false_values:
            return False
    
    return bool(value)