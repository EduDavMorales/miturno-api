from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from typing import List, Optional, Dict, Any
from app.models.auditoria import AuditoriaSistema
from app.schemas.auditoria import *
from app.core.exceptions import NotFoundError, ValidationError
from fastapi import Request
import json

class AuditoriaService:
    
    @staticmethod
    def crear_auditoria_manual(
        db: Session,
        auditoria: AuditoriaCreate,
        request: Optional[Request] = None
    ) -> AuditoriaResponse:
        """Crear entrada de auditoría manualmente (para casos especiales)"""
        
        # Agregar información de la request si está disponible
        if request:
            auditoria.ip_address = request.client.host if request.client else None
            auditoria.user_agent = request.headers.get("user-agent")
        
        db_auditoria = AuditoriaSistema(**auditoria.dict())
        db.add(db_auditoria)
        db.commit()
        db.refresh(db_auditoria)
        
        return AuditoriaResponse.from_orm(db_auditoria)
    
    @staticmethod
    def obtener_auditoria_paginada(
        db: Session,
        filtros: FiltrosAuditoria
    ) -> Dict[str, Any]:
        """Obtener auditoría paginada usando la vista optimizada"""
        
        # Query base usando la vista
        query = "SELECT * FROM auditoria_sistema WHERE 1=1"
        params = {}
        
        # Aplicar filtros dinámicamente
        if filtros.tabla_afectada:
            query += " AND tabla_afectada = :tabla_afectada"
            params['tabla_afectada'] = filtros.tabla_afectada
            
        if filtros.registro_id:
            query += " AND registro_id = :registro_id"
            params['registro_id'] = filtros.registro_id
            
        if filtros.accion:
            query += " AND accion = :accion"
            params['accion'] = filtros.accion
            
        if filtros.usuario_id:
            query += " AND usuario_id = :usuario_id"
            params['usuario_id'] = filtros.usuario_id
            
        if filtros.empresa_id:
            query += " AND empresa_id = :empresa_id"
            params['empresa_id'] = filtros.empresa_id
            
        if filtros.fecha_desde:
            query += " AND fecha_cambio >= :fecha_desde"
            params['fecha_desde'] = filtros.fecha_desde
            
        if filtros.fecha_hasta:
            query += " AND fecha_cambio <= :fecha_hasta"
            params['fecha_hasta'] = filtros.fecha_hasta
            
        if filtros.ip_address:
            query += " AND ip_address = :ip_address"
            params['ip_address'] = filtros.ip_address
            
        if filtros.buscar_texto:
            query += " AND (motivo LIKE :buscar_texto OR accion LIKE :buscar_texto)"
            params['buscar_texto'] = f"%{filtros.buscar_texto}%"
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        total = db.execute(text(count_query), params).scalar()
        
        # Paginación y orden
        offset = (filtros.page - 1) * filtros.size
        query += " ORDER BY fecha_cambio DESC LIMIT :limit OFFSET :offset"
        params.update({'limit': filtros.size, 'offset': offset})
        
        # Ejecutar consulta principal
        result = db.execute(text(query), params).fetchall()
        
        # Procesar resultados
        auditorias = []
        for row in result:
            audit_dict = dict(row._mapping)
            
            # Parsear campos JSON si existen
            for json_field in ['datos_anteriores', 'datos_nuevos', 'metadata']:
                if audit_dict.get(json_field):
                    try:
                        audit_dict[json_field] = json.loads(audit_dict[json_field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            auditorias.append(audit_dict)
        
        return {
            'auditorias': auditorias,
            'total': total,
            'page': filtros.page,
            'size': filtros.size,
            'total_pages': (total + filtros.size - 1) // filtros.size,
            'filtros_aplicados': filtros.dict(exclude_unset=True)
        }
    
    @staticmethod
    def obtener_historial_registro(
        db: Session,
        tabla_afectada: str,
        registro_id: int,
        dias_atras: int = 30
    ) -> HistorialRegistro:
        """Obtener historial completo de un registro específico"""
        
        # Query directo sin función SQL
        query = """
        SELECT 
            auditoria_id,
            tabla_afectada,
            registro_id,
            accion,
            usuario_id,
            empresa_id,
            datos_anteriores,
            datos_nuevos,
            campos_modificados,
            motivo,
            fecha_cambio
        FROM auditoria_sistema
        WHERE tabla_afectada = :tabla
        AND registro_id = :registro_id
        AND fecha_cambio >= DATE_SUB(NOW(), INTERVAL :dias_atras DAY)
        ORDER BY fecha_cambio DESC
        """
        
        result = db.execute(
            text(query),
            {
                'tabla': tabla_afectada,
                'registro_id': registro_id,
                'dias_atras': dias_atras
            }
        ).fetchall()
        
        historial = [dict(row._mapping) for row in result]
        
        return HistorialRegistro(
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            historial=historial,
            total_cambios=len(historial),
            periodo_dias=dias_atras
        )

    @staticmethod
    def obtener_estadisticas(
        db: Session,
        tabla_afectada: Optional[str] = None,
        dias_atras: int = 30
    ) -> EstadisticasAuditoria:
        """Obtener estadísticas de auditoría"""
        
        # Query directo sin función SQL
        base_query = """
        SELECT 
            COUNT(*) as total_cambios,
            COUNT(DISTINCT usuario_id) as usuarios_activos,
            COUNT(DISTINCT empresa_id) as empresas_afectadas
        FROM auditoria_sistema
        WHERE fecha_cambio >= DATE_SUB(NOW(), INTERVAL :dias_atras DAY)
        """
        params = {'dias_atras': dias_atras}
        
        if tabla_afectada:
            base_query += " AND tabla_afectada = :tabla"
            params['tabla'] = tabla_afectada
        
        result = db.execute(text(base_query), params).fetchone()
        
        # Query para acciones por tipo
        acciones_query = """
        SELECT 
            accion,
            COUNT(*) as cantidad
        FROM auditoria_sistema
        WHERE fecha_cambio >= DATE_SUB(NOW(), INTERVAL :dias_atras DAY)
        """
        if tabla_afectada:
            acciones_query += " AND tabla_afectada = :tabla"
        acciones_query += " GROUP BY accion ORDER BY cantidad DESC"
        
        acciones_result = db.execute(text(acciones_query), params).fetchall()
        acciones_por_tipo = [dict(row._mapping) for row in acciones_result]
        
        return EstadisticasAuditoria(
            total_cambios=result.total_cambios if result else 0,
            usuarios_activos=result.usuarios_activos if result else 0,
            empresas_afectadas=result.empresas_afectadas if result else 0,
            acciones_por_tipo=acciones_por_tipo,
            periodo_dias=dias_atras,
            tabla_consultada=tabla_afectada
        )
    
    @staticmethod
    def obtener_actividad_reciente(
        db: Session,
        usuario_id: Optional[int] = None,
        empresa_id: Optional[int] = None,
        limite: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtener actividad más reciente para dashboards"""
    
        query = """
        SELECT 
            a.auditoria_id,
            a.tabla_afectada,
            a.registro_id,
            a.accion,
            a.usuario_id,
            u.nombre as usuario_nombre,
            u.email as usuario_email,
            a.empresa_id,
            e.razon_social as empresa_nombre,
            a.motivo,
            a.fecha_cambio,
            CASE 
                WHEN a.accion LIKE '%SOFT_DELETE%' THEN 'eliminacion'
                WHEN a.accion LIKE '%INSERT%' OR a.accion LIKE '%CREAR%' THEN 'creacion'
                WHEN a.accion LIKE '%UPDATE%' OR a.accion LIKE '%MODIFICAR%' THEN 'modificacion'
                WHEN a.accion LIKE '%LOGIN%' THEN 'acceso'
                ELSE 'otro'
            END as tipo_cambio
        FROM auditoria_sistema a
        LEFT JOIN usuario u ON a.usuario_id = u.usuario_id
        LEFT JOIN empresa e ON a.empresa_id = e.empresa_id
        WHERE 1=1
        """
        params = {}
    
        if usuario_id:
            query += " AND a.usuario_id = :usuario_id"
            params['usuario_id'] = usuario_id
        
        if empresa_id:
            query += " AND a.empresa_id = :empresa_id"
            params['empresa_id'] = empresa_id
    
        query += " ORDER BY a.fecha_cambio DESC LIMIT :limite"
        params['limite'] = limite
    
        result = db.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in result]
