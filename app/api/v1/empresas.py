from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.database import get_db
from app.models.empresa import Empresa
from app.models.user import Usuario, TipoUsuario  # IMPORTAR Usuario y TipoUsuario
from app.models.categoria import Categoria
from app.schemas.empresa import EmpresasListResponse, EmpresaCreate, EmpresaResponse

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/empresas", 
    response_model=EmpresasListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar empresas con filtros",
    description="Obtiene una lista de empresas con filtros por categoria y estado"
)
def get_empresas(
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoria"),
    activa: bool = Query(True, description="Solo empresas activas"),
    skip: int = Query(0, ge=0, description="Numero de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Numero máximo de registros"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de empresas con filtros y paginación
    
    - **categoria_id**: ID de categoría para filtrar (opcional)
    - **activa**: Solo empresas activas (default: True)
    - **skip**: registros a saltar para paginación
    - **limit**: máximo de registros a retornar (1-100)
    """
    try:
        # Construir query base
        query = db.query(Empresa)
        
        # Aplicar filtros
        if categoria_id:
            # Validar que la categoría existe
            categoria = db.query(Categoria).filter(Categoria.categoria_id == categoria_id).first()
            if not categoria:
                logger.warning(f"Categoría {categoria_id} no encontrada")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoría con ID {categoria_id} no encontrada"
                )
            
            query = query.filter(Empresa.categoria_id == categoria_id)
        
        if activa:
            query = query.filter(Empresa.activa == True)
        
        # Contar total antes de aplicar paginación
        total = query.count()
        
        # Aplicar paginación
        empresas = query.offset(skip).limit(limit).all()
        
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
    description="Obtiene los detalles de una empresa específica"
)
def get_empresa(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener una empresa específica por ID
    
    - **empresa_id**: ID único de la empresa
    """
    try:
        empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
        
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
    description="Crea una nueva empresa para un usuario tipo 'empresa'"
)
def create_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva empresa
    
    - **usuario_id**: ID del usuario propietario (debe ser tipo 'empresa')
    - **categoria_id**: ID de la categoría (requerido)
    - **nombre**: Nombre de la empresa (requerido)
    - Otros campos según el schema EmpresaCreate
    
    **Validaciones:**
    - El usuario debe existir
    - El usuario debe ser tipo 'empresa' (no 'cliente')
    - La categoría debe existir  
    - El usuario no puede tener más de una empresa
    """
    try:
        #  PASO 1: Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.usuario_id == empresa.usuario_id).first()
        if not usuario:
            logger.warning(f"Usuario {empresa.usuario_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Usuario con ID {empresa.usuario_id} no encontrado"
            )
        
        #  PASO 2: Verificar que el usuario es tipo 'empresa'
        if usuario.tipo_usuario != TipoUsuario.EMPRESA:
            logger.warning(f"Usuario {empresa.usuario_id} tipo '{usuario.tipo_usuario}' intentó crear empresa")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Solo usuarios tipo 'empresa' pueden crear empresas. Tu tipo actual: '{usuario.tipo_usuario}'"
            )
        
        #  PASO 3: Verificar que la categoría existe
        categoria = db.query(Categoria).filter(Categoria.categoria_id == empresa.categoria_id).first()
        if not categoria:
            logger.warning(f"Categoría {empresa.categoria_id} no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Categoría con ID {empresa.categoria_id} no encontrada"
            )
        
        #  PASO 4: Verificar que el usuario no tenga ya una empresa
        empresa_existente = db.query(Empresa).filter(Empresa.usuario_id == empresa.usuario_id).first()
        if empresa_existente:
            logger.warning(f"Usuario {empresa.usuario_id} ya tiene empresa {empresa_existente.empresa_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El usuario ya tiene una empresa registrada: '{empresa_existente.razon_social}'"
            )
        
        #  PASO 5: Crear nueva empresa
        db_empresa = Empresa(**empresa.dict())
        db.add(db_empresa)
        db.commit()
        db.refresh(db_empresa)
        
        logger.info(f"Empresa '{db_empresa.razon_social}' creada exitosamente para usuario {empresa.usuario_id}")
        
        return db_empresa
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()  # Rollback en caso de error
        logger.error(f"Error al crear empresa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la empresa"
        )

# Endpoint útil: obtener empresa por usuario (solo usuarios tipo empresa)
@router.get(
    "/empresas/usuario/{usuario_id}",
    response_model=EmpresaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener empresa de un usuario",
    description="Obtiene la empresa asociada a un usuario tipo 'empresa'"
)
def get_empresa_by_usuario(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener la empresa de un usuario específico
    
    - **usuario_id**: ID del usuario (debe ser tipo 'empresa')
    """
    try:
        # Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {usuario_id} no encontrado"
            )
        
        # Verificar que es tipo empresa
        if usuario.tipo_usuario != TipoUsuario.EMPRESA:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El usuario tipo '{usuario.tipo_usuario}' no puede tener empresas"
            )
        
        # Buscar empresa del usuario
        empresa = db.query(Empresa).filter(Empresa.usuario_id == usuario_id).first()
        
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