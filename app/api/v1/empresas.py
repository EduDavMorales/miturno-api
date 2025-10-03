from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.user import Usuario, TipoUsuario
from app.schemas.empresa import EmpresasListResponse, EmpresaCreate, EmpresaResponse
from app.services.empresa_service import EmpresaService

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/empresas", 
    response_model=EmpresasListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar empresas con filtros",
    description="Obtiene una lista de empresas con direcciones incluidas"
)
def get_empresas(
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoria"),
    activa: bool = Query(True, description="Solo empresas activas"),
    skip: int = Query(0, ge=0, description="Numero de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Numero máximo de registros"),
    db: Session = Depends(get_db)
):
    try:
        empresas, total = EmpresaService.get_empresas_with_relations(
            db=db,
            categoria_id=categoria_id,
            activa=activa,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"Consulta de empresas: {len(empresas)} de {total} total")
        return EmpresasListResponse(empresas=empresas, total=total)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener empresas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener empresas"
        )

@router.get(
    "/empresas/{empresa_id}",
    response_model=EmpresaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener empresa por ID",
    description="Obtiene una empresa con direccion incluida"
)
def get_empresa(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    try:
        empresa = EmpresaService.get_empresa_by_id(db, empresa_id)
        
        if not empresa:
            logger.warning(f"Empresa {empresa_id} no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        return empresa
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener empresa {empresa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la empresa"
        )

@router.post(
    "/empresas", 
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED,  
    summary="Crear nueva empresa",
    description="Crea una nueva empresa con dirección"
)
def create_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db)
):
    try:
        db_empresa = EmpresaService.create_empresa_complete(db, empresa)
        
        logger.info(f"Empresa '{db_empresa.razon_social}' creada exitosamente para usuario {empresa.usuario_id}")
        return db_empresa
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear empresa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la empresa"
        )

@router.get(
    "/empresas/usuario/{usuario_id}",
    response_model=EmpresaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener empresa de un usuario",
    description="Obtiene la empresa de un usuario con direccion incluida"
)
def get_empresa_by_usuario(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    try:
        usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {usuario_id} no encontrado"
            )
        
        if usuario.tipo_usuario != TipoUsuario.EMPRESA:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El usuario tipo '{usuario.tipo_usuario}' no puede tener empresas"
            )
        
        empresa = EmpresaService.get_empresa_by_usuario_id(db, usuario_id)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El usuario no tiene una empresa registrada"
            )
        
        return empresa
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener empresa del usuario {usuario_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la empresa del usuario"
        )