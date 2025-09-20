from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class TablasAuditadas(str, Enum):
    USUARIO_ROL = "usuario_rol"
    TURNO = "turno"
    EMPRESA = "empresa"
    SERVICIO = "servicio"
    USUARIO = "usuario"

class AccionesComunes(str, Enum):
    # Roles
    ASIGNAR_ROL = "ASIGNAR_ROL"
    DESACTIVAR_ROL = "DESACTIVAR_ROL"
    CAMBIAR_ROL = "CAMBIAR_ROL"
    
    # Turnos
    CREAR_TURNO = "CREAR_TURNO"
    CANCELAR_TURNO = "CANCELAR_TURNO"
    MODIFICAR_TURNO = "MODIFICAR_TURNO"
    ESTADO_CONFIRMADO = "ESTADO_CONFIRMADO"
    ESTADO_COMPLETADO = "ESTADO_COMPLETADO"
    
    # Empresas
    MODIFICAR_EMPRESA = "MODIFICAR_EMPRESA"
    
    # Genéricas
    CREAR = "CREAR"
    ACTUALIZAR = "ACTUALIZAR"
    ELIMINAR = "ELIMINAR"

class AuditoriaBase(BaseModel):
    tabla_afectada: str
    registro_id: int
    accion: str
    usuario_id: int
    empresa_id: Optional[int] = None
    motivo: Optional[str] = None

class AuditoriaCreate(AuditoriaBase):
    datos_anteriores: Optional[Dict[str, Any]] = None
    datos_nuevos: Optional[Dict[str, Any]] = None
    campos_modificados: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditoriaResponse(AuditoriaBase):
    auditoria_id: int
    datos_anteriores: Optional[Dict[str, Any]] = None
    datos_nuevos: Optional[Dict[str, Any]] = None
    campos_modificados: Optional[str] = None
    fecha_cambio: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Campos enriquecidos (de la vista)
    usuario_nombre: Optional[str] = None
    usuario_email: Optional[str] = None
    empresa_nombre: Optional[str] = None
    tipo_cambio: Optional[str] = None
    
    class Config:
        from_attributes = True

class FiltrosAuditoria(BaseModel):
    tabla_afectada: Optional[str] = Field(None, description="Tabla específica a filtrar")
    registro_id: Optional[int] = Field(None, description="ID específico del registro")
    accion: Optional[str] = Field(None, description="Tipo de acción")
    usuario_id: Optional[int] = Field(None, description="Usuario que realizó la acción")
    empresa_id: Optional[int] = Field(None, description="Empresa en contexto")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha hasta")
    ip_address: Optional[str] = Field(None, description="IP address")
    buscar_texto: Optional[str] = Field(None, description="Búsqueda en motivo")
    page: int = Field(default=1, ge=1, description="Página")
    size: int = Field(default=20, ge=1, le=100, description="Elementos por página")

class EstadisticasAuditoria(BaseModel):
    total_cambios: int
    usuarios_activos: int
    empresas_afectadas: int
    acciones_por_tipo: List[Dict[str, Union[str, int]]]
    periodo_dias: int
    tabla_consultada: Optional[str] = None

class HistorialRegistro(BaseModel):
    tabla_afectada: str
    registro_id: int
    historial: List[Dict[str, Any]]
    total_cambios: int
    periodo_dias: int
