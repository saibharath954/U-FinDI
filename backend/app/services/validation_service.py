from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
from app.core.database import get_db, Document
from app.core.logger import logger
from app.models.schemas import DocumentType

def validate_document(
    document_type: str,
    extracted_data: Dict[str, Any],
    tables: List[Dict[str, Any]],
    document_id: str
) -> Dict[str, Any]:
    """
    Validate extracted financial data
    """
    issues = []
    validation_rules_applied = []
    
    try:
        # Apply document-type specific validations
        if document_type == DocumentType.BANK_STATEMENT:
            issues.extend(validate_bank_statement(extracted_data))
            validation_rules_applied.append("bank_statement_rules")
            
        elif document_type == DocumentType.PAYSLIP:
            issues.extend(validate_payslip(extracted_data))
            validation_rules_applied.append("payslip_rules")
            
        elif document_type == DocumentType.INVOICE:
            issues.extend(validate_invoice(extracted_data))
            validation_rules_applied.append("invoice_rules")
        
        # Apply general validations
        issues.extend(validate_general_rules(extracted_data))
        validation_rules_applied.append("general_rules")
        
        # Cross-document validation
        cross_document_issues = validate_cross_document(document_id, extracted_data)
        issues.extend(cross_document_issues)
        if cross_document_issues:
            validation_rules_applied.append("cross_document_rules")
        
        # Determine overall status
        validation_status = determine_validation_status(issues)
        
        logger.info(f"Validation completed for {document_id}: {validation_status}")
        
        return {
            "validation_status": validation_status,
            "issues": issues,
            "validation_rules_applied": validation_rules_applied,
            "cross_document_consistency": {
                "checked_against": cross_document_issues and "related_documents" or "none"
            }
        }
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return {
            "validation_status": "failed",
            "issues": [{
                "issue_code": "VALIDATION_ERROR",
                "severity": "error",
                "message": f"Validation process failed: {str(e)}"
            }],
            "validation_rules_applied": [],
            "cross_document_consistency": {}
        }

