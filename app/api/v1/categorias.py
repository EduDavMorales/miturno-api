from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database import get_db
from app.schemas.categoria import CategoriaSchema, CategoriaCreate
from app.crud import get_categorias
from app.models.categoria import Categoria
from app.models.user import Usuario

router = APIRouter()

@router.get("/categorias", response_model=List[CategoriaSchema])
def leer_categorias(
    skip: int = 0, 
    limit: int = 100, 
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    """Listar todas las categorías"""
    categorias = get_categorias(db, skip=skip, limit=limit)
    return categorias


@router.post("/categorias", response_model=CategoriaSchema, status_code=201)
def crear_categoria(
    categoria: CategoriaCreate,
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    """Crear nueva categoría - Solo admins"""
    
    # Validar que es admin
    if current_user.tipo_usuario.value not in ["ADMIN", "SUPERADMIN"]:  
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden crear categorías"
        )
    
    # Verificar si ya existe
    existe = db.query(Categoria).filter(Categoria.nombre == categoria.nombre).first()
    if existe:
        raise HTTPException(
            status_code=400,
            detail=f"La categoría '{categoria.nombre}' ya existe"
        )
    
    # Crear nueva categoría
    nueva_categoria = Categoria(
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        activa=True
    )
    
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)
    
    return nueva_categoria