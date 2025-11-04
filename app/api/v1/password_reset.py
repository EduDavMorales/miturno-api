from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse,
    PasswordResetSuccessResponse,
    TokenValidationResponse
)
from app.services.password_reset_service import PasswordResetService


router = APIRouter(prefix="/auth", tags=["Recuperación de Contraseña"])


@router.post(
    "/forgot-password",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperación de contraseña",
    description="""
    Envía un email con un link de recuperación de contraseña al usuario.
    
    **Características de seguridad:**
    - Siempre retorna éxito aunque el email no exista (previene enumeración de usuarios)
    - Invalida tokens anteriores del usuario
    - Token expira en 24 horas
    - Registra IP de la solicitud
    
    **Flujo:**
    1. Usuario ingresa su email
    2. Sistema busca el usuario
    3. Si existe, genera token y envía email
    4. Si no existe, retorna mensaje genérico (por seguridad)
    """
)
async def forgot_password(
    request_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Solicita recuperación de contraseña.
    
    Retorna siempre éxito para prevenir enumeración de usuarios.
    """
    email = request_data.email
    
    # Buscar usuario
    usuario = PasswordResetService.get_usuario_by_email(db, email)
    
    if usuario:
        # Obtener IP del cliente
        ip_address = request.client.host if request.client else None
        
        # Crear token de reset
        reset_token = PasswordResetService.create_reset_token(
            db=db,
            usuario_id=usuario.usuario_id,
            ip_address=ip_address
        )
        
        # TODO: Enviar email con el link de recuperación
        # En producción, aquí se enviaría el email real
        # Por ahora, solo generamos el link para testing
        
        # Generar link de reset (usar URL del frontend)
        # En producción: base_url = "https://tu-frontend.com"
        # Para desarrollo:
        base_url = "http://localhost:3000"  # Ajustar según tu frontend
        reset_link = PasswordResetService.get_reset_link(reset_token.token, base_url)
        
        # TODO: Enviar email
        print(f"🔗 Link de recuperación (TEMPORAL - solo para testing):")
        print(f"   {reset_link}")
        print(f"   Token: {reset_token.token}")
        print(f"   Usuario: {usuario.email}")
        print(f"   Expira en: 24 horas")
    
    # IMPORTANTE: Siempre retornar el mismo mensaje (seguridad)
    # Esto previene que atacantes sepan si un email existe o no
    return PasswordResetResponse(
        mensaje="Si el email existe, recibirás un link de recuperación",
        email=email
    )


@router.post(
    "/reset-password",
    response_model=PasswordResetSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Resetear contraseña con token",
    description="""
    Resetea la contraseña del usuario usando un token válido.
    
    **Validaciones:**
    - Token debe ser válido y no expirado
    - Token no debe haber sido usado anteriormente
    - Nueva contraseña debe cumplir requisitos de seguridad:
        - Mínimo 8 caracteres
        - Al menos 1 mayúscula
        - Al menos 1 minúscula
        - Al menos 1 número
    - Contraseña y confirmación deben coincidir
    
    **Efecto:**
    - Actualiza la contraseña del usuario
    - Marca el token como usado
    - Registra IP del reset
    """
)
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Resetea la contraseña usando un token válido.
    """
    # Obtener IP del cliente
    ip_address = request.client.host if request.client else None
    
    # Resetear contraseña
    try:
        usuario = PasswordResetService.reset_password(
            db=db,
            token=reset_data.token,
            nueva_password=reset_data.nueva_password,
            ip_address=ip_address
        )
        
        return PasswordResetSuccessResponse(
            mensaje="Contraseña actualizada exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resetear contraseña: {str(e)}"
        )


@router.get(
    "/validate-reset-token/{token}",
    response_model=TokenValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar token de reset",
    description="""
    Valida si un token de recuperación es válido.
    
    **Útil para:**
    - Verificar en el frontend si el token es válido antes de mostrar el formulario
    - Mostrar mensajes de error si el token expiró
    
    **Retorna:**
    - valido: true/false
    - mensaje: Descripción del estado
    - email: Email del usuario (solo si el token es válido)
    """
)
async def validate_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Valida si un token de reset es válido.
    """
    # Validar token
    token_obj = PasswordResetService.validate_token(db, token)
    
    if not token_obj:
        return TokenValidationResponse(
            valido=False,
            mensaje="Token inválido o expirado",
            email=None
        )
    
    # Obtener email del usuario
    usuario = db.query(PasswordResetService.get_usuario_by_email.__self__).filter(
        PasswordResetService.get_usuario_by_email.__self__.usuario_id == token_obj.usuario_id
    ).first()
    
    from app.models.user import Usuario
    usuario = db.query(Usuario).filter(
        Usuario.usuario_id == token_obj.usuario_id
    ).first()
    
    return TokenValidationResponse(
        valido=True,
        mensaje="Token válido",
        email=usuario.email if usuario else None
    )