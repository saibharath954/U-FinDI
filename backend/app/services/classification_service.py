import os
from typing import Dict, Any
import pytesseract
from PIL import Image
import cv2
import numpy as np
from langdetect import detect
from app.core.logger import logger
from app.models.schemas import DocumentType

def classify_document(filepath: str) -> Dict[str, Any]:
    """
    Classify document type and detect language
    """
    try:
        # Extract text for analysis
        text = extract_text_from_file(filepath)
        
        if not text or len(text.strip()) < 10:
            return {
                "document_type": DocumentType.UNKNOWN,
                "confidence": 0.1,
                "image_quality_score": 0.1
            }
        
        # Detect language
        try:
            language = detect(text[:1000])
        except:
            language = "en"
        
        # Analyze text patterns for classification
        document_type, confidence = analyze_text_patterns(text)
        
        # Calculate image quality score
        quality_score = calculate_image_quality(filepath)
        
        logger.info(f"Document classified as {document_type} with confidence {confidence}")
        
        return {
            "document_type": document_type,
            "confidence": confidence,
            "language": language,
            "image_quality_score": quality_score,
            "text_sample": text[:500]
        }
        
    except Exception as e:
        logger.error(f"Classification failed: {str(e)}")
        return {
            "document_type": DocumentType.UNKNOWN,
            "confidence": 0.0,
            "language": "en",
            "image_quality_score": 0.5
        }

def extract_text_from_file(filepath: str) -> str:
    """Extract text using OCR"""
    try:
        if filepath.lower().endswith('.pdf'):
            from app.utils.pdf_utils import convert_pdf_to_images
            images = convert_pdf_to_images(filepath)
            text = ""
            for img in images[:3]:  # First 3 pages only
                text += pytesseract.image_to_string(img) + "\n"
        else:
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image)
        
        return text
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return ""

def analyze_text_patterns(text: str):
    """Analyze text patterns to classify document type"""
    text_lower = text.lower()
    
    # Keywords for different document types
    keywords = {
        DocumentType.BANK_STATEMENT: [
            "account", "balance", "transaction", "debit", "credit",
            "statement", "bank", "withdrawal", "deposit"
        ],
        DocumentType.PAYSLIP: [
            "salary", "pay slip", "net pay", "gross pay", "deduction",
            "employee", "employer", "tax", "national insurance"
        ],
        DocumentType.INVOICE: [
            "invoice", "bill to", "ship to", "quantity", "total",
            "subtotal", "tax", "amount due", "item"
        ],
        DocumentType.AGREEMENT: [
            "agreement", "contract", "terms", "conditions",
            "party", "signature", "effective date"
        ]
    }
    
    scores = {}
    for doc_type, doc_keywords in keywords.items():
        score = 0
        for keyword in doc_keywords:
            if keyword in text_lower:
                score += 1
        scores[doc_type] = score / max(len(doc_keywords), 1)
    
    # Find best match
    best_type = max(scores.items(), key=lambda x: x[1])
    
    if best_type[1] > 0.3:
        return best_type[0], best_type[1]
    else:
        return DocumentType.UNKNOWN, 0.1

def calculate_image_quality(filepath: str) -> float:
    """Calculate image quality score"""
    try:
        if filepath.lower().endswith('.pdf'):
            from app.utils.pdf_utils import convert_pdf_to_images
            images = convert_pdf_to_images(filepath, limit=1)
            if not images:
                return 0.5
            image = np.array(images[0])
        else:
            image = cv2.imread(filepath)
        
        if image is None:
            return 0.5
        
        # Simple quality metrics
        # 1. Sharpness (Laplacian variance)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 2. Contrast
        contrast = gray.std()
        
        # 3. Brightness
        brightness = gray.mean()
        
        # Normalize scores
        sharpness_score = min(sharpness / 1000, 1.0)
        contrast_score = min(contrast / 100, 1.0)
        brightness_score = 1.0 - abs(brightness - 128) / 128
        
        # Weighted average
        quality_score = (
            sharpness_score * 0.4 +
            contrast_score * 0.3 +
            brightness_score * 0.3
        )
        
        return max(0.1, min(1.0, quality_score))
        
    except Exception as e:
        logger.error(f"Image quality calculation failed: {str(e)}")
        return 0.5