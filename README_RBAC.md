# 🔐 Sistema de Roles y Permisos (RBAC) - MiTurno API

Sistema completo de control de acceso basado en roles (Role-Based Access Control) con permisos granulares y contextos de aplicación.

---

## 🎯 **Características**

- ✅ 7 roles jerárquicos predefinidos
- ✅ 31 permisos granulares
- ✅ Asignación de roles por usuario y contexto (empresa)
- ✅ Permisos globales y específicos por empresa
- ✅ Sistema de jerarquía de roles
- ✅ Validación automática en endpoints
- ✅ Vista consolidada de permisos activos
- ✅ Fecha de vencimiento de roles (opcional)

---

## 👥 **Roles del Sistema**

### **Jerarquía de Roles**

```
SUPER_ADMIN (nivel 7)
    ↓
ADMIN_SISTEMA (nivel 6)
    ↓
DUEÑO_EMPRESA (nivel 5)
    ↓
ADMIN_EMPRESA (nivel 4)
    ↓
RECEPCIONISTA (nivel 3)
    ↓
EMPLEADO (nivel 2)
    ↓
CLIENTE (nivel 1)
```

### **1. CLIENTE** (Nivel 1)

**Descripción:** Usuario que reserva turnos y utiliza servicios

**Permisos:**
- Crear turnos propios
- Ver turnos propios
- Modificar turnos propios
- Cancelar turnos propios
- Crear calificaciones propias
- Ver calificaciones propias
- Crear mensajes propios

**Contexto:** Global (sin empresa asociada)

---

### **2. EMPLEADO** (Nivel 2)

**Descripción:** Trabajador de una empresa específica

**Permisos heredados de CLIENTE +**
- Ver turnos de su empresa
- Ver clientes de su empresa
- Ver servicios de su empresa

**Contexto:** Específico por empresa

---

### **3. RECEPCIONISTA** (Nivel 3)

**Descripción:** Personal de atención al cliente de una empresa

**Permisos heredados de EMPLEADO +**
- Crear turnos para la empresa
- Modificar turnos de la empresa
- Cancelar turnos de la empresa
- Ver estadísticas básicas de la empresa

**Contexto:** Específico por empresa

---

### **4. ADMIN_EMPRESA** (Nivel 4)

**Descripción:** Administrador de una empresa específica

**Permisos heredados de RECEPCIONISTA +**
- Actualizar información de la empresa
- Crear/editar/eliminar servicios
- Gestionar horarios
- Gestionar empleados
- Ver estadísticas completas
- Responder calificaciones

**Contexto:** Específico por empresa

---

### **5. DUEÑO_EMPRESA** (Nivel 5)

**Descripción:** Propietario de una empresa

**Permisos heredados de ADMIN_EMPRESA +**
- Eliminar empresa
- Transferir propiedad
- Gestionar administradores
- Acceso total a la empresa

**Contexto:** Específico por empresa

---

### **6. ADMIN_SISTEMA** (Nivel 6)

**Descripción:** Administrador de la plataforma

**Permisos:**
- Ver todas las empresas
- Ver todas las categorías
- Gestionar usuarios
- Ver estadísticas globales
- Moderar contenido
- Suspender empresas

**Contexto:** Global

---

### **7. SUPER_ADMIN** (Nivel 7)

**Descripción:** Administrador supremo del sistema

**Permisos:**
- Todos los permisos del sistema
- Gestionar roles y permisos
- Acceso completo a la plataforma

**Contexto:** Global

---

## 🔑 **Permisos Granulares**

### **Estructura de Permisos**

Formato: `{recurso}:{acción}:{contexto}`

Ejemplo: `turno:crear:propio`

### **Categorías de Permisos**

#### **1. Turnos (10 permisos)**
- `turno:crear:propio` - Crear turnos propios
- `turno:crear:empresa` - Crear turnos para la empresa
- `turno:leer:propio` - Ver turnos propios
- `turno:leer:empresa` - Ver turnos de la empresa
- `turno:actualizar:propio` - Modificar turnos propios
- `turno:actualizar:empresa` - Modificar turnos de la empresa
- `turno:cancelar:propio` - Cancelar turnos propios
- `turno:cancelar:empresa` - Cancelar turnos de la empresa
- `turno:eliminar:propio` - Eliminar turnos propios
- `turno:eliminar:empresa` - Eliminar turnos de la empresa

