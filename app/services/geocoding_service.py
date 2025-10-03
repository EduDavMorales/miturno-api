# app/services/geocoding_service.py

import httpx
import logging
from typing import Optional, Dict, Any, Tuple
from app.config import settings
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class GeocodingServiceError(Exception):
    """Excepción personalizada para errores de geocodificación"""
    pass

class GeocodingService:
    """
    Servicio para geocodificación usando la API oficial Georef de Argentina.
    
    Responsabilidades:
    - Geocodificar direcciones argentinas a coordenadas lat/lng
    - Normalizar direcciones según estándares oficiales
    - Validar coordenadas dentro de territorio argentino  
    - Manejar errores y reintentos de forma robusta
    """
    
    # API oficial del Estado Argentino - INDEC
    GEOREF_BASE_URL = "https://apis.datos.gob.ar/georef/api"
    
    # Límites geográficos aproximados de Argentina
    ARGENTINA_BOUNDS = {
        'lat_min': -55.1,    # Tierra del Fuego
        'lat_max': -21.8,    # Frontera norte
        'lng_min': -73.6,    # Frontera oeste
        'lng_max': -53.6     # Frontera este
    }
    
    def __init__(self):
        self.timeout = httpx.Timeout(10.0)  # 10 segundos timeout
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza petición HTTP con reintentos automáticos.
        
        Args:
            url: URL del endpoint
            params: Parámetros de la consulta
            
        Returns:
            Dict con la respuesta JSON
            
        Raises:
            GeocodingServiceError: Si la petición falla después de los reintentos
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con Georef API: {e}")
            raise GeocodingServiceError(f"Error de conexión: {str(e)}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP {e.response.status_code} con Georef API: {e}")
            raise GeocodingServiceError(f"Error HTTP {e.response.status_code}")
            
        except Exception as e:
            logger.error(f"Error inesperado en geocodificación: {e}")
            raise GeocodingServiceError(f"Error inesperado: {str(e)}")
    
    def _validate_coordinates(self, lat: float, lng: float) -> bool:
        """
        Valida que las coordenadas estén dentro de Argentina.
        
        Args:
            lat: Latitud
            lng: Longitud
            
        Returns:
            True si las coordenadas son válidas para Argentina
        """
        bounds = self.ARGENTINA_BOUNDS
        return (bounds['lat_min'] <= lat <= bounds['lat_max'] and
                bounds['lng_min'] <= lng <= bounds['lng_max'])
    
    def _build_address_string(self, calle: str, numero: Optional[str] = None, 
                            ciudad: str = None, provincia: str = None) -> str:
        """
        Construye string de dirección para geocodificación.
        
        Args:
            calle: Nombre de la calle
            numero: Número de la dirección
            ciudad: Ciudad/localidad
            provincia: Provincia
            
        Returns:
            String de dirección formateada
        """
        parts = []
        
        # Calle y número
        if calle:
            if numero:
                parts.append(f"{calle.strip()} {numero.strip()}")
            else:
                parts.append(calle.strip())
        
        # Ciudad
        if ciudad:
            parts.append(ciudad.strip())
            
        # Provincia  
        if provincia:
            parts.append(provincia.strip())
            
        return ", ".join(parts)
    
    async def geocode_address(self, calle: str, numero: Optional[str] = None,
                            ciudad: Optional[str] = None, provincia: Optional[str] = None,
                            codigo_postal: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """
        Geocodifica una dirección argentina a coordenadas lat/lng.
        
        Args:
            calle: Nombre de la calle
            numero: Número de la dirección
            ciudad: Ciudad/localidad
            provincia: Provincia
            codigo_postal: Código postal
            
        Returns:
            Tupla (latitud, longitud) o None si no se puede geocodificar
            
        Raises:
            GeocodingServiceError: Si hay error en la geocodificación
        """
        try:
            # Construir parámetros para la API
            params = {
                'direccion': self._build_address_string(calle, numero, ciudad, provincia),
                'formato': 'json',
                'campos': 'basico'
            }
            
            # Agregar provincia si está disponible para mejor precisión
            if provincia:
                params['provincia'] = provincia
                
            # Agregar código postal si está disponible
            if codigo_postal:
                params['cp'] = codigo_postal
            
            logger.info(f"Geocodificando dirección: {params['direccion']}")
            
            # Realizar petición a Georef
            url = f"{self.GEOREF_BASE_URL}/direcciones"
            
            # LOGGING DETALLADO - TEMPORAL
            logger.info(f"URL completa: {url}")
            logger.info(f"Parámetros enviados: {params}")
            
            data = await self._make_request(url, params)
            
            logger.info(f"Respuesta completa de Georef: {data}")
            logger.info(f"¿Tiene 'direcciones'? {bool(data.get('direcciones'))}")
            
            # Verificar respuesta
            if not data.get('direcciones'):
                logger.warning(f"No se encontraron resultados para: {params['direccion']}")
                return None
            
            if data.get('direcciones'):
                logger.info(f"Primera dirección encontrada: {data['direcciones'][0]}")
                
            # Tomar el primer resultado (más relevante)
            direccion_resultado = data['direcciones'][0]
            
            # Extraer coordenadas
            ubicacion = direccion_resultado.get('ubicacion', {})
            lat = ubicacion.get('lat')
            lng = ubicacion.get('lon')
            
            logger.info(f"Coordenadas extraídas - lat: {lat}, lng: {lng}")
            
            if lat is None or lng is None:
                logger.warning(f"Coordenadas no disponibles para: {params['direccion']}")
                return None
                
            # Convertir a float y validar
            lat_float = float(lat)
            lng_float = float(lng)
            
            logger.info(f"Coordenadas convertidas - lat: {lat_float}, lng: {lng_float}")
            
            if not self._validate_coordinates(lat_float, lng_float):
                logger.warning(f"Coordenadas fuera de Argentina: {lat_float}, {lng_float}")
                return None
            
            logger.info(f"Geocodificación exitosa: ({lat_float}, {lng_float})")
            return (lat_float, lng_float)
            
        except GeocodingServiceError:
            # Re-raise errores específicos del servicio
            raise
            
        except Exception as e:
            logger.error(f"Error inesperado en geocode_address: {e}")
            raise GeocodingServiceError(f"Error en geocodificación: {str(e)}")
    
    async def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict[str, str]]:
        """
        Geocodificación inversa: coordenadas a dirección.
        
        Args:
            lat: Latitud
            lng: Longitud
            
        Returns:
            Dict con información de la dirección o None
        """
        try:
            if not self._validate_coordinates(lat, lng):
                logger.warning(f"Coordenadas fuera de Argentina: {lat}, {lng}")
                return None
                
            params = {
                'lat': lat,
                'lon': lng,
                'formato': 'json'
            }
            
            # URL CORRECTA para geocodificación inversa
            url = f"{self.GEOREF_BASE_URL}/ubicacion"
            data = await self._make_request(url, params)
            
            if not data.get('ubicacion'):
                return None
                
            ubicacion = data['ubicacion']
            return {
                'calle': ubicacion.get('calle', ''),
                'numero': str(ubicacion.get('altura', '')),
                'ciudad': ubicacion.get('localidad', ''),
                'provincia': ubicacion.get('provincia', ''),
                'codigo_postal': ubicacion.get('codigo_postal', '')
            }
            
        except Exception as e:
            logger.error(f"Error en reverse_geocode: {e}")
            raise GeocodingServiceError(f"Error en geocodificación inversa: {str(e)}")
    
    async def validate_argentina_address(self, calle: str, ciudad: str, 
                                       provincia: str) -> Dict[str, Any]:
        """
        Valida y normaliza una dirección argentina.
        
        Args:
            calle: Nombre de la calle
            ciudad: Ciudad/localidad
            provincia: Provincia
            
        Returns:
            Dict con información de validación y dirección normalizada
        """
        try:
            # Normalizar provincia
            params = {
                'provincia': provincia,
                'formato': 'json',
                'campos': 'basico'
            }
            
            url = f"{self.GEOREF_BASE_URL}/provincias"
            data = await self._make_request(url, params)
            
            if not data.get('provincias'):
                return {
                    'valida': False,
                    'error': f'Provincia no encontrada: {provincia}'
                }
            
            provincia_normalizada = data['provincias'][0]['nombre']
            
            # Normalizar localidad
            params = {
                'localidad': ciudad,
                'provincia': provincia_normalizada,
                'formato': 'json',
                'campos': 'basico'
            }
            
            url = f"{self.GEOREF_BASE_URL}/localidades"
            data = await self._make_request(url, params)
            
            if not data.get('localidades'):
                return {
                    'valida': False,
                    'error': f'Ciudad no encontrada: {ciudad}'
                }
            
            ciudad_normalizada = data['localidades'][0]['nombre']
            
            return {
                'valida': True,
                'direccion_normalizada': {
                    'calle': calle.title(),
                    'ciudad': ciudad_normalizada,
                    'provincia': provincia_normalizada
                }
            }
            
        except Exception as e:
            logger.error(f"Error en validate_argentina_address: {e}")
            return {
                'valida': False,
                'error': f'Error en validación: {str(e)}'
            }

# Instancia singleton del servicio
geocoding_service = GeocodingService()