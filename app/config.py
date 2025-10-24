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
    OAUTHLIB_INSECURE_TRANSPORT: Optional[str] = None  # Solo para desarrollo local con HTTP
    
    # CORS
    backend_cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Permite variables extra del .env sin causar errores

    def get_database_url(self) -> str:
        """
        Railway compatibility: convierte mysql:// a mysql+pymysql://
        """
        if self.database_url.startswith("mysql://"):
            return self.database_url.replace("mysql://", "mysql+pymysql://", 1)
        return self.database_url


settings = Settings()