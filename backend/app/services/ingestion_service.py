import os
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import magic
from PIL import Image
import cv2
import numpy as np
import json
from pathlib import Path

from app.core.config import settings
from app.core.logger import logger
from app.core.database import get_db, Document, ProcessingLog
from app.utils.image_utils import validate_image_quality, preprocess_image_for_ocr
from app.utils.pdf_utils import convert_pdf_to_images, extract_text_from_pdf, get_pdf_metadata
from app.models.schemas import DocumentType

class IngestionService:
    """Service for document ingestion and initial processing"""
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)
        self.supported_mime_types = {
            'application/pdf': 'pdf',
            'image/png': 'png',
            'image/jpeg': 'jpeg',
            'image/jpg': 'jpg',
            'image/tiff': 'tiff',
            'image/bmp': 'bmp'
        }
    
    async def process_document_upload(
        self,
        document_id: str,
        filepath: str,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process uploaded document - initial analysis and quality checks
        """
        try:
            db = next(get_db())
            
            # Log start
            self._log_processing(db, document_id, "ingestion", "started", "Starting document ingestion")
            
            # 1. Validate file
            validation_result = await self._validate_file(filepath)
            if not validation_result["valid"]:
                self._log_processing(
                    db, document_id, "ingestion", "error",
                    f"File validation failed: {validation_result.get('error')}"
                )
                return validation_result
            
            # 2. Calculate file hash (for deduplication)
            file_hash = self._calculate_file_hash(filepath)
            
            # 3. Detect MIME type
            mime_type = self._detect_mime_type(filepath)
            
            # 4. Extract basic metadata
            file_metadata = await self._extract_file_metadata(filepath, mime_type)
            
            # 5. Check for duplicate files
            duplicate_info = await self._check_duplicate(file_hash, document_id)
            
            # 6. Perform initial OCR/text extraction
            initial_text = await self._extract_initial_text(filepath, mime_type)
            
            # 7. Analyze document structure
            structure_analysis = await self._analyze_document_structure(filepath, mime_type)
            
            # 8. Update database record
            self._update_document_record(
                db, document_id, file_hash, mime_type, file_metadata,
                structure_analysis, duplicate_info, initial_text
            )
            
            # 9. Generate thumbnail for UI
            thumbnail_path = await self._generate_thumbnail(filepath, document_id, mime_type)
            
            # 10. Prepare for next processing stage
            next_steps = self._determine_next_steps(structure_analysis, file_metadata)
            
            result = {
                "status": "success",
                "document_id": document_id,
                "file_hash": file_hash,
                "mime_type": mime_type,
                "file_metadata": file_metadata,
                "structure_analysis": structure_analysis,
                "duplicate_info": duplicate_info,
                "initial_text_sample": initial_text[:500] if initial_text else "",
                "thumbnail_path": thumbnail_path,
                "next_steps": next_steps,
                "quality_score": structure_analysis.get("quality_score", 0.5)
            }
            
            self._log_processing(
                db, document_id, "ingestion", "success",
                f"Document ingestion completed. Quality: {result['quality_score']:.2f}"
            )
            
            # Trigger classification if quality is acceptable
            if result["quality_score"] >= 0.3:
                await self._trigger_classification(document_id)
            else:
                self._log_processing(
                    db, document_id, "ingestion", "warning",
                    "Low quality score, classification may be unreliable"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Document ingestion failed for {document_id}: {str(e)}", exc_info=True)
            
            # Log error
            db = next(get_db())
            self._log_processing(
                db, document_id, "ingestion", "error",
                f"Ingestion failed: {str(e)}",
                {"error": str(e), "traceback": str(e.__traceback__)}
            )
            
            # Update document status
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = "error"
                db.commit()
            
            return {
                "status": "error",
                "document_id": document_id,
                "error": str(e),
                "next_steps": ["manual_review"]
            }
    
    async def _validate_file(self, filepath: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return {"valid": False, "error": "File not found"}
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > settings.max_file_size:
                return {
                    "valid": False,
                    "error": f"File size {file_size} exceeds maximum {settings.max_file_size}"
                }
            
            # Check file extension
            file_ext = os.path.splitext(filepath)[1].lower()
            if file_ext not in settings.allowed_extensions:
                return {
                    "valid": False,
                    "error": f"File extension {file_ext} not allowed"
                }
            
            # Check MIME type
            mime_type = self._detect_mime_type(filepath)
            if mime_type not in self.supported_mime_types:
                return {
                    "valid": False,
                    "error": f"MIME type {mime_type} not supported"
                }
            
            # Check if file is corrupted
            if not await self._check_file_integrity(filepath, mime_type):
                return {"valid": False, "error": "File appears to be corrupted"}
            
            return {"valid": True, "file_size": file_size, "mime_type": mime_type}
            
        except Exception as e:
            logger.error(f"File validation failed: {str(e)}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def _detect_mime_type(self, filepath: str) -> str:
        """Detect MIME type of file"""
        try:
            return self.mime.from_file(filepath)
        except:
            # Fallback based on extension
            ext = os.path.splitext(filepath)[1].lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.tiff': 'image/tiff',
                '.tif': 'image/tiff',
                '.bmp': 'image/bmp'
            }
            return mime_map.get(ext, 'application/octet-stream')
    
    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of file for deduplication"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read file in chunks for memory efficiency
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def _extract_file_metadata(
        self,
        filepath: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """Extract metadata from file"""
        metadata = {
            "filename": os.path.basename(filepath),
            "file_size": os.path.getsize(filepath),
            "mime_type": mime_type,
            "created_at": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
            "modified_at": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
            "extension": os.path.splitext(filepath)[1].lower()
        }
        
        try:
            if mime_type == 'application/pdf':
                pdf_metadata = get_pdf_metadata(filepath)
                metadata.update({
                    "page_count": pdf_metadata.get("page_count", 1),
                    "author": pdf_metadata.get("author"),
                    "title": pdf_metadata.get("title"),
                    "creator": pdf_metadata.get("creator"),
                    "producer": pdf_metadata.get("producer"),
                    "is_scanned": await self._is_scanned_pdf(filepath)
                })
            elif mime_type.startswith('image/'):
                with Image.open(filepath) as img:
                    metadata.update({
                        "dimensions": img.size,
                        "mode": img.mode,
                        "format": img.format,
                        "dpi": img.info.get('dpi', (72, 72)),
                        "color_profile": 'ICC' in img.info
                    })
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {str(e)}")
        
        return metadata
    
    async def _is_scanned_pdf(self, filepath: str) -> bool:
        """Check if PDF is scanned (image-based) vs text-based"""
        try:
            # Extract text from first page
            text = extract_text_from_pdf(filepath)
            
            # If very little text extracted, likely scanned
            if len(text.strip()) < 100:
                return True
            
            # Check for common scanned PDF indicators
            import PyPDF2
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Check if fonts are embedded
                for page in pdf_reader.pages[:2]:  # Check first 2 pages
                    if '/Font' in page.get_object():
                        return False
            
            return True
        except:
            return True  # Assume scanned if check fails
    
    async def _check_duplicate(
        self,
        file_hash: str,
        current_document_id: str
    ) -> Dict[str, Any]:
        """Check for duplicate files"""
        try:
            db = next(get_db())
            
            # Look for documents with same hash
            duplicate_docs = db.query(Document).filter(
                Document.metadata["file_hash"].astext == file_hash,
                Document.id != current_document_id
            ).all()
            
            if duplicate_docs:
                return {
                    "is_duplicate": True,
                    "count": len(duplicate_docs),
                    "duplicate_ids": [doc.id for doc in duplicate_docs],
                    "most_recent": max([doc.uploaded_at for doc in duplicate_docs]).isoformat()
                }
            
            return {"is_duplicate": False}
            
        except Exception as e:
            logger.warning(f"Duplicate check failed: {str(e)}")
            return {"is_duplicate": False, "error": str(e)}
    
    async def _extract_initial_text(
        self,
        filepath: str,
        mime_type: str
    ) -> str:
        """Extract initial text for quick analysis"""
        try:
            if mime_type == 'application/pdf':
                # Extract from first 2 pages only for speed
                text = extract_text_from_pdf(filepath)
                return text[:5000]  # Limit text for initial analysis
            else:
                # For images, do quick OCR on resized image
                import pytesseract
                from PIL import Image
                
                img = Image.open(filepath)
                
                # Resize for faster processing
                max_size = (1000, 1000)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to grayscale
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Quick OCR
                text = pytesseract.image_to_string(img)
                return text[:2000]
                
        except Exception as e:
            logger.warning(f"Initial text extraction failed: {str(e)}")
            return ""
    
    async def _analyze_document_structure(
        self,
        filepath: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """Analyze document structure and quality"""
        try:
            analysis = {
                "quality_score": 0.5,
                "page_count": 1,
                "has_text": False,
                "has_tables": False,
                "has_images": False,
                "orientation": "portrait",
                "skew_angle": 0,
                "issues": []
            }
            
            if mime_type == 'application/pdf':
                # Convert first page to image for analysis
                images = convert_pdf_to_images(filepath, limit=1)
                if images:
                    image = np.array(images[0])
                    page_analysis = await self._analyze_image_structure(image)
                    analysis.update(page_analysis)
                    
                    # Get page count
                    import PyPDF2
                    with open(filepath, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        analysis["page_count"] = len(pdf_reader.pages)
            else:
                # Analyze image directly
                image = cv2.imread(filepath)
                if image is not None:
                    page_analysis = await self._analyze_image_structure(image)
                    analysis.update(page_analysis)
            
            # Validate quality
            quality_result = validate_image_quality(filepath)
            if isinstance(quality_result, tuple) and len(quality_result) == 2:
                is_valid, quality_metrics = quality_result
                if is_valid:
                    analysis["quality_score"] = self._calculate_overall_quality(quality_metrics)
                else:
                    analysis["issues"].append({
                        "type": "quality",
                        "message": quality_metrics.get("error", "Low quality"),
                        "severity": "warning"
                    })
                    analysis["quality_score"] = 0.3
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Structure analysis failed: {str(e)}")
            analysis["issues"].append({
                "type": "analysis_error",
                "message": f"Structure analysis failed: {str(e)}",
                "severity": "warning"
            })
            return analysis
    
    async def _analyze_image_structure(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze structure of an image"""
        try:
            height, width = image.shape[:2]
            
            analysis = {
                "dimensions": {"width": width, "height": height},
                "orientation": "portrait" if height > width else "landscape",
                "aspect_ratio": width / height if height > 0 else 1,
                "has_text": False,
                "has_tables": False,
                "has_images": False,
                "skew_angle": 0,
                "text_density": 0,
                "line_density": 0
            }
            
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Detect text regions
            text_density = self._estimate_text_density(gray)
            analysis["text_density"] = text_density
            analysis["has_text"] = text_density > 0.01
            
            # Detect lines (potential tables)
            line_density = self._detect_line_density(gray)
            analysis["line_density"] = line_density
            analysis["has_tables"] = line_density > 5
            
            # Detect images/photos
            has_images = self._detect_images(gray)
            analysis["has_images"] = has_images
            
            # Detect skew
            skew_angle = self._detect_skew(gray)
            analysis["skew_angle"] = skew_angle
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Image structure analysis failed: {str(e)}")
            return {}
    
    def _estimate_text_density(self, gray_image: np.ndarray) -> float:
        """Estimate text density in image"""
        try:
            # Apply adaptive threshold
            binary = cv2.adaptiveThreshold(
                gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Calculate black pixel ratio (text is usually black)
            total_pixels = gray_image.size
            black_pixels = np.sum(binary == 0)
            
            return black_pixels / total_pixels
            
        except:
            return 0.0
    
    def _detect_line_density(self, gray_image: np.ndarray) -> float:
        """Detect line density for table detection"""
        try:
            # Detect edges
            edges = cv2.Canny(gray_image, 50, 150)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLinesP(
                edges, 1, np.pi/180,
                threshold=50,
                minLineLength=30,
                maxLineGap=10
            )
            
            if lines is None:
                return 0.0
            
            # Normalize by image area
            height, width = gray_image.shape
            image_area = height * width
            
            return len(lines) / image_area * 10000
            
        except:
            return 0.0
    
    def _detect_images(self, gray_image: np.ndarray) -> bool:
        """Detect if image contains photos/non-text elements"""
        try:
            # Calculate variance (photos have higher variance)
            variance = np.var(gray_image)
            
            # Calculate entropy (photos have higher entropy)
            hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
            hist = hist / hist.sum()
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            
            # Heuristic: high variance and moderate entropy suggests photos
            return variance > 1000 and entropy > 5
            
        except:
            return False
    
    def _detect_skew(self, gray_image: np.ndarray) -> float:
        """Detect skew angle of text"""
        try:
            # Apply threshold
            _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            angles = []
            for contour in contours:
                if cv2.contourArea(contour) > 100:  # Only significant contours
                    _, _, angle = cv2.minAreaRect(contour)
                    angles.append(angle)
            
            if angles:
                # Convert angles to -45 to 45 range
                adjusted_angles = []
                for angle in angles:
                    if angle > 45:
                        angle = angle - 90
                    adjusted_angles.append(angle)
                
                return np.median(adjusted_angles)
            
            return 0.0
            
        except:
            return 0.0
    
    def _calculate_overall_quality(self, quality_metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score from metrics"""
        try:
            scores = []
            
            # Sharpness score
            sharpness = quality_metrics.get("sharpness", 0)
            sharpness_score = min(sharpness / 500, 1.0)  # Normalize
            scores.append(sharpness_score * 0.3)
            
            # Contrast score
            contrast = quality_metrics.get("contrast", 0)
            contrast_score = min(contrast / 100, 1.0)  # Normalize
            scores.append(contrast_score * 0.3)
            
            # Brightness score
            brightness = quality_metrics.get("brightness", 128)
            brightness_score = 1.0 - abs(brightness - 128) / 128
            scores.append(brightness_score * 0.2)
            
            # Resolution score
            resolution = quality_metrics.get("resolution", 0)
            resolution_score = min(resolution / (2000 * 2000), 1.0)  # Normalize to 4MP
            scores.append(resolution_score * 0.2)
            
            return sum(scores)
            
        except:
            return 0.5
    
    async def _check_file_integrity(self, filepath: str, mime_type: str) -> bool:
        """Check if file is not corrupted"""
        try:
            if mime_type == 'application/pdf':
                import PyPDF2
                with open(filepath, 'rb') as f:
                    PyPDF2.PdfReader(f)
                return True
            elif mime_type.startswith('image/'):
                with Image.open(filepath) as img:
                    img.verify()  # Verify image integrity
                return True
            return True
        except:
            return False
    
    def _update_document_record(
        self,
        db,
        document_id: str,
        file_hash: str,
        mime_type: str,
        file_metadata: Dict[str, Any],
        structure_analysis: Dict[str, Any],
        duplicate_info: Dict[str, Any],
        initial_text: str
    ):
        """Update document record with ingestion results"""
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found in database")
                return
            
            # Update metadata
            if not document.metadata:
                document.metadata = {}
            
            document.metadata.update({
                "file_hash": file_hash,
                "ingestion_timestamp": datetime.now().isoformat(),
                "structure_analysis": structure_analysis,
                "is_duplicate": duplicate_info.get("is_duplicate", False),
                "duplicate_ids": duplicate_info.get("duplicate_ids", []),
                "initial_text_length": len(initial_text),
                "quality_score": structure_analysis.get("quality_score", 0.5)
            })
            
            # Update image quality score
            document.image_quality_score = structure_analysis.get("quality_score", 0.5)
            
            # Update processing status
            if structure_analysis.get("quality_score", 0) < 0.3:
                document.processing_status = "needs_review"
            else:
                document.processing_status = "ingested"
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update document record: {str(e)}")
            db.rollback()
    
    async def _generate_thumbnail(
        self,
        filepath: str,
        document_id: str,
        mime_type: str
    ) -> Optional[str]:
        """Generate thumbnail for UI display"""
        try:
            thumbnail_dir = os.path.join(settings.upload_dir, "thumbnails")
            os.makedirs(thumbnail_dir, exist_ok=True)
            
            thumbnail_path = os.path.join(thumbnail_dir, f"{document_id}_thumb.jpg")
            
            if mime_type == 'application/pdf':
                # Convert first page to image
                images = convert_pdf_to_images(filepath, dpi=72, limit=1)
                if images:
                    thumbnail = images[0]
            else:
                # Load and resize image
                thumbnail = Image.open(filepath)
            
            # Resize to thumbnail size
            thumbnail.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if thumbnail.mode in ('RGBA', 'LA', 'P'):
                thumbnail = thumbnail.convert('RGB')
            
            # Save thumbnail
            thumbnail.save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {str(e)}")
            return None
    
    def _determine_next_steps(
        self,
        structure_analysis: Dict[str, Any],
        file_metadata: Dict[str, Any]
    ) -> list:
        """Determine next processing steps based on analysis"""
        steps = ["classification"]
        
        quality_score = structure_analysis.get("quality_score", 0.5)
        
        if quality_score < 0.3:
            steps.append("manual_review")
            steps.append("quality_enhancement")
        elif structure_analysis.get("has_tables", False):
            steps.append("table_detection")
        elif structure_analysis.get("skew_angle", 0) > 2:
            steps.append("deskew")
        
        if file_metadata.get("page_count", 1) > 1:
            steps.append("multi_page_processing")
        
        return steps
    
    async def _trigger_classification(self, document_id: str):
        """Trigger document classification"""
        try:
            # In production, this would publish to a message queue
            # For demo, we'll just log
            logger.info(f"Triggering classification for document {document_id}")
            
            # Update status
            db = next(get_db())
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = "classifying"
                db.commit()
            
            # Here you would typically:
            # 1. Publish to Redis/rabbitMQ
            # 2. Trigger async task
            # 3. Or call classification service directly
            
        except Exception as e:
            logger.error(f"Failed to trigger classification: {str(e)}")
    
    def _log_processing(
        self,
        db,
        document_id: str,
        stage: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log processing activity"""
        try:
            log = ProcessingLog(
                document_id=document_id,
                stage=stage,
                status=status,
                message=message,
                details=details or {}
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log processing: {str(e)}")
    
    async def cleanup_old_files(self, days_old: int = 7):
        """Clean up old uploaded files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            db = next(get_db())
            old_documents = db.query(Document).filter(
                Document.uploaded_at < cutoff_date,
                Document.processing_status.in_(["error", "completed"])
            ).all()
            
            for doc in old_documents:
                try:
                    # Delete file
                    if os.path.exists(doc.filepath):
                        os.remove(doc.filepath)
                    
                    # Delete thumbnail if exists
                    thumbnail_path = os.path.join(
                        settings.upload_dir,
                        "thumbnails",
                        f"{doc.id}_thumb.jpg"
                    )
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                    
                    logger.info(f"Cleaned up files for document {doc.id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to clean up files for {doc.id}: {str(e)}")
            
            return {"cleaned": len(old_documents), "status": "success"}
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return {"cleaned": 0, "status": "error", "error": str(e)}
    
    async def reprocess_document(self, document_id: str) -> Dict[str, Any]:
        """Reprocess a document (e.g., after quality enhancement)"""
        try:
            db = next(get_db())
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return {"status": "error", "error": "Document not found"}
            
            # Reset processing status
            document.processing_status = "uploaded"
            db.commit()
            
            # Trigger reprocessing
            return await self.process_document_upload(
                document_id=document_id,
                filepath=document.filepath,
                customer_id=document.metadata.get("customer_id"),
                metadata=document.metadata
            )
            
        except Exception as e:
            logger.error(f"Reprocessing failed: {str(e)}")
            return {"status": "error", "error": str(e)}

# Singleton instance
ingestion_service = IngestionService()

# Async wrapper functions
async def process_document_upload(
    document_id: str,
    filepath: str,
    customer_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Public interface for document upload processing"""
    return await ingestion_service.process_document_upload(
        document_id, filepath, customer_id, metadata
    )

async def reprocess_document(document_id: str) -> Dict[str, Any]:
    """Public interface for document reprocessing"""
    return await ingestion_service.reprocess_document(document_id)

async def cleanup_old_files(days_old: int = 7) -> Dict[str, Any]:
    """Public interface for cleanup"""
    return await ingestion_service.cleanup_old_files(days_old)