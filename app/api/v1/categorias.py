from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.categoria import CategoriaSchema, CategoriaCreate
from app.crud import get_categorias
from app.models.categoria import Categoria

router = APIRouter()

@router.get("/categorias", response_model=List[CategoriaSchema])
def leer_categorias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todas las categorías"""
    categorias = get_categorias(db, skip=skip, limit=limit)
    return categorias


@router.post("/categorias", response_model=CategoriaSchema, status_code=201)
def crear_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db)
):
    """Crear nueva categoría"""
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