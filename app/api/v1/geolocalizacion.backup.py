from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.geo import (
    ResultadoBusquedaGeografica,
    EmpresaConDistancia,
    GeoLocation,
    ActualizarCoordenadasRequest,
    ActualizarCoordenadasResponse
)
from app.services.geolocation_service import geolocation_service
from app.services.geocoding_service_new import geocoding_service
from app.models.empresa import Empresa
from app.models.direccion import Direccion
from app.core.security import get_current_user
from app.models.user import Usuario 
from app.models.rol import UsuarioRol
from app.auth.permissions import PermissionService 

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


@router.put("/empresas/{empresa_id}/coordenadas", response_model=ActualizarCoordenadasResponse)
 
async def actualizar_coordenadas_empresa(
    empresa_id: int,
    request: ActualizarCoordenadasRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza las coordenadas de una empresa.
    
    **Caso de uso principal:** Corrección manual desde mapa interactivo
    - Útil cuando la geocodificación automática de AMBA no es precisa
    - El usuario ajusta el pin en el mapa del frontend
    - Se envían las coordenadas corregidas
    
    Dos modos de operación:
    1. **Manual** (Principal): Proporciona latitud/longitud desde mapa interactivo
    2. **Automático** (Opcional): Geocodifica desde la dirección asociada
    
    Ejemplo manual (desde mapa):
    ```json
    {
        "latitud": -34.6537,
        "longitud": -58.3816,
        "corregido_manualmente": true
    }
    ```
    
    Ejemplo automático (reintentar geocodificación):
    ```json
    {
        "recalcular_desde_direccion": true
    }
    ```
    """
    try:
        # 1. Buscar empresa
        empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
        
        if not empresa:
            raise HTTPException(
                status_code=404,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        # 2. ✅ NUEVA VALIDACIÓN: Verificar que el usuario pertenece a esta empresa
        # Buscar el usuario_rol para validar empresa_id
        usuario_empresa = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()

        if not usuario_empresa:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para actualizar esta empresa. Solo puedes actualizar tu propia empresa."
            )
        
        # ✅ AGREGAR: Validar que tiene el permiso
        permission_service = PermissionService(db)
        tiene_permiso = permission_service.usuario_tiene_permiso(
            usuario_id=current_user.usuario_id,
            permiso_codigo="empresas:actualizar_propia",
            empresa_id=empresa_id
        )
        
        if not tiene_permiso:
            raise HTTPException(
                status_code=403,
                detail="No tienes el permiso necesario (empresas:actualizar_propia)"
            )
        
        # Guardar coordenadas anteriores
        coordenadas_anteriores = None
        if empresa.latitud and empresa.longitud:
            coordenadas_anteriores = {
                "latitud": float(empresa.latitud),
                "longitud": float(empresa.longitud)
            }
        
        # 3. Determinar método de actualización
        if request.recalcular_desde_direccion:
            # MODO AUTOMÁTICO: Geocodificar desde dirección
            if not empresa.direccion_id:
                raise HTTPException(
                    status_code=400,
                    detail="La empresa no tiene dirección asociada para geocodificar"
                )
            
            # Obtener dirección
            direccion = db.query(Direccion).filter(
                Direccion.direccion_id == empresa.direccion_id
            ).first()
            
            if not direccion:
                raise HTTPException(
                    status_code=400,
                    detail="Dirección asociada no encontrada"
                )
            
            # Geocodificar
            resultado_geocoding = await geocoding_service.geocode_address(
                calle=direccion.calle,
                numero=direccion.numero,
                ciudad=direccion.ciudad,
                provincia=direccion.provincia,
                codigo_postal=direccion.codigo_postal
            )
            
            if not resultado_geocoding or not resultado_geocoding.get("coordinates"):
                raise HTTPException(
                    status_code=400,
                    detail=f"No se pudo geocodificar la dirección: {direccion.calle} {direccion.numero}, {direccion.ciudad}"
                )
            
            lat, lng = resultado_geocoding["coordinates"]
            metodo = "geocodificacion"
            
            # Guardar información de validación si existe
            if resultado_geocoding.get("validation"):
                validation = resultado_geocoding["validation"]
                empresa.geocoding_confidence = validation.get("confidence", "unknown")
                if validation.get("validation", {}).get("warning"):
                    empresa.geocoding_warning = validation["validation"]["warning"]
            
        else:
            # MODO MANUAL: Usar coordenadas proporcionadas (ajustadas desde mapa)
            if request.latitud is None or request.longitud is None:
                raise HTTPException(
                    status_code=400,
                    detail="Debe proporcionar latitud y longitud, o activar recalcular_desde_direccion"
                )
            
            lat = request.latitud
            lng = request.longitud
            metodo = "manual"
            
            # Validar que estén dentro de Argentina
            bounds = geocoding_service.ARGENTINA_BOUNDS
            if not (bounds['lat_min'] <= lat <= bounds['lat_max'] and
                    bounds['lng_min'] <= lng <= bounds['lng_max']):
                raise HTTPException(
                    status_code=400,
                    detail="Las coordenadas están fuera del territorio argentino"
                )
            
            # Marcar como corregido manualmente si el usuario lo indica
            if request.corregido_manualmente:
                empresa.geocoding_confidence = "manual_correction"
                empresa.geocoding_warning = "Ubicación ajustada manualmente por el usuario desde el mapa"
        
        # 4. Actualizar empresa
        empresa.latitud = lat
        empresa.longitud = lng
        
        db.commit()
        db.refresh(empresa)
        
        # 5. Construir respuesta
        return ActualizarCoordenadasResponse(
            success=True,
            message="Coordenadas actualizadas exitosamente",
            empresa_id=empresa_id,
            coordenadas_anteriores=coordenadas_anteriores,
            coordenadas_nuevas={
                "latitud": float(lat),
                "longitud": float(lng)
            },
            metodo=metodo
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar coordenadas: {str(e)}"
        )