import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Gestión de Turnos API"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Database
    database_url: str 
    
    # Security
    secret_key: str 
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    OAUTHLIB_INSECURE_TRANSPORT: Optional[str] = None
    
    # CORS - ✅ AGREGADO: URL de Vercel
    backend_cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://mi-turno-frontend.vercel.app",  # ✅ AGREGADO
    ]
    
    # Email Configuration - Brevo (Sendinblue)
    BREVO_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "MiTurno <mi.turno@gmail.com>"
    
    # ✅ NUEVO: Frontend URL dinámica según entorno
    FRONTEND_URL: Optional[str] = None  # Se lee del .env
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def get_database_url(self) -> str:
        """
        Railway compatibility: convierte mysql:// a mysql+pymysql://
        """
        if self.database_url.startswith("mysql://"):
            return self.database_url.replace("mysql://", "mysql+pymysql://", 1)
        return self.database_url
    
    @property
    def brevo_enabled(self) -> bool:
        """
        Verifica si el envío de emails está habilitado via Brevo
        """
        return self.BREVO_API_KEY is not None and len(self.BREVO_API_KEY) > 10
    
    @property
    def frontend_url(self) -> str:
        """
        ✅ NUEVO: Retorna la URL del frontend según el entorno
        Si FRONTEND_URL está definida en .env, la usa.
        Si no, detecta automáticamente el entorno.
        """
        if self.FRONTEND_URL:
            return self.FRONTEND_URL
        
        # Auto-detectar según el entorno
        if self.debug or os.getenv("ENVIRONMENT") == "development":
            return "http://127.0.0.1:5500"  # Live Server local
        else:
            return "https://mi-turno-frontend.vercel.app"  # Producción


settings = Settings()