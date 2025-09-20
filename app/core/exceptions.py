"""
Excepciones personalizadas para MiTurno API
Mantienen compatibilidad con FastAPI HTTPException
"""

from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Clase base para excepciones de la API"""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class ValidationError(BaseAPIException):
    """Error de validación de datos"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class NotFoundError(BaseAPIException):
    """Recurso no encontrado"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class DatabaseError(BaseAPIException):
    """Error de base de datos"""
    def __init__(self, detail: str = "Error interno de base de datos"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuthenticationError(BaseAPIException):
    """Error de autenticación"""
    def __init__(self, detail: str = "Credenciales inválidas"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BaseAPIException):
    """Error de autorización"""
    def __init__(self, detail: str = "Sin permisos suficientes"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)