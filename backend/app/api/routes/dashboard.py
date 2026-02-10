from fastapi import APIRouter, HTTPException
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.core.database import get_db, Document, Extraction, Validation, Correction
from app.models.schemas import DashboardMetrics
from app.core.logger import logger

router = APIRouter()

@router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """
    Get system metrics and performance dashboard
    """
    db = next(get_db())
    
    try:
        # Total documents
        total_documents = db.query(func.count(Document.id)).scalar()
        
        # Documents by type
        docs_by_type = db.query(
            Document.document_type,
            func.count(Document.id)
        ).group_by(Document.document_type).all()
        documents_by_type = {doc_type or "unknown": count for doc_type, count in docs_by_type}
        
        # Recent processing stats
        recent_docs = db.query(Document).filter(
            Document.uploaded_at >= datetime.now() - timedelta(days=7)
        ).all()
        
        # Calculate average processing time (simplified)
        avg_processing_time = 2.5  # Placeholder
        
        # Extraction accuracy (simplified - would use confidence scores)
        extractions = db.query(Extraction).limit(100).all()
        if extractions:
            avg_confidences = {}
            for ext in extractions:
                for field, score in ext.confidence_scores.items():
                    if field not in avg_confidences:
                        avg_confidences[field] = []
                    avg_confidences[field].append(score)
            
            extraction_accuracy = {
                field: sum(scores) / len(scores)
                for field, scores in avg_confidences.items()
            }
        else:
            extraction_accuracy = {}
        
        # Validation failure rate
        total_validations = db.query(func.count(Validation.id)).scalar()
        failed_validations = db.query(func.count(Validation.id)).filter(
            Validation.validation_status == "needs_review"
        ).scalar()
        
        validation_failure_rate = (failed_validations / total_validations * 100) if total_validations > 0 else 0
        
        # Top error codes
        recent_errors = db.query(Validation).filter(
            Validation.issues != None
        ).order_by(desc(Validation.validated_at)).limit(10).all()
        
        error_counts = {}
        for val in recent_errors:
            for issue in val.issues:
                error_code = issue.get("issue_code", "unknown")
                error_counts[error_code] = error_counts.get(error_code, 0) + 1
        
        top_error_codes = [
            {"error_code": code, "count": count}
            for code, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Learning improvements (simplified)
        corrections_count = db.query(func.count(Correction.id)).scalar()
        recent_corrections = db.query(Correction).order_by(
            desc(Correction.corrected_at)
        ).limit(5).all()
        
        recent_corrections_list = [
            {
                "document_id": corr.document_id,
                "field": corr.field_path,
                "old_value": corr.old_value[:50] + "..." if corr.old_value and len(corr.old_value) > 50 else corr.old_value,
                "new_value": corr.new_value[:50] + "..." if corr.new_value and len(corr.new_value) > 50 else corr.new_value,
                "corrected_at": corr.corrected_at.isoformat()
            }
            for corr in recent_corrections
        ]
        
        learning_improvements = {
            "total_corrections": corrections_count,
            "corrections_last_week": db.query(func.count(Correction.id)).filter(
                Correction.corrected_at >= datetime.now() - timedelta(days=7)
            ).scalar(),
            "auto_correction_rate": 0.15  # Placeholder
        }
        
        logger.info("Dashboard metrics generated")
        
        return DashboardMetrics(
            total_documents=total_documents,
            documents_by_type=documents_by_type,
            average_processing_time=avg_processing_time,
            extraction_accuracy=extraction_accuracy,
            validation_failure_rate=validation_failure_rate,
            top_error_codes=top_error_codes,
            learning_improvements=learning_improvements,
            recent_corrections=recent_corrections_list
        )
        
    except Exception as e:
        logger.error(f"Failed to generate dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")