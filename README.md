# MiTurno API

Sistema de gestión de turnos con FastAPI, MySQL y Docker. Conecta empresas prestadoras de servicios con clientes para agendar citas.

## Tabla de Contenidos
- [URLs del Proyecto](#urls-del-proyecto)
- [Estado del Proyecto](#estado-del-proyecto)
- [Stack Tecnológico](#stack-tecnológico)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Características Principales](#características-principales)
- [Inicio Rápido](#inicio-rápido)
- [API Endpoints](#api-endpoints)
- [Base de Datos](#base-de-datos)
- [Desarrollo](#desarrollo)
- [Testing](#testing)
- [Deployment](#deployment)
- [Integración Externa](#integración-externa)
- [Arquitectura](#arquitectura)
- [Documentación Adicional](#documentación-adicional)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [Contacto](#contacto)

## URLs del Proyecto

- **Producción:** https://miturno-api-production.up.railway.app
- **Documentación Producción:** https://miturno-api-production.up.railway.app/docs
- **Desarrollo Local:** http://localhost:8000
- **Documentación Local:** http://localhost:8000/docs

## Estado del Proyecto

**Versión:** v2.1.0-SPRINT2  
**Estado:** Producción 95% + Sprint 2 Geolocalización (60%)  
**Deployment:** Railway (auto-deploy desde main)

## Stack Tecnológico

- Python 3.11 + FastAPI
- MySQL 8.0
- SQLAlchemy 2.0 + Alembic 1.13
- Pydantic v2
- JWT Authentication
- Docker + Docker Compose
- API Georef Argentina (geolocalización)

## Estructura del Proyecto

<details>
<summary>📁 Ver estructura de carpetas</summary>

```
MiTurno/
|   .dockerignore
|   .env
|   .env.example
|   .gitignore
|   alembic.ini
|   debug_enum.py
|   docker-compose.dev.yml
|   docker-compose.prod.yml
|   docker-compose.yml
|   Dockerfile
|   estructura.txt
|   README.md
|   README.md.backup
|   requirements.txt
|   schema_actual.sql
|   test_compare_apis.py
|   test_geocodiing_local.py
|   test_geocoding_local.py
|   
+---alembic
|   |   env.py
|   |   README
|   |   script.py.mako
|   |   
|   \---versions
|           9e275309deea_add_geocoding_metadata_fields.py
|           
+---app
|   |   config.py
|   |   crud.py
|   |   database.py
|   |   enums.py
|   |   main.py
|   |   __init__.py
|   |   
|   +---api
|   |   |   deps.py
|   |   |   __init__.py
|   |   |   
|   |   +---v1
|   |   |   |   auth.py
|   |   |   |   categorias.py
|   |   |   |   empresas.py
|   |   |   |   test_roles.py
|   |   |   |   turnos.py
|   |   |   |   __init__.py
|   |   |   |   
|   |   |   \---__pycache__
|   |   |           auth.cpython-313.pyc
|   |   |           __init__.cpython-313.pyc
|   |   |           
|   |   \---__pycache__
|   |           __init__.cpython-313.pyc
|   |           
|   +---auth
|   |       permissions.py
|   |       
|   +---core
|   |   |   exceptions.py
|   |   |   logger.py
|   |   |   security.py
|   |   |   __init__.py
|   |   |   
|   |   \---__pycache__
|   |           security.cpython-313.pyc
|   |           __init__.cpython-313.pyc
|   |           
|   +---middleware
|   |       auditoria_middleware.py
|   |       
|   +---models
|   |   |   auditoria.py
|   |   |   auditoria_detalle.py
|   |   |   bloqueo_horario.py
|   |   |   categoria.py
|   |   |   direccion.py
|   |   |   empresa.py
|   |   |   horario_empresa.py
|   |   |   mensaje.py
|   |   |   rol.py
|   |   |   servicio.py
|   |   |   turno.py
|   |   |   user.py
|   |   |   __init__.py
|   |   |   
|   |   \---__pycache__
|   |           categoria.cpython-313.pyc
|   |           empresa.cpython-313.pyc
|   |           mensaje.cpython-313.pyc
|   |           servicio.cpython-313.pyc
|   |           turno.cpython-313.pyc
|   |           user.cpython-313.pyc
|   |           __init__.cpython-313.pyc
|   |           
|   +---routers
|   |       auditoria.py
|   |       geo_test.py
|   |       
|   +---schemas
|   |   |   auditoria.py
|   |   |   auth.py
|   |   |   categoria.py
|   |   |   direccion.py
|   |   |   empresa.py
|   |   |   geo.py
|   |   |   turno.py
|   |   |   user.py
|   |   |   __init__.py
|   |   |   
|   |   \---__pycache__
|   |           auth.cpython-313.pyc
|   |           __init__.cpython-313.pyc
|   |           
|   +---services
|   |   |   auditoria_service.py
|   |   |   empresa_service.py
|   |   |   geocoding_service.py
|   |   |   geocoding_service_new.py
|   |   |   geo_validation_service.py
|   |   |   turno_service.py
|   |   |   __init__.py
|   |   |   
|   |   \---__pycache__
|   |           geocoding_service_new.cpython-313.pyc
|   |           __init__.cpython-313.pyc
|   |           
|   +---utils
|   \---__pycache__
|           config.cpython-313.pyc
|           database.cpython-313.pyc
|           main.cpython-313.pyc
|           __init__.cpython-313.pyc
|           
\---docs
        base de datos con auditoria.pdf
        Base de datos geolocalizacion sprint2.pdf
        miturno_estructura.sql
        MiTurno_estructura_normalizada.png
        MiTurno_estructura_normalizada_sprint2.sql
        MiTurno_estructura_nueva.png
        miturno_updated_docs.md
        README.md
        resumen_ejecutivo_bd_miturno_actualizado.html
        sprint2_geolocalizacion.md

```

</details>

### Descripción de la Arquitectura

- **`/app`**: Núcleo de la aplicación FastAPI siguiendo Clean Architecture
- **`/app/api/v1`**: Endpoints REST API versionados
- **`/app/models`**: Modelos SQLAlchemy para base de datos
- **`/app/schemas`**: Esquemas Pydantic para validación y serialización
- **`/app/services`**: Capa de lógica de negocio
- **`/app/core`**: Configuraciones centrales, seguridad y excepciones
- **`/app/auth`**: Sistema de permisos y roles (RBAC)
- **`/app/middleware`**: Middleware personalizado (auditoría)
- **`/alembic`**: Migraciones de base de datos
- **`/docs`**: Documentación técnica y diagramas ER


## Características Principales

### Core (Producción)
- ✅ Autenticación JWT
- ✅ Sistema de roles y permisos (RBAC)
- ✅ Gestión completa de turnos
- ✅ Cálculo de disponibilidad
- ✅ Auditoría de cambios
- ✅ Soft delete

### Sprint 2 - Geolocalización (Desarrollo)
- ✅ Migración BD con 3 campos metadata
- ✅ Índice espacial para búsquedas geográficas
- ✅ GeocodingService (API Georef Argentina)
- ✅ GeoValidationService (validación por zona)
- ✅ Endpoint testing funcional
- ⏳ Búsqueda por proximidad
- ⏳ Endpoints producción

## Inicio Rápido

### Desarrollo Local

```bash
git clone https://github.com/EduDavMorales/miturno-api.git
cd miturno-api
cp .env.example .env
docker-compose up -d
curl http://localhost:8000/docs
```

## API Endpoints

### Autenticación

- `POST /api/auth/login` - Login JWT
- `POST /api/auth/register` - Registro usuarios

### Gestión de Turnos

- `GET /api/v1/empresas/{id}/disponibilidad` - Ver slots disponibles
- `POST /api/v1/turnos/reservar` - Reservar turno
- `GET /api/v1/mis-turnos` - Listar mis turnos
- `PUT /api/v1/turnos/{id}` - Modificar turno
- `PUT /api/v1/turnos/{id}/cancelar` - Cancelar turno

### Geolocalización (Testing - Sprint 2)

- `POST /api/v1/geo-test/geocode` - Geocodificar dirección

**Ejemplo de uso:**

```bash
curl -X POST http://localhost:8000/api/v1/geo-test/geocode \
  -H "Content-Type: application/json" \
  -d '{
    "calle": "Av Corrientes",
    "numero": "1000",
    "ciudad": "CABA",
    "provincia": "Ciudad Autónoma de Buenos Aires",
    "codigo_postal": "1043"
}'
```

## Base de Datos

### Estructura

- 16 tablas de negocio/auditoría
- 1 tabla técnica (alembic_version)
- Total: 17 tablas
- Sistema RBAC (7 roles, 31 permisos)
- Auditoría completa

### Campos Geolocalización (Sprint 2)

```sql
-- Tabla empresa
latitud DECIMAL(10,8)
longitud DECIMAL(11,8)
geocoding_confidence VARCHAR(50)
geocoding_warning TEXT
requires_verification BOOLEAN
INDEX idx_empresa_coordenadas (latitud, longitud)
```

### Migraciones Alembic

```bash
# Dentro del contenedor
docker exec -it turnos-api-backend-1 bash

# Ver estado
alembic current

# Aplicar migraciones
alembic upgrade head

# Crear nueva
alembic revision --autogenerate -m "descripcion"
```

## Desarrollo

### Comandos Docker

```bash
# Logs en tiempo real
docker-compose logs -f backend

# Reiniciar servicio
docker-compose restart backend

# Rebuild completo (sin caché)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Service Layer

- **TurnoService** - Lógica de turnos
- **AuditoriaService** - Tracking de cambios
- **GeocodingService** - Geocodificación (Sprint 2)
- **GeoValidationService** - Validación geográfica (Sprint 2)

## Testing

### Testing manual vía Swagger UI

Actualmente, las pruebas funcionales se realizan manualmente desde la interfaz interactiva de Swagger UI que genera FastAPI:

1. Accede a [http://localhost:8000/docs](http://localhost:8000/docs) (o https://miturno-api-production.up.railway.app/docs).
2. Haz login con el usuario de prueba:
   - **Email:** test.roles.v2@miturno.com
   - **Password:** 12345678
3. Obtén el JWT token y autoriza la sesión (botón "Authorize").
4. Prueba los endpoints protegidos y funcionales desde la interfaz.
5. Para endpoints de geolocalización, utiliza el ejemplo de payload que aparece en la documentación.

### Recomendación para automatización

Para escalar el testing y obtener cobertura automática, se recomienda implementar tests automatizados con `pytest` y `httpx` en el futuro. Ejemplo de comando:

```bash
pytest
```

## Deployment

### Railway (Producción)

- Auto-deploy al pushear a main
- **URL:** https://miturno-api-production.up.railway.app
- Base de datos MySQL Railway
- Logs en Railway dashboard

### Variables de Entorno

**Configuración requerida** (copiar `.env.example` → `.env`):

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+pymysql://USER:PASSWORD@turnos-db:3306/sistema_turnos` | Cadena de conexión a MySQL |
| `SECRET_KEY` | `YOUR_SECRET_KEY_HERE` | Clave para firmar JWT  |
| `DEBUG` | `False` | `True` solo en desarrollo local |
| `BACKEND_PORT` | `8000` | Puerto de la aplicación |
| `GEOREF_API_URL` | `https://apis.datos.gob.ar/georef/api` | Endpoint API Georef Argentina |
| `GEOREF_TIMEOUT` | `5` | Timeout en segundos para geocodificación |

**⚠️ Seguridad:** Nunca subir archivos `.env` al repositorio. Usar solo placeholders en documentación.

## Integración Externa

### API Georef Argentina (Sprint 2)

- **Proveedor:** Estado Argentino (INDEC)
- **Endpoint:** https://apis.datos.gob.ar/georef/api/direcciones
- **Uso:** Geocodificación de direcciones argentinas
- **Status:** ✅ Integrada y funcional

**Limitaciones conocidas:**
- Datos incompletos en algunas zonas
- Calles homónimas pueden dar primera coincidencia
- Sistema de validación automática implementado

## Arquitectura

- Clean Architecture
- Service Layer Pattern
- Repository Pattern (SQLAlchemy)
- Dependency Injection (FastAPI)
- JWT Authentication
- Database Migrations (Alembic)
- Soft Delete

## Documentación Adicional

- **Sprint 2 Geolocalización:** `/docs/sprint2_geolocalizacion.md`
- **Diagrama ER:** `/docs/MiTurno_estructura_nueva.png`
- **Script BD:** `/docs/MiTurno_estructura_normalizada_sprint2.sql`

## Roadmap

### Completado

- ✅ Autenticación JWT
- ✅ Sistema de turnos completo
- ✅ Roles y permisos RBAC
- ✅ Auditoría
- ✅ Migraciones Alembic
- ✅ Servicios geocodificación
- ✅ Endpoint testing geocoding

### En Progreso (Sprint 2)

- 🔄 GeolocationService
- 🔄 Endpoints búsqueda geográfica
- 🔄 Tests geolocalización

### Backlog

- 📋 OAuth Google
- 📋 Notificaciones
- 📋 Dashboard empresarial

## Troubleshooting

```bash
# Verificar servicios
docker-compose ps

# Ver logs con errores
docker logs turnos-api-backend-1 --tail 50

# Reinicio limpio (sin caché)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Contacto

- **Issues:** GitHub Issues
- **Docs:** https://miturno-api-production.up.railway.app/docs

---

**Última actualización:** Octubre 2025 (Sprint 2)  
**Deploy:** Railway Auto-Deploy desde main  
**Status:** Producción + Geolocalización en desarrollo