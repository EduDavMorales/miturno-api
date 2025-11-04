# app/utils/validators.py
"""
Validadores genéricos para el sistema MiTurno
Incluye validaciones de datos, propiedad de recursos y reglas de negocio
"""

from typing import Optional
from datetime import datetime, date, time
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status


# ============================================================================
# VALIDADORES DE PROPIEDAD
# ============================================================================

def verify_empresa_ownership(usuario_id: int, empresa_id: int, db: Session) -> bool:
    """
    Verifica si un usuario es dueño o tiene rol administrativo en una empresa.
    
    Args:
        usuario_id: ID del usuario
        empresa_id: ID de la empresa
        db: Sesión de BD
    
    Returns:
        True si el usuario tiene control sobre la empresa
    
    Raises:
        HTTPException 403: Usuario no tiene acceso a la empresa
        HTTPException 404: Empresa no encontrada
    
    Ejemplo:
        verify_empresa_ownership(current_user.usuario_id, empresa_id, db)
        # Lanza excepción si no tiene acceso
    """
    try:
        # Verificar que la empresa existe
        query_empresa = text("""
            SELECT empresa_id FROM empresa 
            WHERE empresa_id = :empresa_id AND activo = 1
        """)
        empresa = db.execute(query_empresa, {"empresa_id": empresa_id}).fetchone()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa {empresa_id} no encontrada"
            )
        
        # Verificar roles del usuario en la empresa
        query_roles = text("""
            SELECT r.nombre
            FROM usuario_rol ur
            JOIN rol r ON ur.rol_id = r.rol_id
            WHERE ur.usuario_id = :usuario_id
            AND ur.empresa_id = :empresa_id
            AND ur.activo = 1
            AND r.nombre IN ('DUEÑO_EMPRESA', 'ADMIN_EMPRESA', 'SUPER_ADMIN')
        """)
        
        result = db.execute(query_roles, {
            "usuario_id": usuario_id,
            "empresa_id": empresa_id
        }).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso administrativo a esta empresa"
            )
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verificando propiedad de empresa: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verificando acceso a empresa"
        )


def verify_turno_ownership(usuario_id: int, turno_id: int, db: Session) -> bool:
    """
    Verifica si un usuario es dueño de un turno.
    
    Args:
        usuario_id: ID del usuario
        turno_id: ID del turno
        db: Sesión de BD
    
    Returns:
        True si el usuario es dueño del turno
    
    Raises:
        HTTPException 403: Usuario no es dueño del turno
        HTTPException 404: Turno no encontrado
    """
    try:
        query = text("""
            SELECT cliente_id 
            FROM turno 
            WHERE turno_id = :turno_id AND deleted_at IS NULL
        """)
        
        result = db.execute(query, {"turno_id": turno_id}).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Turno {turno_id} no encontrado"
            )
        
        if result.cliente_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar este turno"
            )
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verificando propiedad de turno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verificando acceso a turno"
        )


# ============================================================================
# VALIDADORES DE DATOS
# ============================================================================

def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
    
    Returns:
        True si es válido
    
    Raises:
        HTTPException 400: Email inválido
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de email inválido"
        )
    
    return True


def validate_phone(phone: Optional[str]) -> bool:
    """
    Valida formato de teléfono argentino.
    
    Args:
        phone: Teléfono a validar (puede ser None)
    
    Returns:
        True si es válido o None
    
    Raises:
        HTTPException 400: Teléfono inválido
    """
    if phone is None:
        return True
    
    import re
    # Formato argentino: +54 9 11 1234-5678 o variaciones
    pattern = r'^(\+54)?[\s-]?(9)?[\s-]?(\d{2,4})[\s-]?(\d{6,8})$'
    
    if not re.match(pattern, phone.replace(" ", "").replace("-", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de teléfono inválido. Use formato argentino: +54 9 11 1234-5678"
        )
    
    return True


def validate_date_not_past(fecha: date) -> bool:
    """
    Valida que una fecha no esté en el pasado.
    
    Args:
        fecha: Fecha a validar
    
    Returns:
        True si es válida
    
    Raises:
        HTTPException 400: Fecha en el pasado
    """
    if fecha < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha no puede ser en el pasado"
        )
    
    return True


