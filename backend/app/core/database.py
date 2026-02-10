from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_uuid():
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    uploaded_at = Column(DateTime, default=func.now())
    processing_status = Column(String, default="uploaded")  # uploaded, processing, extracted, validated, error
    document_type = Column(String, nullable=True)
    language = Column(String, nullable=True)
    image_quality_score = Column(Float, nullable=True)
    document_metadata = Column(JSON, default={})
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, type={self.document_type})>"

class Extraction(Base):
    __tablename__ = "extractions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False)
    extracted_fields = Column(JSON, default={})
    tables = Column(JSON, default=[])
    layout_data = Column(JSON, default={})
    confidence_scores = Column(JSON, default={})
    extracted_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Extraction(document_id={self.document_id})>"

class Validation(Base):
    __tablename__ = "validations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False)
    validation_status = Column(String, default="pending")  # passed, needs_review, failed
    issues = Column(JSON, default=[])
    cross_document_checks = Column(JSON, default={})
    validated_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Validation(document_id={self.document_id}, status={self.validation_status})>"

class Correction(Base):
    __tablename__ = "corrections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False)
    field_path = Column(String, nullable=False)  # e.g., "total_amount" or "tables.0.rows.1.amount"
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)
    corrected_by = Column(String, default="human_reviewer")
    corrected_at = Column(DateTime, default=func.now())
    sent_to_backboard = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Correction(document_id={self.document_id}, field={self.field_path})>"

class ProcessingLog(Base):
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False)
    stage = Column(String, nullable=False)  # upload, classification, extraction, validation
    status = Column(String, nullable=False)  # success, error, warning
    message = Column(Text, nullable=False)
    details = Column(JSON, default={})
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<ProcessingLog(document_id={self.document_id}, stage={self.stage})>"