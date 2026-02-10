import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
from app.core.logger import logger
from app.core.backboard_client import BackboardClient
from app.core.database import get_db, Correction

class LearningService:
    def __init__(self):
        self.backboard_client = BackboardClient()
        self.error_patterns = {}
    
    async def store_extraction_pattern(
        self,
        document_id: str,
        extraction_data: Dict[str, Any],
        layout_data: Dict[str, Any]
    ):
        """Store extraction pattern in memory layer"""
        try:
            # Create pattern signature
            pattern_signature = self._create_pattern_signature(layout_data, extraction_data)
            
            # Prepare data for storage
            pattern_data = {
                "document_id": document_id,
                "document_type": extraction_data.get("document_type"),
                "pattern_signature": pattern_signature,
                "extraction_results": extraction_data,
                "layout_features": self._extract_layout_features(layout_data),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in Backboard.io
            await self.backboard_client.store_pattern(
                pattern=pattern_data,
                metadata={"source": "u-findi", "type": "extraction_pattern"}
            )
            
            logger.info(f"Stored extraction pattern for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to store extraction pattern: {str(e)}")
    
    async def store_correction(
        self,
        document_id: str,
        correction: Any,
        document_type: str
    ):
        """Store correction in memory layer"""
        try:
            correction_data = {
                "document_id": document_id,
                "document_type": document_type,
                "field_path": correction.field_path,
                "old_value": correction.old_value,
                "new_value": correction.new_value,
                "correction_id": correction.id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store correction
            await self.backboard_client.store_correction(
                correction=correction_data,
                metadata={"source": "human_reviewer"}
            )
            
            # Update error patterns
            self._update_error_patterns(correction_data)
            
            # Check if we should trigger retraining
            await self._check_retraining_trigger(document_type, correction.field_path)
            
            logger.info(f"Stored correction for document {document_id}, field: {correction.field_path}")
            
        except Exception as e:
            logger.error(f"Failed to store correction: {str(e)}")
    
    async def retrieve_similar_patterns(
        self,
        layout_data: Dict[str, Any],
        document_type: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve similar document patterns from memory"""
        try:
            layout_features = self._extract_layout_features(layout_data)
            
            similar_patterns = await self.backboard_client.search_similar_patterns(
                features=layout_features,
                document_type=document_type,
                limit=limit
            )
            
            return similar_patterns
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar patterns: {str(e)}")
            return []
    
    async def get_suggested_corrections(
        self,
        document_id: str,
        field_path: str,
        current_value: Any
    ) -> List[Dict[str, Any]]:
        """Get suggested corrections based on historical data"""
        try:
            # Get similar corrections from memory
            suggestions = await self.backboard_client.get_field_suggestions(
                field_path=field_path,
                current_value=current_value
            )
            
            # Filter and rank suggestions
            ranked_suggestions = self._rank_suggestions(suggestions)
            
            return ranked_suggestions[:3]  # Return top 3
            
        except Exception as e:
            logger.error(f"Failed to get suggested corrections: {str(e)}")
            return []
    
    def cluster_errors(self, timeframe_days: int = 30) -> Dict[str, Any]:
        """Cluster similar errors for analysis"""
        try:
            db = next(get_db())
            
            # Get recent corrections
            cutoff_date = datetime.now() - timedelta(days=timeframe_days)
            corrections = db.query(Correction).filter(
                Correction.corrected_at >= cutoff_date
            ).all()
            
            # Cluster by field path and document type
            clusters = {}
            for corr in corrections:
                key = f"{corr.field_path}||{corr.document_id}"
                if key not in clusters:
                    clusters[key] = {
                        "field_path": corr.field_path,
                        "document_type": self._get_document_type(corr.document_id),
                        "corrections": [],
                        "count": 0
                    }
                clusters[key]["corrections"].append({
                    "old_value": corr.old_value,
                    "new_value": corr.new_value
                })
                clusters[key]["count"] += 1
            
            # Sort clusters by frequency
            sorted_clusters = sorted(
                clusters.values(),
                key=lambda x: x["count"],
                reverse=True
            )
            
            return {
                "total_corrections": len(corrections),
                "clusters": sorted_clusters[:10],  # Top 10 clusters
                "timeframe_days": timeframe_days
            }
            
        except Exception as e:
            logger.error(f"Error clustering failed: {str(e)}")
            return {"error": str(e)}
    
    def _create_pattern_signature(
        self,
        layout_data: Dict[str, Any],
        extraction_data: Dict[str, Any]
    ) -> str:
        """Create a signature for document pattern"""
        # Extract key features
        features = {
            "region_count": len(layout_data.get("regions", [])),
            "table_count": len(layout_data.get("tables", [])),
            "field_count": len(extraction_data.get("fields", {})),
            "key_fields": list(extraction_data.get("fields", {}).keys())[:5]
        }
        
        # Create hash
        features_str = json.dumps(features, sort_keys=True)
        return hashlib.md5(features_str.encode()).hexdigest()
    
    def _extract_layout_features(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract numerical features from layout data"""
        regions = layout_data.get("regions", [])
        
        features = {
            "total_regions": len(regions),
            "text_regions": sum(1 for r in regions if r.get("type") == "text"),
            "table_regions": sum(1 for r in regions if r.get("type") == "table"),
            "image_regions": sum(1 for r in regions if r.get("type") == "image"),
            "avg_region_area": 0,
            "avg_aspect_ratio": 0
        }
        
        if regions:
            areas = [r.get("area", 0) for r in regions]
            aspect_ratios = [r.get("aspect_ratio", 0) for r in regions]
            
            features["avg_region_area"] = sum(areas) / len(areas)
            features["avg_aspect_ratio"] = sum(aspect_ratios) / len(aspect_ratios)
        
        return features
    
    def _update_error_patterns(self, correction_data: Dict[str, Any]):
        """Update internal error pattern tracking"""
        field_path = correction_data["field_path"]
        document_type = correction_data["document_type"]
        
        key = f"{document_type}:{field_path}"
        
        if key not in self.error_patterns:
            self.error_patterns[key] = {
                "count": 0,
                "first_seen": datetime.now(),
                "last_seen": datetime.now(),
                "common_old_values": {},
                "common_new_values": {}
            }
        
        pattern = self.error_patterns[key]
        pattern["count"] += 1
        pattern["last_seen"] = datetime.now()
        
        # Track common values
        old_val = str(correction_data["old_value"])
        new_val = str(correction_data["new_value"])
        
        pattern["common_old_values"][old_val] = pattern["common_old_values"].get(old_val, 0) + 1
        pattern["common_new_values"][new_val] = pattern["common_new_values"].get(new_val, 0) + 1
    
    async def _check_retraining_trigger(self, document_type: str, field_path: str):
        """Check if we should trigger model retraining"""
        key = f"{document_type}:{field_path}"
        
        if key in self.error_patterns:
            pattern = self.error_patterns[key]
            
            # Trigger retraining if:
            # 1. More than 10 corrections for this pattern
            # 2. Error rate is consistently high
            if pattern["count"] >= 10:
                logger.info(f"Retraining trigger activated for {key} ({pattern['count']} corrections)")
                
                # In production, this would trigger a retraining job
                # For demo, we just log it
                await self._trigger_retraining(document_type, field_path)
    
    async def _trigger_retraining(self, document_type: str, field_path: str):
        """Trigger model retraining (simulated for demo)"""
        # In production, this would:
        # 1. Collect training data from corrections
        # 2. Train a new model
        # 3. Deploy the updated model
        
        logger.info(f"Simulating retraining for {document_type}.{field_path}")
        
        # Simulate retraining delay
        import asyncio
        await asyncio.sleep(0.1)
    
    def _rank_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank correction suggestions by confidence"""
        if not suggestions:
            return []
        
        # Simple ranking by frequency
        ranked = sorted(
            suggestions,
            key=lambda x: x.get("frequency", 0),
            reverse=True
        )
        
        return ranked
    
    def _get_document_type(self, document_id: str) -> str:
        """Get document type from database"""
        try:
            db = next(get_db())
            from app.core.database import Document
            doc = db.query(Document).filter(Document.id == document_id).first()
            return doc.document_type if doc else "unknown"
        except:
            return "unknown"

# Singleton instance
learning_service = LearningService()

# Async wrapper functions for compatibility
async def store_extraction_pattern(document_id: str, extraction_data: Dict[str, Any], layout_data: Dict[str, Any]):
    return await learning_service.store_extraction_pattern(document_id, extraction_data, layout_data)

async def store_correction(document_id: str, correction: Any, document_type: str):
    return await learning_service.store_correction(document_id, correction, document_type)

async def retrieve_similar_patterns(layout_data: Dict[str, Any], document_type: str, limit: int = 5):
    return await learning_service.retrieve_similar_patterns(layout_data, document_type, limit)

async def get_suggested_corrections(document_id: str, field_path: str, current_value: Any):
    return await learning_service.get_suggested_corrections(document_id, field_path, current_value)

def cluster_errors(timeframe_days: int = 30):
    return learning_service.cluster_errors(timeframe_days)