from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.empresa import Empresa  
from app.models.categoria import Categoria
from app.models.user import Usuario, TipoUsuario
from app.models.rol import UsuarioRol, Rol
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegistroRequest, RegistroResponse,
    GoogleAuthRequest, UsuarioResponse,
    RefreshTokenRequest, RefreshTokenResponse, LoginResponseWithRefresh,
    GoogleAuthURL, GoogleCallbackRequest, GoogleAuthResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,  
    ResetPasswordRequest, ResetPasswordResponse     
)
from app.auth.permissions import get_user_roles, assign_role
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_refresh_token_expiry, REFRESH_TOKEN_EXPIRE_DAYS,
    get_current_user
)
from app.config import settings
from typing import Optional
from fastapi.responses import RedirectResponse
import logging
import secrets

# Importar servicios
from app.services.google_oauth_service import google_oauth_service
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================
# ENDPOINTS DE AUTENTICACIÓN TRADICIONAL
# ============================================

@router.post("/login", response_model=LoginResponseWithRefresh)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login con email y password - Devuelve access token y refresh token
    
    Args:
        login_data: Email y password del usuario
        db: Sesión de base de datos
        
    Returns:
        LoginResponseWithRefresh con tokens y datos del usuario
        
    Raises:
        HTTPException 401: Credenciales incorrectas
        HTTPException 400: Cuenta usa Google OAuth
    """
    # Buscar usuario por email
    user = db.query(Usuario).filter(Usuario.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    # Validar que el usuario tenga password (no es OAuth)
    if user.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google login. Please sign in with Google."
        )

    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    # 1. Obtener el rol de sistema más alto del usuario desde la tabla usuario_rol
    roles = get_user_roles(user.usuario_id, db)
    
    # 2. Determinar el valor que irá en el token (priorizar rol de sistema sobre tipo_usuario)
    # Asumimos que get_user_roles devuelve el rol más alto primero (ej: ['SUPERADMIN', 'CLIENTE'])
    rol_principal = None
    if roles:
        # Usamos el primer rol (el más alto) como el rol principal de la sesión
        rol_principal = roles[0] 
    
    # Si no se encontró un rol de sistema, usamos el tipo_usuario estático como respaldo
    if rol_principal is None or rol_principal not in ["SUPERADMIN", "ADMIN", "ADMIN_EMPRESA"]:
        rol_principal = user.tipo_usuario.value
    
    # 3. Crear access token y añadir el campo tipo_usuario con el rol principal
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": str(user.usuario_id),
            "email": user.email,
            # 💡 ESTO AHORA ES CORRECTO: Envía el rol de sistema ('SUPERADMIN')
            "tipo_usuario": rol_principal 
        },
        expires_delta=access_token_expires
    )
    
    # Crear refresh token
    refresh_token_str = create_refresh_token()
    refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token_record = RefreshToken(
        usuario_id=user.usuario_id,
        token=refresh_token_str,
        expira_en=refresh_token_expires,
        revocado=False
    )
    
    db.add(refresh_token_record)
    db.commit()
    
    logger.info(f"Login exitoso para usuario: {user.email}")
    
    return LoginResponseWithRefresh(
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        usuario=UsuarioResponse.model_validate(user)
    )


@router.post("/register", response_model=RegistroResponse)
async def register(
    registro_data: RegistroRequest,
    db: Session = Depends(get_db)
):
    """
    Registro de nuevo usuario (cliente o empresa)
    
    Args:
        registro_data: Datos del nuevo usuario
        db: Sesión de base de datos
        
    Returns:
        RegistroResponse con ID del usuario creado
        
    Raises:
        HTTPException 400: Email ya registrado o datos inválidos
        HTTPException 404: Categoría no existe (para empresas)
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
        
        # 3. Crear nuevo usuario
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
        db.flush()  # Obtener ID del usuario
        
        # 4. Asignar rol según tipo_usuario usando sistema RBAC
        if registro_data.tipo_usuario == TipoUsuario.CLIENTE:
            rol_nombre = "CLIENTE"
            
        elif registro_data.tipo_usuario == TipoUsuario.EMPRESA:
            rol_nombre = "EMPRESA"  # Cuando cree la empresa se cambiará a ADMIN_EMPRESA
            
        else:
            rol_nombre = "CLIENTE"  # Por defecto

        # 5. Asignar rol usando helper (maneja usuario_rol correctamente)
        assign_role(
            usuario_id=new_user.usuario_id,
            rol_nombre=rol_nombre,
            db=db,
            empresa_id=None  # NULL para roles globales
        )
        
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Usuario registrado exitosamente: {new_user.email}")
        
        return RegistroResponse(
            message="User registered successfully",
            usuario_id=new_user.usuario_id
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error durante registro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during registration: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Obtener nuevo access token usando refresh token
    
    Args:
        request: Refresh token
        db: Sesión de base de datos
        
    Returns:
        RefreshTokenResponse con nuevo access token
        
    Raises:
        HTTPException 401: Token inválido o expirado
    """
    try:
        # Buscar token en BD
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == request.refresh_token,
            RefreshToken.revocado == False
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token"
            )
        
        # Verificar si expiró
        if not verify_refresh_token_expiry(token_record):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        
        # Obtener usuario
        user = db.query(Usuario).filter(
            Usuario.usuario_id == token_record.usuario_id
        ).first()
        
        if not user or not user.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        # 🛑 COPIAR LÓGICA DE ROL PRINCIPAL PARA REFRESH 🛑
        roles = get_user_roles(user.usuario_id, db)
        rol_principal = roles[0] if roles else user.tipo_usuario.value
        if rol_principal not in ["SUPERADMIN", "ADMIN"]:
            rol_principal = user.tipo_usuario.value

        # Crear nuevo access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={
                "sub": str(user.usuario_id),
                "email": user.email,
                # 💡 Aquí también se usa el rol principal
                "tipo_usuario": rol_principal 
            },
            expires_delta=access_token_expires
        )
        
        logger.info(f"Access token renovado para usuario: {user.email}")
        
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en refresh_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token"
        )


# ============================================
# GOOGLE OAUTH ENDPOINTS
# ============================================

@router.get("/google/url", response_model=GoogleAuthURL)
async def get_google_auth_url():
    """
    Obtiene la URL de autorización de Google OAuth
    
    Returns:
        GoogleAuthURL con la URL y state token
    """
    try:
        auth_url, state = google_oauth_service.get_authorization_url()
        logger.info(f"URL de autorización generada con state: {state[:10]}...")
        
        return GoogleAuthURL(
            authorization_url=auth_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error generando URL de Google OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating Google OAuth URL"
        )


@router.post("/google/callback", response_model=GoogleAuthResponse)
async def google_callback(
    request: GoogleCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Callback de Google OAuth - procesa el código de autorización
    
    Args:
        request: Código y state de Google
        db: Sesión de base de datos
        
    Returns:
        GoogleAuthResponse con tokens y datos del usuario
        
    Raises:
        HTTPException 400: Error en autenticación con Google
    """
    try:
        # Obtener información del usuario de Google
        user_info = google_oauth_service.get_user_info(request.code)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        # Buscar o crear usuario
        user = db.query(Usuario).filter(Usuario.email == user_info['email']).first()
        
        if not user:
            # Crear nuevo usuario desde Google OAuth
            user = Usuario(
                email=user_info['email'],
                nombre=user_info.get('given_name', ''),
                apellido=user_info.get('family_name', ''),
                google_id=user_info['id'],
                picture_url=user_info.get('picture'),
                password=None,  # No password para OAuth
                tipo_usuario=TipoUsuario.CLIENTE,  # Por defecto cliente
                telefono=None
            )
            
            db.add(user)
            db.flush()
            
            # Asignar rol de CLIENTE usando sistema RBAC
            assign_role(
                usuario_id=user.usuario_id,
                rol_nombre="CLIENTE",
                db=db,
                empresa_id=None
            )
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Nuevo usuario creado via Google OAuth: {user.email}")
        else:
            # Actualizar info de Google si cambió
            if user.google_id != user_info['id']:
                user.google_id = user_info['id']
            if user.picture_url != user_info.get('picture'):
                user.picture_url = user_info.get('picture')
            db.commit()
            
            logger.info(f"Login via Google OAuth: {user.email}")
        
        # Crear tokens usando rol real del sistema RBAC
        roles = get_user_roles(user.usuario_id, db)
        rol_principal = roles[0] if roles else "CLIENTE"
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={
                "sub": str(user.usuario_id),
                "email": user.email,
                "tipo_usuario": rol_principal
            },
            expires_delta=access_token_expires
        )
        
        refresh_token_str = create_refresh_token()
        refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        refresh_token_record = RefreshToken(
            usuario_id=user.usuario_id,
            token=refresh_token_str,
            expira_en=refresh_token_expires,
            revocado=False
        )
        
        db.add(refresh_token_record)
        db.commit()
        
        return GoogleAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            usuario=UsuarioResponse.model_validate(user)
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en Google callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing Google authentication"
        )