def validate_time_range(hora_inicio: time, hora_fin: time) -> bool:
    """
    Valida que hora_fin sea posterior a hora_inicio.
    
    Args:
        hora_inicio: Hora de inicio
        hora_fin: Hora de fin
    
    Returns:
        True si es válido
    
    Raises:
        HTTPException 400: Rango inválido
    """
    if hora_fin <= hora_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La hora de fin debe ser posterior a la hora de inicio"
        )
    
    return True


def validate_precio(precio: float) -> bool:
    """
    Valida que un precio sea positivo.
    
    Args:
        precio: Precio a validar
    
    Returns:
        True si es válido
    
    Raises:
        HTTPException 400: Precio inválido
    """
    if precio <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El precio debe ser mayor a 0"
        )
    
    return True


def validate_duracion_minutos(duracion: int) -> bool:
    """
    Valida que una duración sea razonable (5-480 minutos).
    
    Args:
        duracion: Duración en minutos
    
    Returns:
        True si es válida
    
    Raises:
        HTTPException 400: Duración inválida
    """
    if duracion < 5 or duracion > 480:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La duración debe estar entre 5 y 480 minutos"
        )
    
    return True


# ============================================================================
# VALIDADORES DE EXISTENCIA
# ============================================================================

def validate_empresa_exists(empresa_id: int, db: Session) -> bool:
    """
    Valida que una empresa exista y esté activa.
    
    Args:
        empresa_id: ID de la empresa
        db: Sesión de BD
    
    Returns:
        True si existe y está activa
    
    Raises:
        HTTPException 404: Empresa no encontrada
    """
    query = text("""
        SELECT empresa_id FROM empresa 
        WHERE empresa_id = :empresa_id AND activo = 1
    """)
    
    result = db.execute(query, {"empresa_id": empresa_id}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa {empresa_id} no encontrada o inactiva"
        )
    
    return True


def validate_servicio_exists(servicio_id: int, db: Session) -> bool:
    """
    Valida que un servicio exista y esté activo.
    
    Args:
        servicio_id: ID del servicio
        db: Sesión de BD
    
    Returns:
        True si existe y está activo
    
    Raises:
        HTTPException 404: Servicio no encontrado
    """
    query = text("""
        SELECT servicio_id FROM servicio 
        WHERE servicio_id = :servicio_id AND activo = 1
    """)
    
    result = db.execute(query, {"servicio_id": servicio_id}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servicio {servicio_id} no encontrado o inactivo"
        )
    
    return True


def validate_usuario_exists(usuario_id: int, db: Session) -> bool:
    """
    Valida que un usuario exista y esté activo.
    
    Args:
        usuario_id: ID del usuario
        db: Sesión de BD
    
    Returns:
        True si existe y está activo
    
    Raises:
        HTTPException 404: Usuario no encontrado
    """
    query = text("""
        SELECT usuario_id FROM usuario 
        WHERE usuario_id = :usuario_id AND activo = 1
    """)
    
    result = db.execute(query, {"usuario_id": usuario_id}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {usuario_id} no encontrado o inactivo"
        )
    
    return True


# ============================================================================
# VALIDADORES DE REGLAS DE NEGOCIO
# ============================================================================

def validate_servicio_belongs_to_empresa(
    servicio_id: int, 
    empresa_id: int, 
    db: Session
) -> bool:
    """
    Valida que un servicio pertenezca a una empresa.
    
    Args:
        servicio_id: ID del servicio
        empresa_id: ID de la empresa
        db: Sesión de BD
    
    Returns:
        True si pertenece
    
    Raises:
        HTTPException 400: Servicio no pertenece a la empresa
    """
    query = text("""
        SELECT empresa_id 
        FROM servicio 
        WHERE servicio_id = :servicio_id AND activo = 1
    """)
    
    result = db.execute(query, {"servicio_id": servicio_id}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servicio {servicio_id} no encontrado"
        )
    
    if result.empresa_id != empresa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El servicio {servicio_id} no pertenece a la empresa {empresa_id}"
        )
    
    return True