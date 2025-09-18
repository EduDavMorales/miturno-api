# app/core/logger.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config import settings

def setup_logging():
    """Configurar logging profesional para la aplicación"""
    
    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar formateador
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger principal
    logger = logging.getLogger("miturno")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        log_dir / "miturno.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler específico para autenticación
    auth_handler = RotatingFileHandler(
        log_dir / "auth.log",
        maxBytes=5*1024*1024,   # 5MB
        backupCount=3
    )
    auth_handler.setFormatter(formatter)
    
    # Agregar handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Logger específico para auth
    auth_logger = logging.getLogger("miturno.auth")
    auth_logger.addHandler(auth_handler)
    auth_logger.setLevel(logging.DEBUG)
    
    return logger

def get_logger(name: str = "miturno"):
    """Obtener logger configurado"""
    return logging.getLogger(name)