from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logger import logger
from app.api.routes import upload, extract, validate, review, dashboard
from app.core.database import engine, Base
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("Starting U-FinDI Backend")
    yield
    # Shutdown
    logger.info("Shutting down U-FinDI Backend")

app = FastAPI(
    title="U-FinDI API",
    description="Universal Financial Document Intelligence Engine",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "request_id": request.state.get("request_id", "unknown")
        }
    )

# Include routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(extract.router, prefix="/api", tags=["Extraction"])
app.include_router(validate.router, prefix="/api", tags=["Validation"])
app.include_router(review.router, prefix="/api", tags=["Review"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])

@app.get("/")
async def root():
    return {
        "service": "U-FinDI Backend",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "upload": "/api/upload",
            "extract": "/api/extract/{document_id}",
            "validate": "/api/validate/{document_id}",
            "review": "/api/review/{document_id}",
            "dashboard": "/api/dashboard/metrics"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }