from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import logging
import secrets

from app.database import get_db
from app.models.user import Usuario, TipoUsuario
from app.models.rol import Rol, UsuarioRol
from app.models.auditoria import AuditoriaSistema
from app.auth.permissions import PermissionService  
from app.schemas.empresa import EmpresasListResponse, EmpresaCreate, EmpresaResponse
from app.schemas.equipo import EquipoListResponse, EquipoMiembro, InvitacionCreate, InvitacionResponse, CambiarRolRequest, CambioRolResponse, DesactivarMiembroRequest, DesactivacionResponse
from app.services.empresa_service import EmpresaService
from app.core.security import get_current_user

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/empresas", 
    response_model=EmpresasListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar empresas con filtros",
    description="Obtiene una lista de empresas con direcciones incluidas"
)
def get_empresas(
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoria"),
    activa: bool = Query(True, description="Solo empresas activas"),
    skip: int = Query(0, ge=0, description="Numero de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Numero máximo de registros"),
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    try:
        empresas, total = EmpresaService.get_empresas_with_relations(
            db=db,
            categoria_id=categoria_id,
            activa=activa,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"Consulta de empresas: {len(empresas)} de {total} total")
        return EmpresasListResponse(empresas=empresas, total=total)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener empresas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener empresas"
        )

@router.get(
    "/empresas/{empresa_id}",
    response_model=EmpresaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener empresa por ID",
    description="Obtiene una empresa con direccion incluida"
)
def get_empresa(
    empresa_id: int,
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    try:
        empresa = EmpresaService.get_empresa_by_id(db, empresa_id)
        
        if not empresa:
            logger.warning(f"Empresa {empresa_id} no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        return empresa
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener empresa {empresa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la empresa"
        )

@router.post(
    "/empresas", 
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED,  
    summary="Crear nueva empresa",
    description="Crea una nueva empresa con dirección"
)
def create_empresa(
    empresa: EmpresaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validar que es tipo EMPRESA
    if current_user.tipo_usuario.value != "EMPRESA": 
        raise HTTPException(
            status_code=403,
            detail="Solo usuarios tipo EMPRESA pueden crear empresas"
        )
    try:
        db_empresa = EmpresaService.create_empresa_complete(db, empresa)
        
        logger.info(f"Empresa '{db_empresa.razon_social}' creada exitosamente para usuario {empresa.usuario_id}")
        return db_empresa
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear empresa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la empresa"
        )

@router.get(
    "/empresas/usuario/{usuario_id}",
    response_model=EmpresaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener empresa de un usuario",
    description="Obtiene la empresa de un usuario con direccion incluida"
)
def get_empresa_by_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    # Validar que solo puede ver su propia empresa o es admin
    if current_user.usuario_id != usuario_id and current_user.tipo_usuario.value not in ["ADMIN", "SUPERADMIN"]:  
        raise HTTPException(
            status_code=403,
            detail="Solo puedes ver tu propia empresa"
        )
    try:
        usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {usuario_id} no encontrado"
            )
        
        if usuario.tipo_usuario != TipoUsuario.EMPRESA:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El usuario tipo '{usuario.tipo_usuario}' no puede tener empresas"
            )
        
        empresa = EmpresaService.get_empresa_by_usuario_id(db, usuario_id)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El usuario no tiene una empresa registrada"
            )
        
        return empresa
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener empresa del usuario {usuario_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la empresa del usuario"
        )
# =============================================
# GESTIÓN DE EQUIPO
# =============================================

