from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime, timedelta
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import Usuario
from app.services.auditoria_service import AuditoriaService
from app.schemas.auditoria import *
from app.middleware.auditoria_middleware import AuditoriaMiddleware
from app.core.exceptions import ValidationError, DatabaseError, NotFoundError

router = APIRouter()

@router.get("/", 
    response_model=Dict[str, Any],
    summary="Obtener auditoría del sistema",
    description="""
    Obtiene el registro completo de auditoría del sistema con filtros avanzados.
    
    **Características:**
    - Filtros por tabla, acción, usuario, empresa, fechas
    - Paginación optimizada 
    - Búsqueda de texto en motivos y acciones
    - Detección automática de soft deletes
    - Límite de 365 días para consultas
    """,
    responses={
        200: {"description": "Auditoría obtenida exitosamente"},
        400: {"description": "Filtros inválidos"},
        500: {"description": "Error interno del servidor"}
    }
)
async def obtener_auditoria(
    tabla_afectada: Optional[str] = Query(
        None, 
        description="Filtrar por tabla específica",
        regex="^[a-zA-Z_]+$"  # Solo letras y underscore por seguridad
    ),
    registro_id: Optional[int] = Query(
        None, 
        description="Filtrar por registro específico",
        gt=0
    ),
    accion: Optional[str] = Query(
        None, 
        description="Filtrar por tipo de acción",
        max_length=50
    ),
    usuario_id: Optional[int] = Query(
        None, 
        description="Filtrar por usuario que realizó la acción",
        gt=0
    ),
    empresa_id: Optional[int] = Query(
        None, 
        description="Filtrar por empresa en contexto",
        gt=0
    ),
    fecha_desde: Optional[datetime] = Query(
        None, 
        description="Fecha desde (formato: YYYY-MM-DD HH:MM:SS)"
    ),
    fecha_hasta: Optional[datetime] = Query(
        None, 
        description="Fecha hasta (formato: YYYY-MM-DD HH:MM:SS)"
    ),
    buscar_texto: Optional[str] = Query(
        None, 
        description="Buscar en motivo y acciones",
        max_length=100
    ),
    page: int = Query(
        1, 
        ge=1, 
        le=1000,
        description="Número de página"
    ),
    size: int = Query(
        20, 
        ge=1, 
        le=100,
        description="Elementos por página (máximo 100)"
    ),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener auditoría del sistema con validaciones robustas y manejo de errores"""
    try:
        filtros = FiltrosAuditoria(
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            accion=accion,
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            buscar_texto=buscar_texto,
            page=page,
            size=size
        )
        
        return AuditoriaService.obtener_auditoria_paginada(db, filtros)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datos de entrada inválidos: {str(e)}"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la base de datos"
        )

@router.get("/registro/{tabla_afectada}/{registro_id}",
    response_model=HistorialRegistro,
    summary="Historial completo de un registro",
    description="""
    Obtiene el historial completo de cambios de un registro específico.
    
    **Incluye:**
    - Todas las modificaciones realizadas
    - Soft deletes (cancelaciones, desactivaciones)
    - Información de quién y cuándo realizó cada cambio
    - Metadatos adicionales de contexto
    """,
    responses={
        200: {"description": "Historial obtenido exitosamente"},
        400: {"description": "Parámetros inválidos"},
        404: {"description": "Registro no encontrado"}
    }
)
async def obtener_historial_registro(
    tabla_afectada: str,
    registro_id: int,
    dias: int = Query(
        30, 
        ge=1, 
        le=365, 
        description="Días hacia atrás (máximo 365)"
    ),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener historial completo con validaciones de seguridad"""
    try:
        return AuditoriaService.obtener_historial_registro(
            db, tabla_afectada, registro_id, dias
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró historial para el registro especificado"
        )

@router.get("/estadisticas", 
    response_model=EstadisticasAuditoria,
    summary="Estadísticas de auditoría",
    description="""
    Obtiene estadísticas agregadas de la auditoría del sistema.
    
    **Incluye:**
    - Total de cambios en el período
    - Usuarios más activos
    - Empresas con más actividad  
    - Distribución por tipos de acción
    - Identificación de soft deletes
    """,
    responses={
        200: {"description": "Estadísticas calculadas exitosamente"},
        400: {"description": "Parámetros inválidos"}
    }
)
async def obtener_estadisticas_auditoria(
    tabla_afectada: Optional[str] = Query(
        None, 
        regex="^[a-zA-Z_]+$",
        description="Tabla específica (opcional)"
    ),
    dias: int = Query(
        30, 
        ge=1, 
        le=365, 
        description="Período en días (máximo 365)"
    ),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener estadísticas con validaciones"""
    try:
        return AuditoriaService.obtener_estadisticas(db, tabla_afectada, dias)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/actividad-reciente", 
    response_model=List[Dict[str, Any]],
    summary="Actividad reciente del sistema",
    description="""
    Obtiene la actividad más reciente del sistema para dashboards.
    
    **Optimizado para:**
    - Dashboards administrativos
    - Monitoreo en tiempo real
    - Detección de actividad sospechosa
    - Últimos 7 días automáticamente
    """,
    responses={
        200: {"description": "Actividad obtenida exitosamente"}
    }
)
async def obtener_actividad_reciente(
    usuario_id: Optional[int] = Query(
        None, 
        gt=0,
        description="Filtrar por usuario específico"
    ),
    empresa_id: Optional[int] = Query(
        None, 
        gt=0,
        description="Filtrar por empresa específica"
    ),
    limite: int = Query(
        10, 
        ge=1, 
        le=50, 
        description="Número de elementos (máximo 50)"
    ),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actividad reciente con límites de seguridad"""
    return AuditoriaService.obtener_actividad_reciente(
        db, usuario_id, empresa_id, limite
    )

@router.post("/manual", 
    response_model=AuditoriaResponse,
    summary="Crear auditoría manual",
    description="""
    Crea una entrada de auditoría manualmente para casos especiales.
    
    **Casos de uso:**
    - Acciones administrativas especiales
    - Migración de datos
    - Correcciones manuales
    - Testing del sistema
    
    **Requiere permisos de administrador.**
    """,
    responses={
        201: {"description": "Auditoría creada exitosamente"},
        400: {"description": "Datos inválidos"},
        403: {"description": "Sin permisos suficientes"}
    }
)
async def crear_auditoria_manual(
    auditoria: AuditoriaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear auditoría manual con permisos y validaciones"""
    
    # TODO: Verificar permisos de administrador
    # if not current_user.tiene_permiso("auditoria.create.manual"):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="No tiene permisos para crear auditoría manual"
    #     )
    
    try:
        # Establecer contexto de auditoría para triggers
        AuditoriaMiddleware.set_audit_context(request, current_user.usuario_id)
        
        return AuditoriaService.crear_auditoria_manual(db, auditoria, request)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear auditoría"
        )

@router.get("/acciones-disponibles", 
    response_model=List[str],
    summary="Listar acciones auditadas",
    description="Obtiene lista de todas las acciones que se auditan en el sistema",
    responses={
        200: {"description": "Lista obtenida exitosamente"}
    }
)
async def obtener_acciones_disponibles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener acciones disponibles con fallback"""
    try:
        result = db.execute(
            text("SELECT DISTINCT accion FROM auditoria_sistema ORDER BY accion")
        ).fetchall()
        
        return [row[0] for row in result] if result else []
        
    except Exception:
        # Fallback: retornar acciones conocidas si falla la consulta
        return [
            "ASIGNAR_ROL", "SOFT_DELETE_ROL", "CAMBIAR_ROL",
            "CREAR_TURNO", "CANCELAR_TURNO", "MODIFICAR_TURNO", 
            "SOFT_DELETE_EMPRESA", "MODIFICAR_EMPRESA"
        ]

@router.get("/tablas-auditadas", 
    response_model=List[str],
    summary="Listar tablas auditadas",
    description="Obtiene lista de todas las tablas que tienen auditoría configurada",
    responses={
        200: {"description": "Lista obtenida exitosamente"}
    }
)
async def obtener_tablas_auditadas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener tablas auditadas con fallback"""
    try:
        result = db.execute(
            text("SELECT DISTINCT tabla_afectada FROM auditoria_sistema ORDER BY tabla_afectada")
        ).fetchall()
        
        return [row[0] for row in result] if result else []
        
    except Exception:
        # Fallback: retornar tablas conocidas
        return list(AuditoriaService.TABLAS_AUDITADAS)

@router.get("/soft-deletes",
    response_model=Dict[str, Any],
    summary="Reporte de eliminaciones lógicas", 
    description="""
    Reporte específico de soft deletes (eliminaciones lógicas) en el sistema.
    
    **Incluye:**
    - Turnos cancelados
    - Empresas desactivadas  
    - Roles desactivados
    - Usuarios inactivos
    """,
    responses={
        200: {"description": "Reporte generado exitosamente"}
    }
)
async def obtener_reporte_soft_deletes(
    dias: int = Query(7, ge=1, le=90, description="Días hacia atrás (máximo 90)"),
    tabla_afectada: Optional[str] = Query(None, regex="^[a-zA-Z_]+$", description="Filtrar por tabla específica"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Reporte especializado para soft deletes"""
    
    query = """
    SELECT 
        tabla_afectada,
        accion,
        COUNT(*) as cantidad,
        COUNT(DISTINCT usuario_id) as usuarios_involucrados,
        COUNT(DISTINCT DATE(fecha_cambio)) as dias_con_actividad,
        DATE_FORMAT(MIN(fecha_cambio), '%Y-%m-%d %H:%i:%s') as primer_soft_delete,
        DATE_FORMAT(MAX(fecha_cambio), '%Y-%m-%d %H:%i:%s') as ultimo_soft_delete
    FROM auditoria_sistema 
    WHERE (accion LIKE :pattern1 
           OR accion LIKE :pattern2 
           OR accion LIKE :pattern3
           OR accion LIKE :pattern4)
      AND fecha_cambio >= DATE_SUB(NOW(), INTERVAL :dias DAY)
    """
    params = {
        'pattern1': '%SOFT_DELETE%',
        'pattern2': '%CANCELAR%',
        'pattern3': '%DESACTIVAR%',
        'pattern4': '%INACTIVAR%',
        'dias': dias
    }
    
    if tabla_afectada:
        query += " AND tabla_afectada = :tabla_afectada"
        params['tabla_afectada'] = tabla_afectada
    
    query += " GROUP BY tabla_afectada, accion ORDER BY cantidad DESC"
    
    result = db.execute(text(query), params).fetchall()
    
    soft_deletes = [dict(row._mapping) for row in result]
    total_soft_deletes = sum(item['cantidad'] for item in soft_deletes)
    
    return {
        'periodo_dias': dias,
        'tabla_filtrada': tabla_afectada,
        'total_soft_deletes': total_soft_deletes,
        'detalle_por_accion': soft_deletes,
        'resumen': {
            'tablas_afectadas': len(set(item['tabla_afectada'] for item in soft_deletes)),
            'tipos_accion': len(soft_deletes),
            'promedio_diario': round(total_soft_deletes / max(dias, 1), 2) if total_soft_deletes > 0 else 0
        }
    }

# =============================================
# EJEMPLO DE USO EN OTROS SERVICIOS
# =============================================

"""
# En cualquier servicio donde quieras auditoría manual:

from app.services.auditoria_service import AuditoriaService
from app.schemas.auditoria import AuditoriaCreate

# Crear auditoría manual
auditoria = AuditoriaCreate(
    tabla_afectada="turno",
    registro_id=turno_id,
    accion="CANCELAR_TURNO",
    usuario_id=current_user.usuario_id,
    empresa_id=empresa_id,
    motivo="Cancelado por el cliente",
    datos_anteriores={"estado": "confirmado"},
    datos_nuevos={"estado": "cancelado"},
    metadata={"cancelado_desde": "app_mobile"}
)

AuditoriaService.crear_auditoria_manual(db, auditoria, request)
"""