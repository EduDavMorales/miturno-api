# app/utils/responses.py
"""
Respuestas HTTP estandarizadas para MiTurno API
Proporciona formatos consistentes para éxito, error y paginación
"""

from typing import Any, Dict, List, Optional
from fastapi import status
from fastapi.responses import JSONResponse


# ============================================================================
# RESPUESTAS DE ÉXITO
# ============================================================================

def success_response(
    data: Any = None,
    message: str = "Operación exitosa",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    Respuesta HTTP estándar de éxito.
    
    Args:
        data: Datos a retornar (puede ser dict, list, objeto)
        message: Mensaje descriptivo
        status_code: Código HTTP (default: 200)
    
    Returns:
        JSONResponse con formato estándar
    
    Ejemplo:
        return success_response(
            data={"turno_id": 42},
            message="Turno creado exitosamente",
            status_code=201
        )
        
        # Output:
        # {
        #     "success": true,
        #     "message": "Turno creado exitosamente",
        #     "data": {"turno_id": 42}
        # }
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data
        }
    )


def created_response(data: Any, message: str = "Recurso creado exitosamente") -> JSONResponse:
    """
    Respuesta HTTP 201 Created.
    
    Ejemplo:
        return created_response(
            data=empresa_dict,
            message="Empresa registrada exitosamente"
        )
    """
    return success_response(data, message, status.HTTP_201_CREATED)


def no_content_response(message: str = "Operación exitosa") -> JSONResponse:
    """
    Respuesta HTTP 204 No Content para operaciones sin retorno.
    
    Ejemplo:
        return no_content_response("Turno eliminado")
    """
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content=None
    )


# ============================================================================
# RESPUESTAS DE ERROR
# ============================================================================

