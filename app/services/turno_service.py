# app/services/turno_service.py
from datetime import date, time, datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.turno import Turno
from app.models.empresa import Empresa
from app.models.servicio import Servicio
from app.models.horario_empresa import HorarioEmpresa
from app.models.user import Usuario
from app.schemas.turno import (
    DisponibilidadRequest,
    DisponibilidadResponse,
    SlotDisponible,
    ReservaTurnoRequest,
    TurnoResponse,
    ModificarTurnoRequest,
    FiltrosTurnos,
    TurnosList
)
from app.enums import EstadoTurno, DiaSemana


class TurnoService:
    """Service para manejo de turnos - lógica de negocio"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_disponibilidad(
        self, 
        empresa_id: int, 
        request: DisponibilidadRequest
    ) -> DisponibilidadResponse:
        """
        Calcula la disponibilidad de turnos para una empresa en una fecha específica
        """
        # Verificar que la empresa existe y está activa
        empresa = self.db.query(Empresa).filter(
            Empresa.empresa_id == empresa_id,
            Empresa.activa == True
        ).first()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada o inactiva"
            )
        
        # Obtener día de la semana (lunes=0, domingo=6)
        dia_semana = self._obtener_dia_semana(request.fecha)
        
        # Obtener horarios de trabajo para ese día
        horarios_trabajo = self.db.query(HorarioEmpresa).filter(
            HorarioEmpresa.empresa_id == empresa_id,
            HorarioEmpresa.dia_semana == dia_semana,
            HorarioEmpresa.activo == True
        ).all()
        
        if not horarios_trabajo:
            return DisponibilidadResponse(
                fecha=request.fecha,
                empresa_id=empresa_id,
                empresa_nombre=empresa.razon_social,
                slots_disponibles=[],
                total_slots=0
            )
        
        # Obtener servicios disponibles
        servicios_query = self.db.query(Servicio).filter(
            Servicio.empresa_id == empresa_id,
            Servicio.activo == True
        )
        
        if request.servicio_id:
            servicios_query = servicios_query.filter(
                Servicio.servicio_id == request.servicio_id
            )
        
        servicios = servicios_query.all()
        
        if not servicios:
            return DisponibilidadResponse(
                fecha=request.fecha,
                empresa_id=empresa_id,
                empresa_nombre=empresa.nombre,
                slots_disponibles=[],
                total_slots=0
            )
        
        # Obtener turnos ya reservados para esa fecha
        turnos_ocupados = self.db.query(Turno).filter(
            Turno.empresa_id == empresa_id,
            Turno.fecha == request.fecha,
            Turno.estado.in_([EstadoTurno.PENDIENTE, EstadoTurno.CONFIRMADO])
        ).all()
        
        # Generar slots disponibles
        slots_disponibles = []
        
        for horario in horarios_trabajo:
            for servicio in servicios:
                slots_servicio = self._generar_slots_para_servicio(
                    horario.hora_apertura,
                    horario.hora_cierre,
                    servicio,
                    turnos_ocupados,
                    request.fecha
                )
                slots_disponibles.extend(slots_servicio)
        
        # Ordenar por hora de inicio
        slots_disponibles.sort(key=lambda slot: slot.hora_inicio)
        
        return DisponibilidadResponse(
            fecha=request.fecha,
            empresa_id=empresa_id,
            empresa_nombre=empresa.razon_social,
            slots_disponibles=slots_disponibles,
            total_slots=len(slots_disponibles)
        )
    
    def reservar_turno(
        self, 
        usuario_id: int, 
        request: ReservaTurnoRequest
    ) -> TurnoResponse:
        """
        Reserva un turno para un usuario
        """
        # Validar que la empresa existe
        empresa = self.db.query(Empresa).filter(
            Empresa.empresa_id == request.empresa_id,
            Empresa.activa == True
        ).first()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        # Validar que el servicio existe
        servicio = self.db.query(Servicio).filter(
            Servicio.servicio_id == request.servicio_id,
            Servicio.empresa_id == request.empresa_id,
            Servicio.activo == True
        ).first()
        
        if not servicio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servicio no encontrado"
            )
        
        # Validar disponibilidad del horario
        if not self._validar_horario_disponible(
            request.empresa_id,
            request.fecha,
            request.hora,
            servicio.duracion_minutos
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El horario no está disponible"
            )
        
        # Calcular hora de fin basada en duración del servicio
        hora_fin_calculada = self._calcular_hora_fin(request.hora, servicio.duracion_minutos)
        
        # Crear el turno
        nuevo_turno = Turno(
            empresa_id=request.empresa_id,
            cliente_id=usuario_id,
            servicio_id=request.servicio_id,
            fecha=request.fecha,
            hora=request.hora,
            estado=EstadoTurno.PENDIENTE,
            notas_cliente=request.notas_cliente,
            fecha_creacion=datetime.utcnow()
        )
        
        self.db.add(nuevo_turno)
        self.db.commit()
        self.db.refresh(nuevo_turno)
        
        return self._convertir_a_turno_response(nuevo_turno)
    
    def obtener_turnos_usuario(
        self, 
        usuario_id: int, 
        filtros: Optional[FiltrosTurnos] = None,
        pagina: int = 1,
        por_pagina: int = 10
    ) -> TurnosList:
        """
        Obtiene los turnos de un usuario con filtros y paginación
        """
        query = self.db.query(Turno).filter(Turno.cliente_id == usuario_id)
        
        # Aplicar filtros
        if filtros:
            if filtros.fecha_desde:
                query = query.filter(Turno.fecha >= filtros.fecha_desde)
            if filtros.fecha_hasta:
                query = query.filter(Turno.fecha <= filtros.fecha_hasta)
            if filtros.estado:
                query = query.filter(Turno.estado == filtros.estado)
            if filtros.empresa_id:
                query = query.filter(Turno.empresa_id == filtros.empresa_id)
            if filtros.servicio_id:
                query = query.filter(Turno.servicio_id == filtros.servicio_id)
        
        # Contar total
        total = query.count()
        
        # Aplicar paginación
        offset = (pagina - 1) * por_pagina
        turnos = query.order_by(
            Turno.fecha.desc(),
            Turno.hora.desc()
        ).offset(offset).limit(por_pagina).all()
        
        # Convertir a response
        turnos_response = [
            self._convertir_a_turno_response(turno) for turno in turnos
        ]
        
        # Calcular metadatos de paginación
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return TurnosList(
            turnos=turnos_response,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas,
            tiene_siguiente=pagina < total_paginas,
            tiene_anterior=pagina > 1
        )
    
    def modificar_turno(
        self, 
        turno_id: int, 
        usuario_id: int, 
        request: ModificarTurnoRequest
    ) -> TurnoResponse:
        """
        Modifica un turno existente
        """
        turno = self.db.query(Turno).filter(
            Turno.turno_id == turno_id,
            Turno.cliente_id == usuario_id
        ).first()
        
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turno no encontrado"
            )
        
        # Verificar que el turno se puede modificar
        if turno.estado not in [EstadoTurno.PENDIENTE, EstadoTurno.CONFIRMADO]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El turno no se puede modificar en su estado actual"
            )
        
        # Actualizar campos
        if request.fecha is not None:
            turno.fecha = request.fecha
        if request.hora is not None:
            turno.hora = request.hora
        if request.servicio_id is not None:
            turno.servicio_id = request.servicio_id
        if request.notas_cliente is not None:
            turno.notas_cliente = request.notas_cliente
        
        turno.fecha_actualizacion = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(turno)
        
        return self._convertir_a_turno_response(turno)
    
    def cancelar_turno(
        self, 
        turno_id: int, 
        usuario_id: int, 
        motivo: str
    ) -> TurnoResponse:
        """
        Cancela un turno
        """
        turno = self.db.query(Turno).filter(
            Turno.turno_id == turno_id,
            Turno.cliente_id == usuario_id
        ).first()
        
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turno no encontrado"
            )
        
        if turno.estado == EstadoTurno.CANCELADO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El turno ya está cancelado"
            )
        
        # Cancelar turno
        turno.estado = EstadoTurno.CANCELADO
        turno.cancelado_por = "cliente"
        turno.motivo_cancelacion = motivo
        turno.fecha_cancelacion = datetime.utcnow()
        turno.fecha_actualizacion = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(turno)
        
        return self._convertir_a_turno_response(turno)
    
    # Métodos auxiliares privados
    
    def _obtener_dia_semana(self, fecha: date) -> DiaSemana:
        """Convierte fecha a enum del día de semana"""
        dias = [
            DiaSemana.LUNES, DiaSemana.MARTES, DiaSemana.MIERCOLES,
            DiaSemana.JUEVES, DiaSemana.VIERNES, DiaSemana.SABADO, DiaSemana.DOMINGO
        ]
        return dias[fecha.weekday()]
    
    def _generar_slots_para_servicio(
        self,
        hora_inicio: time,
        hora_fin: time,
        servicio: Servicio,
        turnos_ocupados: List[Turno],
        fecha: date
    ) -> List[SlotDisponible]:
        """Genera slots disponibles para un servicio en un rango horario"""
        slots = []
        
        # Convertir a datetime para facilitar cálculos
        dt_inicio = datetime.combine(fecha, hora_inicio)
        dt_fin = datetime.combine(fecha, hora_fin)
        
        slot_actual = dt_inicio
        duracion = timedelta(minutes=servicio.duracion_minutos)
        
        while slot_actual + duracion <= dt_fin:
            slot_fin = slot_actual + duracion
            
            # Verificar si hay conflicto con turnos existentes
            conflicto = any(
                turno.servicio_id == servicio.servicio_id and
                self._hay_solapamiento(
                    slot_actual.time(),
                    slot_fin.time(),
                    turno.hora,
                    self._calcular_hora_fin(turno.hora, 
                        self.db.query(Servicio).filter(Servicio.servicio_id == turno.servicio_id).first().duracion_minutos
                    )
                )
                for turno in turnos_ocupados
            )
            
            if not conflicto:
                slots.append(SlotDisponible(
                    hora_inicio=slot_actual.time(),
                    hora_fin=slot_fin.time(),
                    servicio_id=servicio.servicio_id,
                    servicio_nombre=servicio.nombre,
                    duracion_minutos=servicio.duracion_minutos,
                    precio=float(servicio.precio)
                ))
            
            # Avanzar al siguiente slot (por ejemplo, cada 30 minutos)
            slot_actual += timedelta(minutes=30)
        
        return slots
    
    def _hay_solapamiento(
        self, 
        inicio1: time, 
        fin1: time, 
        inicio2: time, 
        fin2: time
    ) -> bool:
        """Verifica si dos rangos horarios se solapan"""
        return inicio1 < fin2 and inicio2 < fin1
    
    def _validar_horario_disponible(
        self,
        empresa_id: int,
        fecha: date,
        hora: time,
        duracion_minutos: int
    ) -> bool:
        """Valida si un horario está disponible"""
        hora_fin = self._calcular_hora_fin(hora, duracion_minutos)
        
        # Verificar conflictos con otros turnos
        conflictos = self.db.query(Turno).filter(
            Turno.empresa_id == empresa_id,
            Turno.fecha == fecha,
            Turno.estado.in_([EstadoTurno.PENDIENTE, EstadoTurno.CONFIRMADO]),
            or_(
                and_(Turno.hora <= hora, 
                     func.addtime(Turno.hora, func.sec_to_time(duracion_minutos * 60)) > hora),
                and_(Turno.hora < hora_fin, 
                     func.addtime(Turno.hora, func.sec_to_time(duracion_minutos * 60)) >= hora_fin),
                and_(hora <= Turno.hora, hora_fin > Turno.hora)
            )
        ).first()
        
        return conflictos is None
    
    def _calcular_hora_fin(self, hora_inicio: time, duracion_minutos: int) -> time:
        """Calcula la hora de fin basada en inicio y duración"""
        dt = datetime.combine(date.today(), hora_inicio)
        dt_fin = dt + timedelta(minutes=duracion_minutos)
        return dt_fin.time()
    
    def _convertir_a_turno_response(self, turno: Turno) -> TurnoResponse:
        """Convierte un objeto Turno a TurnoResponse con datos relacionados"""
        # Obtener datos relacionados
        empresa = self.db.query(Empresa).filter(
            Empresa.empresa_id == turno.empresa_id
        ).first()
        
        cliente = self.db.query(Usuario).filter(
            Usuario.usuario_id == turno.cliente_id
        ).first()
        
        servicio = None
        if turno.servicio_id:
            servicio = self.db.query(Servicio).filter(
                Servicio.servicio_id == turno.servicio_id
            ).first()
        
        # Calcular hora_fin dinámicamente basado en duración del servicio
        hora_fin_calculada = turno.hora
        if servicio and servicio.duracion_minutos:
            hora_fin_calculada = self._calcular_hora_fin(turno.hora, servicio.duracion_minutos)
        
        return TurnoResponse(
            turno_id=turno.turno_id,
            empresa_id=turno.empresa_id,
            empresa_nombre=empresa.razon_social if empresa else "N/A",
            cliente_id=turno.cliente_id,
            cliente_nombre=cliente.nombre if cliente else "N/A",
            servicio_id=turno.servicio_id,
            servicio_nombre=servicio.nombre if servicio else "N/A",
            fecha=turno.fecha,
            hora=turno.hora,
            hora_fin=hora_fin_calculada,
            estado=turno.estado,
            notas_cliente=turno.notas_cliente,
            notas_empresa=turno.notas_empresa,
            precio=float(servicio.precio) if servicio and servicio.precio else 0.0,
            fecha_creacion=turno.fecha_creacion,
            fecha_actualizacion=turno.fecha_actualizacion,
            fecha_cancelacion=turno.fecha_cancelacion,
            cancelado_por=turno.cancelado_por,
            motivo_cancelacion=turno.motivo_cancelacion
        )