@router.get(
    "/empresas/{empresa_id}/equipo",
    response_model=EquipoListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar equipo de la empresa",
    description="""
    Lista todos los miembros del equipo de una empresa.
    
    **Permisos requeridos:** roles:leer_empresa
    
    **Incluye:**
    - Miembros activos e inactivos
    - Información de rol asignado
    - Fechas de asignación/desactivación
    """
)
def listar_equipo(
    empresa_id: int,
    solo_activos: bool = Query(True, description="Mostrar solo miembros activos"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista el equipo de una empresa con validación de permisos"""
    
    try:
        # Verificar que el usuario pertenezca a la empresa
        usuario_rol = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver el equipo de esta empresa"
            )
        
        # Obtener equipo
        query = db.query(Usuario, Rol, UsuarioRol)\
            .join(UsuarioRol, Usuario.usuario_id == UsuarioRol.usuario_id)\
            .join(Rol, UsuarioRol.rol_id == Rol.rol_id)\
            .filter(UsuarioRol.empresa_id == empresa_id)
        
        if solo_activos:
            query = query.filter(UsuarioRol.activo == True)
        
        resultado = query.order_by(Rol.nivel.desc(), Usuario.nombre).all()
        
        # Construir respuesta
        equipo = []
        for usuario, rol, usuario_rol in resultado:
            equipo.append(EquipoMiembro(
                usuario_id=usuario.usuario_id,
                nombre=usuario.nombre,
                email=usuario.email,
                rol=rol.nombre,
                rol_id=rol.rol_id,
                activo=usuario_rol.activo,
                fecha_asignado=usuario_rol.fecha_asignado,
                fecha_desactivacion=getattr(usuario_rol, 'fecha_desactivacion', None)
            ))
        
        # Contar totales
        total = len(equipo)
        activos = sum(1 for m in equipo if m.activo)
        
        logger.info(f"Equipo de empresa {empresa_id}: {activos} activos de {total} total")
        
        return EquipoListResponse(
            total=total,
            activos=activos,
            equipo=equipo
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al listar equipo de empresa {empresa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el equipo de la empresa"
        )
# =============================================
# INVITAR NUEVO MIEMBRO
# =============================================

@router.post(
    "/empresas/{empresa_id}/invitaciones",
    response_model=InvitacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invitar nuevo miembro al equipo",
    description="""
    Invita a un nuevo miembro a unirse al equipo de la empresa.
    
    **Permisos requeridos:** usuarios:crear_empresa o roles:asignar_empresa
    
    **Validaciones:**
    - Email no debe existir ya en el sistema
    - Rol debe ser válido para empresas (EMPLEADO, RECEPCIONISTA, ADMIN_EMPRESA)
    - No se puede asignar DUEÑO_EMPRESA
    - El usuario actual debe pertenecer a la empresa
    
    **Auditoría:** Se registra automáticamente la invitación
    """
)
def invitar_miembro(
    empresa_id: int,
    invitacion: InvitacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Invita un nuevo miembro al equipo de la empresa"""
    
    try:
        # Verificar que el usuario actual pertenezca a la empresa
        usuario_rol_actual = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol_actual:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces a esta empresa"
            )
        
        # Verificar permisos usando el servicio de permisos
        permission_service = PermissionService(db)
        
        # Verificar si tiene alguno de los permisos necesarios
        tiene_permiso_crear = permission_service.usuario_tiene_permiso(
            current_user.usuario_id, 
            "usuarios:crear_empresa", 
            empresa_id
        )
        tiene_permiso_asignar = permission_service.usuario_tiene_permiso(
            current_user.usuario_id, 
            "roles:asignar_empresa", 
            empresa_id
        )
        tiene_permiso_gestionar = permission_service.usuario_tiene_permiso(
            current_user.usuario_id, 
            "usuarios:gestionar_empresa", 
            empresa_id
        )
        
        if not (tiene_permiso_crear or tiene_permiso_asignar or tiene_permiso_gestionar):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para invitar miembros. Necesitas uno de: usuarios:crear_empresa, roles:asignar_empresa, usuarios:gestionar_empresa"
            )
        
        # Validar que el rol a asignar existe y es válido
        rol_a_asignar = db.query(Rol).filter(
            Rol.nombre == invitacion.rol.value,
            Rol.activo == True
        ).first()
        
        if not rol_a_asignar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol '{invitacion.rol}' no existe o está inactivo"
            )
        
        # Validar que el rol es de tipo empresa
        if rol_a_asignar.tipo != "empresa":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol '{invitacion.rol}' no es válido para empresas"
            )
        
        # Validar que no intenta asignar DUEÑO_EMPRESA
        if rol_a_asignar.nombre == "DUEÑO_EMPRESA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No se puede asignar el rol DUEÑO_EMPRESA. Solo puede haber un dueño por empresa"
            )
        
        # Verificar si el email ya existe
        usuario_existente = db.query(Usuario).filter(
            Usuario.email == invitacion.email
        ).first()
        
        if usuario_existente:
            # Verificar si ya está en la empresa
            ya_en_empresa = db.query(UsuarioRol).filter(
                UsuarioRol.usuario_id == usuario_existente.usuario_id,
                UsuarioRol.empresa_id == empresa_id
            ).first()
            
            if ya_en_empresa:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este usuario ya pertenece a la empresa"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un usuario con ese email en el sistema"
                )
        
        # Generar token de invitación (simple por ahora, mejorar después)
        token_invitacion = f"inv_{secrets.token_urlsafe(32)}"
        
        # TODO: Guardar invitación en tabla (implementar después)
        # Por ahora solo registramos en auditoría
        
        # Registrar en auditoría
        auditoria = AuditoriaSistema(
            tabla_afectada="invitaciones_pendientes",
            accion="CREAR_INVITACION",
            registro_id=0,  # Temporal: 0 porque no hay tabla de invitaciones aun
            usuario_id=current_user.usuario_id,
            empresa_id=empresa_id,
            datos_nuevos={
                "email": invitacion.email,
                "rol": invitacion.rol.value,
                "empresa_id": empresa_id,
                "invitado_por": current_user.nombre,
                "invitado_por_id": current_user.usuario_id,
                "token": token_invitacion[:20] + "..."  # Solo primeros 20 caracteres por seguridad
            },
            motivo=f"Invitacion a {invitacion.email} como {invitacion.rol.value}",
            ip_address=None,  # TODO: Obtener IP del request
            user_agent=None   # TODO: Obtener user agent del request
        )
        db.add(auditoria)
        
        # TODO: Enviar email con el token de invitación
        # Por ahora, devolvemos el token en la respuesta (EN PRODUCCIÓN ESTO SE ENVIARÍA POR EMAIL)
        
        db.commit()
        
        logger.info(
            f"Invitación creada: {invitacion.email} para empresa {empresa_id} "
            f"con rol {invitacion.rol} por usuario {current_user.email}"
        )
        
        return InvitacionResponse(
            message=f"Invitación enviada exitosamente a {invitacion.email}",
            email=invitacion.email,
            rol=invitacion.rol.value,
            empresa_id=empresa_id,
            token_invitacion=token_invitacion  # EN PRODUCCIÓN: No devolver, enviar por email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear invitación para empresa {empresa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la invitación"
        )
        
