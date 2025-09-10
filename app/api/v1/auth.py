from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Usuario
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegistroRequest, RegistroResponse,
    GoogleAuthRequest, UsuarioResponse
)
from app.core.security import verify_password, get_password_hash, create_access_token
from app.config import settings

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login con email y password
    """
    # Buscar usuario por email
    user = db.query(Usuario).filter(Usuario.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.usuario_id,
            "email": user.email,
            "tipo_usuario": user.tipo_usuario.value
        },
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        message="Login successful",
        token=access_token,
        usuario=UsuarioResponse.model_validate(user)
    )

@router.post("/register", response_model=RegistroResponse)
async def register(
    registro_data: RegistroRequest,
    db: Session = Depends(get_db)
):
    """
    Registro de nuevo usuario (cliente o empresa)
    """
    # Verificar si email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == registro_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(registro_data.password)
    
    new_user = Usuario(
        email=registro_data.email,
        password=hashed_password,
        nombre=registro_data.nombre,
        telefono=registro_data.telefono,
        tipo_usuario=registro_data.tipo_usuario
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RegistroResponse(
        message="User registered successfully",
        usuario_id=new_user.usuario_id
    )

@router.post("/google", response_model=LoginResponse)
async def google_auth(
    google_data: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticación con Google OAuth
    """
    # TODO: Implementar verificación del id_token con Google
    # Por ahora retornamos error hasta implementar Google OAuth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth not implemented yet"
    )