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
        "http://localhost:5173",
    ]
    
    # ========================================
    # EMAIL CONFIGURATION
    # ========================================
    
    # Deprecated: Brevo (Sendinblue) API
    BREVO_API_KEY: Optional[str] = None
    
    # ✅ NUEVO: SMTP Configuration (Gmail)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Email general settings
    # ✅ BUENA PRÁCTICA: Opcional desde .env, con fallback automático a SMTP_USER
    EMAIL_FROM: Optional[str] = None
    EMAIL_FROM_NAME: str = "MiTurno"  # Nombre que aparece en el remitente
    
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
        ⚠️ DEPRECATED: Verifica si el envío de emails está habilitado via Brevo
        Usar smtp_enabled en su lugar
        """
        return self.BREVO_API_KEY is not None and len(self.BREVO_API_KEY) > 10
    
    @property
    def smtp_enabled(self) -> bool:
        """
        ✅ NUEVO: Verifica si el envío de emails está habilitado via SMTP
        Requiere: SMTP_HOST, SMTP_USER y SMTP_PASSWORD
        """
        return bool(
            self.SMTP_HOST and 
            self.SMTP_USER and 
            self.SMTP_PASSWORD
        )
    
    @property
    def email_from(self) -> str:
        """
        ✅ BUENA PRÁCTICA: Retorna el email FROM con fallback inteligente
        
        Prioridad:
        1. Si EMAIL_FROM está en .env → usa ese
        2. Si no, construye automáticamente desde SMTP_USER
        3. Fallback genérico si nada está configurado
        
        Beneficios:
        - No duplica información (DRY principle)
        - Flexible y configurable
        - Siempre consistente con la cuenta SMTP autenticada
        """
        # 1. Si está explícitamente configurado, usar ese
        if self.EMAIL_FROM:
            return self.EMAIL_FROM
        
        # 2. Si SMTP_USER existe, construir automáticamente
        if self.SMTP_USER:
            return f"{self.EMAIL_FROM_NAME} <{self.SMTP_USER}>"
        
        # 3. Fallback genérico (solo si nada está configurado)
        return f"{self.EMAIL_FROM_NAME} <noreply@miturno.com>"
    
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