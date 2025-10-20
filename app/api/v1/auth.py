from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.empresa import Empresa  
from app.models.categoria import Categoria
from app.models.user import Usuario, TipoUsuario
from app.models.rol import UsuarioRol
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegistroRequest, RegistroResponse,
    GoogleAuthRequest, UsuarioResponse
)
from app.core.security import verify_password, get_password_hash, create_access_token
from app.config import settings
from typing import Optional
from fastapi.responses import RedirectResponse
import logging

# Importar el servicio y schemas nuevos
from app.services.google_oauth_service import google_oauth_service
from app.schemas.auth import GoogleAuthURL, GoogleCallbackRequest, GoogleAuthResponse

logger = logging.getLogger(__name__)

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
            "sub": str(user.usuario_id),
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
    try:
        # 1. Verificar si email ya existe
        existing_user = db.query(Usuario).filter(Usuario.email == registro_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 2. Si es empresa, validar categoría ANTES de crear usuario
        if registro_data.tipo_usuario == TipoUsuario.EMPRESA:
            if not registro_data.categoria_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="categoria_id es requerido para registro de empresas"
                )
    
            # Verificar que la categoría existe
            categoria = db.query(Categoria).filter(
                Categoria.categoria_id == registro_data.categoria_id,
                Categoria.activa == True
            ).first()
    
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoría con ID {registro_data.categoria_id} no existe o no está activa"
                )
        
        # 3. Crear nuevo usuario (SIN flush todavía)
        hashed_password = get_password_hash(registro_data.password)
        
        new_user = Usuario(
            email=registro_data.email,
            password=hashed_password,
            nombre=registro_data.nombre,
            apellido=registro_data.apellido,
            telefono=registro_data.telefono,
            tipo_usuario=registro_data.tipo_usuario
        )
        
        db.add(new_user)
        db.flush()  # Ahora sí, flush DESPUÉS de validaciones
        
        # 4. Determinar rol según tipo_usuario
        rol_id = None
        if registro_data.tipo_usuario == TipoUsuario.CLIENTE:
            rol_id = 6  # Rol Cliente
            
        elif registro_data.tipo_usuario == TipoUsuario.EMPRESA:
            rol_id = 4  # Rol Empresa
    
            # Crear registro en tabla empresa
            nueva_empresa = Empresa(
                usuario_id=new_user.usuario_id,
                categoria_id=registro_data.categoria_id,
                razon_social=registro_data.nombre,
                activa=True
            )
            db.add(nueva_empresa)
            
        else:
            # Por defecto, asignar Cliente
            rol_id = 6

        # 5. Crear relación usuario-rol
        usuario_rol = UsuarioRol(
            usuario_id=new_user.usuario_id,
            rol_id=rol_id,
            empresa_id=None,  # Para clientes es NULL
            asignado_por=None,  # Auto-asignado durante registro
            fecha_asignado=datetime.utcnow(),
            fecha_vencimiento=None,
            activo=True
        )
        
        db.add(usuario_rol)
        db.commit()  # Commit de toda la transacción
        db.refresh(new_user)
        
        return RegistroResponse(
            message="User registered successfully",
            usuario_id=new_user.usuario_id
        )
        
    except HTTPException:
        # Re-lanzar HTTPExceptions (como email ya registrado)
        db.rollback()
        raise
    except Exception as e:
        # Rollback en caso de cualquier error inesperado
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during registration: {str(e)}"
        )

@router.post("/google", response_model=LoginResponse)
async def google_auth(
    google_data: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticación con Google OAuth - Recibe id_token del frontend
    """
    try:
        # Verificar el token con Google
        user_info = await google_oauth_service.verify_google_token(google_data.token)
        
        # Buscar o crear usuario
        user = db.query(Usuario).filter(Usuario.google_id == user_info['sub']).first()
        
        if not user:
            # Buscar por email
            user = db.query(Usuario).filter(Usuario.email == user_info['email']).first()
            
            if user:
                # Usuario existe, vincular Google ID
                user.google_id = user_info['sub']
                user.picture_url = user_info.get('picture')
            else:
                # Crear nuevo usuario
                user = Usuario(
                    email=user_info['email'],
                    nombre=user_info.get('given_name', ''),
                    apellido=user_info.get('family_name', ''),
                    google_id=user_info['sub'],
                    picture_url=user_info.get('picture'),
                    tipo_usuario=TipoUsuario.CLIENTE,
                    password=None  # Sin password para OAuth
                )
                db.add(user)
                db.flush()
                
                # Asignar rol Cliente
                usuario_rol = UsuarioRol(
                    usuario_id=user.usuario_id,
                    rol_id=6,  # Cliente
                    activo=True
                )
                db.add(usuario_rol)
            
            db.commit()
            db.refresh(user)
        
        # Crear JWT token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={
                "sub": str(user.usuario_id),
                "email": user.email,
                "tipo_usuario": user.tipo_usuario.value
            },
            expires_delta=access_token_expires
        )
        
        return LoginResponse(
            message="Google login successful",
            token=access_token,
            usuario=UsuarioResponse.model_validate(user)
        )
        
    except Exception as e:
        logger.error(f"Error en Google OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    
# ============================================
# GOOGLE OAUTH ENDPOINTS (Nuevo flujo)
# ============================================

@router.get("/google/login", response_model=GoogleAuthURL)
async def google_login():
    """
    Inicia el flujo de autenticación con Google
    
    Returns:
        URL de autorización de Google donde redirigir al usuario
    """
    try:
        authorization_url = google_oauth_service.get_authorization_url()
        
        return GoogleAuthURL(
            authorization_url=authorization_url,
            message="Redirige al usuario a esta URL"
        )
        
    except Exception as e:
        logger.error(f"Error generando URL de Google: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error iniciando autenticación con Google"
        )


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Callback de Google OAuth - Procesa la respuesta de Google
    
    Args:
        code: Authorization code de Google
        state: Estado de validación opcional
        db: Sesión de base de datos
        
    Returns:
        Redirección al frontend con el token
    """
    try:
        # Procesar el callback
        result = await google_oauth_service.handle_google_callback(code, db)
        
        # URL del frontend (ajusta según tu configuración)
        frontend_url = "http://localhost:3000"  # Cambiar por tu URL de frontend
        
        # Redirigir al frontend con el token y flag de nuevo usuario
        redirect_url = (
            f"{frontend_url}/auth/google/success"
            f"?token={result['access_token']}"
            f"&new_user={str(result['es_nuevo_usuario']).lower()}"
        )
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en callback de Google: {e}")
        
        # Redirigir al frontend con error
        frontend_url = "http://localhost:3000"
        error_url = f"{frontend_url}/auth/google/error?message={str(e)}"
        return RedirectResponse(url=error_url)


@router.post("/google/token", response_model=GoogleAuthResponse)
async def google_auth_token(
    request: GoogleCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint alternativo para recibir el código de Google (para SPAs)
    
    Args:
        request: Request con el código de autorización
        db: Sesión de base de datos
        
    Returns:
        Token JWT y datos del usuario
    """
    try:
        result = await google_oauth_service.handle_google_callback(
            request.code, 
            db
        )
        
        # Convertir usuario a UsuarioResponse
        usuario_data = UsuarioResponse.model_validate(result['usuario'])
        
        return GoogleAuthResponse(
            access_token=result['access_token'],
            token_type=result['token_type'],
            usuario=usuario_data,
            es_nuevo_usuario=result['es_nuevo_usuario']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando token de Google: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en autenticación: {str(e)}"
        )
