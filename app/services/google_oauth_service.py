"""
Google OAuth Service - MiTurno API (Versión con tipo_usuario)
Gestiona autenticación con Google OAuth 2.0 con asignación de roles según tipo
"""

from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from typing import Optional, Dict, Any
from datetime import timedelta
import logging

from app.config import settings
from app.models.user import Usuario
from app.models.rol import Rol, UsuarioRol
from app.core.security import create_access_token
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Servicio para manejo de Google OAuth con roles dinámicos"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Genera URL de autorización de Google
        
        Args:
            state: Estado opcional para validación
            
        Returns:
            URL de autorización de Google
        """
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'
            ]
        )
        
        flow.redirect_uri = self.redirect_uri
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        return authorization_url
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica un ID token de Google
        
        Args:
            token: ID token de Google
            
        Returns:
            Información del usuario de Google
            
        Raises:
            HTTPException: Si el token es inválido
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return idinfo
            
        except ValueError as e:
            logger.error(f"Error verificando token de Google: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de Google inválido"
            )
    
    def validate_and_create_user(
        self, 
        id_token_str: str, 
        tipo_usuario: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Valida token de Google y crea/actualiza usuario con rol según tipo
        
        Args:
            id_token_str: ID token de Google
            tipo_usuario: Tipo de usuario ('cliente' o 'empresa')
            db: Sesión de base de datos
            
        Returns:
            Dict con access_token, usuario y es_nuevo_usuario
        """
        try:
            # Validar token con Google
            google_user_info = self.verify_token(id_token_str)
            
            email = google_user_info.get('email')
            google_id = google_user_info.get('sub')
            nombre = google_user_info.get('given_name', '')
            apellido = google_user_info.get('family_name', '')
            picture_url = google_user_info.get('picture')
            
            if not email or not google_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token de Google no contiene email o ID"
                )
            
            # Buscar usuario existente por email o google_id
            usuario = db.query(Usuario).filter(
                (Usuario.email == email) | (Usuario.google_id == google_id)
            ).first()
            
            es_nuevo_usuario = False
            
            if not usuario:
                # NUEVO USUARIO - Crear según tipo elegido
                es_nuevo_usuario = True
                
                # Mapear tipo_usuario a tipo del modelo
                tipo_usuario_model = 'CLIENTE' if tipo_usuario == 'cliente' else 'EMPRESA'
                
                usuario = Usuario(
                    email=email,
                    nombre=nombre,
                    apellido=apellido,
                    google_id=google_id,
                    picture_url=picture_url,
                    tipo_usuario=tipo_usuario_model,
                    activo=True
                )
                db.add(usuario)
                db.flush()  # Para obtener el ID
                
                # Asignar rol según tipo elegido
                if tipo_usuario == 'cliente':
                    rol = db.query(Rol).filter(Rol.nombre == 'CLIENTE').first()
                else:  # empresa
                    rol = db.query(Rol).filter(Rol.nombre == 'EMPRESA').first()
                
                if rol:
                    usuario_rol = UsuarioRol(
                        usuario_id=usuario.usuario_id,
                        rol_id=rol.rol_id,
                        empresa_id=None,  # Rol global inicialmente
                        activo=True
                    )
                    db.add(usuario_rol)
                else:
                    logger.error(f"Rol no encontrado para tipo: {tipo_usuario}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error asignando rol al usuario"
                    )
                
                db.commit()
                db.refresh(usuario)
                
                logger.info(f"Nuevo usuario {tipo_usuario} creado vía Google OAuth: {email}")
                
            else:
                # USUARIO EXISTENTE
                # Actualizar google_id si no lo tenía
                if not usuario.google_id:
                    usuario.google_id = google_id
                
                # Actualizar picture_url si cambió
                if picture_url and usuario.picture_url != picture_url:
                    usuario.picture_url = picture_url
                
                # Actualizar apellido si estaba vacío
                if not usuario.apellido and apellido:
                    usuario.apellido = apellido
                
                db.commit()
                db.refresh(usuario)
                
                logger.info(f"Usuario existente logueado vía Google OAuth: {email}")
            
            # Generar JWT token
            access_token = create_access_token(
            data={
                "sub": str(usuario.usuario_id),
                "email": usuario.email,
                "tipo_usuario": usuario.tipo_usuario.value
            },
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "usuario": usuario,
                "es_nuevo_usuario": es_nuevo_usuario
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en Google OAuth: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error procesando autenticación de Google: {str(e)}"
            )


# Instancia singleton
google_oauth_service = GoogleOAuthService()