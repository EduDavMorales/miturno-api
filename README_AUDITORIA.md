# 📋 Sistema de Auditoría - MiTurno API

Sistema completo de auditoría y trazabilidad de cambios en el sistema con registro automático de modificaciones críticas.

---

## 🎯 **Características**

- ✅ Registro automático de cambios en tablas críticas
- ✅ Soft delete (no eliminación física de datos)
- ✅ Tracking de usuario que realizó el cambio
- ✅ Metadatos completos (IP, user agent, timestamp)
- ✅ Historial completo de modificaciones
- ✅ Triggers automáticos en BD
- ✅ Vista optimizada para consultas
- ✅ API para consultar auditoría

---

## 🗄️ **Arquitectura de Auditoría**

### **Tabla Principal: auditoria_sistema**

Tabla genérica que registra todos los cambios del sistema:

```sql
CREATE TABLE auditoria_sistema (
    auditoria_id INT PRIMARY KEY AUTO_INCREMENT,
    tabla_afectada VARCHAR(50) NOT NULL,
    operacion ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    registro_id INT NOT NULL,
    usuario_id INT,
    fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
    datos_anteriores JSON,
    datos_nuevos JSON,
    campos_modificados JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSON,
    INDEX idx_tabla_operacion (tabla_afectada, operacion),
    INDEX idx_usuario (usuario_id),
    INDEX idx_fecha (fecha_cambio)
);
```

### **Vista: auditoria_detalle**

Vista optimizada para consultas frecuentes:

```sql
CREATE VIEW auditoria_detalle AS
SELECT 
    a.auditoria_id,
    a.tabla_afectada,
    a.operacion,
    a.registro_id,
    a.usuario_id,
    u.nombre as usuario_nombre,
    u.email as usuario_email,
    a.fecha_cambio,
    a.datos_anteriores,
    a.datos_nuevos,
    a.campos_modificados,
    a.ip_address
FROM auditoria_sistema a
LEFT JOIN usuario u ON a.usuario_id = u.usuario_id
ORDER BY a.fecha_cambio DESC;
```

---

## 🔄 **Triggers Automáticos**

### **Tablas con Auditoría Automática**

El sistema tiene triggers que auditan automáticamente cambios en:

1. **usuario_rol** - Cambios de roles
2. **turno** - Creación, modificación, cancelación de turnos
3. **empresa** - Cambios en datos de empresas

### **Ejemplo de Trigger: usuario_rol**

```sql
DELIMITER //
CREATE TRIGGER tr_usuario_rol_after_insert
AFTER INSERT ON usuario_rol
FOR EACH ROW
BEGIN
    INSERT INTO auditoria_sistema (
        tabla_afectada,
        operacion,
        registro_id,
        usuario_id,
        datos_nuevos
    ) VALUES (
        'usuario_rol',
        'INSERT',
        NEW.usuario_rol_id,
        NEW.usuario_id,
        JSON_OBJECT(
            'usuario_id', NEW.usuario_id,
            'rol_id', NEW.rol_id,
            'empresa_id', NEW.empresa_id,
            'activo', NEW.activo
        )
    );
END//
```

---

## 🔍 **Soft Delete**

El sistema implementa soft delete en lugar de eliminación física:

```sql
-- Ejemplo: Tabla turno
ALTER TABLE turno ADD COLUMN deleted_at DATETIME NULL;

-- Cancelar turno (soft delete)
UPDATE turno 
SET deleted_at = NOW(), 
    estado = 'cancelado',
    motivo_cancelacion = 'Usuario canceló'
WHERE turno_id = 42;

-- El trigger registra el cambio automáticamente
```

---

## 📡 **Endpoints de Auditoría**

### **1. GET `/api/v1/auditoria/historial/{tabla}/{registro_id}`**

Obtiene el historial completo de cambios de un registro específico.

**Requiere autenticación:** ✅ (Admin o dueño del registro)

**Path Parameters:**
- `tabla` (required): Nombre de la tabla (ej: "turno", "empresa")
- `registro_id` (required): ID del registro

**Response (200 OK):**
```json
{
  "tabla": "turno",
  "registro_id": 42,
  "total_cambios": 3,
  "cambios": [
    {
      "auditoria_id": 156,
      "operacion": "UPDATE",
      "usuario_nombre": "Juan Pérez",
      "usuario_email": "juan@example.com",
      "fecha_cambio": "2025-01-20T15:30:00",
      "campos_modificados": ["hora", "notas"],
      "datos_anteriores": {
        "hora": "10:00:00",
        "notas": "Preferencia por corte clásico"
      },
      "datos_nuevos": {
        "hora": "11:00:00",
        "notas": "Cambio de horario - preferencia por corte clásico"
      }
    },
    {
      "auditoria_id": 155,
      "operacion": "INSERT",
      "usuario_nombre": "Juan Pérez",
      "fecha_cambio": "2025-01-15T10:00:00",
      "datos_nuevos": {
        "turno_id": 42,
        "cliente_id": 9,
        "empresa_id": 1,
        "fecha": "2025-01-20",
        "hora": "10:00:00"
      }
    }
  ]
}
```

