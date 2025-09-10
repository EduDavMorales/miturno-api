from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import verify_token
from app.models.user import Usuario, TipoUsuario
from app.schemas.auth import TokenData

# Security scheme
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency para obtener usuario actual autenticado
    """
    # Verificar token
    token_data: TokenData = verify_token(credentials.credentials)
    
    # Buscar usuario en BD
    user = db.query(Usuario).filter(Usuario.usuario_id == token_data.usuario_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

def get_current_client(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependency para verificar que el usuario actual es un cliente
    """
    if current_user.tipo_usuario != TipoUsuario.CLIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Client role required."
        )
    return current_user

def get_current_empresa(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependency para verificar que el usuario actual es una empresa
    """
    if current_user.tipo_usuario != TipoUsuario.EMPRESA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Business role required."
        )
    return current_user