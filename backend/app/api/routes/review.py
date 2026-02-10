from fastapi import APIRouter, HTTPException
from app.core.database import get_db, Document, Correction, Extraction
from app.models.schemas import CorrectionRequest, CorrectionResponse
from app.services.learning_service import store_correction
from app.core.logger import logger
from datetime import datetime

router = APIRouter()

@router.post("/review/{document_id}", response_model=CorrectionResponse)
async def submit_human_correction(
    document_id: str,
    correction: CorrectionRequest
):
    """
    Submit human corrections for extracted data
    """
    db = next(get_db())
    
    try:
        # Verify document exists
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get current extraction
        extraction = db.query(Extraction).filter(
            Extraction.document_id == document_id
        ).first()
        
        if not extraction:
            raise HTTPException(status_code=400, detail="Document not extracted yet")
        
        # Get old value from extraction if not provided
        old_value = correction.old_value
        if old_value is None:
            # Try to find old value in extracted fields
            import jsonpath_ng
            try:
                jsonpath_expr = jsonpath_ng.parse(correction.field)
                matches = [match.value for match in jsonpath_expr.find(extraction.extracted_fields)]
                if matches:
                    old_value = matches[0]
            except:
                old_value = None
        
        # Save correction to database
        correction_record = Correction(
            document_id=document_id,
            field_path=correction.field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(correction.new_value),
            corrected_by="human_reviewer",
            corrected_at=datetime.now()
        )
        db.add(correction_record)
        db.commit()
        db.refresh(correction_record)
        
        # Update extraction with corrected value
        # This is a simplified update - in production, you'd need proper JSON field updating
        extracted_fields = extraction.extracted_fields
        if "." in correction.field:
            # Nested field - simplified handling
            field_parts = correction.field.split(".")
            current = extracted_fields
            for part in field_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[field_parts[-1]] = correction.new_value
        else:
            extracted_fields[correction.field] = correction.new_value
        
        extraction.extracted_fields = extracted_fields
        db.commit()
        
        # Store correction in memory layer (Backboard.io)
        try:
            await store_correction(
                document_id=document_id,
                correction=correction_record,
                document_type=document.document_type
            )
            correction_record.sent_to_backboard = True
            db.commit()
            sent_to_memory = True
        except Exception as e:
            logger.error(f"Failed to store correction in memory layer: {str(e)}")
            sent_to_memory = False
        
        logger.info(f"Correction submitted for document {document_id}, field: {correction.field}")
        
        return CorrectionResponse(
            correction_id=correction_record.id,
            document_id=document_id,
            status="accepted",
            sent_to_memory=sent_to_memory
        )
        
    except Exception as e:
        logger.error(f"Correction submission failed for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Correction submission failed: {str(e)}")