def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Respuesta HTTP estándar de error.
    
    Args:
        message: Mensaje de error principal
        status_code: Código HTTP (default: 400)
        errors: Diccionario con errores detallados (opcional)
    
    Returns:
        JSONResponse con formato estándar de error
    
    Ejemplo:
        return error_response(
            message="Datos inválidos",
            status_code=400,
            errors={"email": "Formato inválido", "telefono": "Requerido"}
        )
        
        # Output:
        # {
        #     "success": false,
        #     "message": "Datos inválidos",
        #     "errors": {
        #         "email": "Formato inválido",
        #         "telefono": "Requerido"
        #     }
        # }
    """
    content = {
        "success": False,
        "message": message
    }
    
    if errors:
        content["errors"] = errors
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def bad_request_response(message: str, errors: Optional[Dict] = None) -> JSONResponse:
    """Respuesta HTTP 400 Bad Request."""
    return error_response(message, status.HTTP_400_BAD_REQUEST, errors)


def unauthorized_response(message: str = "No autenticado") -> JSONResponse:
    """Respuesta HTTP 401 Unauthorized."""
    return error_response(message, status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message: str = "Permiso denegado") -> JSONResponse:
    """Respuesta HTTP 403 Forbidden."""
    return error_response(message, status.HTTP_403_FORBIDDEN)


def not_found_response(message: str = "Recurso no encontrado") -> JSONResponse:
    """Respuesta HTTP 404 Not Found."""
    return error_response(message, status.HTTP_404_NOT_FOUND)


def conflict_response(message: str = "Conflicto con recurso existente") -> JSONResponse:
    """Respuesta HTTP 409 Conflict."""
    return error_response(message, status.HTTP_409_CONFLICT)


def validation_error_response(errors: Dict[str, str]) -> JSONResponse:
    """
    Respuesta HTTP 422 para errores de validación de Pydantic.
    
    Ejemplo:
        return validation_error_response({
            "email": "Email ya está registrado",
            "password": "Debe tener al menos 8 caracteres"
        })
    """
    return error_response(
        message="Error de validación",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=errors
    )


def internal_error_response(
    message: str = "Error interno del servidor"
) -> JSONResponse:
    """Respuesta HTTP 500 Internal Server Error."""
    return error_response(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# RESPUESTAS PAGINADAS
# ============================================================================

def paginated_response(
    data: List[Any],
    total: int,
    skip: int = 0,
    limit: int = 10,
    message: str = "Datos obtenidos exitosamente"
) -> JSONResponse:
    """
    Respuesta HTTP con paginación.
    
    Args:
        data: Lista de elementos de la página actual
        total: Total de elementos en la base de datos
        skip: Número de elementos saltados
        limit: Límite de elementos por página
        message: Mensaje descriptivo
    
    Returns:
        JSONResponse con metadatos de paginación
    
    Ejemplo:
        return paginated_response(
            data=turnos_list,
            total=50,
            skip=0,
            limit=10,
            message="Turnos obtenidos"
        )
        
        # Output:
        # {
        #     "success": true,
        #     "message": "Turnos obtenidos",
        #     "data": [...],
        #     "pagination": {
        #         "total": 50,
        #         "count": 10,
        #         "skip": 0,
        #         "limit": 10,
        #         "has_next": true,
        #         "has_previous": false,
        #         "page": 1,
        #         "total_pages": 5
        #     }
        # }
    """
    count = len(data)
    has_next = (skip + limit) < total
    has_previous = skip > 0
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": message,
            "data": data,
            "pagination": {
                "total": total,
                "count": count,
                "skip": skip,
                "limit": limit,
                "has_next": has_next,
                "has_previous": has_previous,
                "page": page,
                "total_pages": total_pages
            }
        }
    )


# ============================================================================
# RESPUESTAS DE OPERACIONES ESPECÍFICAS
# ============================================================================

def turno_created_response(turno_data: Dict) -> JSONResponse:
    """
    Respuesta específica para creación de turno.
    
    Ejemplo:
        return turno_created_response({
            "turno_id": 42,
            "fecha": "2025-01-20",
            "hora": "10:00:00"
        })
    """
    return created_response(
        data=turno_data,
        message="Turno reservado exitosamente"
    )


def turno_cancelled_response(turno_id: int) -> JSONResponse:
    """
    Respuesta específica para cancelación de turno.
    
    Ejemplo:
        return turno_cancelled_response(turno_id=42)
    """
    return success_response(
        data={"turno_id": turno_id, "estado": "cancelado"},
        message="Turno cancelado exitosamente"
    )


def empresa_registered_response(empresa_data: Dict) -> JSONResponse:
    """
    Respuesta específica para registro de empresa.
    
    Ejemplo:
        return empresa_registered_response({
            "empresa_id": 5,
            "razon_social": "Mi Barbería"
        })
    """
    return created_response(
        data=empresa_data,
        message="Empresa registrada exitosamente"
    )


def login_success_response(token_data: Dict) -> JSONResponse:
    """
    Respuesta específica para login exitoso.
    
    Ejemplo:
        return login_success_response({
            "access_token": "eyJ...",
            "token_type": "bearer",
            "usuario": {...}
        })
    """
    return success_response(
        data=token_data,
        message="Login exitoso"
    )


def permissions_response(permissions: List[Dict]) -> JSONResponse:
    """
    Respuesta específica para listar permisos de usuario.
    
    Ejemplo:
        return permissions_response([
            {"codigo": "turno:crear:propio", "nombre": "Crear turno propio"},
            {"codigo": "turno:leer:propio", "nombre": "Ver turnos propios"}
        ])
    """
    return success_response(
        data={
            "permisos": permissions,
            "total": len(permissions)
        },
        message="Permisos obtenidos exitosamente"
    )


# ============================================================================
# RESPUESTAS CON METADATOS
# ============================================================================

def response_with_metadata(
    data: Any,
    metadata: Dict[str, Any],
    message: str = "Operación exitosa"
) -> JSONResponse:
    """
    Respuesta con datos adicionales de metadatos.
    
    Args:
        data: Datos principales
        metadata: Metadatos adicionales
        message: Mensaje descriptivo
    
    Returns:
        JSONResponse con sección de metadata
    
    Ejemplo:
        return response_with_metadata(
            data=empresas_list,
            metadata={
                "total_empresas": 150,
                "activas": 145,
                "inactivas": 5,
                "por_categoria": {"peluqueria": 50, "spa": 30}
            },
            message="Empresas obtenidas"
        )
        
        # Output:
        # {
        #     "success": true,
        #     "message": "Empresas obtenidas",
        #     "data": [...],
        #     "metadata": {
        #         "total_empresas": 150,
        #         ...
        #     }
        # }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": message,
            "data": data,
            "metadata": metadata
        }
    )