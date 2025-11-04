# app/services/horario_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from typing import List, Optional, Tuple
from datetime import date, time, datetime, timedelta
import logging

from app.models.horario_empresa import HorarioEmpresa
from app.models.bloqueo_horario import BloqueoHorario
from app.models.empresa import Empresa
from app.schemas.horario import (
    HorarioCreate, HorarioUpdate, HorarioResponse,
    BloqueoCreate, BloqueoUpdate, BloqueoResponse
)

logger = logging.getLogger(__name__)

class HorarioService:
    """Servicio para gestión de horarios y bloqueos de empresas"""
    
    # ============================================
    # CRUD DE HORARIOS
    # ============================================
    
    @staticmethod
    def crear_horario(db: Session, horario_data: HorarioCreate) -> HorarioEmpresa:
        """
        Crea un nuevo horario para una empresa
        
        Validaciones:
        - La empresa debe existir
        - No debe existir otro horario para el mismo día
        - Hora apertura < hora cierre
        """
        # Validar que la empresa existe
        empresa = db.query(Empresa).filter(Empresa.empresa_id == horario_data.empresa_id).first()
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {horario_data.empresa_id} no encontrada"
            )
        
        # Validar que no existe horario para ese día
        horario_existente = db.query(HorarioEmpresa).filter(
            HorarioEmpresa.empresa_id == horario_data.empresa_id,
            HorarioEmpresa.dia_semana == horario_data.dia_semana.value
        ).first()
        
        if horario_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un horario para {horario_data.dia_semana.value}"
            )
        
        # Crear horario
        nuevo_horario = HorarioEmpresa(
            empresa_id=horario_data.empresa_id,
            dia_semana=horario_data.dia_semana.value,
            hora_apertura=horario_data.hora_apertura,
            hora_cierre=horario_data.hora_cierre,
            activo=horario_data.activo
        )
        
        db.add(nuevo_horario)
        db.commit()
        db.refresh(nuevo_horario)
        
        logger.info(f"Horario creado: {horario_data.dia_semana.value} para empresa {horario_data.empresa_id}")
        return nuevo_horario
    
    @staticmethod
    def crear_horarios_bulk(db: Session, empresa_id: int, horarios: List[dict]) -> List[HorarioEmpresa]:
        """
        Crea múltiples horarios para una empresa de una vez
        Útil para configuración inicial
        """
        empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        horarios_creados = []
        
        for horario_data in horarios:
            # Verificar que no exista
            existe = db.query(HorarioEmpresa).filter(
                HorarioEmpresa.empresa_id == empresa_id,
                HorarioEmpresa.dia_semana == horario_data['dia_semana']
            ).first()
            
            if not existe:
                nuevo_horario = HorarioEmpresa(
                    empresa_id=empresa_id,
                    dia_semana=horario_data['dia_semana'],
                    hora_apertura=horario_data['hora_apertura'],
                    hora_cierre=horario_data['hora_cierre'],
                    activo=horario_data.get('activo', True)
                )
                db.add(nuevo_horario)
                horarios_creados.append(nuevo_horario)
        
        db.commit()
        logger.info(f"{len(horarios_creados)} horarios creados para empresa {empresa_id}")
        return horarios_creados
    
    @staticmethod
    def obtener_horarios(db: Session, empresa_id: int, solo_activos: bool = True) -> List[HorarioEmpresa]:
        """Obtiene todos los horarios de una empresa"""
        query = db.query(HorarioEmpresa).filter(HorarioEmpresa.empresa_id == empresa_id)
        
        if solo_activos:
            query = query.filter(HorarioEmpresa.activo == True)
        
        horarios = query.all()
        return horarios
    
    @staticmethod
    def obtener_horario_por_dia(db: Session, empresa_id: int, dia_semana: str) -> Optional[HorarioEmpresa]:
        """Obtiene el horario de un día específico"""
        horario = db.query(HorarioEmpresa).filter(
            HorarioEmpresa.empresa_id == empresa_id,
            HorarioEmpresa.dia_semana == dia_semana
        ).first()
        
        return horario
    
    @staticmethod
    def actualizar_horario(
        db: Session, 
        empresa_id: int, 
        dia_semana: str, 
        horario_data: HorarioUpdate
    ) -> HorarioEmpresa:
        """
        Actualiza un horario existente
        Solo actualiza los campos que se envían (actualización parcial)
        """
        horario = HorarioService.obtener_horario_por_dia(db, empresa_id, dia_semana)
        
        if not horario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe horario para {dia_semana} en esta empresa"
            )
        
        # Actualizar solo los campos enviados
        if horario_data.hora_apertura is not None:
            horario.hora_apertura = horario_data.hora_apertura
        
        if horario_data.hora_cierre is not None:
            horario.hora_cierre = horario_data.hora_cierre
        
        if horario_data.activo is not None:
            horario.activo = horario_data.activo
        
        # Validar que hora_cierre > hora_apertura después de actualizar
        if horario.hora_cierre <= horario.hora_apertura:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La hora de cierre debe ser posterior a la hora de apertura"
            )
        
        db.commit()
        db.refresh(horario)
        
        logger.info(f"Horario actualizado: {dia_semana} para empresa {empresa_id}")
        return horario
    
    @staticmethod
    @staticmethod
    def desactivar_horario(db: Session, empresa_id: int, dia_semana: str) -> HorarioEmpresa:
        """Soft delete: desactiva un horario sin eliminarlo"""
        horario = HorarioService.obtener_horario_por_dia(db, empresa_id, dia_semana)
        
        if not horario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe horario para {dia_semana} en esta empresa"
            )
        
        horario.activo = False
        db.commit()
        db.refresh(horario)
        
        logger.info(f"Horario desactivado: {dia_semana} para empresa {empresa_id}")
        return horario
    
    # ============================================
    # CRUD DE BLOQUEOS
    # ============================================
    
    @staticmethod
    def crear_bloqueo(db: Session, bloqueo_data: BloqueoCreate) -> BloqueoHorario:
        """
        Crea un nuevo bloqueo de horario
        
        Validaciones:
        - La empresa debe existir
        - Fecha fin >= fecha inicio
        - Si hay horas, hora_fin > hora_inicio
        """
        empresa = db.query(Empresa).filter(Empresa.empresa_id == bloqueo_data.empresa_id).first()
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {bloqueo_data.empresa_id} no encontrada"
            )
        
        nuevo_bloqueo = BloqueoHorario(
            empresa_id=bloqueo_data.empresa_id,
            fecha_inicio=bloqueo_data.fecha_inicio,
            fecha_fin=bloqueo_data.fecha_fin,
            hora_inicio=bloqueo_data.hora_inicio,
            hora_fin=bloqueo_data.hora_fin,
            motivo=bloqueo_data.motivo,
            tipo=bloqueo_data.tipo.value
        )
        
        db.add(nuevo_bloqueo)
        db.commit()
        db.refresh(nuevo_bloqueo)
        
        logger.info(f"Bloqueo creado para empresa {bloqueo_data.empresa_id}: {bloqueo_data.fecha_inicio} - {bloqueo_data.fecha_fin}")
        return nuevo_bloqueo
    
    @staticmethod
    def obtener_bloqueos(
        db: Session, 
        empresa_id: int,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[BloqueoHorario]:
        """
        Obtiene bloqueos de una empresa
        Opcionalmente filtra por rango de fechas
        """
        query = db.query(BloqueoHorario).filter(BloqueoHorario.empresa_id == empresa_id)
        
        if fecha_desde:
            query = query.filter(BloqueoHorario.fecha_fin >= fecha_desde)
        
        if fecha_hasta:
            query = query.filter(BloqueoHorario.fecha_inicio <= fecha_hasta)
        
        bloqueos = query.order_by(BloqueoHorario.fecha_inicio).all()
        return bloqueos
    
    @staticmethod
    def obtener_bloqueo_por_id(db: Session, bloqueo_id: int) -> Optional[BloqueoHorario]:
        """Obtiene un bloqueo específico por ID"""
        bloqueo = db.query(BloqueoHorario).filter(BloqueoHorario.bloqueo_id == bloqueo_id).first()
        return bloqueo
    
    @staticmethod
    def actualizar_bloqueo(
        db: Session,
        bloqueo_id: int,
        bloqueo_data: BloqueoUpdate
    ) -> BloqueoHorario:
        """Actualiza un bloqueo existente"""
        bloqueo = HorarioService.obtener_bloqueo_por_id(db, bloqueo_id)
        
        if not bloqueo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bloqueo con ID {bloqueo_id} no encontrado"
            )
        
        # Actualizar campos enviados
        if bloqueo_data.fecha_inicio is not None:
            bloqueo.fecha_inicio = bloqueo_data.fecha_inicio
        
        if bloqueo_data.fecha_fin is not None:
            bloqueo.fecha_fin = bloqueo_data.fecha_fin
        
        if bloqueo_data.hora_inicio is not None:
            bloqueo.hora_inicio = bloqueo_data.hora_inicio
        
        if bloqueo_data.hora_fin is not None:
            bloqueo.hora_fin = bloqueo_data.hora_fin
        
        if bloqueo_data.motivo is not None:
            bloqueo.motivo = bloqueo_data.motivo
        
        if bloqueo_data.tipo is not None:
            bloqueo.tipo = bloqueo_data.tipo.value
        
        # Validar fechas
        if bloqueo.fecha_fin < bloqueo.fecha_inicio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de fin debe ser posterior o igual a la fecha de inicio"
            )
        
        db.commit()
        db.refresh(bloqueo)
        
        logger.info(f"Bloqueo actualizado: {bloqueo_id}")
        return bloqueo
    
    @staticmethod
    def desactivar_bloqueo(db: Session, bloqueo_id: int) -> BloqueoHorario:
        """Desactiva un bloqueo (soft delete)"""
        bloqueo = HorarioService.obtener_bloqueo_por_id(db, bloqueo_id)
        
        if not bloqueo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bloqueo con ID {bloqueo_id} no encontrado"
            )
        
        bloqueo.activo = False
        db.commit()
        db.refresh(bloqueo)
        
        logger.info(f"Bloqueo desactivado: {bloqueo_id}")
        return bloqueo
    
    # ============================================
    # HELPERS Y VALIDACIONES
    # ============================================
    
    @staticmethod
    def verificar_disponibilidad(
        db: Session,
        empresa_id: int,
        fecha: date
    ) -> Tuple[bool, Optional[HorarioEmpresa], List[BloqueoHorario]]:
        """
        Verifica si una empresa está disponible en una fecha específica
        
        Returns:
            (disponible, horario, bloqueos_activos)
        """
        # Obtener día de la semana
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        dia_semana = dias_semana[fecha.weekday()]
        
        # Obtener horario del día
        horario = HorarioService.obtener_horario_por_dia(db, empresa_id, dia_semana)
        
        if not horario or not horario.activo:
            return (False, None, [])
        
        # Obtener bloqueos activos para esa fecha
        bloqueos = db.query(BloqueoHorario).filter(
            BloqueoHorario.empresa_id == empresa_id,
            BloqueoHorario.fecha_inicio <= fecha,
            BloqueoHorario.fecha_fin >= fecha
        ).all()
        
        # Si hay bloqueos de día completo (sin horas), no está disponible
        bloqueos_dia_completo = [b for b in bloqueos if b.hora_inicio is None and b.hora_fin is None]
        if bloqueos_dia_completo:
            return (False, horario, bloqueos)
        
        # Si solo hay bloqueos parciales, está disponible (pero con restricciones)
        disponible = True
        
        return (disponible, horario, bloqueos)
    
    @staticmethod
    def obtener_dias_disponibles(
        db: Session,
        empresa_id: int,
        fecha_desde: date,
        fecha_hasta: date
    ) -> List[dict]:
        """
        Obtiene lista de días disponibles en un rango de fechas
        Útil para mostrar calendario
        """
        dias_disponibles = []
        fecha_actual = fecha_desde
        
        while fecha_actual <= fecha_hasta:
            disponible, horario, bloqueos = HorarioService.verificar_disponibilidad(
                db, empresa_id, fecha_actual
            )
            
            dias_disponibles.append({
                'fecha': fecha_actual,
                'disponible': disponible,
                'horario': horario,
                'bloqueos': bloqueos
            })
            
            fecha_actual += timedelta(days=1)
        
        return dias_disponibles
    
    @staticmethod
    def validar_permisos_empresa(db: Session, usuario_id: int, empresa_id: int) -> bool:
        """
        Valida que el usuario tenga permisos para modificar horarios de la empresa
        """
        from app.models.empresa import Empresa
        
        empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
        if not empresa:
            return False
        
        # Verificar que el usuario es dueño de la empresa
        if empresa.usuario_id == usuario_id:
            return True
        
        # TODO: Verificar roles adicionales (ADMIN_EMPRESA, etc)
        
        return False