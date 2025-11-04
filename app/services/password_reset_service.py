import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import Usuario
from app.models.password_reset_token import PasswordResetToken
from app.core.security import get_password_hash


class PasswordResetService:
    """
    Servicio para gestionar recuperación de contraseñas.
    """
    
    @staticmethod
    def generate_token() -> str:
        """
        Genera un token único seguro.
        
        Returns:
            Token de 64 caracteres hexadecimales
        """
        return secrets.token_urlsafe(48)  # Genera ~64 caracteres
    
    @staticmethod
    def create_reset_token(
        db: Session,
        usuario_id: int,
        ip_address: Optional[str] = None,
        expiration_hours: int = 24
    ) -> PasswordResetToken:
        """
        Crea un token de reset de contraseña para un usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            ip_address: IP desde donde se solicita
            expiration_hours: Horas hasta expiración (default: 24)
            
        Returns:
            Token creado
        """
        # Invalidar tokens anteriores del usuario
        PasswordResetService._invalidate_previous_tokens(db, usuario_id)
        
        # Crear nuevo token
        token = PasswordResetToken(
            usuario_id=usuario_id,
            token=PasswordResetService.generate_token(),
            fecha_expiracion=datetime.utcnow() + timedelta(hours=expiration_hours),
            ip_solicitud=ip_address
        )
        
        db.add(token)
        db.commit()
        db.refresh(token)
        
        return token
    
    @staticmethod
    def _invalidate_previous_tokens(db: Session, usuario_id: int):
        """
        Invalida todos los tokens anteriores del usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
        """
        db.query(PasswordResetToken).filter(
            PasswordResetToken.usuario_id == usuario_id,
            PasswordResetToken.usado == False
        ).update({"usado": True, "fecha_uso": datetime.utcnow()})
        db.commit()
    
    @staticmethod
    def validate_token(db: Session, token: str) -> Optional[PasswordResetToken]:
        """
        Valida un token de reset.
        
        Args:
            db: Sesión de base de datos
            token: Token a validar
            
        Returns:
            Token si es válido, None si no existe o es inválido
        """
        token_obj = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()
        
        if not token_obj:
            return None
        
        # Verificar si es válido (no usado y no expirado)
        if not token_obj.is_valid():
            return None
        
        return token_obj
    
    @staticmethod
    def reset_password(
        db: Session,
        token: str,
        nueva_password: str,
        ip_address: Optional[str] = None
    ) -> Usuario:
        """
        Resetea la contraseña de un usuario usando un token válido.
        
        Args:
            db: Sesión de base de datos
            token: Token de reset
            nueva_password: Nueva contraseña en texto plano
            ip_address: IP desde donde se resetea
            
        Returns:
            Usuario actualizado
            
        Raises:
            HTTPException: Si el token es inválido o expirado
        """
        # Validar token
        token_obj = PasswordResetService.validate_token(db, token)
        
        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido o expirado"
            )
        
        # Obtener usuario
        usuario = db.query(Usuario).filter(
            Usuario.usuario_id == token_obj.usuario_id
        ).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Actualizar contraseña
        usuario.password = get_password_hash(nueva_password)
        
        # Marcar token como usado
        token_obj.usado = True
        token_obj.fecha_uso = datetime.utcnow()
        token_obj.ip_uso = ip_address
        
        db.commit()
        db.refresh(usuario)
        
        return usuario
    
    @staticmethod
    def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
        """
        Busca un usuario por email.
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            
        Returns:
            Usuario si existe, None si no
        """
        return db.query(Usuario).filter(
            Usuario.email == email,
            Usuario.activo == True
        ).first()
    
    @staticmethod
    def cleanup_expired_tokens(db: Session, days_old: int = 7):
        """
        Limpia tokens expirados de la base de datos.
        
        Args:
            db: Sesión de base de datos
            days_old: Días de antigüedad para eliminar (default: 7)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        db.query(PasswordResetToken).filter(
            PasswordResetToken.fecha_expiracion < cutoff_date
        ).delete()
        
        db.commit()
    
    @staticmethod
    def get_reset_link(token: str, base_url: str) -> str:
        """
        Genera el link completo de recuperación.
        
        Args:
            token: Token de reset
            base_url: URL base del frontend
            
        Returns:
            URL completa de reset
        """
        return f"{base_url}/reset-password?token={token}"