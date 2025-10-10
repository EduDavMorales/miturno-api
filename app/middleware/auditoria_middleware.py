from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import SessionLocal

class AuditoriaMiddleware:
    """Middleware para capturar información de request en auditoría"""
    
    @staticmethod
    def set_audit_context(request: Request, user_id: int):
        """Establecer contexto de auditoría en variables de sesión MySQL"""
        
        db: Session = SessionLocal()
        try:
            # Establecer variables de sesión para triggers
            db.execute(
                text("SET @current_user_id = :user_id"),
                {'user_id': user_id}
            )
            
            if hasattr(request, 'client') and request.client:
                db.execute(
                    text("SET @client_ip = :ip"),
                    {'ip': request.client.host}
                )
            
            db.commit()
        finally:
            db.close()