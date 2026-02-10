import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application
    app_name: str = "U-FinDI"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ufindi.db")
    postgres_db: Optional[str] = os.getenv("POSTGRES_DB")
    postgres_user: Optional[str] = os.getenv("POSTGRES_USER")
    postgres_password: Optional[str] = os.getenv("POSTGRES_PASSWORD")
    postgres_host: Optional[str] = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: Optional[str] = os.getenv("POSTGRES_PORT", "5432")
    
    # File storage
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    allowed_extensions: list = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]
    
    # AI/ML Services
    ocr_engine: str = os.getenv("OCR_ENGINE", "tesseract")  # or "google_vision", "aws_textract"
    classification_model: str = os.getenv("CLASSIFICATION_MODEL", "layoutlm")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Backboard.io (Memory Layer)
    backboard_api_key: Optional[str] = os.getenv("BACKBOARD_API_KEY")
    backboard_base_url: str = os.getenv("BACKBOARD_BASE_URL", "https://api.backboard.io/v1")
    
    # Redis (for async processing)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Validation thresholds
    min_confidence: float = float(os.getenv("MIN_CONFIDENCE", 0.7))
    validation_timeout: int = int(os.getenv("VALIDATION_TIMEOUT", 30))
    
    class Config:
        env_file = ".env"

settings = Settings()

# Build database URL if not provided
if settings.database_url == "sqlite:///./ufindi.db" and settings.postgres_db:
    settings.database_url = (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )