import pytesseract
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
from app.core.logger import logger
from app.models.schemas import DocumentType
from app.utils.normalization import normalize_date, normalize_currency, normalize_amount

def extract_fields(filepath: str, document_type: str, layout_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract fields from document based on type and layout
    """
    try:
        # Extract text from document
        text = extract_text_with_ocr(filepath)
        
        # Extract based on document type
        if document_type == DocumentType.BANK_STATEMENT:
            return extract_bank_statement_fields(text, layout_data)
        elif document_type == DocumentType.PAYSLIP:
            return extract_payslip_fields(text, layout_data)
        elif document_type == DocumentType.INVOICE:
            return extract_invoice_fields(text, layout_data)
        elif document_type == DocumentType.AGREEMENT:
            return extract_agreement_fields(text, layout_data)
        else:
            return extract_generic_fields(text, layout_data)
            
    except Exception as e:
        logger.error(f"Field extraction failed: {str(e)}")
        return {"fields": {}, "tables": [], "confidence_scores": {}}

def extract_text_with_ocr(filepath: str) -> str:
    """Extract text using OCR with preprocessing"""
    try:
        if filepath.lower().endswith('.pdf'):
            from app.utils.pdf_utils import convert_pdf_to_images
            images = convert_pdf_to_images(filepath, limit=5)  # First 5 pages
            full_text = ""
            for i, img in enumerate(images):
                # Preprocess image for better OCR
                processed_img = preprocess_image_for_ocr(np.array(img))
                text = pytesseract.image_to_string(Image.fromarray(processed_img))
                full_text += f"\n--- Page {i+1} ---\n{text}\n"
            return full_text
        else:
            image = Image.open(filepath)
            processed_img = preprocess_image_for_ocr(np.array(image))
            return pytesseract.image_to_string(Image.fromarray(processed_img))
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        return ""

def preprocess_image_for_ocr(image: np.ndarray) -> np.ndarray:
    """Preprocess image for better OCR results"""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Binarize
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def extract_bank_statement_fields(text: str, layout_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract fields from bank statement"""
    fields = {}
    confidence_scores = {}
    
    # Extract account information
    account_patterns = {
        "account_number": r"Account\s*[#:]?\s*(\d{8,16})",
        "account_holder": r"Account\s*Holder\s*[:]?\s*([A-Za-z\s\.]+)",
        "bank_name": r"(?:Bank|Financial Institution)\s*[:]?\s*([A-Za-z\s\.]+)",
        "statement_date": r"Statement\s*Date\s*[:]?\s*([\d\/\.-]+)",
        "opening_balance": r"Opening\s*Balance\s*[:]?\s*([\d,]+\.?\d*)",
        "closing_balance": r"(?:Closing|Ending)\s*Balance\s*[:]?\s*([\d,]+\.?\d*)"
    }
    
    for field_name, pattern in account_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields[field_name] = match.group(1).strip()
            confidence_scores[field_name] = 0.9
    
    # Extract transaction table (simplified)
    transactions = extract_transaction_table(text)
    if transactions:
        fields["transactions"] = transactions
        confidence_scores["transactions"] = 0.7
    
    # Extract totals
    total_patterns = {
        "total_credits": r"Total\s*Credits\s*[:]?\s*([\d,]+\.?\d*)",
        "total_debits": r"Total\s*Debits\s*[:]?\s*([\d,]+\.?\d*)"
    }
    
    for field_name, pattern in total_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields[field_name] = normalize_amount(match.group(1))
            confidence_scores[field_name] = 0.8
    
    return {
        "fields": fields,
        "tables": extract_tables_from_layout(layout_data),
        "confidence_scores": confidence_scores
    }

def extract_payslip_fields(text: str, layout_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract fields from payslip"""
    fields = {}
    confidence_scores = {}
    
    payslip_patterns = {
        "employee_name": r"Employee\s*Name\s*[:]?\s*([A-Za-z\s\.]+)",
        "employee_id": r"Employee\s*[I#]D\s*[:]?\s*(\w+)",
        "employer_name": r"Employer\s*[:]?\s*([A-Za-z\s\.&]+)",
        "pay_period": r"Pay\s*Period\s*[:]?\s*([\d\/\.\s-]+(?:to|through)[\d\/\.\s-]+)",
        "gross_pay": r"Gross\s*Pay\s*[:]?\s*([\d,]+\.?\d*)",
        "net_pay": r"Net\s*Pay\s*[:]?\s*([\d,]+\.?\d*)",
        "tax_amount": r"Tax\s*[:]?\s*([\d,]+\.?\d*)",
        "insurance_amount": r"(?:National\s*)?Insurance\s*[:]?\s*([\d,]+\.?\d*)"
    }
    
    for field_name, pattern in payslip_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Normalize amounts
            if "pay" in field_name or "amount" in field_name:
                value = normalize_amount(value)
            fields[field_name] = value
            confidence_scores[field_name] = 0.85
    
    # Extract deduction breakdown
    deductions = extract_deductions(text)
    if deductions:
        fields["deductions"] = deductions
        confidence_scores["deductions"] = 0.7
    
    return {
        "fields": fields,
        "tables": extract_tables_from_layout(layout_data),
        "confidence_scores": confidence_scores
    }

def extract_invoice_fields(text: str, layout_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract fields from invoice"""
    fields = {}
    confidence_scores = {}
    
    invoice_patterns = {
        "invoice_number": r"Invoice\s*[#:]?\s*(\w+)",
        "invoice_date": r"Invoice\s*Date\s*[:]?\s*([\d\/\.-]+)",
        "due_date": r"Due\s*Date\s*[:]?\s*([\d\/\.-]+)",
        "bill_to": r"Bill\s*To\s*[:]?\s*(.+)",
        "ship_to": r"Ship\s*To\s*[:]?\s*(.+)",
        "total_amount": r"Total\s*(?:Amount)?\s*[:]?\s*([\d,]+\.?\d*)",
        "tax_amount": r"Tax\s*[:]?\s*([\d,]+\.?\d*)",
        "subtotal": r"Subtotal\s*[:]?\s*([\d,]+\.?\d*)"
    }
    
    for field_name, pattern in invoice_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Normalize amounts and dates
            if "amount" in field_name or "total" in field_name or "subtotal" in field_name:
                value = normalize_amount(value)
            elif "date" in field_name:
                value = normalize_date(value)
            fields[field_name] = value
            confidence_scores[field_name] = 0.85
    
    # Extract line items
    line_items = extract_line_items(text)
    if line_items:
        fields["line_items"] = line_items
        confidence_scores["line_items"] = 0.7
    
    return {
        "fields": fields,
        "tables": extract_tables_from_layout(layout_data),
        "confidence_scores": confidence_scores
    }

def extract_generic_fields(text: str, layout_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract generic fields from any document"""
    fields = {}
    confidence_scores = {}
    
    # Extract dates
    date_patterns = [
        r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}",
        r"\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}",
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}"
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        dates_found.extend(matches)
    
    if dates_found:
        fields["dates"] = [normalize_date(d) for d in dates_found[:5]]
        confidence_scores["dates"] = 0.8
    
    # Extract amounts
    amount_pattern = r"\$?\s*(\d{1,3}(?:,\d{3})*\.?\d{0,2})"
    amounts = re.findall(amount_pattern, text)
    if amounts:
        fields["amounts"] = [normalize_amount(a) for a in amounts[:10]]
        confidence_scores["amounts"] = 0.7
    
    # Extract names (simple pattern)
    name_pattern = r"(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
    names = re.findall(name_pattern, text)
    if names:
        fields["names"] = names[:5]
        confidence_scores["names"] = 0.6
    
    return {
        "fields": fields,
        "tables": extract_tables_from_layout(layout_data),
        "confidence_scores": confidence_scores
    }

def extract_transaction_table(text: str) -> List[Dict[str, Any]]:
    """Extract transactions from text (simplified)"""
    transactions = []
    
    # Look for transaction patterns
    lines = text.split('\n')
    for line in lines:
        # Simple pattern for date, description, amount
        pattern = r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d{2})"
        match = re.search(pattern, line)
        if match:
            transactions.append({
                "date": normalize_date(match.group(1)),
                "description": match.group(2).strip(),
                "amount": normalize_amount(match.group(3))
            })
    
    return transactions[:20]  # Limit to 20 transactions

def extract_deductions(text: str) -> List[Dict[str, Any]]:
    """Extract deductions from payslip"""
    deductions = []
    
    # Look for deduction lines
    lines = text.split('\n')
    deduction_keywords = ["tax", "insurance", "pension", "deduction", "withholding"]
    
    for line in lines:
        if any(keyword in line.lower() for keyword in deduction_keywords):
            # Try to extract amount
            amount_match = re.search(r"([\d,]+\.?\d{2})", line)
            if amount_match:
                deduction_name = line.split(':')[0].strip() if ':' in line else line.strip()
                deductions.append({
                    "name": deduction_name[:50],
                    "amount": normalize_amount(amount_match.group(1))
                })
    
    return deductions[:10]

def extract_line_items(text: str) -> List[Dict[str, Any]]:
    """Extract line items from invoice"""
    line_items = []
    
    # Look for item patterns (simplified)
    lines = text.split('\n')
    item_pattern = r"(\d+)\s+(.+?)\s+([\d,]+\.?\d{2})\s+([\d,]+\.?\d{2})"
    
    for line in lines:
        match = re.search(item_pattern, line)
        if match:
            line_items.append({
                "quantity": int(match.group(1)),
                "description": match.group(2).strip(),
                "unit_price": normalize_amount(match.group(3)),
                "total": normalize_amount(match.group(4))
            })
    
    return line_items[:20]

def extract_tables_from_layout(layout_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert layout tables to extracted tables"""
    tables = []
    
    for i, table in enumerate(layout_data.get("tables", [])[:5]):
        tables.append({
            "table_id": f"table_{i}",
            "bbox": table.get("bbox", []),
            "cell_count": table.get("cell_count", 1),
            "confidence": table.get("confidence", 0.5)
        })
    
    return tables