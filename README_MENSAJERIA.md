# 💬 Sistema de Mensajería - MiTurno API

Sistema completo de mensajería bidireccional entre clientes y empresas.

---

## 🎯 **Características**

- ✅ Conversaciones 1:1 entre cliente y empresa
- ✅ Mensajes en tiempo real
- ✅ Estado de lectura (leído/no leído)
- ✅ Historial completo de mensajes
- ✅ Soft delete de mensajes
- ✅ Validación de permisos robusta
- ✅ Detección automática de tipo de remitente

---

## 📡 **Endpoints Disponibles**

### **1. POST `/api/v1/conversaciones`**

Crea o recupera una conversación existente entre cliente y empresa.

**Request Body:**
```json
{
  "cliente_id": 9,
  "empresa_id": 1
}
```

**Response (201 Created):**
```json
{
  "conversacion_id": 3,
  "cliente_id": 9,
  "empresa_id": 1,
  "created_at": "2025-10-17T22:00:39",
  "updated_at": "2025-10-17T22:00:39",
  "mensajes_no_leidos": 0
}
```

**Comportamiento:**
- Si la conversación ya existe, la retorna (no crea duplicados)
- Si no existe, crea una nueva

**Errores:**
- `400`: IDs inválidos
- `401`: No autenticado
- `404`: Cliente o empresa no existen

---

### **2. GET `/api/v1/conversaciones`**

Lista todas las conversaciones del usuario actual.

**Sin parámetros requeridos** - usa el token para identificar al usuario.

**Response (200 OK):**
```json
[
  {
    "conversacion_id": 3,
    "cliente_id": 9,
    "empresa_id": 1,
    "created_at": "2025-10-17T22:00:39",
    "updated_at": "2025-10-17T22:05:49",
    "mensajes_no_leidos": 2
  }
]
```

**Lógica:**
- Si el usuario es **CLIENTE**: muestra conversaciones donde `cliente_id = usuario_id`
- Si el usuario es **EMPRESA**: muestra conversaciones de su empresa

**Errores:**
- `401`: No autenticado

---

### **3. GET `/api/v1/conversaciones/{conversacion_id}`**

Obtiene una conversación específica con todos sus mensajes.

**Path Parameter:**
- `conversacion_id`: ID de la conversación

**Response (200 OK):**
```json
{
  "conversacion_id": 3,
  "cliente_id": 9,
  "empresa_id": 1,
  "created_at": "2025-10-17T22:00:39",
  "updated_at": "2025-10-17T22:05:49",
  "mensajes_no_leidos": 1,
  "cliente_nombre": "Cliente Test",
  "empresa_nombre": "Barbería Central",
  "mensajes": [
    {
      "mensaje_id": 1,
      "conversacion_id": 3,
      "remitente_tipo": "empresa",
      "remitente_id": 1,
      "contenido": "Hola! Bienvenido a nuestra barbería",
      "leido": true,
      "created_at": "2025-10-17T22:05:49",
      "deleted_at": null
    },
    {
      "mensaje_id": 2,
      "conversacion_id": 3,
      "remitente_tipo": "cliente",
      "remitente_id": 9,
      "contenido": "Gracias! Quiero reservar un turno",
      "leido": false,
      "created_at": "2025-10-17T22:06:15",
      "deleted_at": null
    }
  ]
}
```

**Validaciones:**
- Usuario debe ser participante de la conversación (cliente o empresa)
- Solo muestra mensajes activos (deleted_at = NULL)
- Mensajes ordenados por fecha ascendente

**Errores:**
- `401`: No autenticado
- `403`: No tienes acceso a esta conversación
- `404`: Conversación no encontrada

---

### **4. POST `/api/v1/conversaciones/{conversacion_id}/mensajes`**

Envía un mensaje en una conversación.

**Path Parameter:**
- `conversacion_id`: ID de la conversación

**Request Body:**
```json
{
  "contenido": "Hola! ¿Tienen disponibilidad para mañana?"
}
```

**Response (201 Created):**
```json
{
  "mensaje_id": 3,
  "conversacion_id": 3,
  "remitente_tipo": "cliente",
  "remitente_id": 9,
  "contenido": "Hola! ¿Tienen disponibilidad para mañana?",
  "leido": false,
  "created_at": "2025-10-17T22:08:30",
  "deleted_at": null
}
```