#### **2. Empresas (7 permisos)**
- `empresa:crear` - Crear nueva empresa
- `empresa:leer:propia` - Ver información de su empresa
- `empresa:leer:todas` - Ver todas las empresas
- `empresa:actualizar:propia` - Actualizar su empresa
- `empresa:eliminar:propia` - Eliminar su empresa
- `empresa:gestionar:usuarios` - Gestionar usuarios de la empresa
- `empresa:ver:estadisticas` - Ver estadísticas

#### **3. Servicios (4 permisos)**
- `servicio:crear` - Crear servicios
- `servicio:leer` - Ver servicios
- `servicio:actualizar` - Actualizar servicios
- `servicio:eliminar` - Eliminar servicios

#### **4. Calificaciones (3 permisos)**
- `calificacion:crear:propia` - Crear calificaciones propias
- `calificacion:leer:propia` - Ver calificaciones propias
- `calificacion:responder` - Responder calificaciones

#### **5. Mensajes (3 permisos)**
- `mensaje:crear:propio` - Enviar mensajes propios
- `mensaje:leer:propio` - Ver mensajes propios
- `mensaje:leer:empresa` - Ver mensajes de la empresa

#### **6. Sistema (4 permisos)**
- `sistema:administrar:usuarios` - Gestionar usuarios del sistema
- `sistema:administrar:roles` - Gestionar roles y permisos
- `sistema:ver:estadisticas` - Ver estadísticas globales
- `sistema:moderar:contenido` - Moderar contenido de la plataforma

---

## 📡 **Endpoints Disponibles**

### **1. GET `/api/v1/test/mis-permisos`**

Obtiene todos los permisos activos del usuario autenticado.

**Requiere autenticación:** ✅

**Response (200 OK):**
```json
{
  "usuario_id": 9,
  "email": "test.cliente@miturno.com",
  "roles": [
    {
      "rol_id": 1,
      "nombre": "CLIENTE",
      "tipo": "SISTEMA",
      "nivel": 1,
      "empresa_id": null,
      "empresa_nombre": null,
      "activo": true,
      "fecha_asignacion": "2025-01-15T10:00:00"
    }
  ],
  "permisos": [
    {
      "codigo": "turno:crear:propio",
      "nombre": "Crear turno propio",
      "recurso": "turno",
      "accion": "crear",
      "requiere_contexto": true,
      "rol_origen": "CLIENTE"
    },
    {
      "codigo": "turno:leer:propio",
      "nombre": "Ver turnos propios",
      "recurso": "turno",
      "accion": "leer",
      "requiere_contexto": true,
      "rol_origen": "CLIENTE"
    }
  ],
  "total_permisos": 7
}
```

**Errores:**
- `401`: No autenticado

---

### **2. GET `/api/v1/test/verificar-permiso/{codigo_permiso}`**

Verifica si el usuario tiene un permiso específico.

**Requiere autenticación:** ✅

**Path Parameters:**
- `codigo_permiso` (required): Código del permiso a verificar (ej: "turno:crear:propio")

**Response (200 OK):**
```json
{
  "tiene_permiso": true,
  "codigo": "turno:crear:propio",
  "nombre": "Crear turno propio",
  "mensaje": "Usuario tiene el permiso"
}
```

**Response (403 Forbidden):**
```json
{
  "tiene_permiso": false,
  "codigo": "turno:crear:empresa",
  "mensaje": "Usuario no tiene el permiso"
}
```

**Errores:**
- `401`: No autenticado
- `404`: Permiso no existe

---

## 🔐 **Autenticación y Validación**

### **Validación Automática en Endpoints**

Cada endpoint protegido valida automáticamente los permisos requeridos:

```python
@router.post("/turnos/reservar")
async def reservar_turno(
    current_user: Usuario = Depends(require_permission("turno:crear:propio"))
):
    # Endpoint solo accesible si el usuario tiene el permiso
    pass
```

### **Contexto de Empresa**

Los permisos específicos de empresa se validan con el contexto:

```python
# Ejemplo: Solo empleados de la empresa pueden ver sus turnos
@router.get("/empresas/{empresa_id}/turnos")
async def listar_turnos_empresa(
    empresa_id: int,
    current_user: Usuario = Depends(require_permission("turno:leer:empresa"))
):
    # Valida que el usuario tenga el rol en esa empresa específica
    pass
```

---

## 🧪 **Ejemplos de Uso**

### **Caso 1: Cliente verifica sus permisos**

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/test/mis-permisos',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

const data = await response.json();