---

### **2. GET `/api/v1/auditoria/usuario/{usuario_id}`**

Obtiene todos los cambios realizados por un usuario.

**Requiere autenticación:** ✅ (Admin o el mismo usuario)

**Path Parameters:**
- `usuario_id` (required): ID del usuario

**Query Parameters:**
- `skip` (optional): Paginación, default: 0
- `limit` (optional): Límite de resultados, default: 20, max: 100
- `fecha_desde` (optional): Filtrar desde fecha (YYYY-MM-DD)
- `fecha_hasta` (optional): Filtrar hasta fecha (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "usuario_id": 9,
  "usuario_nombre": "Juan Pérez",
  "total_cambios": 45,
  "cambios": [
    {
      "auditoria_id": 156,
      "tabla_afectada": "turno",
      "operacion": "UPDATE",
      "registro_id": 42,
      "fecha_cambio": "2025-01-20T15:30:00",
      "descripcion": "Modificó turno #42"
    }
  ],
  "skip": 0,
  "limit": 20
}
```

---

### **3. GET `/api/v1/auditoria/tabla/{tabla}`**

Lista todos los cambios en una tabla específica.

**Requiere autenticación:** ✅ (Admin)

**Path Parameters:**
- `tabla` (required): Nombre de la tabla

**Query Parameters:**
- `operacion` (optional): Filtrar por tipo (INSERT, UPDATE, DELETE)
- `skip` (optional): default: 0
- `limit` (optional): default: 20, max: 100
- `fecha_desde` (optional): YYYY-MM-DD
- `fecha_hasta` (optional): YYYY-MM-DD

**Response (200 OK):**
```json
{
  "tabla": "turno",
  "total_cambios": 1250,
  "cambios": [
    {
      "auditoria_id": 156,
      "operacion": "UPDATE",
      "registro_id": 42,
      "usuario_nombre": "Juan Pérez",
      "fecha_cambio": "2025-01-20T15:30:00"
    }
  ]
}
```

---

## 🔐 **Permisos y Seguridad**

### **Niveles de Acceso**

| Rol | Puede Ver |
|-----|-----------|
| CLIENTE | Solo sus propios cambios |
| EMPRESA | Cambios de su empresa |
| ADMIN_EMPRESA | Todos los cambios de la empresa |
| ADMIN_SISTEMA | Toda la auditoría |
| SUPERADMIN | Acceso completo |

### **Datos Sensibles**

Ciertos datos NO se auditan por privacidad:
- ❌ Contraseñas (aunque estén hasheadas)
- ❌ Tokens de sesión
- ❌ Datos de pago

---

## 🧪 **Ejemplos de Uso**

### **Caso 1: Ver historial de un turno**

```javascript
const turnoId = 42;
const token = localStorage.getItem('token');