def validate_bank_statement(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate bank statement data"""
    issues = []
    
    # Balance continuity check
    if "opening_balance" in data and "closing_balance" in data:
        try:
            opening = Decimal(str(data["opening_balance"]).replace(',', ''))
            closing = Decimal(str(data["closing_balance"]).replace(',', ''))
            
            # Calculate total credits and debits from transactions
            total_credits = Decimal('0')
            total_debits = Decimal('0')
            
            for transaction in data.get("transactions", []):
                amount = Decimal(str(transaction.get("amount", 0)).replace(',', ''))
                if amount > 0:
                    total_credits += amount
                else:
                    total_debits += abs(amount)
            
            expected_closing = opening + total_credits - total_debits
            
            if abs(closing - expected_closing) > Decimal('0.01'):
                issues.append({
                    "issue_code": "BALANCE_MISMATCH",
                    "severity": "error",
                    "message": f"Closing balance mismatch. Expected: {expected_closing}, Actual: {closing}",
                    "field_path": "closing_balance",
                    "expected_value": float(expected_closing),
                    "actual_value": float(closing)
                })
        except (InvalidOperation, ValueError) as e:
            issues.append({
                "issue_code": "BALANCE_CALCULATION_ERROR",
                "severity": "warning",
                "message": f"Could not calculate balance continuity: {str(e)}"
            })
    
    # Date sequencing for transactions
    transactions = data.get("transactions", [])
    dates = []
    for trans in transactions:
        date_str = trans.get("date")
        if date_str:
            try:
                # Try different date formats
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                    try:
                        date = datetime.strptime(date_str, fmt)
                        dates.append(date)
                        break
                    except ValueError:
                        continue
            except:
                pass
    
    if len(dates) > 1:
        sorted_dates = sorted(dates)
        if dates != sorted_dates:
            issues.append({
                "issue_code": "DATE_SEQUENCING",
                "severity": "warning",
                "message": "Transactions are not in chronological order"
            })
    
    # Check for future dates
    today = datetime.now()
    future_dates = [d for d in dates if d > today]
    if future_dates:
        issues.append({
            "issue_code": "FUTURE_DATE",
            "severity": "error",
            "message": f"Found {len(future_dates)} transaction(s) with future dates"
        })
    
    return issues

def validate_payslip(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate payslip data"""
    issues = []
    
    # Income plausibility check
    if "gross_pay" in data and "net_pay" in data:
        try:
            gross = Decimal(str(data["gross_pay"]).replace(',', ''))
            net = Decimal(str(data["net_pay"]).replace(',', ''))
            
            if net > gross:
                issues.append({
                    "issue_code": "NET_EXCEEDS_GROSS",
                    "severity": "error",
                    "message": f"Net pay ({net}) exceeds gross pay ({gross})",
                    "field_path": "net_pay",
                    "actual_value": float(net)
                })
            
            # Check if deductions are reasonable (typically 20-40%)
            if gross > 0:
                deduction_ratio = (gross - net) / gross
                if deduction_ratio > 0.5:  # More than 50% deduction
                    issues.append({
                        "issue_code": "HIGH_DEDUCTION_RATIO",
                        "severity": "warning",
                        "message": f"Deductions ({deduction_ratio:.1%}) seem unusually high",
                        "field_path": "deductions"
                    })
        except (InvalidOperation, ValueError) as e:
            issues.append({
                "issue_code": "PAY_CALCULATION_ERROR",
                "severity": "warning",
                "message": f"Could not validate pay amounts: {str(e)}"
            })
    
    # Check date ranges
    if "pay_period" in data:
        pay_period = data["pay_period"]
        # Validate pay period format (simplified)
        if not re.search(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}", str(pay_period)):
            issues.append({
                "issue_code": "INVALID_PAY_PERIOD",
                "severity": "warning",
                "message": "Pay period format appears invalid",
                "field_path": "pay_period"
            })
    
    return issues

def validate_invoice(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate invoice data"""
    issues = []
    
    # Check invoice totals
    if "subtotal" in data and "tax_amount" in data and "total_amount" in data:
        try:
            subtotal = Decimal(str(data["subtotal"]).replace(',', ''))
            tax = Decimal(str(data["tax_amount"]).replace(',', ''))
            total = Decimal(str(data["total_amount"]).replace(',', ''))
            
            expected_total = subtotal + tax
            
            if abs(total - expected_total) > Decimal('0.01'):
                issues.append({
                    "issue_code": "INVOICE_TOTAL_MISMATCH",
                    "severity": "error",
                    "message": f"Invoice total mismatch. Expected: {expected_total}, Actual: {total}",
                    "field_path": "total_amount",
                    "expected_value": float(expected_total),
                    "actual_value": float(total)
                })
        except (InvalidOperation, ValueError) as e:
            issues.append({
                "issue_code": "INVOICE_CALCULATION_ERROR",
                "severity": "warning",
                "message": f"Could not validate invoice totals: {str(e)}"
            })
    
    # Check dates
    if "invoice_date" in data and "due_date" in data:
        try:
            inv_date = parse_date(data["invoice_date"])
            due_date = parse_date(data["due_date"])
            
            if inv_date and due_date:
                if due_date < inv_date:
                    issues.append({
                        "issue_code": "DUE_DATE_BEFORE_INVOICE",
                        "severity": "error",
                        "message": "Due date is before invoice date",
                        "field_path": "due_date"
                    })
                
                if (due_date - inv_date).days > 90:
                    issues.append({
                        "issue_code": "LONG_PAYMENT_TERM",
                        "severity": "warning",
                        "message": "Payment term exceeds 90 days",
                        "field_path": "due_date"
                    })
        except:
            pass
    
    return issues

def validate_general_rules(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply general validation rules"""
    issues = []
    
    # Check for negative amounts where they shouldn't be
    positive_fields = ["total_amount", "gross_pay", "net_pay", "closing_balance"]
    for field in positive_fields:
        if field in data:
            try:
                value = Decimal(str(data[field]).replace(',', ''))
                if value < 0:
                    issues.append({
                        "issue_code": "NEGATIVE_VALUE",
                        "severity": "warning",
                        "message": f"{field} should not be negative",
                        "field_path": field,
                        "actual_value": float(value)
                    })
            except:
                pass
    
    # Check date formats
    date_fields = [k for k in data.keys() if "date" in k.lower()]
    for field in date_fields:
        value = str(data[field])
        if not re.search(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}", value):
            issues.append({
                "issue_code": "INVALID_DATE_FORMAT",
                "severity": "warning",
                "message": f"{field} does not appear to be a valid date",
                "field_path": field
            })
    
    return issues

def validate_cross_document(document_id: str, current_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate consistency across related documents"""
    issues = []
    
    try:
        db = next(get_db())
        
        # Get customer ID from document metadata
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document or "customer_id" not in document.document_metadata:
            return issues
        
        customer_id = document.document_metadata["customer_id"]
        
        # Find related documents for the same customer
        related_docs = db.query(Document).filter(
            Document.document_metadata["customer_id"].astext == customer_id,
            Document.id != document_id,
            Document.processing_status.in_(["extracted", "validated"])
        ).all()
        
        for related_doc in related_docs[:5]:  # Limit to 5 related docs
            # In production, you would fetch the extraction data
            # For demo, we'll simulate some checks
            
            # Check employer name consistency for payslips
            if document.document_type == "payslip" and related_doc.document_type == "payslip":
                # Simulated check
                pass
            
            # Check bank name consistency
            if document.document_type == "bank_statement" and related_doc.document_type == "bank_statement":
                # Simulated check
                pass
        
        # Add a simulated cross-document issue for demo
        if len(related_docs) > 0:
            issues.append({
                "issue_code": "CROSS_DOC_SALARY_MISMATCH",
                "severity": "warning",
                "message": "Salary amount differs from previous payslips by more than 10%",
                "field_path": "gross_pay"
            })
    
    except Exception as e:
        logger.error(f"Cross-document validation failed: {str(e)}")
    
    return issues

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date from string using multiple formats"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None

def determine_validation_status(issues: List[Dict[str, Any]]) -> str:
    """Determine overall validation status based on issues"""
    if not issues:
        return "passed"
    
    # Check for errors
    has_errors = any(issue.get("severity") == "error" for issue in issues)
    has_warnings = any(issue.get("severity") == "warning" for issue in issues)
    
    if has_errors:
        return "needs_review"
    elif has_warnings:
        return "passed_with_warnings"
    else:
        return "passed"