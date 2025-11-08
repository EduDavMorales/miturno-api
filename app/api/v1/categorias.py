from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from sqlalchemy.orm import Session
from app.auth.permissions import user_has_role
from app.core.security import get_current_user
from app.database import get_db
from app.schemas.categoria import CategoriaSchema, CategoriaCreate, CategoriaUpdate
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
    return JSONResponse(
        content=[CategoriaSchema.from_orm(cat).dict() for cat in categorias],
        status_code=200,
        # Opcional pero explícito, asegura que se envía el header charset=utf-8
        media_type="application/json", 
        headers={"Content-Type": "application/json; charset=utf-8"} 
    )


@router.post("/categorias", response_model=CategoriaSchema, status_code=201)
def crear_categoria(
    categoria: CategoriaCreate,
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    """Crear nueva categoría - Solo admins"""
    
    # Verificar que tiene rol de admin usando el sistema RBAC correcto
    if not (user_has_role(current_user.usuario_id, "SUPERADMIN", db) or 
            user_has_role(current_user.usuario_id, "ADMIN_EMPRESA", db)):
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden actualizar categorías"
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
    
@router.patch("/categorias/{categoria_id}", response_model=CategoriaSchema)
def actualizar_categoria(
    categoria_id: int,
    categoria_in: CategoriaUpdate, # Usamos el esquema de actualización parcial
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar categoría existente - Solo admins"""

    # Verificar que tiene rol de admin usando el sistema RBAC correcto
    if not (user_has_role(current_user.usuario_id, "SUPERADMIN", db) or 
            user_has_role(current_user.usuario_id, "ADMIN_EMPRESA", db)):
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden actualizar categorías"
        )

    # 1. Obtener la categoría existente
    categoria_db = db.query(Categoria).filter(Categoria.categoria_id == categoria_id).first()

    if not categoria_db:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # 2. Preparar datos para la actualización
    # 🛑 Esto es clave para PATCH: excluye los valores None (los campos que no se enviaron)
    update_data = categoria_in.model_dump(exclude_unset=True) 
    
    # 3. Aplicar la actualización a los campos del modelo SQLAlchemy
    for key, value in update_data.items():
        setattr(categoria_db, key, value)

    # 4. Guardar en la base de datos
    db.add(categoria_db)
    db.commit()
    db.refresh(categoria_db)
    
    # 5. Devolver la respuesta a través de JSONResponse para mantener UTF-8
    return JSONResponse(
        content=CategoriaSchema.model_validate(categoria_db).model_dump(),
        status_code=200,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )