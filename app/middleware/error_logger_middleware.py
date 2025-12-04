# app/middleware/error_logger_middleware.py
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("miturno")


class ErrorLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware que captura y loguea automáticamente todos los errores.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            
            # Loguear errores HTTP (4xx y 5xx)
            if response.status_code >= 400:
                logger.warning(
                    f"HTTP {response.status_code} | "
                    f"{request.method} {request.url.path} | "
                    f"Client: {request.client.host}"
                )
            
            return response
            
        except Exception as exc:
            # Capturar cualquier excepción no manejada
            error_trace = traceback.format_exc()
            
            logger.error(
                f"EXCEPCIÓN NO MANEJADA | "
                f"{request.method} {request.url.path} | "
                f"Error: {str(exc)}\n"
                f"Traceback:\n{error_trace}"
            )
            
            # Retornar respuesta de error genérica
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Error interno del servidor",
                    "error_id": f"{request.method}_{request.url.path}"
                }
            )