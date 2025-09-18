"""
Script de diagnóstico para identificar el problema con EstadoTurno
"""
import sys
import os

# Agregar el directorio app al path para imports
sys.path.append('/app')

from sqlalchemy import create_engine, MetaData, inspect
from app.database import engine, get_db
from app.models.turno import Turno, EstadoTurno
from app.enums import EstadoTurno as CentralEstadoTurno

print("=== DIAGNÓSTICO DE ENUM EstadoTurno ===\n")

# 1. Verificar la definición centralizada
print("1. ENUM CENTRALIZADO (app/enums.py):")
print(f"   Clase: {CentralEstadoTurno}")
for estado in CentralEstadoTurno:
    print(f"   {estado.name} = '{estado.value}'")
print()

# 2. Verificar la definición en el modelo
print("2. ENUM EN MODELO (app/models/turno.py):")
print(f"   Importado como: {EstadoTurno}")
print(f"   Son la misma clase: {EstadoTurno is CentralEstadoTurno}")
for estado in EstadoTurno:
    print(f"   {estado.name} = '{estado.value}'")
print()

# 3. Inspeccionar la tabla real en la BD usando reflexión
print("3. TABLA REAL EN BASE DE DATOS (reflexión):")
try:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    if 'turno' in metadata.tables:
        turno_table = metadata.tables['turno']
        estado_column = turno_table.columns['estado']
        
        print(f"   Tipo de columna: {estado_column.type}")
        print(f"   Tipo Python: {type(estado_column.type)}")
        
        # Intentar obtener los valores del enum
        if hasattr(estado_column.type, 'enums'):
            print(f"   Valores en enum: {estado_column.type.enums}")
        
        if hasattr(estado_column.type, '_valid_lookup'):
            print(f"   Valid lookup: {estado_column.type._valid_lookup}")
            
        print(f"   Default: {estado_column.default}")
    else:
        print("   ⚠️  Tabla 'turno' no encontrada en reflexión")
        
except Exception as e:
    print(f"   ❌ Error en reflexión: {e}")

print()

# 4. Inspeccionar usando el inspector de SQLAlchemy
print("4. INSPECTOR DE SQLALCHEMY:")
try:
    inspector = inspect(engine)
    columns = inspector.get_columns('turno')
    
    for col in columns:
        if col['name'] == 'estado':
            print(f"   Nombre: {col['name']}")
            print(f"   Tipo: {col['type']}")
            print(f"   Nullable: {col['nullable']}")
            print(f"   Default: {col['default']}")
            break
    else:
        print("   ⚠️  Columna 'estado' no encontrada")
        
except Exception as e:
    print(f"   ❌ Error en inspector: {e}")

print()

# 5. Verificar la definición del modelo SQLAlchemy
print("5. MODELO SQLALCHEMY:")
try:
    turno_class = Turno
    estado_column = turno_class.__table__.columns['estado']
    
    print(f"   Columna: {estado_column}")
    print(f"   Tipo: {estado_column.type}")
    print(f"   Tipo Python: {type(estado_column.type)}")
    
    # Verificar el enum asociado
    if hasattr(estado_column.type, 'enum_class'):
        print(f"   Enum class: {estado_column.type.enum_class}")
        
    if hasattr(estado_column.type, 'enums'):
        print(f"   Enums: {estado_column.type.enums}")
        
    print(f"   Default: {estado_column.default}")
    
except Exception as e:
    print(f"   ❌ Error en modelo: {e}")

print()

# 6. Probar crear una instancia del enum
print("6. TEST DE INSTANCIACIÓN:")
try:
    # Probar con valores en minúsculas
    test_pendiente = EstadoTurno.PENDIENTE
    print(f"   EstadoTurno.PENDIENTE = '{test_pendiente.value}'")
    
    # Verificar que sea válido
    print(f"   Es válido: {'pendiente' in [e.value for e in EstadoTurno]}")
    
except Exception as e:
    print(f"   ❌ Error en test: {e}")

print("\n=== FIN DIAGNÓSTICO ===")