# =============================================
# CAMBIAR ROL DE MIEMBRO
# =============================================

@router.put(
    "/empresas/{empresa_id}/equipo/{usuario_id}/rol",
    response_model=CambioRolResponse,
    status_code=status.HTTP_200_OK,
    summary="Cambiar rol de un miembro del equipo",
    description="""
    Cambia el rol asignado a un miembro del equipo.
    
    **Permisos requeridos:** roles:asignar_empresa
    
    **Validaciones:**
    - Solo usuarios con permiso pueden cambiar roles
    - No puede cambiar su propio rol
    - No puede asignar DUEÑO_EMPRESA
    - El nuevo rol debe ser válido para empresas
    - El usuario debe pertenecer a la empresa
    
    **Auditoría:** Se registra automáticamente el cambio de rol
    """
)
def cambiar_rol_miembro(
    empresa_id: int,
    usuario_id: int,
    cambio_rol: CambiarRolRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Cambia el rol de un miembro del equipo"""
    
    try:
        # Verificar que el usuario actual pertenezca a la empresa
        usuario_rol_actual = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol_actual:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces a esta empresa"
            )
        
        # Verificar permisos
        permission_service = PermissionService(db)
        tiene_permiso = permission_service.usuario_tiene_permiso(
            current_user.usuario_id,
            "roles:asignar_empresa",
            empresa_id
        )
        
        if not tiene_permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para cambiar roles. Necesitas: roles:asignar_empresa"
            )
        
        # Validar que no intenta cambiar su propio rol
        if usuario_id == current_user.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes cambiar tu propio rol"
            )
        
        # Obtener el usuario_rol del miembro a modificar
        usuario_rol_modificar = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol_modificar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no pertenece a esta empresa o está inactivo"
            )
        
        # Obtener rol anterior para auditoría
        rol_anterior = db.query(Rol).filter(
            Rol.rol_id == usuario_rol_modificar.rol_id
        ).first()
        
        # Validar que el nuevo rol existe y es válido
        nuevo_rol = db.query(Rol).filter(
            Rol.nombre == cambio_rol.nuevo_rol.value,
            Rol.activo == True
        ).first()
        
        if not nuevo_rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol '{cambio_rol.nuevo_rol}' no existe o está inactivo"
            )
        
        # Validar que el rol es de tipo empresa
        if nuevo_rol.tipo != "empresa":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol '{cambio_rol.nuevo_rol}' no es válido para empresas"
            )
        
        # Validar que no intenta asignar DUEÑO_EMPRESA
        if nuevo_rol.nombre == "DUEÑO_EMPRESA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No se puede asignar el rol DUEÑO_EMPRESA. Solo puede haber un dueño por empresa"
            )
        
        # Validar que el nuevo rol es diferente al actual
        if usuario_rol_modificar.rol_id == nuevo_rol.rol_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El usuario ya tiene el rol {nuevo_rol.nombre}"
            )
        
        # Obtener información del usuario para la respuesta
        usuario_modificado = db.query(Usuario).filter(
            Usuario.usuario_id == usuario_id
        ).first()
        
        # Registrar en auditoría ANTES del cambio
        auditoria = AuditoriaSistema(
            tabla_afectada="usuario_rol",
            accion="CAMBIO_ROL",
            registro_id=usuario_rol_modificar.usuario_rol_id,
            usuario_id=current_user.usuario_id,
            empresa_id=empresa_id,
            datos_anteriores={
                "usuario_id": usuario_id,
                "rol_anterior": rol_anterior.nombre,
                "rol_anterior_id": rol_anterior.rol_id
            },
            datos_nuevos={
                "usuario_id": usuario_id,
                "rol_nuevo": nuevo_rol.nombre,
                "rol_nuevo_id": nuevo_rol.rol_id
            },
            motivo=f"Cambio de rol de {usuario_modificado.nombre}: {rol_anterior.nombre} → {nuevo_rol.nombre}",
            ip_address=None,
            user_agent=None
        )
        db.add(auditoria)
        
        # Actualizar el rol
        usuario_rol_modificar.rol_id = nuevo_rol.rol_id
        usuario_rol_modificar.asignado_por = current_user.usuario_id
        
        db.commit()
        fecha_cambio = datetime.now()
        db.refresh(usuario_rol_modificar)
        
        logger.info(
            f"Rol cambiado para usuario {usuario_id} en empresa {empresa_id}: "
            f"{rol_anterior.nombre} → {nuevo_rol.nombre} por {current_user.email}"
        )
        
        return CambioRolResponse(
            message=f"Rol cambiado exitosamente de {rol_anterior.nombre} a {nuevo_rol.nombre}",
            usuario_id=usuario_id,
            usuario_nombre=usuario_modificado.nombre,
            rol_anterior=rol_anterior.nombre,
            rol_nuevo=nuevo_rol.nombre,
            cambiado_por=current_user.nombre,
            fecha_cambio=fecha_cambio
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al cambiar rol en empresa {empresa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cambiar el rol del miembro"
        )
# =============================================
# ENDPOINT TEMPORAL PARA TESTING - CREAR MIEMBRO DIRECTO
# =============================================

@router.post(
    "/empresas/{empresa_id}/equipo/crear-test",
    response_model=EquipoMiembro,
    status_code=status.HTTP_201_CREATED,
    summary="[TESTING] Crear miembro directamente",
    description="""
    **ENDPOINT TEMPORAL PARA TESTING**
    
    Crea un usuario y lo asigna directamente a la empresa con un rol.
    Este endpoint salta el flujo de invitaciones para facilitar las pruebas.
    
    **TODO: ELIMINAR en producción**
    """
)
def crear_miembro_test(
    empresa_id: int,
    email: str = Query(..., description="Email del nuevo miembro"),
    nombre: str = Query(..., description="Nombre del nuevo miembro"),
    rol: str = Query("EMPLEADO", description="Rol a asignar (EMPLEADO, RECEPCIONISTA, ADMIN_EMPRESA)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """[TESTING] Crea un miembro directamente sin flujo de invitación"""
    
    try:
        # Verificar que el usuario actual pertenezca a la empresa
        usuario_rol_actual = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol_actual:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces a esta empresa"
            )
        
        # Verificar si el email ya existe
        usuario_existente = db.query(Usuario).filter(
            Usuario.email == email
        ).first()
        
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese email"
            )
        
        # Obtener el rol
        rol_asignar = db.query(Rol).filter(
            Rol.nombre == rol,
            Rol.activo == True
        ).first()
        
        if not rol_asignar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol '{rol}' no existe"
            )
        
        # Crear el usuario
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        nuevo_usuario = Usuario(
            email=email,
            password=pwd_context.hash("Test123456"),  # Password fijo para testing
            nombre=nombre,
            telefono="0000000000",
            tipo_usuario=TipoUsuario.EMPRESA
        )
        db.add(nuevo_usuario)
        db.flush()  # Para obtener el usuario_id
        
        # Asignar rol en la empresa
        nuevo_usuario_rol = UsuarioRol(
            usuario_id=nuevo_usuario.usuario_id,
            rol_id=rol_asignar.rol_id,
            empresa_id=empresa_id,
            asignado_por=current_user.usuario_id,
            activo=True
        )
        db.add(nuevo_usuario_rol)
        
        # Registrar en auditoría
        auditoria = AuditoriaSistema(
            tabla_afectada="usuario",
            accion="CREAR_USUARIO_TEST",
            registro_id=nuevo_usuario.usuario_id,
            usuario_id=current_user.usuario_id,
            empresa_id=empresa_id,
            datos_nuevos={
                "email": email,
                "nombre": nombre,
                "rol": rol,
                "tipo": "testing"
            },
            motivo=f"Usuario de prueba creado: {nombre} ({rol})",
            ip_address=None,
            user_agent=None
        )
        db.add(auditoria)
        
        db.commit()
        db.refresh(nuevo_usuario)
        db.refresh(nuevo_usuario_rol)
        
        logger.info(f"[TESTING] Usuario de prueba creado: {email} con rol {rol} en empresa {empresa_id}")
        
        return EquipoMiembro(
            usuario_id=nuevo_usuario.usuario_id,
            nombre=nuevo_usuario.nombre,
            email=nuevo_usuario.email,
            rol=rol_asignar.nombre,
            rol_id=rol_asignar.rol_id,
            activo=True,
            fecha_asignado=nuevo_usuario_rol.fecha_asignado,
            fecha_desactivacion=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear usuario de prueba: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario de prueba: {str(e)}"
        )        

# =============================================
# DESACTIVAR MIEMBRO (SOFT DELETE)
# =============================================

@router.patch(
    "/empresas/{empresa_id}/equipo/{usuario_id}/desactivar",
    response_model=DesactivacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar un miembro del equipo",
    description="""
    Desactiva un miembro del equipo (soft delete).
    
    **Permisos requeridos:** usuarios:desactivar_empresa
    
    **Validaciones:**
    - Solo usuarios con permiso pueden desactivar
    - No puede desactivarse a sí mismo
    - El usuario debe pertenecer a la empresa y estar activo
    - Debe proporcionar un motivo
    
    **Auditoría:** Se registra automáticamente la desactivación
    
    **Nota:** Esto es un SOFT DELETE - el usuario no se elimina de la BD
    """
)
def desactivar_miembro(
    empresa_id: int,
    usuario_id: int,
    desactivacion: DesactivarMiembroRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Desactiva un miembro del equipo (soft delete)"""
    
    try:
        # Verificar que el usuario actual pertenezca a la empresa
        usuario_rol_actual = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol_actual:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces a esta empresa"
            )
        
        # Verificar permisos
        permission_service = PermissionService(db)
        tiene_permiso = permission_service.usuario_tiene_permiso(
            current_user.usuario_id,
            "usuarios:desactivar_empresa",
            empresa_id
        )
        
        if not tiene_permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para desactivar miembros. Necesitas: usuarios:desactivar_empresa"
            )
        
        # Validar que no intenta desactivarse a sí mismo
        if usuario_id == current_user.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes desactivarte a ti mismo"
            )
        
        # Obtener el usuario_rol del miembro a desactivar
        usuario_rol_desactivar = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol_desactivar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no pertenece a esta empresa o ya está inactivo"
            )
        
        # Obtener información del usuario y rol para la respuesta
        usuario_desactivado = db.query(Usuario).filter(
            Usuario.usuario_id == usuario_id
        ).first()
        
        rol_usuario = db.query(Rol).filter(
            Rol.rol_id == usuario_rol_desactivar.rol_id
        ).first()
        
        # Registrar en auditoría ANTES de desactivar
        from datetime import datetime
        fecha_cambio = datetime.now()
        
        auditoria = AuditoriaSistema(
            tabla_afectada="usuario_rol",
            accion="DESACTIVAR_MIEMBRO",
            registro_id=usuario_rol_desactivar.usuario_rol_id,
            usuario_id=current_user.usuario_id,
            empresa_id=empresa_id,
            datos_anteriores={
                "usuario_id": usuario_id,
                "usuario_nombre": usuario_desactivado.nombre,
                "rol": rol_usuario.nombre,
                "activo": True
            },
            datos_nuevos={
                "usuario_id": usuario_id,
                "usuario_nombre": usuario_desactivado.nombre,
                "rol": rol_usuario.nombre,
                "activo": False,
                "motivo": desactivacion.motivo
            },
            motivo=f"Desactivación de {usuario_desactivado.nombre}: {desactivacion.motivo}",
            ip_address=None,
            user_agent=None
        )
        db.add(auditoria)
        
        # Desactivar el miembro (SOFT DELETE)
        usuario_rol_desactivar.activo = False
        usuario_rol_desactivar.motivo_inactivacion = desactivacion.motivo
        
        db.commit()
        db.refresh(usuario_rol_desactivar)
        
        logger.info(
            f"Miembro desactivado: usuario {usuario_id} en empresa {empresa_id} "
            f"por {current_user.email}. Motivo: {desactivacion.motivo}"
        )
        
        return DesactivacionResponse(
            message=f"Miembro {usuario_desactivado.nombre} desactivado exitosamente",
            usuario_id=usuario_id,
            activo=False,
            fecha_cambio=fecha_cambio,
            motivo=desactivacion.motivo
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al desactivar miembro en empresa {empresa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desactivar el miembro"
        )

# =============================================
# REACTIVAR MIEMBRO
# =============================================

@router.patch(
    "/empresas/{empresa_id}/equipo/{usuario_id}/reactivar",
    response_model=DesactivacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivar un miembro del equipo",
    description="""
    Reactiva un miembro del equipo que fue desactivado previamente.
    
    **Permisos requeridos:** usuarios:gestionar_empresa
    
    **Validaciones:**
    - Solo usuarios con permiso pueden reactivar
    - El usuario debe pertenecer a la empresa y estar inactivo
    - Se elimina el motivo de inactivación al reactivar
    
    **Auditoría:** Se registra automáticamente la reactivación
    """
)
def reactivar_miembro(
    empresa_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Reactiva un miembro del equipo previamente desactivado"""
    
    try:
        # Verificar que el usuario actual pertenezca a la empresa
        usuario_rol_actual = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == current_user.usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == True
        ).first()
        
        if not usuario_rol_actual:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No perteneces a esta empresa"
            )
        
        # Verificar permisos
        permission_service = PermissionService(db)
        tiene_permiso = permission_service.usuario_tiene_permiso(
            current_user.usuario_id,
            "usuarios:gestionar_empresa",
            empresa_id
        )
        
        if not tiene_permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para reactivar miembros. Necesitas: usuarios:gestionar_empresa"
            )
        
        # Obtener el usuario_rol del miembro a reactivar (debe estar inactivo)
        usuario_rol_reactivar = db.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.empresa_id == empresa_id,
            UsuarioRol.activo == False
        ).first()
        
        if not usuario_rol_reactivar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no pertenece a esta empresa o ya está activo"
            )
        
        # Obtener información del usuario y rol para la respuesta
        usuario_reactivado = db.query(Usuario).filter(
            Usuario.usuario_id == usuario_id
        ).first()
        
        rol_usuario = db.query(Rol).filter(
            Rol.rol_id == usuario_rol_reactivar.rol_id
        ).first()
        
        # Guardar motivo anterior para auditoría
        motivo_anterior = usuario_rol_reactivar.motivo_inactivacion
        
        # Registrar en auditoría ANTES de reactivar
        from datetime import datetime
        fecha_cambio = datetime.now()
        
        auditoria = AuditoriaSistema(
            tabla_afectada="usuario_rol",
            accion="REACTIVAR_MIEMBRO",
            registro_id=usuario_rol_reactivar.usuario_rol_id,
            usuario_id=current_user.usuario_id,
            empresa_id=empresa_id,
            datos_anteriores={
                "usuario_id": usuario_id,
                "usuario_nombre": usuario_reactivado.nombre,
                "rol": rol_usuario.nombre,
                "activo": False,
                "motivo_inactivacion": motivo_anterior
            },
            datos_nuevos={
                "usuario_id": usuario_id,
                "usuario_nombre": usuario_reactivado.nombre,
                "rol": rol_usuario.nombre,
                "activo": True,
                "motivo_inactivacion": None
            },
            motivo=f"Reactivación de {usuario_reactivado.nombre} (anteriormente desactivado por: {motivo_anterior or 'sin motivo'})",
            ip_address=None,
            user_agent=None
        )
        db.add(auditoria)
        
        # Reactivar el miembro
        usuario_rol_reactivar.activo = True
        usuario_rol_reactivar.motivo_inactivacion = None
        
        db.commit()
        db.refresh(usuario_rol_reactivar)
        
        logger.info(
            f"Miembro reactivado: usuario {usuario_id} en empresa {empresa_id} "
            f"por {current_user.email}"
        )
        
        return DesactivacionResponse(
            message=f"Miembro {usuario_reactivado.nombre} reactivado exitosamente",
            usuario_id=usuario_id,
            activo=True,
            fecha_cambio=fecha_cambio,
            motivo=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al reactivar miembro en empresa {empresa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al reactivar el miembro"
        )