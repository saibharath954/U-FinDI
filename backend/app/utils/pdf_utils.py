import os
import tempfile
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
from typing import List, Optional
from app.core.logger import logger

def convert_pdf_to_images(
    pdf_path: str,
    dpi: int = 200,
    limit: Optional[int] = None
) -> List[Image.Image]:
    """
    Convert PDF to list of images
    """
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        
        if limit and len(images) > limit:
            images = images[:limit]
        
        logger.info(f"Converted PDF to {len(images)} images")
        return images
        
    except Exception as e:
        logger.error(f"PDF conversion failed: {str(e)}")
        return []

def convert_pdf_bytes_to_images(
    pdf_bytes: bytes,
    dpi: int = 200,
    limit: Optional[int] = None
) -> List[Image.Image]:
    """
    Convert PDF bytes to list of images
    """
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        
        if limit and len(images) > limit:
            images = images[:limit]
        
        logger.info(f"Converted PDF bytes to {len(images)} images")
        return images
        
    except Exception as e:
        logger.error(f"PDF bytes conversion failed: {str(e)}")
        return []

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using OCR
    """
    try:
        import pytesseract
        images = convert_pdf_to_images(pdf_path, limit=3)  # First 3 pages
        
        text = ""
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img)
            text += f"\n--- Page {i+1} ---\n{page_text}\n"
        
        return text
        
    except Exception as e:
        logger.error(f"PDF text extraction failed: {str(e)}")
        return ""

def get_pdf_metadata(pdf_path: str) -> dict:
    """
    Get PDF metadata
    """
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            metadata = {
                "page_count": len(pdf_reader.pages),
                "author": pdf_reader.metadata.get("/Author", ""),
                "creator": pdf_reader.metadata.get("/Creator", ""),
                "producer": pdf_reader.metadata.get("/Producer", ""),
                "title": pdf_reader.metadata.get("/Title", ""),
                "subject": pdf_reader.metadata.get("/Subject", ""),
                "created": pdf_reader.metadata.get("/CreationDate", ""),
                "modified": pdf_reader.metadata.get("/ModDate", "")
            }
            
            return metadata
            
    except Exception as e:
        logger.error(f"PDF metadata extraction failed: {str(e)}")
        return {}