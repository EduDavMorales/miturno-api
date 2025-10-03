from .auth import *
from .empresa import EmpresaCreate, EmpresaResponse, EmpresasListResponse, EmpresaUpdate
from .direccion import DireccionCreate, DireccionResponse, DireccionUpdate

__all__ = [
    # Auth schemas
    "LoginRequest", "LoginResponse",
    "GoogleAuthRequest", 
    "RegistroRequest", "RegistroResponse",
    "UsuarioResponse",
    "Token", "TokenData",
    
    # Empresa schemas
    "EmpresaCreate", "EmpresaResponse", "EmpresasListResponse", "EmpresaUpdate",
    
    # Direccion schemas (NUEVOS - CRÍTICOS)
    "DireccionCreate", "DireccionResponse", "DireccionUpdate",
]