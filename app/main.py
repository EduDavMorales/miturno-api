from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, empresas, categorias, turnos
from app.database import engine
from app.models import user  # Importar para crear tablas

# Crear las tablas en la base de datos
user.Base.metadata.create_all(bind=engine)

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para la gestión de turnos entre empresas y clientes",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(empresas.router, prefix="/api/v1", tags=["Empresas"])
app.include_router(categorias.router, prefix="/api/v1", tags=["Categorías"])
app.include_router(turnos.router, prefix="/api/v1", tags=["Turnos"])

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Gestión de Turnos API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}