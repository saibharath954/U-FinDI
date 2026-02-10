from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    BANK_STATEMENT = "bank_statement"
    INVOICE = "invoice"
    PAYSLIP = "payslip"
    AGREEMENT = "agreement"
    SETTLEMENT_LETTER = "settlement_letter"
    TAX_FORM = "tax_form"
    ID_PROOF = "id_proof"
    UNKNOWN = "unknown"

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    uploaded_at: datetime

class ExtractionRequest(BaseModel):
    document_id: str
    force_reprocess: bool = False

class FieldExtraction(BaseModel):
    field_name: str
    value: Any
    confidence: float
    bounding_box: Optional[List[float]] = None
    page_number: Optional[int] = None

class TableCell(BaseModel):
    row: int
    col: int
    content: str
    confidence: float

class ExtractedTable(BaseModel):
    table_id: str
    rows: Optional[int] = None
    columns: Optional[int] = None
    cells: Optional[list[list[str]]] = None
    bounding_box: Optional[list[int]] = None
    page_number: Optional[int] = None
    confidence: float
    
class ExtractionResponse(BaseModel):
    document_id: str
    document_type: DocumentType
    extracted_fields: Dict[str, Any]
    tables: List[ExtractedTable]
    confidence_scores: Dict[str, float]
    layout_analysis: Dict[str, Any]
    processing_time: float

class ValidationIssue(BaseModel):
    issue_code: str
    severity: str  # error, warning, info
    message: str
    field_path: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None

class ValidationResponse(BaseModel):
    document_id: str
    validation_status: str  # passed, needs_review, failed
    issues: List[ValidationIssue]
    validation_rules_applied: List[str]
    cross_document_consistency: Dict[str, Any]

class CorrectionRequest(BaseModel):
    field: str
    old_value: Optional[Any] = None
    new_value: Any
    reason: Optional[str] = None

class CorrectionResponse(BaseModel):
    correction_id: int
    document_id: str
    status: str
    sent_to_memory: bool

class DashboardMetrics(BaseModel):
    total_documents: int
    documents_by_type: Dict[str, int]
    average_processing_time: float
    extraction_accuracy: Dict[str, float]
    validation_failure_rate: float
    top_error_codes: List[Dict[str, Any]]
    learning_improvements: Dict[str, float]
    recent_corrections: List[Dict[str, Any]]

class FinancialEntity(BaseModel):
    entity_type: str  # bank, employer, account
    entity_name: str
    entity_id: Optional[str] = None
    confidence: float
    normalized_name: Optional[str] = None