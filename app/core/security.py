# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.schemas.auth import TokenData
from app.database import get_db
from app.models.user import Usuario
from app.core.logger import get_logger

import secrets

# Logger específico para autenticación
auth_logger = get_logger("miturno.auth")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme - auto_error=False para manejar manualmente el error 401
oauth2_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar password con hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Crear hash de password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear JWT token"""
    auth_logger.debug(f"Creando token para: {data.get('email', 'unknown')}")
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        auth_logger.info(f"Token creado exitosamente para usuario: {data.get('email')}")
        return encoded_jwt
    except Exception as e:
        auth_logger.error(f"Error creando token: {str(e)}")
        raise

def verify_token(token: str) -> TokenData:
    """Verificar y decodificar JWT token"""
    auth_logger.debug("Iniciando verificación de token")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_logger.debug(f"Decodificando token con SECRET_KEY: {settings.secret_key[:10]}... y algoritmo: {settings.algorithm}")
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        auth_logger.debug("Token decodificado exitosamente")
        
        usuario_id: int = int(payload.get("sub"))
        email: str = payload.get("email")
        tipo_usuario: str = payload.get("tipo_usuario")
        
        auth_logger.debug(f"Datos extraídos - usuario_id: {usuario_id}, email: {email}")
        
        if usuario_id is None:
            auth_logger.warning("Token válido pero sin usuario_id en payload")
            raise credentials_exception
            
        token_data = TokenData(
            usuario_id=usuario_id,
            email=email,
            tipo_usuario=tipo_usuario
        )
        
        auth_logger.info(f"Token verificado exitosamente para usuario: {email}")
        return token_data
        
    except JWTError as e:
        auth_logger.error(f"Error JWT al verificar token: {str(e)}")
        raise credentials_exception
    except Exception as e:
        auth_logger.error(f"Error inesperado verificando token: {str(e)}, tipo: {type(e)}")
        raise credentials_exception

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Obtener usuario actual desde JWT token
    Para usar como dependencia en endpoints protegidos
    
    Retorna:
    - Usuario si el token es válido
    
    Errores:
    - 401: Sin token o token inválido (no autenticado)
    - 500: Error de base de datos
    """
    auth_logger.debug("Iniciando get_current_user")
    
    # Excepción estándar para problemas de autenticación
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # ✅ NUEVO: Verificar si hay credenciales (token presente)
        if credentials is None:
            auth_logger.warning("Intento de acceso sin token de autenticación")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se proporcionó token de autenticación",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar token
        token_data = verify_token(credentials.credentials)
        auth_logger.debug(f"Token verificado, buscando usuario ID: {token_data.usuario_id}")
        
        # Buscar usuario en BD
        user = db.query(Usuario).filter(Usuario.usuario_id == token_data.usuario_id).first()
        
        if user is None:
            auth_logger.warning(f"Usuario {token_data.usuario_id} no encontrado en BD")
            raise credentials_exception
        
        # Verificar que el usuario esté activo
        if not user.activo:
            auth_logger.warning(f"Intento de acceso con usuario inactivo: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo",
                headers={"WWW-Authenticate": "Bearer"},
        )
            
        auth_logger.info(f"Usuario autenticado exitosamente: {user.email}")
        return user
        
    except HTTPException as e:
        auth_logger.error(f"HTTPException en get_current_user: {e.detail}")
        raise e
    except SQLAlchemyError as e:
        auth_logger.error(f"Error de BD en get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during authentication"
        )
    except Exception as e:
        auth_logger.error(f"Error inesperado en get_current_user: {str(e)}")
        raise credentials_exception
    
# Configuración de refresh tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_refresh_token() -> str:
    """
    Genera un refresh token aleatorio seguro
    """
    return secrets.token_urlsafe(64)

def verify_refresh_token_expiry(expira_en: datetime) -> bool:
    """
    Verifica si un refresh token ha expirado
    """
    return datetime.utcnow() < expira_en