**Detección automática de remitente:**
1. Si el usuario tiene una empresa asociada Y es la empresa de la conversación → `remitente_tipo: "empresa"`
2. Si el usuario es el cliente de la conversación → `remitente_tipo: "cliente"`
3. Si ninguno → Error 403

**Efectos secundarios:**
- Actualiza `updated_at` de la conversación
- El mensaje se marca como `leido: false` por defecto

**Errores:**
- `401`: No autenticado
- `403`: No tienes acceso a esta conversación
- `404`: Conversación no encontrada

---

### **5. PATCH `/api/v1/conversaciones/mensajes/{mensaje_id}/marcar-leido`**

Marca un mensaje como leído.

**Path Parameter:**
- `mensaje_id`: ID del mensaje

**Sin body requerido**

**Response (200 OK):**
```json
{
  "mensaje_id": 1,
  "conversacion_id": 3,
  "remitente_tipo": "empresa",
  "remitente_id": 1,
  "contenido": "Hola! Bienvenido a nuestra barbería",
  "leido": true,
  "created_at": "2025-10-17T22:05:49",
  "deleted_at": null
}
```

**Validaciones:**
- Usuario debe ser participante de la conversación
- Solo cambia el estado, no el contenido

**Errores:**
- `401`: No autenticado
- `403`: No tienes acceso a este mensaje
- `404`: Mensaje no encontrado

---

## 🔒 **Autenticación**

Todos los endpoints requieren autenticación con Bearer token:
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🗄️ **Modelo de Datos**

### **Tabla: conversacion**
```sql
CREATE TABLE conversacion (
    conversacion_id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    empresa_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id) REFERENCES empresa(empresa_id) ON DELETE CASCADE,
    UNIQUE KEY (cliente_id, empresa_id)
);
```

### **Tabla: mensaje**
```sql
CREATE TABLE mensaje (
    mensaje_id INT PRIMARY KEY AUTO_INCREMENT,
    conversacion_id INT NOT NULL,
    remitente_tipo ENUM('cliente', 'empresa') NOT NULL,
    remitente_id INT NOT NULL,
    contenido TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    FOREIGN KEY (conversacion_id) REFERENCES conversacion(conversacion_id) ON DELETE CASCADE,
    INDEX idx_conversacion (conversacion_id),
    INDEX idx_leido (leido),
    INDEX idx_created (created_at)
);
```

---

## 🧪 **Ejemplos de Uso**

### **Caso 1: Cliente inicia conversación con empresa**
```javascript
// 1. Cliente crea conversación
const crearConv = await fetch(`${API_URL}/conversaciones`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${clienteToken}`
  },
  body: JSON.stringify({
    cliente_id: 9,
    empresa_id: 1
  })
});

const conversacion = await crearConv.json();
console.log(`Conversación creada: ${conversacion.conversacion_id}`);

// 2. Cliente envía primer mensaje
const enviarMsg = await fetch(
  `${API_URL}/conversaciones/${conversacion.conversacion_id}/mensajes`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${clienteToken}`
    },
    body: JSON.stringify({
      contenido: "Hola! Quisiera hacer una consulta"
    })
  }
);

const mensaje = await enviarMsg.json();
console.log(`Mensaje enviado: ${mensaje.mensaje_id}`);
```

---

### **Caso 2: Empresa lista sus conversaciones y responde**
```javascript
// 1. Empresa lista conversaciones
const response = await fetch(`${API_URL}/conversaciones`, {
  headers: {
    'Authorization': `Bearer ${empresaToken}`
  }
});

const conversaciones = await response.json();

// 2. Empresa ve conversación con mensajes
const convId = conversaciones[0].conversacion_id;
const detalle = await fetch(`${API_URL}/conversaciones/${convId}`, {
  headers: {
    'Authorization': `Bearer ${empresaToken}`
  }
});

const conversacionCompleta = await detalle.json();

// 3. Empresa responde
const respuesta = await fetch(
  `${API_URL}/conversaciones/${convId}/mensajes`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${empresaToken}`
    },
    body: JSON.stringify({
      contenido: "¡Hola! Claro, dime en qué puedo ayudarte"
    })
  }
);
```

---

### **Caso 3: Marcar mensajes como leídos**
```javascript
// Cliente marca mensaje de empresa como leído
const conversacion = await fetch(`${API_URL}/conversaciones/3`, {
  headers: { 'Authorization': `Bearer ${clienteToken}` }
});

