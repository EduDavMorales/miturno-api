# 🚀 MiTurno API

Sistema de gestión de turnos - Backend API desarrollado con FastAPI y MySQL.

## 📊 Estado del Proyecto
- **Progreso:** 70% completado
- **Tecnologías:** Python 3.11, FastAPI, MySQL, Docker
- **Documentación:** [API Integration Guide](./API_Integration_Guide.md)

## 🌐 URLs

### Desarrollo Local
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

### Producción (Temporal)
- **API:** https://f07c14a7d2fa.ngrok-free.app
- **Docs:** https://f07c14a7d2fa.ngrok-free.app/docs

## ⚡ Inicio Rápido

### Prerrequisitos
- Docker Desktop
- Git

### Instalación
```bash
# Clonar repositorio
git clone https://github.com/EduDavMorales/miturno-api.git
cd miturno-api

# Iniciar servicios
start_miturno_ngrok.bat
# O manualmente:
docker-compose up -d
```

## 🔧 Desarrollo

### Estructura de la Base de Datos
- 9 tablas implementadas
- Relaciones FK correctas
- Script SQL incluido

### Endpoints Implementados
- ✅ `POST /auth/login` - Autenticación
- ✅ `POST /auth/register` - Registro
- ✅ `GET /health` - Estado de la API

### Endpoints Pendientes
- ⏳ `GET /empresas` - Lista de empresas
- ⏳ `POST /turnos` - Reservar turno
- ⏳ `GET /turnos/{id}/mensajes` - Mensajería

## 📚 Documentación

- **[Guía de Integración Frontend](./API_Integration_Guide.md)**
- **[Estado de Implementación](./BACKEND_STATUS.md)**
- **[Documentación Automática](http://localhost:8000/docs)**

## 🐳 Docker

```bash
# Desarrollo
docker-compose up -d

# Rebuild completo
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Parar servicios
docker-compose down
```

## 🚀 Deployment

- **Desarrollo:** ngrok tunnel
- **Producción:** Render/Railway/Oracle Cloud
- **Frontend:** Repositorio separado

## 🤝 Colaboración

### Frontend Repository
- **Repo:** [Link al repo del frontend]
- **Coordinación:** Issues y documentación compartida

### Equipo
- **Backend:** [Tu nombre]
- **Frontend:** [Nombres del equipo]

## 📞 Contacto

- **Issues:** [GitHub Issues](../../issues)
- **API Docs:** [Swagger UI](http://localhost:8000/docs)

---

**Última actualización:** Septiembre 2025