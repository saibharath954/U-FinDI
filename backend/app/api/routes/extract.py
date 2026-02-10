from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db, Document, Extraction, ProcessingLog
from app.models.schemas import ExtractionRequest, ExtractionResponse
from app.services.classification_service import classify_document
from app.services.layout_service import analyze_layout
from app.services.extraction_service import extract_fields
from app.core.logger import logger
import time

router = APIRouter()

@router.post("/extract/{document_id}", response_model=ExtractionResponse)
async def extract_document_data(
    document_id: str,
    background_tasks: BackgroundTasks,
    request: Optional[ExtractionRequest] = None
):
    """
    Extract data from a document
    """
    start_time = time.time()
    db = next(get_db())
    
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if already extracted
        existing_extraction = db.query(Extraction).filter(
            Extraction.document_id == document_id
        ).first()
        
        if existing_extraction and not (request and request.force_reprocess):
            logger.info(f"Using cached extraction for document {document_id}")
            # Return cached result
            return ExtractionResponse(
                document_id=document_id,
                document_type=document.document_type,
                extracted_fields=existing_extraction.extracted_fields,
                tables=existing_extraction.tables,
                confidence_scores=existing_extraction.confidence_scores,
                layout_analysis=existing_extraction.layout_data,
                processing_time=0.0
            )
        
        # Update document status
        document.processing_status = "processing"
        db.commit()
        
        # Log start
        log = ProcessingLog(
            document_id=document_id,
            stage="extraction",
            status="started",
            message="Starting document extraction pipeline"
        )
        db.add(log)
        db.commit()
        
        # Step 1: Document Classification
        logger.info(f"Classifying document {document_id}")
        classification_result = classify_document(document.filepath)
        document.document_type = classification_result["document_type"]
        document.language = classification_result.get("language")
        document.image_quality_score = classification_result.get("image_quality_score", 0.8)
        
        # Log classification
        log = ProcessingLog(
            document_id=document_id,
            stage="classification",
            status="success",
            message=f"Document classified as {document.document_type}",
            details=classification_result
        )
        db.add(log)
        
        # Step 2: Layout Analysis
        logger.info(f"Analyzing layout for document {document_id}")
        layout_result = analyze_layout(
            document.filepath,
            document_type=document.document_type
        )
        
        log = ProcessingLog(
            document_id=document_id,
            stage="layout_analysis",
            status="success",
            message="Layout analysis completed",
            details={"regions_found": len(layout_result.get("regions", []))}
        )
        db.add(log)
        
        # Step 3: Field Extraction
        logger.info(f"Extracting fields from document {document_id}")
        extraction_result = extract_fields(
            document.filepath,
            document_type=document.document_type,
            layout_data=layout_result
        )
        
        log = ProcessingLog(
            document_id=document_id,
            stage="field_extraction",
            status="success",
            message=f"Extracted {len(extraction_result.get('fields', {}))} fields",
            details={"fields_extracted": list(extraction_result.get('fields', {}).keys())}
        )
        db.add(log)
        
        # Step 4: Table Reconstruction
        tables = extraction_result.get("tables", [])
        
        # Save extraction results
        extraction = Extraction(
            document_id=document_id,
            extracted_fields=extraction_result.get("fields", {}),
            tables=tables,
            layout_data=layout_result,
            confidence_scores=extraction_result.get("confidence_scores", {})
        )
        db.add(extraction)
        
        # Update document status
        document.processing_status = "extracted"
        db.commit()
        
        processing_time = time.time() - start_time
        
        logger.info(f"Extraction completed for document {document_id} in {processing_time:.2f}s")
        
        # Background task for learning from extraction
        background_tasks.add_task(
            learn_from_extraction,
            document_id=document_id,
            extraction_result=extraction_result,
            layout_result=layout_result
        )
        
        return ExtractionResponse(
            document_id=document_id,
            document_type=document.document_type,
            extracted_fields=extraction_result.get("fields", {}),
            tables=tables,
            confidence_scores=extraction_result.get("confidence_scores", {}),
            layout_analysis=layout_result,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Extraction failed for document {document_id}: {str(e)}")
        
        # Log error
        log = ProcessingLog(
            document_id=document_id,
            stage="extraction",
            status="error",
            message=f"Extraction failed: {str(e)}",
            details={"error": str(e)}
        )
        db.add(log)
        
        # Update document status
        if document:
            document.processing_status = "error"
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

async def learn_from_extraction(document_id: str, extraction_result: dict, layout_result: dict):
    """Background task to learn from extraction results"""
    from app.services.learning_service import store_extraction_pattern
    try:
        await store_extraction_pattern(
            document_id=document_id,
            extraction_data=extraction_result,
            layout_data=layout_result
        )
        logger.info(f"Learning completed for document {document_id}")
    except Exception as e:
        logger.error(f"Learning failed for document {document_id}: {str(e)}")