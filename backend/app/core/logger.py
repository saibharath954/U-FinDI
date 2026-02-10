import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            f"logs/ufindi_{datetime.now().strftime('%Y%m%d')}.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("U-FinDI")

# Optional: Add structured logging
class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def info(self, message, **kwargs):
        extra = {**kwargs, "timestamp": datetime.now().isoformat()}
        self.logger.info(message, extra=extra)
    
    def error(self, message, exc_info=False, **kwargs):
        extra = {**kwargs, "timestamp": datetime.now().isoformat()}
        self.logger.error(message, exc_info=exc_info, extra=extra)
    
    def warning(self, message, **kwargs):
        extra = {**kwargs, "timestamp": datetime.now().isoformat()}
        self.logger.warning(message, extra=extra)
    
    def debug(self, message, **kwargs):
        extra = {**kwargs, "timestamp": datetime.now().isoformat()}
        self.logger.debug(message, extra=extra)

# Create structured logger instance
structured_logger = StructuredLogger("U-FinDI-Structured")