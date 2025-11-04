from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional, List, Tuple
from fastapi import HTTPException, status

from app.models.empresa import Empresa
from app.models.direccion import Direccion
from app.models.horario_empresa import HorarioEmpresa
from app.models.categoria import Categoria
from app.models.user import Usuario, TipoUsuario
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate
from app.schemas.direccion import DireccionCreate

class EmpresaService:
    """Service para manejar operaciones complejas de empresa con estructura normalizada"""
    
    @staticmethod
    def get_empresas_with_relations(
        db: Session,
        categoria_id: Optional[int] = None,
        activa: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Empresa], int]:
        """Obtener empresas con direcciones y horarios incluidos"""
        # Query con joins optimizados
        query = db.query(Empresa).options(
            joinedload(Empresa.direccion),
            joinedload(Empresa.horarios),
            joinedload(Empresa.categoria)
        )
        
        # Aplicar filtros
        if categoria_id:
            # Validar que categoría existe
            categoria = db.query(Categoria).filter(Categoria.categoria_id == categoria_id).first()
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoría con ID {categoria_id} no encontrada"
                )
            query = query.filter(Empresa.categoria_id == categoria_id)
        
        if activa:
            query = query.filter(Empresa.activa == True)
        
        # Contar total
        total = query.count()
        
        # Aplicar paginación
        empresas = query.offset(skip).limit(limit).all()
        
        return empresas, total
    
    @staticmethod
    def get_empresa_by_id(db: Session, empresa_id: int) -> Optional[Empresa]:
        """Obtener empresa por ID con relaciones"""
        return db.query(Empresa).options(
            joinedload(Empresa.direccion),
            joinedload(Empresa.horarios),
            joinedload(Empresa.categoria)
        ).filter(Empresa.empresa_id == empresa_id).first()
    
    @staticmethod
    def get_empresa_by_usuario_id(db: Session, usuario_id: int) -> Optional[Empresa]:
        """Obtener empresa por usuario_id con relaciones"""
        return db.query(Empresa).options(
            joinedload(Empresa.direccion),
            joinedload(Empresa.horarios),
            joinedload(Empresa.categoria)
        ).filter(Empresa.usuario_id == usuario_id).first()
    
    @staticmethod
    def create_empresa_complete(
        db: Session, 
        empresa_data: EmpresaCreate
    ) -> Empresa:
        """Crear empresa con direccion en transacción"""
        try:
            # Validaciones previas
            EmpresaService._validate_empresa_creation(db, empresa_data)
            
            # Crear dirección primero
            direccion = Direccion(**empresa_data.direccion.model_dump())
            db.add(direccion)
            db.flush()  # Para obtener direccion_id
            
            # Crear empresa con direccion_id
            empresa_dict = empresa_data.model_dump(exclude={'direccion'})
            empresa_dict['direccion_id'] = direccion.direccion_id
            
            empresa = Empresa(**empresa_dict)
            db.add(empresa)
            db.flush()  # Para obtener empresa_id
            
            db.commit()
            db.refresh(empresa)
            
            # Cargar relaciones para respuesta
            return EmpresaService.get_empresa_by_id(db, empresa.empresa_id)
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def _validate_empresa_creation(db: Session, empresa_data: EmpresaCreate):
        """Validaciones para creación de empresa"""
        # Validar usuario existe
        usuario = db.query(Usuario).filter(Usuario.usuario_id == empresa_data.usuario_id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {empresa_data.usuario_id} no encontrado"
            )
        
        # Validar tipo usuario
        if usuario.tipo_usuario != TipoUsuario.EMPRESA:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Solo usuarios tipo 'empresa' pueden crear empresas. Tu tipo actual: '{usuario.tipo_usuario}'"
            )
        
        # Validar categoría existe
        categoria = db.query(Categoria).filter(Categoria.categoria_id == empresa_data.categoria_id).first()
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con ID {empresa_data.categoria_id} no encontrada"
            )
        
        # Validar usuario no tiene empresa
        empresa_existente = db.query(Empresa).filter(Empresa.usuario_id == empresa_data.usuario_id).first()
        if empresa_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El usuario ya tiene una empresa registrada: '{empresa_existente.razon_social}'"
            )    
    @staticmethod
    def update_empresa_completa(
        db: Session,
        empresa_id: int,
        empresa_update: EmpresaUpdate
    ) -> Empresa:
        """Actualiza empresa completa con dirección (PUT)"""
        try:
            # 1. Verificar que empresa existe
            empresa = db.query(Empresa).filter(
                Empresa.empresa_id == empresa_id
            ).first()
            
            if not empresa:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empresa con ID {empresa_id} no encontrada"
                )
            
            # 2. Si hay datos de categoría, validar que existe
            if empresa_update.categoria_id:
                categoria = db.query(Categoria).filter(
                    Categoria.categoria_id == empresa_update.categoria_id
                ).first()
                if not categoria:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Categoría con ID {empresa_update.categoria_id} no encontrada"
                    )
            
            # 3. Actualizar datos de empresa (excluir dirección)
            empresa_dict = empresa_update.model_dump(exclude={'direccion'}, exclude_unset=False)
            for campo, valor in empresa_dict.items():
                if valor is not None:
                    setattr(empresa, campo, valor)
            
            # 4. Actualizar dirección si se provee
            if empresa_update.direccion:
                direccion = db.query(Direccion).filter(
                    Direccion.direccion_id == empresa.direccion_id
                ).first()
                
                if direccion:
                    # Actualizar dirección existente
                    direccion_dict = empresa_update.direccion.model_dump(exclude_unset=False)
                    for campo, valor in direccion_dict.items():
                        if valor is not None:
                            setattr(direccion, campo, valor)
                else:
                    # Crear nueva dirección si no existe (caso excepcional)
                    direccion = Direccion(**empresa_update.direccion.model_dump())
                    db.add(direccion)
                    db.flush()
                    empresa.direccion_id = direccion.direccion_id
            
            db.commit()
            db.refresh(empresa)
            
            # Retornar con relaciones cargadas
            return EmpresaService.get_empresa_by_id(db, empresa_id)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar empresa: {str(e)}"
            )
    
    @staticmethod
    def update_empresa_parcial(
        db: Session,
        empresa_id: int,
        empresa_update: EmpresaUpdate
    ) -> Empresa:
        """Actualiza solo los campos enviados de empresa (PATCH)"""
        try:
            # 1. Verificar que empresa existe
            empresa = db.query(Empresa).filter(
                Empresa.empresa_id == empresa_id
            ).first()
            
            if not empresa:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empresa con ID {empresa_id} no encontrada"
                )
            
            # 2. Si hay datos de categoría, validar que existe
            if empresa_update.categoria_id:
                categoria = db.query(Categoria).filter(
                    Categoria.categoria_id == empresa_update.categoria_id
                ).first()
                if not categoria:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Categoría con ID {empresa_update.categoria_id} no encontrada"
                    )
            
            # 3. Actualizar solo campos enviados de empresa (exclude_unset=True)
            empresa_dict = empresa_update.model_dump(
                exclude={'direccion'}, 
                exclude_unset=True  # Solo campos enviados
            )
            for campo, valor in empresa_dict.items():
                setattr(empresa, campo, valor)
            
            # 4. Actualizar dirección parcialmente si se provee
            if empresa_update.direccion:
                direccion = db.query(Direccion).filter(
                    Direccion.direccion_id == empresa.direccion_id
                ).first()
                
                if direccion:
                    # Actualizar solo campos enviados de dirección
                    direccion_dict = empresa_update.direccion.model_dump(exclude_unset=True)
                    for campo, valor in direccion_dict.items():
                        setattr(direccion, campo, valor)
                else:
                    # Crear nueva dirección si no existe (caso excepcional)
                    direccion = Direccion(**empresa_update.direccion.model_dump(exclude_unset=True))
                    db.add(direccion)
                    db.flush()
                    empresa.direccion_id = direccion.direccion_id
            
            db.commit()
            db.refresh(empresa)
            
            # Retornar con relaciones cargadas
            return EmpresaService.get_empresa_by_id(db, empresa_id)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar empresa parcialmente: {str(e)}"
            )