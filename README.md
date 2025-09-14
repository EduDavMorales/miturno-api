# MiTurno API

Sistema completo de gestión de turnos desarrollado con FastAPI, MySQL y Docker.

## Estado del Proyecto

- **Progreso:** 85% completado
- **Tecnologías:** Python 3.11, FastAPI, MySQL 8.0, Docker, Pydantic
- **Arquitectura:** Clean Architecture con separación de capas
- **Testing:** Validación funcional completa

## Funcionalidades Implementadas

### Sistema de Usuarios
- Registro y autenticación de usuarios
- Roles diferenciados: `cliente` y `empresa`  
- Validaciones de tipo de usuario
- Schemas completos con validaciones

### Sistema de Empresas
- CRUD completo de empresas
- Validación: solo usuarios tipo `empresa` pueden crear empresas
- Filtros por categoría y estado activo
- Paginación integrada
- Un usuario empresa = una empresa (regla de negocio)

### Sistema de Turnos
- **Crear turnos:** Clientes pueden reservar en múltiples empresas
- **Listar turnos:** Con filtros por cliente y paginación
- **Cancelar turnos:** Con metadatos (quien cancela, motivo)
- **Estados:** pendiente, confirmado, cancelado, completado
- **Validaciones:** Horarios, fechas futuras, disponibilidad

### Sistema de Categorías
- Listado de categorías de empresas
- 10 categorías predefinidas (Salud, Servicios, etc.)

### Arquitectura Técnica
- **Enums centralizados** - Principio DRY aplicado
- **Configuración por entornos** - Desarrollo/Producción separados
- **Docker Compose** - Desarrollo con hot-reload
- **Status codes HTTP correctos** - 201 Created, 409 Conflict, etc.

## URLs de Desarrollo

- **API Base:** http://localhost:8000
- **Documentación Swagger:** http://localhost:8000/docs
- **Base de datos:** localhost:3307

## Inicio Rápido

### Prerrequisitos
- Docker Desktop
- Git

### Instalación
```bash
# Clonar repositorio
git clone https://github.com/EduDavMorales/miturno-api.git
cd miturno-api

# Configurar entorno de desarrollo
cp .env.development .env

# Iniciar servicios (desarrollo)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Ver logs
docker-compose logs -f backend
```

## API Endpoints

### Autenticación
- `POST /api/auth/register` - Registro de usuarios
- `POST /api/auth/login` - Login
- `POST /api/auth/google` - OAuth Google

### Empresas
- `GET /api/v1/empresas` - Listar empresas con filtros
- `POST /api/v1/empresas` - Crear empresa (solo usuarios tipo empresa)
- `GET /api/v1/empresas/{id}` - Obtener empresa específica
- `GET /api/v1/empresas/usuario/{usuario_id}` - Empresa de un usuario

### Turnos
- `GET /api/v1/turnos` - Listar turnos con filtros
- `POST /api/v1/turnos` - Crear turno (solo clientes)
- `GET /api/v1/turnos/{id}` - Obtener turno específico  
- `DELETE /api/v1/turnos/{id}` - Cancelar turno con metadatos

### Categorías
- `GET /api/v1/categorias` - Listar categorías

## Estructura del Proyecto

```
turnos-api/
├── app/
│   ├── api/v1/          # Endpoints REST
│   ├── core/            # Configuración y seguridad
│   ├── models/          # Modelos SQLAlchemy
│   ├── schemas/         # Schemas Pydantic
│   ├── enums.py         # Enums centralizados
│   ├── crud.py          # Operaciones de base de datos
│   └── main.py          # Aplicación FastAPI
├── docker-compose.yml   # Configuración base
├── docker-compose.dev.yml  # Override desarrollo
├── sistema_turnos.sql   # Schema de base de datos
└── README.md
```

## Base de Datos

### Tablas Implementadas
- `usuario` - Usuarios del sistema (clientes y empresas)
- `empresa` - Datos de empresas registradas
- `categoria` - Categorías de empresas  
- `turno` - Turnos con campos de cancelación
- `servicio` - Servicios ofrecidos por empresas
- `mensaje` - Sistema de mensajería

### Comandos Útiles
```bash
# Conectar a MySQL
docker-compose exec database mysql -u root -p sistema_turnos
# Password: password

# Ver estructura de tabla
SHOW COLUMNS FROM turno;

# Backup
docker-compose exec database mysqldump -u root -p sistema_turnos > backup.sql
```

## Desarrollo

### Comandos Docker
```bash
# Desarrollo con hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Rebuild completo  
docker-compose down && docker-compose up -d --build

# Ver logs en tiempo real
docker-compose logs -f backend

# Limpiar todo
docker-compose down -v
```

### Configuración de Entornos

**Desarrollo:** `docker-compose.dev.yml`
- Hot-reload automático
- Debug habilitado
- Volúmenes montados

**Producción:** `docker-compose.prod.yml`  
- Múltiples workers
- Sin debug
- Configuración optimizada

## Próximas Funcionalidades

### En Desarrollo
- `GET /empresas/{id}/availability` - Horarios disponibles
- Sistema de servicios CRUD
- Notificaciones y recordatorios
- Reportes para empresas

### Backlog  
- Sistema de mensajería en tiempo real
- Integración con WhatsApp/Email
- Dashboard para empresas
- Sistema de reviews/calificaciones

## Testing

```bash
# Ejecutar pruebas (cuando se implementen)
docker-compose exec backend pytest

# Testing manual con curl
curl -X GET "http://localhost:8000/api/v1/categorias"
curl -X POST "http://localhost:8000/api/v1/empresas" \
  -H "Content-Type: application/json" \
  -d '{"usuario_id": 1, "categoria_id": 1, ...}'
```

## Colaboración

### Git Workflow
- **Main branch:** Código estable y probado
- **Feature branches:** Para nuevas funcionalidades (próximamente)
- **Commits:** Mensajes descriptivos con feat:, fix:, docs:

### Equipo
- **Backend Lead:** [Eduardo Morales]
- **Backend Developer:** [Tomas Rossi]
- **Frontend Team:** [En coordinación]

## Troubleshooting

### Problemas Comunes

**Error 500 en turnos:**
- Verificar enum EstadoTurno en app/enums.py
- Restart: `docker-compose restart backend`

**Problema de volúmenes:**
- Restart Docker Desktop
- `docker-compose down -v && docker-compose up -d`

**Base de datos no conecta:**
- Verificar puerto 3307 libre
- Health check: `docker-compose logs database`

## Contacto

- **GitHub Issues:** Para bugs y features
- **Documentación:** http://localhost:8000/docs
- **API Health:** http://localhost:8000/health

---

**Última actualización:** Septiembre 2025  
**Versión:** v1.0.0-beta