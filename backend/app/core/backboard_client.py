"""
Mock Backboard.io client for demonstration purposes.
In production, this would connect to the actual Backboard.io API.
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from app.core.logger import logger

class BackboardClient:
    """Mock client for Backboard.io memory layer"""
    
    def __init__(self):
        self.patterns = {}
        self.corrections = {}
        self.suggestions = {}
        logger.info("Backboard.io mock client initialized")
    
    async def store_pattern(self, pattern: Dict[str, Any], metadata: Dict[str, Any]):
        """Store document pattern in memory"""
        pattern_id = pattern.get("pattern_signature", "unknown")
        self.patterns[pattern_id] = {
            "pattern": pattern,
            "metadata": metadata,
            "stored_at": datetime.now().isoformat()
        }
        
        logger.debug(f"Stored pattern: {pattern_id}")
        await asyncio.sleep(0.01)  # Simulate API call
    
    async def store_correction(self, correction: Dict[str, Any], metadata: Dict[str, Any]):
        """Store correction in memory"""
        correction_id = f"corr_{len(self.corrections) + 1}"
        self.corrections[correction_id] = {
            "correction": correction,
            "metadata": metadata,
            "stored_at": datetime.now().isoformat()
        }
        
        # Update suggestions based on corrections
        field_path = correction["field_path"]
        new_value = correction["new_value"]
        
        if field_path not in self.suggestions:
            self.suggestions[field_path] = {}
        
        if new_value not in self.suggestions[field_path]:
            self.suggestions[field_path][new_value] = 0
        
        self.suggestions[field_path][new_value] += 1
        
        logger.debug(f"Stored correction: {correction_id} for field {field_path}")
        await asyncio.sleep(0.01)
    
    async def search_similar_patterns(
        self,
        features: Dict[str, Any],
        document_type: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar document patterns"""
        # Simple mock search - in production, this would use vector similarity
        similar = []
        
        for pattern_id, data in self.patterns.items():
            pattern = data["pattern"]
            
            if pattern.get("document_type") == document_type:
                # Calculate simple similarity score
                score = self._calculate_similarity_score(features, pattern.get("layout_features", {}))
                
                if score > 0.5:
                    similar.append({
                        "pattern_id": pattern_id,
                        "similarity_score": score,
                        "extraction_results": pattern.get("extraction_results", {}),
                        "document_id": pattern.get("document_id")
                    })
        
        # Sort by similarity and limit
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.debug(f"Found {len(similar)} similar patterns for {document_type}")
        await asyncio.sleep(0.02)
        
        return similar[:limit]
    
    async def get_field_suggestions(
        self,
        field_path: str,
        current_value: Any
    ) -> List[Dict[str, Any]]:
        """Get suggested values for a field based on historical corrections"""
        suggestions = []
        
        if field_path in self.suggestions:
            for value, frequency in self.suggestions[field_path].items():
                suggestions.append({
                    "field_path": field_path,
                    "suggested_value": value,
                    "frequency": frequency,
                    "confidence": min(frequency / 10, 1.0)  # Simple confidence calculation
                })
        
        # Also look for similar field paths
        for stored_path, values in self.suggestions.items():
            if stored_path != field_path and stored_path.split('.')[-1] == field_path.split('.')[-1]:
                for value, frequency in values.items():
                    suggestions.append({
                        "field_path": stored_path,
                        "suggested_value": value,
                        "frequency": frequency,
                        "confidence": min(frequency / 20, 0.5)  # Lower confidence for similar fields
                    })
        
        logger.debug(f"Found {len(suggestions)} suggestions for field {field_path}")
        await asyncio.sleep(0.01)
        
        return suggestions
    
    def _calculate_similarity_score(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two feature sets"""
        if not features1 or not features2:
            return 0.0
        
        score = 0.0
        matching_features = 0
        
        for key in set(features1.keys()) & set(features2.keys()):
            val1 = features1[key]
            val2 = features2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Normalize and compare
                max_val = max(abs(val1), abs(val2), 1)
                diff = abs(val1 - val2) / max_val
                score += 1.0 - diff
                matching_features += 1
        
        return score / max(matching_features, 1)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check connection health"""
        return {
            "status": "healthy",
            "patterns_stored": len(self.patterns),
            "corrections_stored": len(self.corrections),
            "timestamp": datetime.now().isoformat()
        }