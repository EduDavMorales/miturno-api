# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

from app.config import settings
from app.core.logger import setup_logging, get_logger
from app.api.v1 import auth, empresas, categorias, turnos, test_roles, geolocalizacion, conversaciones, calificaciones, servicios, horarios
from app.routers import auditoria, geo_test
from app.database import engine
from app.models import user  

# Configurar logging al inicio de la aplicación
logger = setup_logging()
app_logger = get_logger("miturno.app")

# Crear las tablas en la base de datos
try:
    user.Base.metadata.create_all(bind=engine)
    app_logger.info("Base de datos inicializada correctamente")
except Exception as e:
    app_logger.error(f"Error inicializando base de datos: {str(e)}")
    raise

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API para la gestión de turnos entre empresas y clientes",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar esquema de seguridad JWT para Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Usar get_openapi en lugar de app.openapi() para evitar recursión
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Agregar esquema de seguridad Bearer JWT
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Ingrese el token JWT sin el prefijo 'Bearer'"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================
# SECURITY HEADERS MIDDLEWARE - NUEVO
# ============================================
@app.middleware("http")
async def add_security_headers(request, call_next):
    """
    Agregar headers de seguridad a todas las respuestas
    Protege contra ataques comunes como XSS, clickjacking, etc.
    """
    response = await call_next(request)
    
    # Prevenir MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevenir clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Habilitar protección XSS del navegador
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Content Security Policy - Incluye CDN para Swagger UI
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://apis.google.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "connect-src 'self' https://accounts.google.com https://www.googleapis.com; "
        "frame-src 'self' https://accounts.google.com;"
    )
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy (antes Feature-Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(self), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )
    
    # HSTS - Solo descomentar en producción con HTTPS
    # if not settings.debug:
    #     response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
    
# Event handlers
@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    app_logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    app_logger.info(f"Debug mode: {settings.debug}")
    app_logger.info(f"CORS origins configurados: {settings.backend_cors_origins}")
    
    # Inicializar Redis y FastAPILimiter para rate limiting
    try:
        redis_url = os.getenv("REDIS_URL") or "redis://redis:6379"
        app_logger.info(f"Conectando a Redis: {redis_url}")
        
        redis_connection = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        await FastAPILimiter.init(redis_connection)
        app_logger.info("✅ FastAPILimiter inicializado correctamente con Redis")
    except Exception as e:
        app_logger.error(f"❌ Error inicializando FastAPILimiter: {str(e)}")
        app_logger.warning("⚠️ Rate limiting no estará disponible")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    app_logger.info("Cerrando aplicación MiTurno API")
    
    # Cerrar conexión de FastAPILimiter
    try:
        await FastAPILimiter.close()
        app_logger.info("✅ FastAPILimiter cerrado correctamente")
    except Exception as e:
        app_logger.error(f"Error cerrando FastAPILimiter: {str(e)}")

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["🔐 Autenticación"])
app.include_router(empresas.router, prefix="/api/v1", tags=["🏢 Empresas"])
app.include_router(horarios.router, prefix="/api/v1", tags=["📅 Horarios y Bloqueos"])
app.include_router(servicios.router, prefix="/api/v1")
app.include_router(categorias.router, prefix="/api/v1", tags=["📂 Categorías"])
app.include_router(turnos.router, prefix="/api/v1", tags=["📅 Turnos"])
app.include_router(test_roles.router, prefix="/api/v1/test", tags=["⚙️ Test Roles"])
app.include_router(auditoria.router)
app.include_router(geo_test.router)
app.include_router(geolocalizacion.router, prefix="/api/v1", tags=["🗺️ Geolocalización"])
app.include_router(conversaciones.router, prefix="/api/v1")
app.include_router(calificaciones.router, prefix="/api/v1")

app_logger.info("Todos los routers registrados correctamente")

# Health check endpoints
@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return {"message": "Gestión de Turnos API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint para monitoreo"""
    app_logger.debug("Health check solicitado")
    return {
        "status": "healthy", 
        "version": settings.app_version,
        "app_name": settings.app_name
    }