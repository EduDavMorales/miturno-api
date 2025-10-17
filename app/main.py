# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.core.logger import setup_logging, get_logger
from app.api.v1 import auth, empresas, categorias, turnos, test_roles, geolocalizacion, conversaciones
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

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    app_logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    app_logger.info(f"Debug mode: {settings.debug}")
    app_logger.info(f"CORS origins configurados: {settings.backend_cors_origins}")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    app_logger.info("Cerrando aplicación MiTurno API")

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=[" 🔐 Autenticación"])
app.include_router(empresas.router, prefix="/api/v1", tags=[" 🏢 Empresas"])
app.include_router(categorias.router, prefix="/api/v1", tags=[" 📂 Categorías"])
app.include_router(turnos.router, prefix="/api/v1", tags=[" 📅 Turnos"])
app.include_router(test_roles.router, prefix="/api/v1/test", tags=[" ⚙️ Test Roles"])
app.include_router(auditoria.router)
app.include_router(geo_test.router)
app.include_router(geolocalizacion.router, prefix="/api/v1", tags=["📍 Geolocalización"])
app.include_router(conversaciones.router, prefix="/api/v1")

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