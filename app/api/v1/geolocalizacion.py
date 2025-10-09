from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.geo import (
    ResultadoBusquedaGeografica,
    EmpresaConDistancia,
    GeoLocation
)
from app.services.geolocation_service import geolocation_service
from app.services.geocoding_service_new import geocoding_service

router = APIRouter(prefix="/geolocalizacion")


@router.get("/empresas-cercanas", response_model=ResultadoBusquedaGeografica)
async def buscar_empresas_cercanas(
    latitud: float = Query(..., ge=-90, le=90, description="Latitud del punto de búsqueda"),
    longitud: float = Query(..., ge=-180, le=180, description="Longitud del punto de búsqueda"),
    radio_km: float = Query(10.0, gt=0, le=100, description="Radio de búsqueda en km (máx 100)"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoría específica"),
    db: Session = Depends(get_db)
):
    """
    Busca empresas cercanas a coordenadas específicas.
    
    Ejemplo: /geolocalizacion/empresas-cercanas?latitud=-34.6537&longitud=-58.6199&radio_km=10
    """
    try:
        # Buscar empresas cercanas
        empresas_encontradas = geolocation_service.find_nearby_empresas(
            db=db,
            latitud=latitud,
            longitud=longitud,
            radio_km=radio_km,
            categoria_id=categoria_id,
            limit=50
        )
        
        # Convertir a schema de respuesta
        empresas_response = [
            EmpresaConDistancia(
                empresa_id=emp["empresa_id"],
                razon_social=emp["nombre"],
                descripcion=emp["descripcion"],
                categoria_id=emp["categoria_id"],
                coordenadas=GeoLocation(
                    latitud=emp["latitud"],
                    longitud=emp["longitud"]
                ),
                distancia_km=emp["distancia_km"],
                activa=True
            )
            for emp in empresas_encontradas
        ]
        
        return ResultadoBusquedaGeografica(
            punto_busqueda=GeoLocation(
                latitud=latitud,
                longitud=longitud
            ),
            radio_km=radio_km,
            total_encontradas=len(empresas_response),
            empresas=empresas_response
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar empresas cercanas: {str(e)}"
        )


@router.get("/buscar-por-direccion", response_model=ResultadoBusquedaGeografica)
async def buscar_por_direccion(
    calle: str = Query(..., min_length=1, description="Nombre de la calle"),
    numero: Optional[str] = Query(None, description="Número de la dirección"),
    ciudad: Optional[str] = Query(None, description="Ciudad o localidad"),
    provincia: Optional[str] = Query(None, description="Provincia"),
    codigo_postal: Optional[str] = Query(None, description="Código postal"),
    radio_km: float = Query(10.0, gt=0, le=100, description="Radio de búsqueda en km"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    db: Session = Depends(get_db)
):
    """
    Busca empresas cercanas a una dirección.
    
    Primero geocodifica la dirección y luego busca empresas en el radio especificado.
    
    Ejemplo: /geolocalizacion/buscar-por-direccion?calle=Av%20Corrientes&numero=1000&ciudad=CABA&provincia=Buenos%20Aires&radio_km=50
    """
    try:
        # 1. Geocodificar la dirección
        resultado_geocoding = await geocoding_service.geocode_address(
            calle=calle,
            numero=numero,
            ciudad=ciudad,
            provincia=provincia,
            codigo_postal=codigo_postal
        )
        
        # Verificar que se obtuvo resultado válido
        if not resultado_geocoding or not resultado_geocoding.get("coordinates"):
            raise HTTPException(
                status_code=400,
                detail="No se pudo geocodificar la dirección proporcionada"
            )
        
        # Extraer coordenadas (formato: tuple (lat, lng))
        lat, lng = resultado_geocoding["coordinates"]
        
        # 2. Buscar empresas cercanas
        empresas_encontradas = geolocation_service.find_nearby_empresas(
            db=db,
            latitud=lat,
            longitud=lng,
            radio_km=radio_km,
            categoria_id=categoria_id,
            limit=50
        )
        
        # 3. Convertir a schema de respuesta
        empresas_response = [
            EmpresaConDistancia(
                empresa_id=emp["empresa_id"],
                razon_social=emp["nombre"],
                descripcion=emp["descripcion"],
                categoria_id=emp["categoria_id"],
                coordenadas=GeoLocation(
                    latitud=emp["latitud"],
                    longitud=emp["longitud"]
                ),
                distancia_km=emp["distancia_km"],
                activa=True
            )
            for emp in empresas_encontradas
        ]
        
        return ResultadoBusquedaGeografica(
            punto_busqueda=GeoLocation(
                latitud=lat,
                longitud=lng
            ),
            radio_km=radio_km,
            total_encontradas=len(empresas_response),
            empresas=empresas_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar por dirección: {str(e)}"
        )