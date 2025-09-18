from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Rol(Base):
    __tablename__ = "rol"
    
    rol_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(20), nullable=False)  # 'global' o 'empresa'
    nivel = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuario_roles = relationship("UsuarioRol", back_populates="rol")
    permisos = relationship("Permiso", secondary="rol_permiso", back_populates="roles")

class Permiso(Base):
    __tablename__ = "permiso"
    
    permiso_id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(100), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(50), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    
    # Relaciones
    roles = relationship("Rol", secondary="rol_permiso", back_populates="permisos")

class RolPermiso(Base):
    __tablename__ = "rol_permiso"
    
    rol_permiso_id = Column(Integer, primary_key=True, index=True)
    rol_id = Column(Integer, ForeignKey("rol.rol_id"), nullable=False)
    permiso_id = Column(Integer, ForeignKey("permiso.permiso_id"), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_asignado = Column(DateTime, server_default=func.now())

class UsuarioRol(Base):
    __tablename__ = "usuario_rol"
    
    usuario_rol_id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    rol_id = Column(Integer, ForeignKey("rol.rol_id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id"), nullable=True)
    asignado_por = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=True)
    fecha_asignado = Column(DateTime, server_default=func.now())
    fecha_vencimiento = Column(DateTime, nullable=True)
    activo = Column(Boolean, default=True)
    motivo_inactivacion = Column(Text, nullable=True)
    
    # Relaciones
    rol = relationship("Rol", back_populates="usuario_roles")
    # usuario = relationship("Usuario", foreign_keys=[usuario_id], back_populates="roles")
    # asignado_por_usuario = relationship("Usuario", foreign_keys=[asignado_por])

class AutorizacionSoporte(Base):
    __tablename__ = "autorizacion_soporte"
    
    autorizacion_id = Column(Integer, primary_key=True, index=True)
    usuario_solicitante_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    usuario_autorizado_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id"), nullable=True)
    nivel_acceso = Column(String(20), nullable=False)
    motivo = Column(Text, nullable=False)
    fecha_solicitud = Column(DateTime, server_default=func.now())
    fecha_autorizacion = Column(DateTime, nullable=True)
    fecha_vencimiento = Column(DateTime, nullable=False)
    activo = Column(Boolean, default=True)
    token_acceso = Column(String(255), unique=True, nullable=True)