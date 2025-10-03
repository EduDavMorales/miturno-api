# app/services/geo_validation_service.py

import logging
from typing import Tuple, Optional, Dict, Any
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)

class GeoValidationService:
    """
    Servicio para validar resultados de geocodificacion.
    Detecta inconsistencias y errores en coordenadas devueltas.
    """
    
    # Centros aproximados de ciudades principales del Gran Buenos Aires
    CITY_CENTERS = {
        # CABA
        "ciudad autonoma de buenos aires": (-34.6037, -58.3816),
        "caba": (-34.6037, -58.3816),
        "capital federal": (-34.6037, -58.3816),
        
        # Zona Sur
        "avellaneda": (-34.6612, -58.3667),
        "lanus": (-34.7004, -58.3955),
        "lomas de zamora": (-34.7593, -58.4065),
        "quilmes": (-34.7203, -58.2663),
        "berazategui": (-34.7635, -58.2125),
        "florencio varela": (-34.7960, -58.2750),
        "almirante brown": (-34.8152, -58.3977),
        "esteban echeverria": (-34.8167, -58.4667),
        "monte grande": (-34.8167, -58.4667),
        "adrogue": (-34.8000, -58.3833),
        
        # Zona Norte
        "san isidro": (-34.4708, -58.5127),
        "vicente lopez": (-34.5267, -58.4833),
        "san fernando": (-34.4400, -58.5592),
        "tigre": (-34.4261, -58.5797),
        "san miguel": (-34.5417, -58.7083),
        
        # Zona Oeste
        "moron": (-34.6533, -58.6197),
        "la matanza": (-34.7000, -58.6333),
        "tres de febrero": (-34.6000, -58.5667),
        "hurlingham": (-34.5897, -58.6367),
        "ituzaingo": (-34.6597, -58.6731),
        "merlo": (-34.6667, -58.7333),
        "moreno": (-34.6500, -58.7833),
        
        # Localidades especificas
        "san antonio de padua": (-34.6717, -58.6983),
        "luis guillon": (-34.8000, -58.4500),
    }
    
    # Radio maximo aceptable desde centro de ciudad (en km)
    MAX_DISTANCE_FROM_CENTER = 15  # 15km
    
    def __init__(self):
        pass
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calcula distancia entre dos puntos usando formula de Haversine.
        
        Args:
            lat1, lon1: Coordenadas del primer punto
            lat2, lon2: Coordenadas del segundo punto
            
        Returns:
            Distancia en kilometros
        """
        # Convertir a radianes
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Formula de Haversine
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radio de la Tierra en km
        r = 6371
        
        return c * r
    
    def normalize_city_name(self, ciudad: str) -> str:
        """
        Normaliza nombre de ciudad para busqueda.
        """
        if not ciudad:
            return ""
        
        # Convertir a minusculas
        normalized = ciudad.lower().strip()
        
        # Usar metodo simple sin caracteres especiales
        import unicodedata
        normalized = ''.join(
            c for c in unicodedata.normalize('NFD', normalized)
            if unicodedata.category(c) != 'Mn'
        )
        
        return normalized
    
    def validate_coordinates_for_city(self, lat: float, lng: float, 
                                     ciudad: str, 
                                     provincia: str) -> Dict[str, Any]:
        """
        Valida que coordenadas correspondan a la ciudad esperada.
        
        Args:
            lat: Latitud
            lng: Longitud
            ciudad: Ciudad esperada
            provincia: Provincia esperada
            
        Returns:
            Dict con resultado de validacion
        """
        # Normalizar nombre de ciudad
        ciudad_normalized = self.normalize_city_name(ciudad)
        
        # Buscar centro de la ciudad
        city_center = self.CITY_CENTERS.get(ciudad_normalized)
        
        if not city_center:
            # Ciudad no en base de datos - no podemos validar
            return {
                "valid": None,
                "warning": f"Ciudad '{ciudad}' no esta en base de validacion",
                "distance_km": None,
                "requires_manual_review": True
            }
        
        # Calcular distancia desde centro de ciudad
        distance_km = self.calculate_distance(
            lat, lng, 
            city_center[0], city_center[1]
        )
        
        # Validar distancia
        is_valid = distance_km <= self.MAX_DISTANCE_FROM_CENTER
        
        result = {
            "valid": is_valid,
            "distance_from_center_km": round(distance_km, 2),
            "city_center": city_center,
            "max_distance_km": self.MAX_DISTANCE_FROM_CENTER
        }
        
        if not is_valid:
            result["warning"] = (
                f"Coordenadas a {distance_km:.1f}km del centro de {ciudad}. "
                f"Maximo aceptable: {self.MAX_DISTANCE_FROM_CENTER}km"
            )
            result["requires_manual_review"] = True
            
            # Buscar ciudad mas cercana
            closest_city = self.find_closest_city(lat, lng)
            if closest_city:
                result["closest_city"] = closest_city
                result["suggestion"] = (
                    f"Las coordenadas parecen estar en {closest_city['name']} "
                    f"({closest_city['distance_km']:.1f}km del centro)"
                )
        
        return result
    
    def find_closest_city(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        Encuentra la ciudad mas cercana a las coordenadas dadas.
        
        Args:
            lat: Latitud
            lng: Longitud
            
        Returns:
            Dict con info de ciudad mas cercana o None
        """
        closest_city = None
        min_distance = float('inf')
        
        for city_name, (city_lat, city_lng) in self.CITY_CENTERS.items():
            distance = self.calculate_distance(lat, lng, city_lat, city_lng)
            
            if distance < min_distance:
                min_distance = distance
                closest_city = {
                    "name": city_name,
                    "distance_km": round(distance, 2),
                    "coordinates": (city_lat, city_lng)
                }
        
        return closest_city
    
    def validate_geocoding_result(self, 
                                 coordenadas: Tuple[float, float],
                                 direccion_input: Dict[str, str]) -> Dict[str, Any]:
        """
        Validacion completa de resultado de geocodificacion.
        
        Args:
            coordenadas: Tupla (lat, lng)
            direccion_input: Dict con calle, ciudad, provincia original
            
        Returns:
            Dict con resultado completo de validacion
        """
        lat, lng = coordenadas
        ciudad = direccion_input.get('ciudad', '')
        provincia = direccion_input.get('provincia', '')
        
        # Validar coordenadas para ciudad
        city_validation = self.validate_coordinates_for_city(
            lat, lng, ciudad, provincia
        )
        
        result = {
            "coordinates": {"latitud": lat, "longitud": lng},
            "input_city": ciudad,
            "validation": city_validation
        }
        
        # Determinar nivel de confianza
        if city_validation.get("valid") is True:
            result["confidence"] = "high"
            result["safe_to_use"] = True
        elif city_validation.get("valid") is False:
            result["confidence"] = "low"
            result["safe_to_use"] = False
        else:
            result["confidence"] = "medium"
            result["safe_to_use"] = True
            result["note"] = "Ciudad no validable - usar con precaucion"
        
        logger.info(f"Validacion: {ciudad} -> Confianza: {result['confidence']}")
        
        return result


# Instancia singleton
geo_validation_service = GeoValidationService()