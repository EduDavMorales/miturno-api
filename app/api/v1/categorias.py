from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.categoria import CategoriaSchema
from app.crud import get_categorias

router = APIRouter()

@router.get("/categorias", response_model=List[CategoriaSchema])
def leer_categorias(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    categorias = get_categorias(db, skip=skip, limit=limit)
    return categorias
