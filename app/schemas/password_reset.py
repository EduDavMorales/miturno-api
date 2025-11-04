from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional


class PasswordResetRequest(BaseModel):
    """Schema para solicitar reset de contraseña"""
    email: EmailStr = Field(..., description="Email del usuario que solicita el reset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Schema para confirmar reset de contraseña con token"""
    token: str = Field(..., min_length=32, max_length=255, description="Token de recuperación")
    nueva_password: str = Field(..., min_length=8, max_length=100, description="Nueva contraseña")
    confirmar_password: str = Field(..., min_length=8, max_length=100, description="Confirmación de contraseña")
    
    @validator('confirmar_password')
    def passwords_match(cls, v, values):
        """Validar que las contraseñas coincidan"""
        if 'nueva_password' in values and v != values['nueva_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v
    
    @validator('nueva_password')
    def password_strength(cls, v):
        """Validar fortaleza de la contraseña"""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "nueva_password": "NuevaPassword123",
                "confirmar_password": "NuevaPassword123"
            }
        }


class PasswordResetResponse(BaseModel):
    """Schema para respuesta de solicitud de reset"""
    mensaje: str = Field(..., description="Mensaje de confirmación")
    email: str = Field(..., description="Email al que se envió el link")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mensaje": "Si el email existe, recibirás un link de recuperación",
                "email": "usuario@ejemplo.com"
            }
        }


class PasswordResetSuccessResponse(BaseModel):
    """Schema para respuesta exitosa de reset"""
    mensaje: str = Field(..., description="Mensaje de éxito")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mensaje": "Contraseña actualizada exitosamente"
            }
        }


class TokenValidationResponse(BaseModel):
    """Schema para validación de token"""
    valido: bool = Field(..., description="Si el token es válido")
    mensaje: str = Field(..., description="Mensaje descriptivo")
    email: Optional[str] = Field(None, description="Email del usuario (si el token es válido)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valido": True,
                "mensaje": "Token válido",
                "email": "usuario@ejemplo.com"
            }
        }