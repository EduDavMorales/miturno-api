# app/routers/geo_test.py
# -*- coding: utf-8 -*-
# ENDPOINT TEMPORAL PARA PROBAR GEOCODIFICACION

from fastapi import APIRouter, HTTPException
from app.services.geocoding_service_new import geocoding_service, GeocodingServiceError
from app.schemas.geo import (
    DireccionGeocode, 
    DireccionGeocodeResponse, 
    GeoLocation,
    ReverseGeocodeRequest
)
from typing import Optional

router = APIRouter()

@router.post("/geocode", response_model=DireccionGeocodeResponse)
async def test_geocode_direccion(direccion: DireccionGeocode):
    """
    ENDPOINT DE PRUEBA - Geocodificar una direccion argentina CON VALIDACION
    
    Ejemplos para probar:
    - Av. Corrientes 1000, Ciudad Autonoma de Buenos Aires
    - Cabildo 2000, Vicente Lopez, Buenos Aires  
    - San Martin 500, Quilmes, Buenos Aires
    """
    try:
        # Llamar al servicio de geocodificacion (ahora retorna Dict)
        resultado = await geocoding_service.geocode_address(
            calle=direccion.calle,
            numero=direccion.numero,
            ciudad=direccion.ciudad,
            provincia=direccion.provincia,
            codigo_postal=direccion.codigo_postal
        )
        
        if resultado:
            # Extraer coordenadas del Dict
            coords = resultado['coordinates']
            validation = resultado.get('validation')
            
            # Verificar si la validacion indica problema
            is_safe = True
            error_msg = None
            
            if validation:
                is_safe = validation.get('safe_to_use', True)
                
                # Si no es seguro usar, agregar warning
                if not is_safe:
                    val_details = validation.get('validation', {})
                    error_msg = val_details.get('warning', 'Coordenadas sospechosas')
                    
                    # Agregar sugerencia si existe
                    if val_details.get('suggestion'):
                        error_msg += f" - {val_details['suggestion']}"
            
            return DireccionGeocodeResponse(
                direccion_original=direccion,
                coordenadas=GeoLocation(
                    latitud=coords[0],
                    longitud=coords[1]
                ),
                valida=is_safe,
                error=error_msg if not is_safe else None
            )
        else:
            return DireccionGeocodeResponse(
                direccion_original=direccion,
                valida=False,
                error="No se pudo geocodificar la direccion"
            )
            
    except GeocodingServiceError as e:
        return DireccionGeocodeResponse(
            direccion_original=direccion,
            valida=False,
            error=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/reverse-geocode")
async def test_reverse_geocode(request: ReverseGeocodeRequest):
    """
    ENDPOINT DE PRUEBA - Geocodificacion inversa (coordenadas -> direccion)
    
    Ejemplos para probar:
    - lat: -34.6037, lng: -58.3816 (Obelisco, Buenos Aires)
    - lat: -34.7226, lng: -58.2664 (Quilmes)
    """
    try:
        resultado = await geocoding_service.reverse_geocode(
            lat=request.latitud,
            lng=request.longitud
        )
        
        if resultado:
            return {
                "coordenadas_originales": {
                    "latitud": request.latitud,
                    "longitud": request.longitud
                },
                "direccion_encontrada": resultado,
                "exitoso": True
            }
        else:
            return {
                "coordenadas_originales": {
                    "latitud": request.latitud,
                    "longitud": request.longitud
                },
                "direccion_encontrada": None,
                "exitoso": False,
                "error": "No se encontro direccion para estas coordenadas"
            }
            
    except GeocodingServiceError as e:
        return {
            "coordenadas_originales": {
                "latitud": request.latitud,
                "longitud": request.longitud
            },
            "exitoso": False,
            "error": str(e)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/test-examples")
async def get_test_examples():
    """
    Ejemplos de direcciones argentinas para probar
    """
    return {
        "mensaje": "Ejemplos de direcciones argentinas para testear",
        "ejemplos_geocoding": [
            {
                "descripcion": "Obelisco - CABA",
                "direccion": {
                    "calle": "Av. Corrientes",
                    "numero": "1000", 
                    "ciudad": "Ciudad Autonoma de Buenos Aires",
                    "provincia": "Ciudad Autonoma de Buenos Aires"
                }
            },
            {
                "descripcion": "Quilmes Centro",
                "direccion": {
                    "calle": "Rivadavia",
                    "numero": "350",
                    "ciudad": "Quilmes",
                    "provincia": "Buenos Aires"  
                }
            },
            {
                "descripcion": "Rosario - Santa Fe",
                "direccion": {
                    "calle": "San Lorenzo",
                    "numero": "1234",
                    "ciudad": "Rosario", 
                    "provincia": "Santa Fe"
                }
            }
        ],
        "ejemplos_reverse_geocoding": [
            {
                "descripcion": "Obelisco",
                "coordenadas": {
                    "latitud": -34.6037,
                    "longitud": -58.3816
                }
            },
            {
                "descripcion": "Quilmes Centro",
                "coordenadas": {
                    "latitud": -34.7226,
                    "longitud": -58.2664
                }
            }
        ],
        "instrucciones": [
            "1. Usa POST /api/v1/geo-test/geocode para probar geocodificacion",
            "2. Usa POST /api/v1/geo-test/reverse-geocode para geocodificacion inversa", 
            "3. Los ejemplos de arriba estan listos para copy-paste"
        ]
    }