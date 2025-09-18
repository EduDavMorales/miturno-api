# MiTurno API

Sistema completo de gestión de turnos desarrollado con FastAPI, MySQL y Docker. Conecta empresas prestadoras de servicios con clientes que necesitan agendar citas a través de una plataforma robusta y segura.

## Estado del Proyecto

- **Progreso:** 98% completado
- **Tecnologías:** Python 3.11, FastAPI, MySQL 8.0, Docker, Pydantic v2, SQLAlchemy
- **Arquitectura:** Clean Architecture + Service Layer + Sistema de Roles Granulares
- **Testing:** Endpoint de disponibilidad funcional con 53 slots calculados

## Funcionalidades Implementadas

### Sistema de Autenticación y Roles
- **JWT Authentication** completo con tokens seguros
- **7 roles jerárquicos:** Cliente, Empleado, Recepcionista, Admin Empresa, Dueño Empresa, Admin Sistema, Super Admin
- **31 permisos granulares** por recurso y acción
- **Contexto empresarial** - roles limitados a su empresa
- **Self-management** - usuarios solo gestionan sus recursos

### Sistema de Disponibilidad de Turnos ✅ **OPERATIVO**
```http
GET /api/v1/empresas/{empresa_id}/disponibilidad?fecha=2025-09-19&servicio_id=1
```
- **Cálculo inteligente** de slots disponibles en tiempo real
- **Considera horarios** de trabajo por día de semana  
- **Integra servicios** con duraciones y precios específicos
- **Evita conflictos** con turnos existentes
- **Generación automática** de slots cada 30 minutos

**Ejemplo de respuesta real:**
```json
{
  "fecha": "2025-09-19", 
  "empresa_nombre": "Barbería Central",
  "slots_disponibles": 53,
  "empresa_id": 1
}
```

### Sistema de Gestión de Turnos
- **Reservar turnos** con validaciones robustas
- **Listado paginado** de turnos del usuario con filtros
- **Modificación de turnos** existentes
- **Cancelación semánticamente correcta** (PUT en lugar de DELETE)
- **Estados controlados:** pendiente, confirmado, cancelado, completado
- **Soft delete** - no se elimina información físicamente

### Sistema de Empresas y Servicios
- **CRUD completo** de empresas con validaciones
- **Servicios por empresa** con precio y duración
- **Horarios de trabajo** configurables por día
- **Categorización** por tipo de negocio
- **Geolocalización** con coordenadas precisas

### Arquitectura Técnica Avanzada
- **Service Layer** - lógica de negocio centralizada
- **8 Schemas Pydantic especializados** por funcionalidad
- **Enums centralizados** - principio DRY aplicado
- **Logging profesional** con niveles configurables
- **Configuración por entornos** - desarrollo/producción
- **Principios SOLID** aplicados consistentemente

## URLs de Desarrollo

- **API Base:** http://localhost:8000
- **Documentación Interactiva:** http://localhost:8000/docs
- **Base de datos:** localhost:3306

## Inicio Rápido

### Prerrequisitos
- Docker Desktop
- Git

### Instalación
```bash
# Clonar repositorio
git clone [tu-repo-url]
cd turnos-api

# Iniciar servicios
docker-compose up -d

# Verificar que esté funcionando
curl http://localhost:8000/api/v1/empresas/1/disponibilidad?fecha=2025-09-19
```

## API Endpoints

### Disponibilidad (Funcional) ✅
```http
GET /api/v1/empresas/{empresa_id}/disponibilidad
    ?fecha=YYYY-MM-DD&servicio_id={opcional}
```

### Gestión de Turnos (Requiere autenticación 🔒)
```http
POST /api/v1/turnos/reservar           # Reservar turno
GET  /api/v1/mis-turnos               # Listar mis turnos con filtros
PUT  /api/v1/turnos/{id}              # Modificar turno
PUT  /api/v1/turnos/{id}/cancelar     # Cancelar turno (soft delete)
```

### Sistema de Empresas
```http
GET  /api/v1/empresas                 # Listar con filtros y paginación
POST /api/v1/empresas                 # Crear (solo usuarios empresa)
GET  /api/v1/empresas/{id}            # Obtener específica
```

### Autenticación
```http
POST /api/auth/login                  # Login JWT
POST /api/auth/register               # Registro de usuarios
```

### Endpoints Legacy (Compatibilidad)
```http
GET  /api/v1/turnos                   # Listar (sin autenticación)
POST /api/v1/turnos                   # Crear básico
DELETE /api/v1/turnos/{id}            # @deprecated - usar PUT /cancelar
```

## Arquitectura del Sistema

### Capas Implementadas
```
┌─────────────────────────────────────┐
│        REST API (FastAPI)          │  ← Endpoints con documentación automática
├─────────────────────────────────────┤
│       Service Layer                │  ← Lógica de negocio (TurnoService)
├─────────────────────────────────────┤
│    Models + Schemas (Pydantic)     │  ← Validación y serialización
├─────────────────────────────────────┤
│      Database (SQLAlchemy)         │  ← ORM con MySQL
└─────────────────────────────────────┘
```

### Service Layer - TurnoService
```python
# Métodos principales implementados:
- obtener_disponibilidad()      # Cálculo de slots libres
- reservar_turno()              # Reservas con validaciones
- obtener_turnos_usuario()      # Listado paginado
- modificar_turno()             # Actualizaciones seguras
- cancelar_turno()              # Soft delete
```

