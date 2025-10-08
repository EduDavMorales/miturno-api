from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import math
from app.models.empresa import Empresa
from app.models.categoria import Categoria

class GeolocationService:
    """
    Servicio para búsqueda geográfica de empresas.
    Utiliza la fórmula de Haversine para calcular distancias.
    """
    
    # Radio de la Tierra en kilómetros
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def calculate_distance(
        lat1: float, 
        lng1: float, 
        lat2: float, 
        lng2: float
    ) -> float:
        """
        Calcula la distancia entre dos puntos geográficos usando Haversine.
        
        Args:
            lat1, lng1: Coordenadas del primer punto
            lat2, lng2: Coordenadas del segundo punto
            
        Returns:
            float: Distancia en kilómetros
        """
        # Convertir grados a radianes
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lng1_rad = math.radians(lng1)
        lng2_rad = math.radians(lng2)
        
        # Diferencias
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        # Fórmula de Haversine
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = GeolocationService.EARTH_RADIUS_KM * c
        return round(distance, 2)
    
    @staticmethod
    def get_bounding_box(
        lat: float, 
        lng: float, 
        radio_km: float
    ) -> Tuple[float, float, float, float]:
        """
        Calcula el bounding box (caja delimitadora) para optimizar la búsqueda.
        
        Args:
            lat, lng: Coordenadas del centro
            radio_km: Radio de búsqueda en km
            
        Returns:
            Tuple: (min_lat, max_lat, min_lng, max_lng)
        """
        # Aproximación: 1 grado de latitud ≈ 111 km
        # 1 grado de longitud varía según la latitud
        lat_degree_km = 111.0
        lng_degree_km = 111.0 * math.cos(math.radians(lat))
        
        delta_lat = radio_km / lat_degree_km
        delta_lng = radio_km / lng_degree_km
        
        min_lat = lat - delta_lat
        max_lat = lat + delta_lat
        min_lng = lng - delta_lng
        max_lng = lng + delta_lng
        
        return (min_lat, max_lat, min_lng, max_lng)
    
    @staticmethod
    def find_nearby_empresas(
        db: Session,
        latitud: float,
        longitud: float,
        radio_km: float = 10.0,
        categoria_id: Optional[int] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        Busca empresas cercanas a una ubicación.
        
        Args:
            db: Sesión de base de datos
            latitud, longitud: Coordenadas del punto de búsqueda
            radio_km: Radio de búsqueda en kilómetros (default: 10)
            categoria_id: ID de categoría para filtrar (opcional)
            limit: Máximo número de resultados (default: 50)
            
        Returns:
            List[dict]: Lista de empresas con distancia calculada
        """
        # Calcular bounding box para optimizar query
        min_lat, max_lat, min_lng, max_lng = GeolocationService.get_bounding_box(
            latitud, longitud, radio_km
        )
        
        # Query base: empresas activas con coordenadas dentro del bounding box
        query = db.query(Empresa).filter(
            and_(
                Empresa.activa == True,
                Empresa.latitud.isnot(None),
                Empresa.longitud.isnot(None),
                Empresa.latitud.between(min_lat, max_lat),
                Empresa.longitud.between(min_lng, max_lng)
            )
        )
        
        # Filtrar por categoría si se especifica
        if categoria_id:
            query = query.filter(Empresa.categoria_id == categoria_id)
        
        # Ejecutar query
        empresas = query.all()
        
        # Calcular distancia exacta y filtrar por radio
        resultados = []
        for empresa in empresas:
            distancia = GeolocationService.calculate_distance(
                latitud, longitud,
                float(empresa.latitud), float(empresa.longitud)
            )
            
            # Solo incluir si está dentro del radio
            if distancia <= radio_km:
                resultados.append({
                    "empresa_id": empresa.empresa_id,
                    "nombre": empresa.razon_social,
                    "descripcion": empresa.descripcion,
                    "latitud": float(empresa.latitud),
                    "longitud": float(empresa.longitud),
                    "distancia_km": distancia,
                    "categoria_id": empresa.categoria_id,
                })
        
        # Ordenar por distancia (más cercano primero)
        resultados.sort(key=lambda x: x["distancia_km"])
        
        # Limitar resultados
        return resultados[:limit]
    
    @staticmethod
    def get_empresas_in_bounds(
        db: Session,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float
    ) -> List[Empresa]:
        """
        Obtiene todas las empresas dentro de un área rectangular.
        Útil para mostrar en mapas.
        
        Args:
            db: Sesión de base de datos
            min_lat, max_lat: Rango de latitudes
            min_lng, max_lng: Rango de longitudes
            
        Returns:
            List[Empresa]: Empresas dentro del área
        """
        return db.query(Empresa).filter(
            and_(
                Empresa.activo == True,
                Empresa.latitud.isnot(None),
                Empresa.longitud.isnot(None),
                Empresa.latitud.between(min_lat, max_lat),
                Empresa.longitud.between(min_lng, max_lng)
            )
        ).all()


# Instancia singleton del servicio
geolocation_service = GeolocationService()