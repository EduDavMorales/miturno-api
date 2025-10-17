from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.mensaje import (
    ConversacionCreate,
    ConversacionResponse,
    ConversacionDetalle,
    MensajeCreate,
    MensajeResponse,
    MensajeEnviar
)
from app.models.mensaje import Conversacion, Mensaje, RemitenteEnum
from app.models.user import Usuario
from app.api.deps import get_current_user

router = APIRouter(prefix="/conversaciones", tags=[" 💬  Conversaciones"])


@router.post("", response_model=ConversacionResponse, status_code=status.HTTP_201_CREATED)
def crear_conversacion(
    conversacion: ConversacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear o recuperar una conversación existente entre cliente y empresa"""
    
    # Verificar si ya existe una conversación
    conversacion_existente = db.query(Conversacion).filter(
        Conversacion.cliente_id == conversacion.cliente_id,
        Conversacion.empresa_id == conversacion.empresa_id
    ).first()
    
    if conversacion_existente:
        return conversacion_existente
    
    # Crear nueva conversación
    nueva_conversacion = Conversacion(**conversacion.dict())
    db.add(nueva_conversacion)
    db.commit()
    db.refresh(nueva_conversacion)
    
    return nueva_conversacion


@router.get("", response_model=List[ConversacionResponse])
def listar_conversaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todas las conversaciones del usuario actual"""
    
    # Si es cliente, buscar por cliente_id
    # Si es empresa, buscar por empresa_id
    if current_user.tipo_usuario.value == "cliente":
        conversaciones = db.query(Conversacion).filter(
            Conversacion.cliente_id == current_user.usuario_id
        ).all()
    else:
        # Buscar la empresa del usuario
        from app.models.empresa import Empresa
        empresa = db.query(Empresa).filter(
            Empresa.usuario_id == current_user.usuario_id
        ).first()
        
        if not empresa:
            return []
        
        conversaciones = db.query(Conversacion).filter(
            Conversacion.empresa_id == empresa.empresa_id
        ).all()
    
    return conversaciones


@router.get("/{conversacion_id}", response_model=ConversacionDetalle)
def obtener_conversacion(
    conversacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una conversación específica con todos sus mensajes"""
    
    conversacion = db.query(Conversacion).filter(
        Conversacion.conversacion_id == conversacion_id
    ).first()
    
    if not conversacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )
    
    # Verificar que el usuario tenga acceso a esta conversación
    from app.models.empresa import Empresa
    empresa = db.query(Empresa).filter(
        Empresa.usuario_id == current_user.usuario_id
    ).first()
    
    es_cliente = conversacion.cliente_id == current_user.usuario_id
    es_empresa = empresa and conversacion.empresa_id == empresa.empresa_id
    
    if not (es_cliente or es_empresa):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta conversación"
        )
    
    # Cargar mensajes
    mensajes = db.query(Mensaje).filter(
        Mensaje.conversacion_id == conversacion_id,
        Mensaje.deleted_at.is_(None)
    ).order_by(Mensaje.created_at.asc()).all()
    
    # Construir respuesta
    return {
        **conversacion.__dict__,
        "mensajes": mensajes
    }


@router.post("/{conversacion_id}/mensajes", response_model=MensajeResponse, status_code=status.HTTP_201_CREATED)
def enviar_mensaje(
    conversacion_id: int,
    mensaje: MensajeEnviar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Enviar un mensaje en una conversación"""
    
    # Verificar que la conversación existe
    conversacion = db.query(Conversacion).filter(
        Conversacion.conversacion_id == conversacion_id
    ).first()
    
    if not conversacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )
    
    # Determinar tipo de remitente
    from app.models.empresa import Empresa
    empresa = db.query(Empresa).filter(
        Empresa.usuario_id == current_user.usuario_id
    ).first()

    # ? VERIFICAR EMPRESA PRIMERO
    if empresa and conversacion.empresa_id == empresa.empresa_id:
        remitente_tipo = RemitenteEnum.empresa
        remitente_id = empresa.empresa_id
    elif conversacion.cliente_id == current_user.usuario_id:
        remitente_tipo = RemitenteEnum.cliente
        remitente_id = current_user.usuario_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta conversación"
        )

    # Crear mensaje
    nuevo_mensaje = Mensaje(
        conversacion_id=conversacion_id,
        remitente_tipo=remitente_tipo,
        remitente_id=remitente_id,
        contenido=mensaje.contenido,
        leido=False
    )
    
    db.add(nuevo_mensaje)
    
    # Actualizar fecha de última actualización de la conversación
    from sqlalchemy import func
    conversacion.updated_at = func.now()
    
    db.commit()
    db.refresh(nuevo_mensaje)
    
    return nuevo_mensaje


@router.patch("/mensajes/{mensaje_id}/marcar-leido", response_model=MensajeResponse)
def marcar_mensaje_leido(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marcar un mensaje como leído"""
    
    mensaje = db.query(Mensaje).filter(
        Mensaje.mensaje_id == mensaje_id
    ).first()
    
    if not mensaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado"
        )
    
    # Verificar acceso
    conversacion = db.query(Conversacion).filter(
        Conversacion.conversacion_id == mensaje.conversacion_id
    ).first()
    
    from app.models.empresa import Empresa
    empresa = db.query(Empresa).filter(
        Empresa.usuario_id == current_user.usuario_id
    ).first()
    
    es_cliente = conversacion.cliente_id == current_user.usuario_id
    es_empresa = empresa and conversacion.empresa_id == empresa.empresa_id
    
    if not (es_cliente or es_empresa):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este mensaje"
        )
    
    # Marcar como leído
    mensaje.leido = True
    db.commit()
    db.refresh(mensaje)
    
    return mensaje