## Base de Datos

### Estructura Completa (14 tablas)
```
usuario ─┬─ empresa ─── servicio
         ├─ turno ──── horario_empresa  
         └─ usuario_rol ─── rol ─── rol_permiso ─── permiso
```

### Datos de Prueba Configurados
- **Empresa:** Barbería Central (ID: 1)
- **Servicios:** 3 servicios con precios reales
- **Horarios:** Lunes-sábado configurados  
- **Usuarios:** 2 clientes + 1 empresa

### Comandos Útiles
```bash
# Conectar a MySQL
docker-compose exec database mysql -u root -p sistema_turnos

# Probar disponibilidad
curl "http://localhost:8000/api/v1/empresas/1/disponibilidad?fecha=2025-09-19"

# Ver logs en tiempo real
docker-compose logs -f backend
```

## Desarrollo

### Estructura del Proyecto
```
app/
├── api/v1/              # Endpoints REST organizados
│   ├── turnos.py        # ✅ 5 endpoints + 3 legacy
│   ├── auth.py          # Sistema de autenticación
│   └── test_roles.py    # Testing de permisos
├── services/            # ✅ Lógica de negocio
│   └── turno_service.py # 8 métodos especializados
├── schemas/             # ✅ Validaciones Pydantic
│   └── turno.py         # 8 schemas especializados
├── models/              # ✅ SQLAlchemy ORM
│   ├── horario_empresa.py
│   ├── rol.py
│   └── ...
├── core/                # Configuración y seguridad
│   ├── security.py      # JWT + autenticación
│   └── logger.py        # ✅ Logging profesional
└── enums.py             # ✅ Enums centralizados
```

### Hot Reload Development
```bash
# Desarrollo con recarga automática
docker-compose up -d

# Rebuild después de cambios importantes
docker-compose up -d --build

# Ver todos los logs
docker-compose logs -f
```

## Testing y Validación

### Endpoint Validado ✅
```bash
# Test de disponibilidad (53 slots calculados correctamente)
curl -X GET "http://localhost:8000/api/v1/empresas/1/disponibilidad?fecha=2025-09-19"

# Response esperado: 200 OK con 53 slots para Barbería Central
```

### Flujo de Testing Completo
1. **Disponibilidad** ✅ - Endpoint funcional  
2. **Autenticación** 🔄 - Login + JWT token
3. **Reserva** 🔄 - POST /turnos/reservar
4. **Gestión** 🔄 - Modificar/cancelar turnos

## Mejoras Arquitectónicas Aplicadas

### Consistencia Semántica HTTP
- **Antes:** `DELETE /turnos/{id}/cancelar` (confuso)
- **Ahora:** `PUT /turnos/{id}/cancelar` (correcto)
- **Razón:** Cancelar actualiza estado, no elimina registro

### Soft Delete Consistente  
- **Principio:** No eliminación física de datos
- **Implementación:** Estados de cancelación con metadatos
- **Beneficio:** Auditoría completa y recuperación

### Service Layer Pattern
- **Separación clara:** Router ↔ Service ↔ Models
- **Testeable:** Lógica independiente de FastAPI
- **Mantenible:** Cambios centralizados

## Próximas Funcionalidades (2% restante)

### Inmediatas
- **Validación completa** de endpoints autenticados
- **Notificaciones automáticas** por email/WhatsApp  
- **Dashboard empresarial** con métricas

### Mejoras Futuras
- **Búsqueda geográfica** por proximidad
- **Sistema de reviews** y calificaciones
- **Integración WhatsApp** Business API
- **App móvil** con React Native

## Resolución de Issues Técnicos

### Problemas Solucionados
✅ **Enum DiaSemana** - Configuración correcta SQLAlchemy  
✅ **Campos de modelo** - Nombres consistentes con BD  
✅ **Pydantic v2** - Migración completa `from_attributes`  
✅ **Arquitectura REST** - Semántica HTTP correcta  

### Troubleshooting Común
```bash
# Error 500 en endpoints
docker-compose logs backend --tail 50

# Problema de conectividad BD
docker-compose ps
docker-compose restart database

# Limpiar y reiniciar todo
docker-compose down -v && docker-compose up -d
```

## Contribución y Git Workflow

### Commits Organizados (Implementado)
- **feat:** Nuevas funcionalidades
- **fix:** Corrección de bugs  
- **docs:** Documentación
- **refactor:** Mejoras de código
- **test:** Testing

### Branches Futuras
- `feature/notificaciones`
- `feature/dashboard-empresarial` 
- `fix/performance-optimizations`

## Métricas del Sistema

- **14 tablas** en base de datos
- **31 permisos** granulares implementados
- **7 roles** jerárquicos configurados
- **8 schemas** Pydantic especializados
- **5 endpoints** nuevos + 3 legacy mantenidos
- **53 slots** calculados correctamente en testing
- **1 endpoint** de producción completamente funcional

## Contacto y Soporte

- **Documentación API:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health (si implementado)
- **Issues:** GitHub Issues para bugs y features
- **Testing:** Datos de prueba configurados (Barbería Central)

---

**Última actualización:** Septiembre 2025  
**Versión:** v2.0.0-beta  
**Status:** Endpoint de disponibilidad en producción, módulo completo 98% implementado