# ============================================
# PASSWORD RESET ENDPOINTS
# ============================================

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Solicita recuperación de contraseña - envía email con token
    
    CORREGIDO: Ahora maneja errores apropiadamente:
    - Modo desarrollo (sin API key): loguea en consola y retorna 200
    - Modo producción (con API key): exige envío exitoso o retorna 500
    
    Args:
        request: Email del usuario
        db: Sesión de base de datos
        
    Returns:
        ForgotPasswordResponse con mensaje genérico (por seguridad)
        
    Raises:
        HTTPException 500: Error enviando email (solo en producción)
    """
    try:
        # Mensaje genérico (por seguridad - no revelar si el email existe)
        response_message = "Si el email existe, recibirás un correo con instrucciones"
        
        logger.info(f"Solicitud de recuperación de contraseña para: {request.email}")
        
        # Buscar usuario
        usuario = db.query(Usuario).filter(
            Usuario.email == request.email,
            Usuario.activo == True
        ).first()
        
        if usuario:
            logger.info(f"Usuario encontrado: {usuario.email} (ID: {usuario.usuario_id})")
            
            # Verificar que el usuario tenga password (no sea OAuth)
            if usuario.password is None:
                logger.info(f"Intento de recuperación para cuenta OAuth: {request.email}")
                # Por seguridad, retornar el mismo mensaje
                return ForgotPasswordResponse(
                    message=response_message,
                    email=request.email
                )
            
            # Generar token único
            token = secrets.token_urlsafe(32)
            logger.info(f"Token generado para: {usuario.email}")
            
            # Crear registro en BD
            reset_token = PasswordResetToken(
                usuario_id=usuario.usuario_id,
                token=token,
                fecha_expiracion=datetime.utcnow() + timedelta(hours=1),
                usado=False
            )
            
            db.add(reset_token)
            db.commit()
            logger.info(f"Token guardado en BD para: {usuario.email}")
            
            # ========================================
            # ENVIAR EMAIL - SECCIÓN CRÍTICA
            # ========================================
            try:
                email_enviado = EmailService.enviar_recuperacion_password(
                    email=usuario.email,
                    token=token,
                    nombre=usuario.nombre
                )
                
                # ✅ CORREGIDO: Verificar resultado según modo
                if settings.brevo_enabled:
                    # MODO PRODUCCIÓN: Email debe enviarse exitosamente
                    if not email_enviado:
                        logger.error(f"Error enviando email a: {usuario.email}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error enviando email de recuperación. Intenta nuevamente."
                        )
                    logger.info(f"✅ Email enviado exitosamente a: {usuario.email}")
                else:
                    # MODO DESARROLLO: Email logueado en consola
                    logger.info(f"✅ Email logueado en consola (modo desarrollo) para: {usuario.email}")
                
            except HTTPException:
                # Re-lanzar HTTPException sin modificar
                raise
            except Exception as email_error:
                logger.error(f"Excepción enviando email a {usuario.email}: {email_error}")
                
                # En producción, esto es un error crítico
                if settings.brevo_enabled:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error enviando email de recuperación. Intenta nuevamente."
                    )
                # En desarrollo, continuar (el token está logueado)
                logger.warning("⚠️ Error en desarrollo - continuando (token logueado en consola)")
                    
        else:
            logger.info(f"Email no encontrado o usuario inactivo: {request.email}")
        
        # Siempre retornar el mismo mensaje (por seguridad)
        return ForgotPasswordResponse(
            message=response_message,
            email=request.email
        )
        
    except HTTPException:
        # Re-lanzar HTTPException sin modificar
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error general en forgot_password: {e}")
        # Por seguridad, NO revelar detalles del error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando solicitud. Intenta nuevamente."
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Resetea la contraseña usando el token enviado por email
    
    Args:
        request: Token y nueva contraseña
        db: Sesión de base de datos
        
    Returns:
        ResetPasswordResponse confirmando el cambio
        
    Raises:
        HTTPException 400: Token inválido, expirado o ya usado
        HTTPException 404: Token no encontrado
    """
    try:
        # Buscar token en BD
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == request.token,
            PasswordResetToken.usado == False
        ).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token inválido o ya usado"
            )
        
        # Verificar si expiró
        if reset_token.fecha_expiracion < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token expirado. Solicita uno nuevo."
            )
        
        # Obtener usuario
        usuario = db.query(Usuario).filter(
            Usuario.usuario_id == reset_token.usuario_id
        ).first()
        
        if not usuario or not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado o inactivo"
            )
        
        # Actualizar contraseña
        usuario.password = get_password_hash(request.new_password)
        
        # Marcar token como usado
        reset_token.usado = True
        reset_token.fecha_uso = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Contraseña reseteada exitosamente para: {usuario.email}")
        
        return ResetPasswordResponse(
            message="Contraseña actualizada exitosamente",
            success=True
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en reset_password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al resetear contraseña"
        )


# ============================================
# ENDPOINTS DE UTILIDAD
# ============================================

@router.post("/logout")
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Cierra sesión revocando el refresh token
    
    Args:
        refresh_token: Token a revocar
        db: Sesión de base de datos
        
    Returns:
        Mensaje de confirmación
    """
    try:
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        if token_record:
            token_record.revocado = True
            db.commit()
            logger.info(f"Refresh token revocado para usuario: {token_record.usuario_id}")
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        db.rollback()
        return {"message": "Logout successful"}  # Siempre confirmar logout


@router.get("/verify-token")
async def verify_token(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifica si el token JWT es válido
    
    Útil para validar tokens en el frontend sin hacer una request completa.
    
    Args:
        current_user: Usuario autenticado (inyectado por dependency)
        db: Sesión de base de datos
        
    Returns:
        Información básica del usuario con roles reales
    """
    roles = get_user_roles(current_user.usuario_id, db)
    return {
        "valid": True,
        "usuario_id": current_user.usuario_id,
        "email": current_user.email,
        "roles": roles,
        "rol_principal": roles[0] if roles else None
    }