console.log(`Usuario: ${data.email}`);
console.log(`Roles: ${data.roles.length}`);
console.log(`Total permisos: ${data.total_permisos}`);

// Listar permisos
data.permisos.forEach(permiso => {
  console.log(`- ${permiso.nombre} (${permiso.codigo})`);
});
```

---

### **Caso 2: Verificar permiso específico**

```javascript
const codigoPermiso = 'turno:crear:empresa';

const response = await fetch(
  `http://localhost:8000/api/v1/test/verificar-permiso/${codigoPermiso}`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

const resultado = await response.json();

if (resultado.tiene_permiso) {
  console.log('✅ Usuario puede crear turnos para la empresa');
  // Mostrar botón "Crear Turno"
} else {
  console.log('❌ Usuario no tiene permiso');
  // Ocultar funcionalidad
}
```

---

### **Caso 3: Frontend adapta UI según permisos**

```javascript
async function cargarPermisos() {
  const token = localStorage.getItem('token');
  
  const response = await fetch('/api/v1/test/mis-permisos', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const { permisos } = await response.json();
  
  // Crear mapa de permisos para acceso rápido
  const permisosMap = {};
  permisos.forEach(p => {
    permisosMap[p.codigo] = true;
  });
  
  // Mostrar/ocultar elementos según permisos
  if (permisosMap['turno:crear:empresa']) {
    document.getElementById('btn-crear-turno').style.display = 'block';
  }
  
  if (permisosMap['empresa:ver:estadisticas']) {
    document.getElementById('menu-estadisticas').style.display = 'block';
  }
  
  if (permisosMap['calificacion:responder']) {
    document.getElementById('btn-responder').style.display = 'block';
  }
}
```

---

## 🎨 **Integración con Frontend**

### **React - Hook de Permisos**

```jsx
import { useState, useEffect, createContext, useContext } from 'react';

const PermisosContext = createContext();

export function PermisosProvider({ children }) {
  const [permisos, setPermisos] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarPermisos();
  }, []);

  const cargarPermisos = async () => {
    const token = localStorage.getItem('token');
    
    const response = await fetch(`${API_URL}/test/mis-permisos`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const data = await response.json();
    
    // Crear mapa de permisos
    const permisosMap = {};
    data.permisos.forEach(p => {
      permisosMap[p.codigo] = true;
    });
    
    setPermisos(permisosMap);
    setLoading(false);
  };

  const tienePermiso = (codigo) => {
    return !!permisos[codigo];
  };

  return (
    <PermisosContext.Provider value={{ permisos, tienePermiso, loading }}>
      {children}
    </PermisosContext.Provider>
  );
}

// Hook personalizado
export function usePermisos() {
  return useContext(PermisosContext);
}
```

### **Uso del Hook**

```jsx
function Dashboard() {
  const { tienePermiso, loading } = usePermisos();

  if (loading) return <p>Cargando permisos...</p>;

  return (
    <div className="dashboard">
      <h1>Panel de Control</h1>
      
      {tienePermiso('turno:crear:empresa') && (
        <button onClick={crearTurno}>Crear Turno</button>
      )}
      
      {tienePermiso('empresa:ver:estadisticas') && (
        <EstadisticasComponent />
      )}
      
      {tienePermiso('calificacion:responder') && (
        <ResponderCalificacionesComponent />
      )}
      
      {!tienePermiso('turno:crear:empresa') && (
        <p>No tienes permisos para crear turnos</p>
      )}
    </div>
  );
}
```

### **Componente de Protección**

```jsx
function ProtectedComponent({ requiredPermission, children, fallback }) {
  const { tienePermiso } = usePermisos();
  
  if (!tienePermiso(requiredPermission)) {
    return fallback || <p>No tienes permiso para ver esto</p>;
  }
  
  return children;
}

// Uso
<ProtectedComponent requiredPermission="empresa:ver:estadisticas">
  <EstadisticasComponent />
</ProtectedComponent>
```

---

## 🗄️ **Base de Datos**

### **Tabla: rol**

```sql
CREATE TABLE rol (
    rol_id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    tipo ENUM('SISTEMA', 'EMPRESA', 'PERSONALIZADO') DEFAULT 'SISTEMA',
    nivel INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_nombre (nombre),
    INDEX idx_nivel (nivel)
);
```

### **Tabla: permiso**

```sql
CREATE TABLE permiso (
    permiso_id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    recurso VARCHAR(50) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    requiere_contexto BOOLEAN DEFAULT FALSE,
    requiere_consentimiento BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_codigo (codigo),
    INDEX idx_recurso (recurso)
);
```

### **Tabla: rol_permiso**

```sql
CREATE TABLE rol_permiso (
    rol_id INT NOT NULL,
    permiso_id INT NOT NULL,
    PRIMARY KEY (rol_id, permiso_id),
    FOREIGN KEY (rol_id) REFERENCES rol(rol_id) ON DELETE CASCADE,
    FOREIGN KEY (permiso_id) REFERENCES permiso(permiso_id) ON DELETE CASCADE
);
```

### **Tabla: usuario_rol**

```sql
CREATE TABLE usuario_rol (
    usuario_rol_id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    rol_id INT NOT NULL,
    empresa_id INT,
    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento DATE,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (rol_id) REFERENCES rol(rol_id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id) REFERENCES empresa(empresa_id) ON DELETE CASCADE,
    INDEX idx_usuario (usuario_id),
    INDEX idx_rol (rol_id),
    INDEX idx_empresa (empresa_id)
);
```

### **Vista: usuario_permisos_activos**

```sql
CREATE VIEW usuario_permisos_activos AS
SELECT 
    ur.usuario_id,
    ur.empresa_id,
    p.codigo AS permiso_codigo,
    p.nombre AS permiso_nombre,
    p.recurso,
    p.accion,
    p.requiere_contexto,
    p.requiere_consentimiento,
    r.nombre AS rol_nombre,
    r.tipo AS rol_tipo,
    r.nivel AS rol_nivel
FROM usuario_rol ur
JOIN rol r ON ur.rol_id = r.rol_id
JOIN rol_permiso rp ON r.rol_id = rp.rol_id
JOIN permiso p ON rp.permiso_id = p.permiso_id
WHERE 
    ur.activo = TRUE 
    AND r.activo = TRUE 
    AND p.activo = TRUE
    AND (ur.fecha_vencimiento IS NULL OR ur.fecha_vencimiento > CURDATE());
```

---

## 🔍 **Troubleshooting**

### **Error 403: "No tienes permiso para esta acción"**

**Causa:** El usuario no tiene el permiso requerido.

**Solución:**
1. Verificar permisos actuales con `/test/mis-permisos`
2. Confirmar que el rol asignado tiene ese permiso
3. Verificar que el contexto (empresa) sea correcto
4. Contactar administrador para asignación de permisos

---

### **Usuario con múltiples roles**

**Comportamiento:** El sistema combina todos los permisos de todos los roles activos.

**Ejemplo:**
- Usuario es CLIENTE (global) + EMPLEADO (Empresa A)
- Tiene permisos de ambos roles
- Los permisos de EMPLEADO solo aplican en contexto de Empresa A

---

### **Roles vencidos**

**Comportamiento:** Roles con `fecha_vencimiento` pasada no otorgan permisos.

**Solución:**
- Administrador debe renovar el rol
- O asignar nuevo rol si corresponde

---

## 📊 **Performance**

- **Consulta de permisos:** ~50-80ms (con vista optimizada)
- **Verificación de permiso:** ~20-40ms (cache en memoria)
- **Listado de roles:** ~30-50ms

**Optimizaciones aplicadas:**
- ✅ Vista `usuario_permisos_activos` precalculada
- ✅ Índices en todas las tablas
- ✅ Queries optimizados con JOINs eficientes
- ✅ Cache de permisos en sesión de usuario

---

## 🎯 **Buenas Prácticas**

### **Frontend:**
1. Cargar permisos una vez al login
2. Guardar en contexto/state global
3. Ocultar UI no accesible (mejor UX)
4. Manejar errores 403 gracefully

### **Backend:**
1. Validar permisos en cada endpoint
2. Usar decoradores/middleware para permisos
3. Loguear intentos de acceso no autorizado
4. Mantener permisos granulares y específicos

### **Seguridad:**
1. Nunca confiar solo en validación frontend
2. Siempre validar permisos en backend
3. Auditar cambios de roles/permisos
4. Revisar permisos periódicamente

---

## 🚀 **Roadmap**

- [ ] Roles personalizados por empresa
- [ ] Permisos temporales con expiración automática
- [ ] Dashboard de gestión de permisos
- [ ] Auditoría de cambios de roles
- [ ] Sistema de aprobación para permisos críticos
- [ ] Roles dinámicos basados en reglas

---

**Última actualización:** 20 de Octubre 2025  
**Versión:** 1.0.0  
**Estado:** ✅ Productivo y funcional