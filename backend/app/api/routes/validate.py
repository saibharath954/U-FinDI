from fastapi import APIRouter, HTTPException
from app.core.database import get_db, Document, Extraction, Validation
from app.models.schemas import ValidationResponse, ValidationIssue
from app.services.validation_service import validate_document
from app.core.logger import logger

router = APIRouter()

@router.post("/validate/{document_id}", response_model=ValidationResponse)
async def validate_document_data(document_id: str):
    """
    Validate extracted financial data
    """
    db = next(get_db())
    
    try:
        # Get document and extraction
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        extraction = db.query(Extraction).filter(
            Extraction.document_id == document_id
        ).first()
        
        if not extraction:
            raise HTTPException(status_code=400, detail="Document not extracted yet")
        
        # Run validation
        validation_result = validate_document(
            document_type=document.document_type,
            extracted_data=extraction.extracted_fields,
            tables=extraction.tables,
            document_id=document_id
        )
        
        # Save validation results
        validation = Validation(
            document_id=document_id,
            validation_status=validation_result["validation_status"],
            issues=validation_result["issues"],
            cross_document_checks=validation_result.get("cross_document_consistency", {})
        )
        db.add(validation)
        
        # Update document status
        document.processing_status = "validated"
        db.commit()
        
        # Convert issues to Pydantic models
        validation_issues = [
            ValidationIssue(
                issue_code=issue["issue_code"],
                severity=issue["severity"],
                message=issue["message"],
                field_path=issue.get("field_path"),
                expected_value=issue.get("expected_value"),
                actual_value=issue.get("actual_value")
            )
            for issue in validation_result["issues"]
        ]
        
        logger.info(f"Validation completed for document {document_id}: {validation_result['validation_status']}")
        
        return ValidationResponse(
            document_id=document_id,
            validation_status=validation_result["validation_status"],
            issues=validation_issues,
            validation_rules_applied=validation_result.get("validation_rules_applied", []),
            cross_document_consistency=validation_result.get("cross_document_consistency", {})
        )
        
    except Exception as e:
        logger.error(f"Validation failed for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")