from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging
import asyncio

from app.database import get_db
from app.schemas.geo import (
    ResultadoBusquedaGeografica,
    EmpresaConDistancia,
    GeoLocation,
    ActualizarCoordenadasRequest,
    ActualizarCoordenadasResponse,
    BusquedaPorDireccion
)
from app.services.geolocation_service import geolocation_service
from app.services.geocoding_service_new import geocoding_service
from app.models.empresa import Empresa
from app.models.direccion import Direccion
from app.models.categoria import Categoria
from app.core.security import get_current_user
from app.models.user import Usuario 
from app.models.rol import UsuarioRol
from app.auth.permissions import PermissionService

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geolocalizacion")


@router.get("/empresas-cercanas", response_model=ResultadoBusquedaGeografica)
async def buscar_empresas_cercanas(
    latitud: float = Query(..., ge=-90, le=90, description="Latitud del punto de búsqueda"),
    longitud: float = Query(..., ge=-180, le=180, description="Longitud del punto de búsqueda"),
    radio_km: float = Query(10.0, gt=0, le=100, description="Radio de búsqueda en km (máx 100)"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoría específica"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca empresas cercanas a coordenadas específicas.
    
    **Validaciones:**
    - Coordenadas dentro de rango válido
    - Radio entre 0 y 100 km
    - Categoría existe (si se proporciona)
    
    **Errores posibles:**
    - 400: Parámetros inválidos, categoría no existe
    - 500: Error de base de datos o servicio
    
    Ejemplo: /geolocalizacion/empresas-cercanas?latitud=-34.6537&longitud=-58.6199&radio_km=10
    """
    try:
        # 1. Validar que la categoría existe (si se proporciona)
        if categoria_id is not None:
            categoria = db.query(Categoria).filter(
                Categoria.categoria_id == categoria_id
            ).first()
            
            if not categoria:
                raise HTTPException(
                    status_code=400,
                    detail=f"Categoría con ID {categoria_id} no existe"
                )
            
            logger.info(f"Búsqueda con filtro de categoría: {categoria.nombre}")
        
        # 2. Validar coordenadas dentro de Argentina (opcional pero recomendado)
        bounds = geocoding_service.ARGENTINA_BOUNDS
        if not (bounds['lat_min'] <= latitud <= bounds['lat_max'] and
                bounds['lng_min'] <= longitud <= bounds['lng_max']):
            logger.warning(f"Coordenadas fuera de Argentina: ({latitud}, {longitud})")
            # No bloqueamos, pero logueamos
        
        # 3. Buscar empresas cercanas
        logger.info(f"Buscando empresas en radio {radio_km}km desde ({latitud}, {longitud})")
        
        empresas_encontradas = geolocation_service.find_nearby_empresas(
            db=db,
            latitud=latitud,
            longitud=longitud,
            radio_km=radio_km,
            categoria_id=categoria_id,
            limit=50
        )
        
        # 4. Validar que hay resultados o devolver lista vacía (no es error)
        if not empresas_encontradas:
            logger.info("No se encontraron empresas en el radio especificado")
            return ResultadoBusquedaGeografica(
                punto_busqueda=GeoLocation(
                    latitud=latitud,
                    longitud=longitud
                ),
                radio_km=radio_km,
                total_encontradas=0,
                empresas=[]
            )
        
        # 5. Convertir a schema de respuesta
        empresas_response = []
        for emp in empresas_encontradas:
            try:
                # Validar que la empresa tenga los datos necesarios
                if not emp.get("latitud") or not emp.get("longitud"):
                    logger.warning(f"Empresa {emp.get('empresa_id')} sin coordenadas, omitiendo")
                    continue
                
                empresas_response.append(
                    EmpresaConDistancia(
                        empresa_id=emp["empresa_id"],
                        razon_social=emp["nombre"],
                        descripcion=emp.get("descripcion", ""),
                        categoria_id=emp["categoria_id"],
                        coordenadas=GeoLocation(
                            latitud=emp["latitud"],
                            longitud=emp["longitud"]
                        ),
                        distancia_km=emp["distancia_km"],
                        activa=True
                    )
                )
            except (KeyError, ValueError) as e:
                logger.error(f"Error procesando empresa {emp.get('empresa_id')}: {str(e)}")
                continue
        
        logger.info(f"Se encontraron {len(empresas_response)} empresas válidas")
        
        return ResultadoBusquedaGeografica(
            punto_busqueda=GeoLocation(
                latitud=latitud,
                longitud=longitud
            ),
            radio_km=radio_km,
            total_encontradas=len(empresas_response),
            empresas=empresas_response
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación de datos: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Datos inválidos: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado en búsqueda cercana: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al buscar empresas. Por favor, intente nuevamente."
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
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca empresas cercanas a una dirección.
    
    Primero geocodifica la dirección y luego busca empresas en el radio especificado.
    
    **Validaciones:**
    - Dirección debe poder geocodificarse
    - Categoría existe (si se proporciona)
    - Timeout de 10 segundos para geocodificación
    
    **Errores posibles:**
    - 400: Dirección no geocodificable, categoría no existe
    - 408: Timeout de servicio de geocodificación
    - 500: Error de base de datos o servicio
    
    Ejemplo: /geolocalizacion/buscar-por-direccion?calle=Av%20Corrientes&numero=1000&ciudad=CABA&provincia=Buenos%20Aires&radio_km=5
    """
    try:
        # 1. Validar categoría si se proporciona
        if categoria_id is not None:
            categoria = db.query(Categoria).filter(
                Categoria.categoria_id == categoria_id
            ).first()
            
            if not categoria:
                raise HTTPException(
                    status_code=400,
                    detail=f"Categoría con ID {categoria_id} no existe"
                )
        
        # 2. Construir dirección legible para logging
        direccion_str = f"{calle}"
        if numero:
            direccion_str += f" {numero}"
        if ciudad:
            direccion_str += f", {ciudad}"
        if provincia:
            direccion_str += f", {provincia}"
        
        logger.info(f"Geocodificando dirección: {direccion_str}")
        
        # 3. Geocodificar con timeout de 10 segundos
        try:
            resultado_geocoding = await asyncio.wait_for(
                geocoding_service.geocode_address(
                    calle=calle,
                    numero=numero,
                    ciudad=ciudad,
                    provincia=provincia,
                    codigo_postal=codigo_postal
                ),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout al geocodificar: {direccion_str}")
            raise HTTPException(
                status_code=408,
                detail="El servicio de geocodificación tardó demasiado. Por favor, intente nuevamente."
            )
        
        # 4. Verificar resultado válido
        if not resultado_geocoding:
            logger.warning(f"No se obtuvo resultado al geocodificar: {direccion_str}")
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo encontrar la dirección: {direccion_str}"
            )
        
        if not resultado_geocoding.get("coordinates"):
            logger.warning(f"Geocodificación sin coordenadas: {direccion_str}")
            raise HTTPException(
                status_code=400,
                detail=f"La dirección '{direccion_str}' no pudo ser localizada en el mapa. Verifique los datos ingresados."
            )
        
        # 5. Extraer coordenadas
        try:
            lat, lng = resultado_geocoding["coordinates"]
            logger.info(f"Dirección geocodificada: ({lat}, {lng})")
        except (ValueError, TypeError) as e:
            logger.error(f"Error extrayendo coordenadas: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error procesando las coordenadas de la dirección"
            )
        
        # 6. Buscar empresas cercanas
        empresas_encontradas = geolocation_service.find_nearby_empresas(
            db=db,
            latitud=lat,
            longitud=lng,
            radio_km=radio_km,
            categoria_id=categoria_id,
            limit=50
        )
        
        # 7. Construir respuesta
        if not empresas_encontradas:
            logger.info(f"No hay empresas cerca de {direccion_str} en {radio_km}km")
            return ResultadoBusquedaGeografica(
                punto_busqueda=GeoLocation(latitud=lat, longitud=lng),
                radio_km=radio_km,
                total_encontradas=0,
                empresas=[]
            )
        
        # 8. Convertir a schema
        empresas_response = []
        for emp in empresas_encontradas:
            try:
                if not emp.get("latitud") or not emp.get("longitud"):
                    continue
                
                empresas_response.append(
                    EmpresaConDistancia(
                        empresa_id=emp["empresa_id"],
                        razon_social=emp["nombre"],
                        descripcion=emp.get("descripcion", ""),
                        categoria_id=emp["categoria_id"],
                        coordenadas=GeoLocation(
                            latitud=emp["latitud"],
                            longitud=emp["longitud"]
                        ),
                        distancia_km=emp["distancia_km"],
                        activa=True
                    )
                )
            except (KeyError, ValueError) as e:
                logger.error(f"Error procesando empresa: {str(e)}")
                continue
        
        logger.info(f"Encontradas {len(empresas_response)} empresas cerca de {direccion_str}")
        
        return ResultadoBusquedaGeografica(
            punto_busqueda=GeoLocation(latitud=lat, longitud=lng),
            radio_km=radio_km,
            total_encontradas=len(empresas_response),
            empresas=empresas_response
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Datos inválidos: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado en búsqueda por dirección: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor. Por favor, intente nuevamente."
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
    
    **Validaciones:**
    - Usuario debe pertenecer a la empresa
    - Usuario debe tener permiso 'empresas:actualizar_propia'
    - Empresa debe existir y estar activa
    - Coordenadas dentro de Argentina
    - Timeout de 10 segundos para geocodificación automática
    
    **Errores posibles:**
    - 400: Datos inválidos, empresa sin dirección para geocodificar
    - 403: Sin permisos para esta empresa
    - 404: Empresa no encontrada
    - 408: Timeout de geocodificación
    - 500: Error de base de datos
    
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
        # 1. Validar empresa_id positivo
        if empresa_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="ID de empresa inválido"
            )
        
        # 2. Buscar empresa
        empresa = db.query(Empresa).filter(
            Empresa.empresa_id == empresa_id
        ).first()
        
        if not empresa:
            logger.warning(f"Intento de actualizar empresa inexistente: {empresa_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        # 3. Validar que la empresa esté activa
        if not empresa.activa:
            logger.warning(f"Intento de actualizar empresa inactiva: {empresa_id}")
            raise HTTPException(
                status_code=400,
                detail="No se pueden actualizar coordenadas de una empresa inactiva"
            )
        
        # 4. Verificar que el usuario pertenece a esta empresa
        usuario_empresa = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()

        if not usuario_empresa:
            logger.warning(
                f"Usuario {current_user.usuario_id} intentó actualizar empresa {empresa_id} sin pertenencia"
            )
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para actualizar esta empresa. Solo puedes actualizar empresas a las que perteneces."
            )
        
        # 5. Validar permisos
        permission_service = PermissionService(db)
        tiene_permiso = permission_service.usuario_tiene_permiso(
            usuario_id=current_user.usuario_id,
            permiso_codigo="empresas:actualizar_propia",
            empresa_id=empresa_id
        )
        
        if not tiene_permiso:
            logger.warning(
                f"Usuario {current_user.usuario_id} sin permiso empresas:actualizar_propia"
            )
            raise HTTPException(
                status_code=403,
                detail="No tienes el permiso necesario (empresas:actualizar_propia)"
            )
        
        # 6. Guardar coordenadas anteriores
        coordenadas_anteriores = None
        if empresa.latitud and empresa.longitud:
            coordenadas_anteriores = {
                "latitud": float(empresa.latitud),
                "longitud": float(empresa.longitud)
            }
            logger.info(f"Coordenadas anteriores: {coordenadas_anteriores}")
        
        # 7. Determinar método de actualización
        if request.recalcular_desde_direccion:
            # ===== MODO AUTOMÁTICO: Geocodificar desde dirección =====
            logger.info(f"Modo automático: Geocodificando dirección de empresa {empresa_id}")
            
            if not empresa.direccion_id:
                raise HTTPException(
                    status_code=400,
                    detail="La empresa no tiene dirección asociada para geocodificar. Use el modo manual proporcionando latitud y longitud."
                )
            
            # Obtener dirección
            direccion = db.query(Direccion).filter(
                Direccion.direccion_id == empresa.direccion_id
            ).first()
            
            if not direccion:
                logger.error(f"Dirección {empresa.direccion_id} no encontrada")
                raise HTTPException(
                    status_code=500,
                    detail="Error interno: Dirección asociada no encontrada en la base de datos"
                )
            
            # Construir dirección para logging
            direccion_str = f"{direccion.calle}"
            if direccion.numero:
                direccion_str += f" {direccion.numero}"
            if direccion.ciudad:
                direccion_str += f", {direccion.ciudad}"
            
            logger.info(f"Geocodificando: {direccion_str}")
            
            # Geocodificar con timeout
            try:
                resultado_geocoding = await asyncio.wait_for(
                    geocoding_service.geocode_address(
                        calle=direccion.calle,
                        numero=direccion.numero,
                        ciudad=direccion.ciudad,
                        provincia=direccion.provincia,
                        codigo_postal=direccion.codigo_postal
                    ),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout geocodificando: {direccion_str}")
                raise HTTPException(
                    status_code=408,
                    detail=f"El servicio de geocodificación tardó demasiado. Intente con modo manual."
                )
            
            if not resultado_geocoding or not resultado_geocoding.get("coordinates"):
                logger.warning(f"No se pudo geocodificar: {direccion_str}")
                raise HTTPException(
                    status_code=400,
                    detail=f"No se pudo geocodificar la dirección: {direccion_str}. Use el modo manual para establecer coordenadas."
                )
            
            lat, lng = resultado_geocoding["coordinates"]
            metodo = "geocodificacion"
            
            # Guardar información de validación si existe
            if resultado_geocoding.get("validation"):
                validation = resultado_geocoding["validation"]
                empresa.geocoding_confidence = validation.get("confidence", "unknown")
                if validation.get("validation", {}).get("warning"):
                    empresa.geocoding_warning = validation["validation"]["warning"]
            
            logger.info(f"Geocodificación exitosa: ({lat}, {lng})")
            
        else:
            # ===== MODO MANUAL: Usar coordenadas proporcionadas =====
            logger.info(f"Modo manual: Actualizando coordenadas de empresa {empresa_id}")
            
            if request.latitud is None or request.longitud is None:
                raise HTTPException(
                    status_code=400,
                    detail="Debe proporcionar latitud y longitud, o activar recalcular_desde_direccion=true"
                )
            
            lat = request.latitud
            lng = request.longitud
            metodo = "manual"
            
            # Validar rango de coordenadas
            if not (-90 <= lat <= 90):
                raise HTTPException(
                    status_code=400,
                    detail=f"Latitud inválida: {lat}. Debe estar entre -90 y 90"
                )
            
            if not (-180 <= lng <= 180):
                raise HTTPException(
                    status_code=400,
                    detail=f"Longitud inválida: {lng}. Debe estar entre -180 y 180"
                )
            
            # Validar que estén dentro de Argentina
            bounds = geocoding_service.ARGENTINA_BOUNDS
            if not (bounds['lat_min'] <= lat <= bounds['lat_max'] and
                    bounds['lng_min'] <= lng <= bounds['lng_max']):
                logger.warning(f"Coordenadas fuera de Argentina: ({lat}, {lng})")
                raise HTTPException(
                    status_code=400,
                    detail=f"Las coordenadas ({lat}, {lng}) están fuera del territorio argentino. "
                           f"Rango válido: Lat {bounds['lat_min']} a {bounds['lat_max']}, "
                           f"Lng {bounds['lng_min']} a {bounds['lng_max']}"
                )
            
            # Marcar como corregido manualmente
            if request.corregido_manualmente:
                empresa.geocoding_confidence = "manual_correction"
                empresa.geocoding_warning = "Ubicación ajustada manualmente por el usuario desde el mapa"
                logger.info("Marcado como corrección manual")
        
        # 8. Actualizar empresa
        empresa.latitud = lat
        empresa.longitud = lng
        
        db.commit()
        db.refresh(empresa)
        
        logger.info(
            f"Coordenadas actualizadas exitosamente para empresa {empresa_id}: "
            f"({lat}, {lng}) [método: {metodo}]"
        )
        
        # 9. Construir respuesta
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
    except ValueError as e:
        db.rollback()
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Datos inválidos: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error inesperado actualizando coordenadas empresa {empresa_id}: {str(e)}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al actualizar coordenadas. Por favor, intente nuevamente."
        )
@router.post("/empresas/buscar-por-ubicacion", response_model=ResultadoBusquedaGeografica)
async def buscar_empresas_por_ubicacion(
    busqueda: BusquedaPorDireccion,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca empresas cercanas a una dirección proporcionada en el body.
    
    **Ventajas del POST vs GET:**
    - Mejor para datos estructurados complejos
    - No expone datos sensibles en la URL
    - Más fácil de extender con nuevos filtros
    
    **Proceso:**
    1. Geocodifica la dirección del body
    2. Busca empresas en el radio especificado
    3. Retorna empresas ordenadas por distancia
    
    **Validaciones:**
    - Dirección debe poder geocodificarse
    - Radio entre 0.1 y 100 km
    - Categoría existe (si se proporciona)
    - Timeout de 10 segundos para geocodificación
    
    **Errores posibles:**
    - 400: Dirección no geocodificable, categoría no existe
    - 408: Timeout de servicio de geocodificación
    - 422: Validación de datos fallida
    - 500: Error de base de datos o servicio
    
    **Ejemplo de body:**
    ```json
    {
        "direccion": {
            "calle": "Av Corrientes",
            "numero": "1000",
            "ciudad": "CABA",
            "provincia": "Buenos Aires"
        },
        "radio_km": 5,
        "categoria_id": 1
    }
    ```
    """
    try:
        # 1. Validar que la categoría existe (si se proporciona)
        if busqueda.categoria_id is not None:
            categoria = db.query(Categoria).filter(
                Categoria.categoria_id == busqueda.categoria_id
            ).first()
            
            if not categoria:
                raise HTTPException(
                    status_code=400,
                    detail=f"Categoría con ID {busqueda.categoria_id} no existe"
                )
            
            logger.info(f"Búsqueda POST con filtro de categoría: {categoria.nombre}")
        
        # 2. Construir dirección legible para logging
        dir_data = busqueda.direccion
        direccion_str = f"{dir_data.calle}"
        if dir_data.numero:
            direccion_str += f" {dir_data.numero}"
        if dir_data.ciudad:
            direccion_str += f", {dir_data.ciudad}"
        if dir_data.provincia:
            direccion_str += f", {dir_data.provincia}"
        
        logger.info(f"POST - Geocodificando dirección: {direccion_str}")
        
        # 3. Geocodificar con timeout de 10 segundos
        try:
            resultado_geocoding = await asyncio.wait_for(
                geocoding_service.geocode_address(
                    calle=dir_data.calle,
                    numero=dir_data.numero,
                    ciudad=dir_data.ciudad,
                    provincia=dir_data.provincia,
                    codigo_postal=dir_data.codigo_postal
                ),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout al geocodificar: {direccion_str}")
            raise HTTPException(
                status_code=408,
                detail="El servicio de geocodificación tardó demasiado. Por favor, intente nuevamente."
            )
        
        # 4. Verificar resultado válido
        if not resultado_geocoding:
            logger.warning(f"No se obtuvo resultado al geocodificar: {direccion_str}")
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo encontrar la dirección: {direccion_str}"
            )
        
        if not resultado_geocoding.get("coordinates"):
            logger.warning(f"Geocodificación sin coordenadas: {direccion_str}")
            raise HTTPException(
                status_code=400,
                detail=f"La dirección '{direccion_str}' no pudo ser localizada en el mapa. Verifique los datos ingresados."
            )
        
        # 5. Extraer coordenadas
        try:
            lat, lng = resultado_geocoding["coordinates"]
            logger.info(f"POST - Dirección geocodificada: ({lat}, {lng})")
        except (ValueError, TypeError) as e:
            logger.error(f"Error extrayendo coordenadas: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error procesando las coordenadas de la dirección"
            )
        
        # 6. Buscar empresas cercanas
        logger.info(f"Buscando empresas en radio {busqueda.radio_km}km")
        
        empresas_encontradas = geolocation_service.find_nearby_empresas(
            db=db,
            latitud=lat,
            longitud=lng,
            radio_km=busqueda.radio_km,
            categoria_id=busqueda.categoria_id,
            limit=50
        )
        
        # 7. Construir respuesta
        if not empresas_encontradas:
            logger.info(f"No hay empresas cerca de {direccion_str} en {busqueda.radio_km}km")
            return ResultadoBusquedaGeografica(
                punto_busqueda=GeoLocation(latitud=lat, longitud=lng),
                radio_km=busqueda.radio_km,
                total_encontradas=0,
                empresas=[]
            )
        
        # 8. Convertir a schema
        empresas_response = []
        for emp in empresas_encontradas:
            try:
                if not emp.get("latitud") or not emp.get("longitud"):
                    logger.warning(f"Empresa {emp.get('empresa_id')} sin coordenadas, omitiendo")
                    continue
                
                empresas_response.append(
                    EmpresaConDistancia(
                        empresa_id=emp["empresa_id"],
                        razon_social=emp["nombre"],
                        descripcion=emp.get("descripcion", ""),
                        categoria_id=emp["categoria_id"],
                        coordenadas=GeoLocation(
                            latitud=emp["latitud"],
                            longitud=emp["longitud"]
                        ),
                        distancia_km=emp["distancia_km"],
                        activa=True
                    )
                )
            except (KeyError, ValueError) as e:
                logger.error(f"Error procesando empresa: {str(e)}")
                continue
        
        logger.info(f"POST - Encontradas {len(empresas_response)} empresas cerca de {direccion_str}")
        
        return ResultadoBusquedaGeografica(
            punto_busqueda=GeoLocation(latitud=lat, longitud=lng),
            radio_km=busqueda.radio_km,
            total_encontradas=len(empresas_response),
            empresas=empresas_response
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación en POST búsqueda: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Datos inválidos: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado en POST búsqueda por ubicación: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor. Por favor, intente nuevamente."
        )