import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional
from app.core.logger import logger

def validate_image_quality(image_path: str) -> Tuple[bool, dict]:
    """
    Validate image quality for OCR
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return False, {"error": "Failed to load image"}
        
        height, width = image.shape[:2]
        
        # Check resolution
        min_resolution = 1000 * 1000  # 1MP
        resolution = height * width
        
        if resolution < min_resolution:
            return False, {
                "error": f"Image resolution too low: {resolution} pixels",
                "min_required": min_resolution
            }
        
        # Check aspect ratio (typical document ratios)
        aspect_ratio = width / height
        if aspect_ratio < 0.5 or aspect_ratio > 2.5:
            return False, {
                "error": f"Unusual aspect ratio: {aspect_ratio:.2f}",
                "expected": "0.7 to 1.5 for documents"
            }
        
        # Calculate quality metrics
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Sharpness (Laplacian variance)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Contrast
        contrast = gray.std()
        
        # Brightness
        brightness = gray.mean()
        
        metrics = {
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "sharpness": sharpness,
            "contrast": contrast,
            "brightness": brightness,
            "width": width,
            "height": height
        }
        
        # Check thresholds
        if sharpness < 100:
            return False, {
                **metrics,
                "error": f"Image too blurry, sharpness: {sharpness:.1f}",
                "min_sharpness": 100
            }
        
        if contrast < 30:
            return False, {
                **metrics,
                "error": f"Contrast too low: {contrast:.1f}",
                "min_contrast": 30
            }
        
        if brightness < 30 or brightness > 220:
            return False, {
                **metrics,
                "error": f"Brightness out of range: {brightness:.1f}",
                "range": "30-220"
            }
        
        return True, metrics
        
    except Exception as e:
        logger.error(f"Image quality validation failed: {str(e)}")
        return False, {"error": str(e)}

def preprocess_image_for_ocr(
    image: np.ndarray,
    enhance: bool = True,
    denoise: bool = True
) -> np.ndarray:
    """
    Preprocess image for better OCR results
    """
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Denoise
        if denoise:
            gray = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast
        if enhance:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        
        # Binarize
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Optional: deskew
        binary = deskew_image(binary)
        
        return binary
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return image

def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew image to correct rotation
    """
    try:
        # Compute the skew angle
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = 90 + angle
        
        # Rotate the image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h),
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
        
    except:
        return image

def calculate_image_similarity(image1: np.ndarray, image2: np.ndarray) -> float:
    """
    Calculate similarity between two images
    """
    try:
        # Resize to same dimensions
        height = min(image1.shape[0], image2.shape[0])
        width = min(image1.shape[1], image2.shape[1])
        
        img1_resized = cv2.resize(image1, (width, height))
        img2_resized = cv2.resize(image2, (width, height))
        
        # Convert to grayscale if needed
        if len(img1_resized.shape) == 3:
            img1_resized = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
        if len(img2_resized.shape) == 3:
            img2_resized = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)
        
        # Calculate structural similarity
        from skimage.metrics import structural_similarity as ssim
        score, _ = ssim(img1_resized, img2_resized, full=True)
        
        return float(score)
        
    except Exception as e:
        logger.error(f"Image similarity calculation failed: {str(e)}")
        return 0.0