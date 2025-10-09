# test_geocoding_local.py
import asyncio
import sys
import os
import logging

# Configurar logging para ver TODOS los logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio app al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.geocoding_service_new import geocoding_service

async def test_geocoding():
    """Prueba la geocodificación directamente"""
    
    print("=" * 60)
    print("PRUEBA DE GEOCODIFICACIÓN LOCAL (SIN DOCKER)")
    print("=" * 60)
    
    # Direcciones de prueba
    direcciones_test = [
        {
            "nombre": "Obelisco - CABA",
            "calle": "Av. Corrientes",
            "numero": "1000",
            "ciudad": "Ciudad Autónoma de Buenos Aires",
            "provincia": "Ciudad Autónoma de Buenos Aires"
        },
        {
            "nombre": "Plaza de Mayo",
            "calle": "Hipólito Yrigoyen", 
            "numero": "250",
            "ciudad": "Ciudad Autónoma de Buenos Aires",
            "provincia": "Ciudad Autónoma de Buenos Aires"
        },
        {
            "nombre": "Quilmes Centro",
            "calle": "Rivadavia",
            "numero": "350", 
            "ciudad": "Quilmes",
            "provincia": "Buenos Aires"
        }
    ]
    
    for i, direccion in enumerate(direcciones_test, 1):
        print(f"\n🔄 PRUEBA {i}: {direccion['nombre']}")
        print(f"Dirección: {direccion['calle']} {direccion['numero']}, {direccion['ciudad']}")
        
        try:
            resultado = await geocoding_service.geocode_address(
                calle=direccion['calle'],
                numero=direccion['numero'],
                ciudad=direccion['ciudad'], 
                provincia=direccion['provincia']
            )
            
            if resultado:
                lat, lng = resultado
                print(f"✅ ÉXITO: Coordenadas ({lat}, {lng})")
            else:
                print("❌ ERROR: No se pudieron obtener coordenadas")
                
        except Exception as e:
            print(f"❌ EXCEPCIÓN: {str(e)}")
        
        print("-" * 50)
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_geocoding())