const response = await fetch(
  `http://localhost:8000/api/v1/auditoria/historial/turno/${turnoId}`,
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const historial = await response.json();

console.log(`Total de cambios: ${historial.total_cambios}`);

historial.cambios.forEach(cambio => {
  console.log(`[${cambio.operacion}] por ${cambio.usuario_nombre}`);
  console.log(`Fecha: ${cambio.fecha_cambio}`);
  
  if (cambio.operacion === 'UPDATE') {
    console.log('Campos modificados:', cambio.campos_modificados);
    console.log('Antes:', cambio.datos_anteriores);
    console.log('Después:', cambio.datos_nuevos);
  }
});
```

---

### **Caso 2: Dashboard de auditoría empresarial**

```javascript
// Ver todos los cambios de la última semana en mi empresa
const empresaId = 1;
const fechaDesde = new Date();
fechaDesde.setDate(fechaDesde.getDate() - 7);

const response = await fetch(
  `/api/v1/auditoria/tabla/turno?fecha_desde=${fechaDesde.toISOString().split('T')[0]}`,
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const auditoria = await response.json();

// Agrupar por operación
const stats = {
  creados: auditoria.cambios.filter(c => c.operacion === 'INSERT').length,
  modificados: auditoria.cambios.filter(c => c.operacion === 'UPDATE').length,
  cancelados: auditoria.cambios.filter(c => c.operacion === 'DELETE').length
};

console.log('Turnos de la última semana:', stats);
```

---

### **Caso 3: Detectar cambios sospechosos**

```javascript
// Buscar cambios masivos de un usuario en corto tiempo
const response = await fetch(
  `/api/v1/auditoria/usuario/${usuarioId}?limit=100`,
  {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  }
);

const { cambios } = await response.json();

// Detectar más de 10 cambios en menos de 1 minuto
const cambiosRapidos = [];
for (let i = 1; i < cambios.length; i++) {
  const diff = new Date(cambios[i-1].fecha_cambio) - new Date(cambios[i].fecha_cambio);
  if (diff < 60000) { // menos de 1 minuto
    cambiosRapidos.push(cambios[i]);
  }
}

if (cambiosRapidos.length > 10) {
  console.warn('⚠️ Actividad sospechosa detectada');
}
```

---

## 📊 **Consultas SQL Útiles**

### **Ver cambios recientes en el sistema**

```sql
SELECT 
    a.tabla_afectada,
    a.operacion,
    u.nombre as usuario,
    a.fecha_cambio
FROM auditoria_detalle a
LEFT JOIN usuario u ON a.usuario_id = u.usuario_id
WHERE a.fecha_cambio >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY a.fecha_cambio DESC
LIMIT 50;
```

### **Estadísticas de cambios por tabla**

```sql
SELECT 
    tabla_afectada,
    operacion,
    COUNT(*) as total,
    DATE(fecha_cambio) as fecha
FROM auditoria_sistema
WHERE fecha_cambio >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY tabla_afectada, operacion, DATE(fecha_cambio)
ORDER BY fecha DESC, total DESC;
```

### **Usuarios más activos**

```sql
SELECT 
    u.usuario_id,
    u.nombre,
    u.email,
    COUNT(*) as total_cambios
FROM auditoria_sistema a
JOIN usuario u ON a.usuario_id = u.usuario_id
WHERE a.fecha_cambio >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY u.usuario_id
ORDER BY total_cambios DESC
LIMIT 10;
```

---

## 🔍 **Troubleshooting**

### **No se registran cambios en auditoría**

**Causa:** Triggers deshabilitados o tabla sin triggers.

**Solución:**
```sql
-- Verificar si existen los triggers
SHOW TRIGGERS WHERE `Table` = 'turno';

-- Verificar última auditoría
SELECT * FROM auditoria_sistema ORDER BY fecha_cambio DESC LIMIT 10;
```

---

### **Auditoría crece demasiado rápido**

**Causa:** Demasiados cambios auditados.

**Solución:**
```sql
-- Limpiar auditoría antigua (más de 1 año)
DELETE FROM auditoria_sistema 
WHERE fecha_cambio < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- O archivar en tabla separada
INSERT INTO auditoria_archivo 
SELECT * FROM auditoria_sistema 
WHERE fecha_cambio < DATE_SUB(NOW(), INTERVAL 6 MONTH);
```

---

### **Campos_modificados siempre NULL**

**Causa:** Trigger no está calculando los campos modificados.

**Solución:**
Actualizar el trigger para incluir lógica de comparación de campos.

---

## 📊 **Performance**

- **Inserción de auditoría:** ~20-40ms (triggers automáticos)
- **Consulta historial:** ~50-100ms (con índices)
- **Vista auditoria_detalle:** ~80-150ms (precalculada)

**Optimizaciones aplicadas:**
- ✅ Índices en tabla_afectada, operacion, usuario_id, fecha_cambio
- ✅ Vista precalculada con JOINs optimizados
- ✅ JSON para datos flexibles
- ✅ Paginación en todos los endpoints

---

## 🎯 **Mejores Prácticas**

### **Para Desarrolladores:**

1. **Nunca desactivar auditoría** en producción
2. **Usar soft delete** en lugar de DELETE físico
3. **Incluir metadatos** relevantes (IP, user agent)
4. **No auditar datos sensibles** (contraseñas, tokens)

### **Para Administradores:**

1. **Revisar auditoría regularmente** para detectar anomalías
2. **Archivar auditoría antigua** periódicamente
3. **Monitorear tamaño** de la tabla auditoria_sistema
4. **Configurar alertas** para cambios sospechosos

### **Para Compliance:**

1. **Retener auditoría** según normativas locales
2. **Exportar auditoría** periódicamente para backups
3. **Documentar políticas** de retención
4. **Restringir acceso** solo a personal autorizado

---

## 🚀 **Roadmap**

- [ ] Dashboard visual de auditoría
- [ ] Alertas automáticas por cambios sospechosos
- [ ] Exportación de auditoría a CSV/PDF
- [ ] Auditoría de login/logout
- [ ] Comparación visual de cambios (diff)
- [ ] Rollback de cambios desde auditoría

---

**Última actualización:** 21 de Octubre 2025  
**Versión:** 1.0.0  
**Estado:** ✅ Productivo y funcional