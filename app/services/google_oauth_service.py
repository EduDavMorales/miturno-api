"""
Google OAuth Service - MiTurno API
Gestiona autenticación con Google OAuth 2.0
"""

from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from typing import Optional, Dict, Any
import logging

from app.config import settings
from app.models.user import Usuario
from app.models.rol import Rol, UsuarioRol
from app.core.security import create_access_token
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Servicio para manejo de Google OAuth"""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        
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
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='select_account'
        )
        
        return authorization_url
    
    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica y decodifica token de Google
        
        Args:
            token: Token ID de Google
            
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
            
            # Verificar que el token es para nuestra aplicación
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido: emisor no reconocido"
                )
            
            return idinfo
            
        except ValueError as e:
            logger.error(f"Error verificando token de Google: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de Google inválido o expirado"
            )
    
    async def handle_google_callback(
        self, 
        authorization_code: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Procesa el callback de Google OAuth
        
        Args:
            authorization_code: Código de autorización de Google
            db: Sesión de base de datos
            
        Returns:
            Dict con access_token, usuario y si es nuevo
        """
        try:
            # Crear flow para obtener tokens
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
            
            # Intercambiar código por tokens
            flow.fetch_token(code=authorization_code)
            
            # Obtener credenciales
            credentials = flow.credentials
            
            # Verificar el ID token
            idinfo = await self.verify_google_token(credentials.id_token)
            
            # Extraer información del usuario
            email = idinfo.get('email')
            nombre_completo = idinfo.get('name', '')
            google_id = idinfo.get('sub')
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo obtener el email de Google"
                )
            
            # Separar nombre y apellido
            partes_nombre = nombre_completo.split(' ', 1)
            nombre = partes_nombre[0]
            apellido = partes_nombre[1] if len(partes_nombre) > 1 else ''
            
            # Buscar o crear usuario
            usuario = db.query(Usuario).filter(Usuario.email == email).first()
            
            es_nuevo_usuario = False
            
            if not usuario:
                # Crear nuevo usuario
                from app.enums import TipoUsuario
                usuario = Usuario(
                    email=email,
                    nombre=nombre,
                    apellido=apellido,
                    telefono='',  # Vacío, puede completarlo después
                    password='',  # Vacío para usuarios OAuth
                    tipo_usuario=TipoUsuario.CLIENTE,
                    google_id=google_id,
                    activo=True
                )
                db.add(usuario)
                db.flush()  # Para obtener el ID
                
                # Asignar rol CLIENTE por defecto
                rol_cliente = db.query(Rol).filter(Rol.nombre == 'CLIENTE').first()
                if rol_cliente:
                    usuario_rol = UsuarioRol(
                        usuario_id=usuario.usuario_id,
                        rol_id=rol_cliente.rol_id,
                        empresa_id=None,  # Rol global
                        activo=True
                    )
                    db.add(usuario_rol)
                
                db.commit()
                db.refresh(usuario)
                
                es_nuevo_usuario = True
                logger.info(f"Nuevo usuario creado vía Google OAuth: {email}")
            else:
                # Actualizar google_id si no lo tenía
                if not usuario.google_id:
                    usuario.google_id = google_id
                    db.commit()
                    db.refresh(usuario)
                
                logger.info(f"Usuario existente logueado vía Google OAuth: {email}")
            
            # Generar JWT token
            access_token = create_access_token(data={"sub": str(usuario.usuario_id)})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "usuario": usuario,
                "es_nuevo_usuario": es_nuevo_usuario
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en Google OAuth callback: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error procesando autenticación de Google: {str(e)}"
            )


# Instancia singleton
google_oauth_service = GoogleOAuthService()