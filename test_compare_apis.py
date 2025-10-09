# test_compare_apis.py
# Script para comparar Georef vs Nominatim en direcciones del AMBA

import httpx
import asyncio
from typing import Optional, Tuple, Dict, Any
from math import radians, cos, sin, asin, sqrt
import time

class GeocodingComparison:
    """Compara resultados de Georef y Nominatim"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(10.0)
        self.last_nominatim_request = 0
        
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calcula distancia en km usando Haversine"""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return c * 6371  # Radio de la Tierra en km
    
    async def geocode_georef(self, direccion: str, provincia: str = "Buenos Aires") -> Optional[Tuple[float, float]]:
        """Geocodifica usando API Georef"""
        url = "https://apis.datos.gob.ar/georef/api/direcciones"
        params = {
            'direccion': direccion,
            'provincia': provincia,
            'formato': 'json',
            'campos': 'completo'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get('direcciones'):
                    ubicacion = data['direcciones'][0].get('ubicacion', {})
                    lat = ubicacion.get('lat')
                    lon = ubicacion.get('lon')
                    if lat and lon:
                        return (float(lat), float(lon))
        except Exception as e:
            print(f"  Error Georef: {e}")
        
        return None
    
    async def geocode_nominatim(self, direccion: str) -> Optional[Tuple[float, float]]:
        """Geocodifica usando Nominatim (OSM)"""
        # Rate limit: 1 request/segundo
        elapsed = time.time() - self.last_nominatim_request
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{direccion}, Argentina",
            'format': 'json',
            'countrycodes': 'ar',
            'limit': 1
        }
        headers = {
            'User-Agent': 'MiTurno-Academic-Comparison/1.0'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                self.last_nominatim_request = time.time()
                
                if data and len(data) > 0:
                    result = data[0]
                    return (float(result['lat']), float(result['lon']))
        except Exception as e:
            print(f"  Error Nominatim: {e}")
        
        return None
    
    async def compare_address(self, direccion: str, zona: str) -> Dict[str, Any]:
        """Compara una direccion en ambas APIs"""
        print(f"\n{'='*70}")
        print(f"Direccion: {direccion}")
        print(f"Zona: {zona}")
        print(f"{'='*70}")
        
        # Geocodificar con ambas APIs
        print("Geocodificando con Georef...")
        georef_coords = await self.geocode_georef(direccion)
        
        print("Geocodificando con Nominatim...")
        nominatim_coords = await self.geocode_nominatim(direccion)
        
        # Analizar resultados
        result = {
            'direccion': direccion,
            'zona': zona,
            'georef': georef_coords,
            'nominatim': nominatim_coords
        }
        
        if georef_coords:
            print(f"  Georef:    ({georef_coords[0]:.6f}, {georef_coords[1]:.6f})")
        else:
            print(f"  Georef:    NO ENCONTRADO")
        
        if nominatim_coords:
            print(f"  Nominatim: ({nominatim_coords[0]:.6f}, {nominatim_coords[1]:.6f})")
        else:
            print(f"  Nominatim: NO ENCONTRADO")
        
        # Calcular diferencia si ambos encontraron
        if georef_coords and nominatim_coords:
            distance = self.calculate_distance(
                georef_coords[0], georef_coords[1],
                nominatim_coords[0], nominatim_coords[1]
            )
            result['distance_km'] = distance
            
            if distance < 0.5:
                status = "CONSENSO ALTO"
                symbol = "✓"
            elif distance < 2.0:
                status = "CONSENSO MEDIO"
                symbol = "~"
            else:
                status = "DISCREPANCIA"
                symbol = "✗"
            
            print(f"\n  {symbol} Diferencia: {distance:.2f} km - {status}")
            result['status'] = status
        elif georef_coords or nominatim_coords:
            result['status'] = "SOLO UNA API"
            print(f"\n  ! Solo una API encontro resultado")
        else:
            result['status'] = "AMBAS FALLARON"
            print(f"\n  ✗ Ninguna API encontro resultado")
        
        return result
    
    async def run_comparison(self):
        """Ejecuta comparacion completa"""
        
        # Direcciones de prueba representativas del AMBA
        test_addresses = [
            # CABA - Centro
            ("Av. Corrientes 1000, Ciudad Autonoma de Buenos Aires", "CABA Centro"),
            ("Florida 500, Ciudad Autonoma de Buenos Aires", "CABA Centro"),
            
            # CABA - Barrios
            ("Av. Cabildo 2000, Ciudad Autonoma de Buenos Aires", "CABA Norte"),
            ("Av. Rivadavia 5000, Ciudad Autonoma de Buenos Aires", "CABA Oeste"),
            
            # Zona Norte
            ("Av. Libertador 15000, San Isidro, Buenos Aires", "Zona Norte"),
            ("Maipu 1000, Vicente Lopez, Buenos Aires", "Zona Norte"),
            
            # Zona Sur - casos problematicos
            ("Independencia 806, Monte Grande, Buenos Aires", "Zona Sur"),
            ("Hipolito Yrigoyen 500, Quilmes, Buenos Aires", "Zona Sur"),
            ("Alsina 350, Lomas de Zamora, Buenos Aires", "Zona Sur"),
            ("Mitre 1200, Avellaneda, Buenos Aires", "Zona Sur"),
            
            # Zona Oeste
            ("Rivadavia 18000, Moron, Buenos Aires", "Zona Oeste"),
            ("Libertad 200, San Antonio de Padua, Buenos Aires", "Zona Oeste"),
            
            # Zona Oeste - Mas alejado
            ("Belgrano 300, Merlo, Buenos Aires", "Zona Oeste"),
        ]
        
        print("\n" + "="*70)
        print("COMPARACION GEOREF vs NOMINATIM - AMBA")
        print("="*70)
        
        results = []
        for direccion, zona in test_addresses:
            result = await self.compare_address(direccion, zona)
            results.append(result)
            await asyncio.sleep(0.5)  # Pausa entre tests
        
        # Resumen final
        print("\n\n" + "="*70)
        print("RESUMEN COMPARATIVO")
        print("="*70)
        
        consenso_alto = sum(1 for r in results if r.get('status') == 'CONSENSO ALTO')
        consenso_medio = sum(1 for r in results if r.get('status') == 'CONSENSO MEDIO')
        discrepancia = sum(1 for r in results if r.get('status') == 'DISCREPANCIA')
        solo_una = sum(1 for r in results if r.get('status') == 'SOLO UNA API')
        ambas_fallaron = sum(1 for r in results if r.get('status') == 'AMBAS FALLARON')
        
        total = len(results)
        
        print(f"\nTotal direcciones probadas: {total}")
        print(f"Consenso alto (<0.5km):     {consenso_alto} ({consenso_alto/total*100:.1f}%)")
        print(f"Consenso medio (<2km):      {consenso_medio} ({consenso_medio/total*100:.1f}%)")
        print(f"Discrepancia (>2km):        {discrepancia} ({discrepancia/total*100:.1f}%)")
        print(f"Solo una API funciono:      {solo_una} ({solo_una/total*100:.1f}%)")
        print(f"Ambas APIs fallaron:        {ambas_fallaron} ({ambas_fallaron/total*100:.1f}%)")
        
        # Mostrar casos con mayor discrepancia
        discrepancias_grandes = [r for r in results if r.get('distance_km', 0) > 2.0]
        if discrepancias_grandes:
            print(f"\nCASOS CON MAYOR DISCREPANCIA:")
            for r in sorted(discrepancias_grandes, key=lambda x: x.get('distance_km', 0), reverse=True):
                print(f"  - {r['direccion'][:50]:50} | {r['distance_km']:.2f} km")
        
        # Analisis por zona
        print(f"\nANALISIS POR ZONA:")
        zonas = {}
        for r in results:
            zona = r['zona']
            if zona not in zonas:
                zonas[zona] = {'total': 0, 'consenso': 0}
            zonas[zona]['total'] += 1
            if r.get('status') in ['CONSENSO ALTO', 'CONSENSO MEDIO']:
                zonas[zona]['consenso'] += 1
        
        for zona, stats in sorted(zonas.items()):
            porcentaje = stats['consenso'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {zona:20} | Consenso: {stats['consenso']}/{stats['total']} ({porcentaje:.0f}%)")
        
        print("\n" + "="*70)
        print("CONCLUSION:")
        consenso_total = consenso_alto + consenso_medio
        if consenso_total / total > 0.7:
            print("Ambas APIs muestran alto nivel de concordancia en AMBA")
            print("Recomendacion: Sistema de consenso es viable")
        elif consenso_total / total > 0.4:
            print("Concordancia moderada - hay discrepancias significativas")
            print("Recomendacion: Usar validacion y revisar casos conflictivos")
        else:
            print("Baja concordancia entre APIs")
            print("Recomendacion: Requiere validacion manual extensa")
        print("="*70)


async def main():
    """Ejecuta el test comparativo"""
    comparator = GeocodingComparison()
    await comparator.run_comparison()


if __name__ == "__main__":
    print("Iniciando comparacion de APIs de geocodificacion...")
    print("Esto tomara aproximadamente 2-3 minutos (rate limiting)\n")
    asyncio.run(main())