"""
Enums centralizados para todo el proyecto.
Principio DRY: Una sola fuente de verdad para cada enum.
"""
import enum


class TipoUsuario(str, enum.Enum):
    """Tipos de usuario en el sistema"""
    CLIENTE = "CLIENTE"
    EMPRESA = "EMPRESA"


class EstadoTurno(str, enum.Enum):
    """Estados posibles de un turno"""
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    COMPLETADO = "completado"


class TipoNotificacion(str, enum.Enum):
    """Tipos de notificación"""
    RECORDATORIO = "recordatorio"
    CONFIRMACION = "confirmacion"
    CANCELACION = "cancelacion"


class CanalNotificacion(str, enum.Enum):
    """Canales para envío de notificaciones"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class TipoBloqueo(str, enum.Enum):
    """Tipos de bloqueo de horarios"""
    FERIADO = "feriado"
    VACACIONES = "vacaciones"
    MANTENIMIENTO = "mantenimiento"
    OTRO = "otro"


class DiaSemana(str, enum.Enum):
    """Días de la semana"""
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sabado"
    DOMINGO = "domingo"