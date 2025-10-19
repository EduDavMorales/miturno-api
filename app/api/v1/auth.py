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
    Autenticación con Google OAuth
    """
    # TODO: Implementar verificación del id_token con Google
    # Por ahora retornamos error hasta implementar Google OAuth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth not implemented yet"
    )