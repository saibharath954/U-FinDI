import cv2
import numpy as np
from typing import Dict, Any, List
import pytesseract
from PIL import Image
import json
from app.core.logger import logger

def analyze_layout(filepath: str, document_type: str) -> Dict[str, Any]:
    """
    Analyze document layout and detect regions
    """
    try:
        # Load image
        if filepath.lower().endswith('.pdf'):
            from app.utils.pdf_utils import convert_pdf_to_images
            images = convert_pdf_to_images(filepath, limit=1)
            if not images:
                return {"error": "Failed to load PDF"}
            image = np.array(images[0])
        else:
            image = cv2.imread(filepath)
        
        if image is None:
            return {"error": "Failed to load image"}
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Detect contours for layout analysis
        contours, _ = cv2.findContours(
            255 - binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter and process contours
        regions = []
        min_area = image.shape[0] * image.shape[1] * 0.001  # 0.1% of image area
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Classify region type
                region_type = classify_region(image[y:y+h, x:x+w], document_type)
                
                regions.append({
                    "type": region_type,
                    "bbox": [x, y, x + w, y + h],
                    "area": area,
                    "aspect_ratio": w / h if h > 0 else 0
                })
        
        # Detect tables
        tables = detect_tables(binary)
        
        # Detect text orientation
        orientation = detect_text_orientation(binary)
        
        logger.info(f"Layout analysis complete: {len(regions)} regions, {len(tables)} tables")
        
        return {
            "regions": regions,
            "tables": tables,
            "image_dimensions": {
                "width": image.shape[1],
                "height": image.shape[0]
            },
            "text_orientation": orientation,
            "page_count": 1  # Simplified
        }
        
    except Exception as e:
        logger.error(f"Layout analysis failed: {str(e)}")
        return {"error": str(e), "regions": [], "tables": []}

def classify_region(region_image: np.ndarray, document_type: str) -> str:
    """Classify region type"""
    try:
        height, width = region_image.shape[:2]
        
        # Calculate features
        gray = cv2.cvtColor(region_image, cv2.COLOR_BGR2GRAY) if len(region_image.shape) == 3 else region_image
        
        # Text density (using OCR)
        text = pytesseract.image_to_string(Image.fromarray(gray))
        text_density = len(text.strip()) / (height * width) if height * width > 0 else 0
        
        # Line detection
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
        line_density = len(lines) / (height * width) * 10000 if lines is not None and height * width > 0 else 0
        
        # Region classification logic
        if text_density > 0.01:
            if line_density > 5:
                return "table"
            else:
                return "text"
        elif line_density > 10:
            return "separator"
        else:
            return "image"
            
    except:
        return "unknown"

def detect_tables(binary_image: np.ndarray) -> List[Dict[str, Any]]:
    """Detect tables in binary image"""
    tables = []
    
    try:
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Combine lines
        table_structure = cv2.add(horizontal_lines, vertical_lines)
        
        # Find contours of table cells
        contours, _ = cv2.findContours(table_structure, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 50 and h > 20:  # Minimum size for table cell
                tables.append({
                    "bbox": [x, y, x + w, y + h],
                    "cell_count": 1,  # Simplified
                    "confidence": 0.8
                })
        
    except Exception as e:
        logger.error(f"Table detection failed: {str(e)}")
    
    return tables

def detect_text_orientation(binary_image: np.ndarray) -> str:
    """Detect text orientation"""
    try:
        # Use Hough transform to detect line angles
        edges = cv2.Canny(binary_image, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            angles = []
            for line in lines[:min(10, len(lines))]:
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                if angle > 45:
                    angle = angle - 90
                angles.append(angle)
            
            if angles:
                avg_angle = np.mean(angles)
                if abs(avg_angle) < 10:
                    return "horizontal"
                elif abs(avg_angle - 90) < 10:
                    return "vertical"
        
        return "horizontal"
    except:
        return "horizontal"