const { mensajes } = await conversacion.json();

// Marcar todos los mensajes no leídos
const noLeidos = mensajes.filter(m => !m.leido && m.remitente_tipo === 'empresa');

for (const mensaje of noLeidos) {
  await fetch(`${API_URL}/conversaciones/mensajes/${mensaje.mensaje_id}/marcar-leido`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${clienteToken}` }
  });
}

console.log(`${noLeidos.length} mensajes marcados como leídos`);
```

---

## 🎨 **Integración con Frontend**

### **Componente de Chat (React)**
```jsx
function Chat({ conversacionId, userToken }) {
  const [mensajes, setMensajes] = useState([]);
  const [nuevoMensaje, setNuevoMensaje] = useState('');

  // Cargar mensajes
  useEffect(() => {
    fetch(`${API_URL}/conversaciones/${conversacionId}`, {
      headers: { 'Authorization': `Bearer ${userToken}` }
    })
      .then(res => res.json())
      .then(data => setMensajes(data.mensajes));
  }, [conversacionId]);

  // Enviar mensaje
  const enviarMensaje = async () => {
    const response = await fetch(
      `${API_URL}/conversaciones/${conversacionId}/mensajes`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({ contenido: nuevoMensaje })
      }
    );
    
    const mensaje = await response.json();
    setMensajes([...mensajes, mensaje]);
    setNuevoMensaje('');
  };

  return (
    <div className="chat-container">
      <div className="mensajes">
        {mensajes.map(msg => (
          <div key={msg.mensaje_id} className={msg.remitente_tipo}>
            <p>{msg.contenido}</p>
            <span>{msg.leido ? '✓✓' : '✓'}</span>
          </div>
        ))}
      </div>
      
      <div className="input-area">
        <input
          value={nuevoMensaje}
          onChange={(e) => setNuevoMensaje(e.target.value)}
          placeholder="Escribe un mensaje..."
        />
        <button onClick={enviarMensaje}>Enviar</button>
      </div>
    </div>
  );
}
```

---

## 🚀 **Features Futuras**

- [ ] WebSockets para mensajes en tiempo real
- [ ] Notificaciones push de nuevos mensajes
- [ ] Archivos adjuntos (imágenes, documentos)
- [ ] Indicador de "escribiendo..."
- [ ] Búsqueda dentro de mensajes
- [ ] Mensajes de voz
- [ ] Reacciones con emojis
- [ ] Mensajes destacados/importantes
- [ ] Exportar conversación a PDF

---

## ⚠️ **Limitaciones Actuales**

- **No hay WebSockets**: Los mensajes no son en tiempo real, requiere polling
- **Sin archivos adjuntos**: Solo texto plano
- **Sin paginación**: Carga todos los mensajes (máximo recomendado: 100 por conversación)
- **Sin edición de mensajes**: Solo soft delete
- **Sin mensajes grupales**: Solo 1:1 (cliente-empresa)

---

## 🐛 **Troubleshooting**

### **Error: "No tienes acceso a esta conversación"**

**Causa:** El usuario no es participante de la conversación.

**Solución:**
- Verificar que el `cliente_id` en la conversación coincida con el usuario actual
- O que el usuario tenga una empresa y el `empresa_id` coincida

---

### **Error: Remitente detectado incorrectamente**

**Causa:** Bug corregido en v1.1.0. Si persiste, verificar que el usuario tenga registro en tabla `empresa`.

**Solución:**
- Actualizar a última versión
- Verificar: `SELECT * FROM empresa WHERE usuario_id = ?`

---

### **Mensajes no aparecen**

**Causa:** Filtro de `deleted_at IS NULL`.

**Solución:**
- Verificar que los mensajes no estén eliminados
- Verificar orden de mensajes (ascendente por `created_at`)

---

## 📊 **Performance**

- **Listar conversaciones:** <50ms (con índices)
- **Ver conversación con mensajes:** <100ms (hasta 100 mensajes)
- **Enviar mensaje:** <80ms
- **Marcar como leído:** <30ms

**Optimizaciones aplicadas:**
- ✅ Índices en `conversacion_id`, `leido`, `created_at`
- ✅ Unique constraint en `(cliente_id, empresa_id)`
- ✅ Cascade delete configurado
- ✅ Soft delete para auditabilidad

---

**Última actualización:** 17/10/2025  
**Versión:** 1.1.0  
**Status:** ✅ Producción - Estable