from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import shutil
from datetime import datetime
from typing import Optional
import uuid

from app.core.config import settings
from app.core.logger import logger
from app.core.database import get_db, Document
from app.models.schemas import UploadResponse
from app.services.ingestion_service import process_document_upload
from app.utils.image_utils import validate_image_quality

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    customer_id: Optional[str] = None,
    document_category: Optional[str] = None
):
    """
    Upload a financial document for processing
    """
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
            )
        
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Generate unique filename
        document_id = str(uuid.uuid4())
        filename = f"{document_id}{file_ext}"
        filepath = os.path.join(settings.upload_dir, filename)
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        db = next(get_db())
        document = Document(
            id=document_id,
            filename=file.filename,
            filepath=filepath,
            file_size=file_size,
            mime_type=file.content_type,
            document_metadata={
                "customer_id": customer_id,
                "category": document_category,
                "original_filename": file.filename
            }
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Add background task for initial processing
        background_tasks.add_task(
            process_document_upload,
            document_id=document_id,
            filepath=filepath,
            customer_id=customer_id,
        )
        
        logger.info(f"Document uploaded: {document_id}, filename: {file.filename}")
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="uploaded",
            uploaded_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")