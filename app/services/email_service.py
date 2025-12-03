"""
Servicio de envío de emails usando Brevo (Sendinblue)
Gestiona todos los emails del sistema: invitaciones, notificaciones, etc.

MODO DESARROLLO: Si no hay API key de Brevo, loguea los emails en consola
"""
from typing import Optional
from datetime import datetime
from app.config import settings
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)
"""
Servicio de envío de emails usando Gmail SMTP
Gestiona todos los emails del sistema: invitaciones, notificaciones, recuperación de contraseña.

MODO DESARROLLO: Si no hay credenciales SMTP, loguea los emails en consola
"""
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Verificar configuración SMTP
smtp_enabled = bool(
    getattr(settings, 'SMTP_HOST', None) and 
    getattr(settings, 'SMTP_USER', None) and 
    getattr(settings, 'SMTP_PASSWORD', None)
)

if smtp_enabled:
    logger.info(f"✅ SMTP configurado correctamente ({settings.SMTP_HOST}:{settings.SMTP_PORT})")
else:
    logger.warning("⚠️ SMTP no configurado - Modo desarrollo: emails se loguearán en consola")


class EmailService:
    """Servicio centralizado para envío de emails"""
    
    @staticmethod
    def _send_email_smtp(to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        """
        Envía email via Gmail SMTP
        
        Args:
            to_email: Destinatario
            to_name: Nombre del destinatario
            subject: Asunto
            html_content: Contenido HTML
            
        Returns:
            bool: True si se envió correctamente
        """
        if not smtp_enabled:
            logger.error("❌ SMTP no está configurado")
            return False
        
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"MiTurno <{settings.SMTP_USER}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Agregar contenido HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Conectar y enviar
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()  # Seguridad TLS
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ Email enviado via SMTP a: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Error de autenticación SMTP: {str(e)}")
            logger.error("   Verifica SMTP_USER y SMTP_PASSWORD (usa App Password para Gmail)")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado enviando email: {str(e)}")
            return False
    
    @staticmethod
    def enviar_invitacion_equipo(
        email: str,
        token: str,
        empresa_nombre: str,
        rol: str,
        invitante_nombre: str,
        mensaje_personalizado: Optional[str] = None
    ) -> bool:
        """
        Envía email de invitación a unirse al equipo de una empresa
        """
        link_invitacion = f"{settings.FRONTEND_URL}/invitacion/{token}"
        
        # Traducir rol a español
        roles_esp = {
            "EMPLEADO": "Empleado",
            "RECEPCIONISTA": "Recepcionista",
            "ADMIN_EMPRESA": "Administrador"
        }
        rol_texto = roles_esp.get(rol, rol)
        
        # HTML del email
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e0e0e0;
                    border-top: none;
                }}
                .button {{
                    display: inline-block;
                    background: #4CAF50;
                    color: white !important;
                    padding: 14px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .info-box {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 ¡Has sido invitado!</h1>
            </div>
            
            <div class="content">
                <p>Hola,</p>
                
                <p><strong>{invitante_nombre}</strong> te ha invitado a unirte al equipo de <strong>{empresa_nombre}</strong> en MiTurno.</p>
                
                <div class="info-box">
                    <p style="margin: 5px 0;"><strong>🏢 Empresa:</strong> {empresa_nombre}</p>
                    <p style="margin: 5px 0;"><strong>👤 Rol asignado:</strong> {rol_texto}</p>
                    <p style="margin: 5px 0;"><strong>✉️ Tu email:</strong> {email}</p>
                </div>
                
                {"<div style='background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;'><strong>Mensaje de " + invitante_nombre + ":</strong><br>" + mensaje_personalizado + "</div>" if mensaje_personalizado else ""}
                
                <p>Para aceptar la invitación y crear tu cuenta, haz click en el siguiente botón:</p>
                
                <div style="text-align: center;">
                    <a href="{link_invitacion}" class="button">
                        ✅ Aceptar Invitación
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    ⏰ Esta invitación expira en 7 días.<br>
                    Si no puedes hacer click en el botón, copia este enlace:<br>
                    <a href="{link_invitacion}">{link_invitacion}</a>
                </p>
            </div>
            
            <div class="footer">
                <p>Este email fue enviado por MiTurno</p>
                <p>Si no esperabas esta invitación, puedes ignorar este mensaje.</p>
            </div>
        </body>
        </html>
        """
        
        # MODO DESARROLLO: Solo loguear
        if not smtp_enabled:
            logger.info("📧 [MODO DESARROLLO] Email de invitación")
            logger.info(f"   Para: {email}")
            logger.info(f"   Empresa: {empresa_nombre}")
            logger.info(f"   URL: {link_invitacion}")
            print("\n" + "="*60)
            print("📧 EMAIL DE INVITACIÓN [MODO DESARROLLO]")
            print("="*60)
            print(f"Para: {email}")
            print(f"Empresa: {empresa_nombre}")
            print(f"Rol: {rol_texto}")
            print(f"URL: {link_invitacion}")
            print("="*60 + "\n")
            return True
        
        # MODO PRODUCCIÓN: Enviar via SMTP
        return EmailService._send_email_smtp(
            to_email=email,
            to_name=email.split('@')[0],
            subject=f"Invitación para unirte a {empresa_nombre} 🎉",
            html_content=html
        )
    
    @staticmethod
    def enviar_recuperacion_password(
        email: str,
        token: str,
        nombre: str
    ) -> bool:
        """
        Envía email para recuperar contraseña
        """
        link_reset = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        # Loguear siempre para debugging
        logger.info("="*60)
        logger.info("📧 Recuperación de contraseña solicitada")
        logger.info(f"   Email: {email}")
        logger.info(f"   Nombre: {nombre}")
        logger.info(f"   Token: {token[:20]}...")
        logger.info("="*60)
        
        # MODO DESARROLLO: Solo loguear
        if not smtp_enabled:
            print("\n" + "="*60)
            print("📧 EMAIL DE RECUPERACIÓN DE CONTRASEÑA [MODO DESARROLLO]")
            print("="*60)
            print(f"📬 Para: {email}")
            print(f"👤 Nombre: {nombre}")
            print(f"🔑 Token: {token}")
            print(f"🔗 URL: {link_reset}")
            print(f"⏰ Expira en: 1 hora")
            print("="*60 + "\n")
            return True
        
        # MODO PRODUCCIÓN: Enviar via SMTP
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e0e0e0;
                    border-top: none;
                }}
                .button {{
                    display: inline-block;
                    background: #4CAF50;
                    color: white !important;
                    padding: 14px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .warning-box {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔐 Recuperación de Contraseña</h1>
            </div>
            
            <div class="content">
                <p>Hola {nombre},</p>
                
                <p>Recibimos una solicitud para recuperar la contraseña de tu cuenta.</p>
                
                <p>Para crear una nueva contraseña, haz clic aquí:</p>
                
                <div style="text-align: center;">
                    <a href="{link_reset}" class="button">
                        🔓 Cambiar Contraseña
                    </a>
                </div>
                
                <div class="warning-box">
                    <p style="margin: 5px 0;"><strong>⏰ Este enlace expira en 1 hora</strong></p>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Si no puedes hacer clic, copia este enlace:<br>
                    <a href="{link_reset}">{link_reset}</a>
                </p>
                
                <p style="font-size: 14px; color: #999; margin-top: 30px;">
                    ⚠️ ¿No solicitaste esto? Ignora este email.
                </p>
            </div>
            
            <div class="footer">
                <p>MiTurno - Sistema de Gestión de Turnos</p>
            </div>
        </body>
        </html>
        """
        
        return EmailService._send_email_smtp(
            to_email=email,
            to_name=nombre,
            subject="🔐 Recuperación de Contraseña - MiTurno",
            html_content=html
        )

# Configurar Brevo si está habilitado
if settings.brevo_enabled:
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    logger.info("✅ Brevo configurado correctamente")
else:
    logger.warning("⚠️ BREVO_API_KEY no configurada - Modo desarrollo: emails se loguearán en consola")


class EmailService:
    """Servicio centralizado para envío de emails"""
    
    @staticmethod
    def _send_email_brevo(to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        """
        Envía email via Brevo API
        
        Args:
            to_email: Destinatario
            to_name: Nombre del destinatario
            subject: Asunto
            html_content: Contenido HTML
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
            
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email, "name": to_name}],
                sender={"email": "mi.turno@gmail.com", "name": "MiTurno"},
                subject=subject,
                html_content=html_content
            )
            
            api_response = api_instance.send_transac_email(send_smtp_email)
            logger.info(f"✅ Email enviado via Brevo a: {to_email} - ID: {api_response.message_id}")
            return True
            
        except ApiException as e:
            logger.error(f"❌ Error enviando email via Brevo: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado enviando email: {str(e)}")
            return False
    
    @staticmethod
    def enviar_invitacion_equipo(
        email: str,
        token: str,
        empresa_nombre: str,
        rol: str,
        invitante_nombre: str,
        mensaje_personalizado: Optional[str] = None
    ) -> bool:
        """
        Envía email de invitación a unirse al equipo de una empresa
        """
        link_invitacion = f"{settings.FRONTEND_URL}/invitacion/{token}"
        
        # Traducir rol a español
        roles_esp = {
            "EMPLEADO": "Empleado",
            "RECEPCIONISTA": "Recepcionista",
            "ADMIN_EMPRESA": "Administrador"
        }
        rol_texto = roles_esp.get(rol, rol)
        
        # HTML del email
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e0e0e0;
                    border-top: none;
                }}
                .button {{
                    display: inline-block;
                    background: #4CAF50;
                    color: white !important;
                    padding: 14px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .info-box {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 ¡Has sido invitado!</h1>
            </div>
            
            <div class="content">
                <p>Hola,</p>
                
                <p><strong>{invitante_nombre}</strong> te ha invitado a unirte al equipo de <strong>{empresa_nombre}</strong> en MiTurno.</p>
                
                <div class="info-box">
                    <p style="margin: 5px 0;"><strong>🏢 Empresa:</strong> {empresa_nombre}</p>
                    <p style="margin: 5px 0;"><strong>👤 Rol asignado:</strong> {rol_texto}</p>
                    <p style="margin: 5px 0;"><strong>✉️ Tu email:</strong> {email}</p>
                </div>
                
                {"<div style='background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;'><strong>Mensaje de " + invitante_nombre + ":</strong><br>" + mensaje_personalizado + "</div>" if mensaje_personalizado else ""}
                
                <p>Para aceptar la invitación y crear tu cuenta, haz click en el siguiente botón:</p>
                
                <div style="text-align: center;">
                    <a href="{link_invitacion}" class="button">
                        ✅ Aceptar Invitación
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    ⏰ Esta invitación expira en 7 días.<br>
                    Si no puedes hacer click en el botón, copia este enlace:<br>
                    <a href="{link_invitacion}">{link_invitacion}</a>
                </p>
            </div>
            
            <div class="footer">
                <p>Este email fue enviado por MiTurno</p>
                <p>Si no esperabas esta invitación, puedes ignorar este mensaje.</p>
            </div>
        </body>
        </html>
        """
        
        # MODO DESARROLLO: Solo loguear
        if not settings.brevo_enabled:
            logger.info("📧 [MODO DESARROLLO] Email de invitación")
            logger.info(f"   Para: {email}")
            logger.info(f"   Empresa: {empresa_nombre}")
            logger.info(f"   URL: {link_invitacion}")
            print("\n" + "="*60)
            print("📧 EMAIL DE INVITACIÓN [MODO DESARROLLO]")
            print("="*60)
            print(f"Para: {email}")
            print(f"Empresa: {empresa_nombre}")
            print(f"Rol: {rol_texto}")
            print(f"URL: {link_invitacion}")
            print("="*60 + "\n")
            return True
        
        # MODO PRODUCCIÓN: Enviar via Brevo
        return EmailService._send_email_brevo(
            to_email=email,
            to_name=email.split('@')[0],
            subject=f"Invitación para unirte a {empresa_nombre} 🎉",
            html_content=html
        )
    
    @staticmethod
    def enviar_recuperacion_password(
        email: str,
        token: str,
        nombre: str
    ) -> bool:
        """
        Envía email para recuperar contraseña
        """
        link_reset = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        # Loguear siempre para debugging
        logger.info("="*60)
        logger.info("📧 Recuperación de contraseña solicitada")
        logger.info(f"   Email: {email}")
        logger.info(f"   Nombre: {nombre}")
        logger.info(f"   Token: {token[:20]}...")
        logger.info("="*60)
        
        # MODO DESARROLLO: Solo loguear
        if not settings.brevo_enabled:
            print("\n" + "="*60)
            print("📧 EMAIL DE RECUPERACIÓN DE CONTRASEÑA [MODO DESARROLLO]")
            print("="*60)
            print(f"📬 Para: {email}")
            print(f"👤 Nombre: {nombre}")
            print(f"🔑 Token: {token}")
            print(f"🔗 URL: {link_reset}")
            print(f"⏰ Expira en: 1 hora")
            print("="*60 + "\n")
            return True
        
        # MODO PRODUCCIÓN: Enviar via Brevo
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e0e0e0;
                    border-top: none;
                }}
                .button {{
                    display: inline-block;
                    background: #4CAF50;
                    color: white !important;
                    padding: 14px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .warning-box {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔐 Recuperación de Contraseña</h1>
            </div>
            
            <div class="content">
                <p>Hola {nombre},</p>
                
                <p>Recibimos una solicitud para recuperar la contraseña de tu cuenta.</p>
                
                <p>Para crear una nueva contraseña, haz clic aquí:</p>
                
                <div style="text-align: center;">
                    <a href="{link_reset}" class="button">
                        🔓 Cambiar Contraseña
                    </a>
                </div>
                
                <div class="warning-box">
                    <p style="margin: 5px 0;"><strong>⏰ Este enlace expira en 1 hora</strong></p>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Si no puedes hacer clic, copia este enlace:<br>
                    <a href="{link_reset}">{link_reset}</a>
                </p>
                
                <p style="font-size: 14px; color: #999; margin-top: 30px;">
                    ⚠️ ¿No solicitaste esto? Ignora este email.
                </p>
            </div>
            
            <div class="footer">
                <p>MiTurno - Sistema de Gestión de Turnos</p>
            </div>
        </body>
        </html>
        """
        
        return EmailService._send_email_brevo(
            to_email=email,
            to_name=nombre,
            subject="🔐 Recuperación de Contraseña - MiTurno",
            html_content=html
        )