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
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # CORS
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_database_url(self) -> str:
        """
        Railway compatibility: convierte mysql:// a mysql+pymysql://
        """
        if self.database_url.startswith("mysql://"):
            return self.database_url.replace("mysql://", "mysql+pymysql://", 1)
        return self.database_url


settings = Settings()