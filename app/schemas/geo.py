# app/schemas/geo.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict 
from decimal import Decimal

class GeoLocation(BaseModel):
    """Coordenadas geográficas"""
    latitud: float = Field(..., ge=-90, le=90, description="Latitud en grados decimales")
    longitud: float = Field(..., ge=-180, le=180, description="Longitud en grados decimales")
    
    @validator('latitud')
    def validate_latitud_argentina(cls, v):
        """Valida que la latitud esté dentro de Argentina"""
        if not (-55.1 <= v <= -21.8):
            raise ValueError('Latitud fuera de territorio argentino')
        return v
    
    @validator('longitud') 
    def validate_longitud_argentina(cls, v):
        """Valida que la longitud esté dentro de Argentina"""
        if not (-73.6 <= v <= -53.6):
            raise ValueError('Longitud fuera de territorio argentino')
        return v

class DireccionGeocode(BaseModel):
    """Request para geocodificar una dirección"""
    calle: str = Field(..., min_length=1, max_length=200, description="Nombre de la calle")
    numero: Optional[str] = Field(None, max_length=10, description="Número de la dirección")
    ciudad: Optional[str] = Field(None, max_length=100, description="Ciudad o localidad")
    provincia: Optional[str] = Field(None, max_length=100, description="Provincia")
    codigo_postal: Optional[str] = Field(None, max_length=10, description="Código postal")

class DireccionGeocodeResponse(BaseModel):
    """Response de geocodificación exitosa"""
    direccion_original: DireccionGeocode
    coordenadas: Optional[GeoLocation] = None
    direccion_normalizada: Optional[Dict[str, str]] = None
    valida: bool = Field(default=False, description="Si la dirección fue geocodificada exitosamente")
    error: Optional[str] = Field(None, description="Mensaje de error si falló la geocodificación")

class BusquedaGeografica(BaseModel):
    """Parámetros para búsqueda geográfica de empresas"""
    latitud: float = Field(..., ge=-90, le=90, description="Latitud del punto de búsqueda")
    longitud: float = Field(..., ge=-180, le=180, description="Longitud del punto de búsqueda") 
    radio_km: float = Field(10, ge=0.1, le=100, description="Radio de búsqueda en kilómetros")
    categoria_id: Optional[int] = Field(None, description="ID de categoría para filtrar")
    
    @validator('latitud')
    def validate_latitud_argentina(cls, v):
        if not (-55.1 <= v <= -21.8):
            raise ValueError('Latitud fuera de territorio argentino')
        return v
    
    @validator('longitud')
    def validate_longitud_argentina(cls, v):
        if not (-73.6 <= v <= -53.6):
            raise ValueError('Longitud fuera de territorio argentino')
        return v

class BusquedaPorDireccion(BaseModel):
    """Búsqueda de empresas cerca de una dirección"""
    direccion: DireccionGeocode
    radio_km: float = Field(10, ge=0.1, le=100, description="Radio de búsqueda en kilómetros")
    categoria_id: Optional[int] = Field(None, description="ID de categoría para filtrar")

class EmpresaConDistancia(BaseModel):
    """Empresa con información de distancia"""
    empresa_id: int
    razon_social: str
    descripcion: Optional[str] = None
    categoria_id: int
    categoria_nombre: Optional[str] = None
    direccion: Optional[Dict[str, str]] = None
    coordenadas: Optional[GeoLocation] = None
    distancia_km: Optional[float] = Field(None, description="Distancia en kilómetros")
    duracion_turno_minutos: Optional[int] = None
    logo_url: Optional[str] = None
    activa: bool = True

class ResultadoBusquedaGeografica(BaseModel):
    """Resultado de búsqueda geográfica"""
    punto_busqueda: GeoLocation
    radio_km: float
    total_encontradas: int
    empresas: List[EmpresaConDistancia]
    
class ReverseGeocodeRequest(BaseModel):
    """Request para geocodificación inversa"""
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    
    @validator('latitud')
    def validate_latitud_argentina(cls, v):
        if not (-55.1 <= v <= -21.8):
            raise ValueError('Latitud fuera de territorio argentino')
        return v
    
    @validator('longitud')
    def validate_longitud_argentina(cls, v):
        if not (-73.6 <= v <= -53.6):
            raise ValueError('Longitud fuera de territorio argentino')
        return v

class ValidacionDireccion(BaseModel):
    """Request para validar una dirección argentina"""
    calle: str = Field(..., min_length=1, max_length=200)
    ciudad: str = Field(..., min_length=1, max_length=100)
    provincia: str = Field(..., min_length=1, max_length=100)

class ValidacionDireccionResponse(BaseModel):
    """Response de validación de dirección"""
    valida: bool
    direccion_normalizada: Optional[Dict[str, str]] = None
    error: Optional[str] = None

class UpdateCoordinatesRequest(BaseModel):
    """Request para actualizar coordenadas de una empresa"""
    empresa_id: int
    forzar_actualizacion: bool = Field(False, description="Forzar actualización aunque ya tenga coordenadas")

class UpdateCoordinatesResponse(BaseModel):
    """Response de actualización de coordenadas"""
    empresa_id: int
    coordenadas_anteriores: Optional[GeoLocation] = None
    coordenadas_nuevas: Optional[GeoLocation] = None
    actualizado: bool
    error: Optional[str] = None
    
class ActualizarCoordenadasRequest(BaseModel):
    """Request para actualizar coordenadas de empresa"""
    latitud: Optional[float] = Field(None, ge=-90, le=90, description="Latitud")
    longitud: Optional[float] = Field(None, ge=-180, le=180, description="Longitud")
    recalcular_desde_direccion: bool = Field(False, description="Si es True, geocodifica desde la dirección asociada")
    corregido_manualmente: bool = Field(False, description="Si es True, indica que el usuario ajustó desde el mapa")

class ActualizarCoordenadasResponse(BaseModel):
    """Response de actualización de coordenadas"""
    success: bool
    message: str
    empresa_id: int
    coordenadas_anteriores: Optional[dict] = None
    coordenadas_nuevas: dict
    metodo: str  # 'manual' o 'geocodificacion'