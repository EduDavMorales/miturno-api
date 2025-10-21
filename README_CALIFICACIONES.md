# ⭐ Sistema de Calificaciones y Reviews - MiTurno API

Sistema completo de calificaciones y reseñas para empresas con rating promedio, comentarios y respuestas de empresas.

---

## 🎯 **Características**

- ✅ Calificaciones de 1 a 5 estrellas
- ✅ Comentarios opcionales de clientes
- ✅ Respuestas de empresas a las calificaciones
- ✅ Cálculo automático de rating promedio
- ✅ Una calificación por turno completado
- ✅ Validación de turnos completados
- ✅ Sistema de moderación
- ✅ Soft delete de calificaciones

---

## 📡 **Endpoints Disponibles**

### **1. POST `/api/v1/calificaciones/`**

Crea una nueva calificación para una empresa.

**Requiere autenticación:** ✅

**Request Body:**
```json
{
  "turno_id": 42,
  "puntuacion": 5,
  "comentario": "Excelente servicio, muy profesional y puntual"
}
```

**Response (201 Created):**
```json
{
  "calificacion_id": 15,
  "turno_id": 42,
  "cliente_id": 9,
  "cliente_nombre": "Juan",
  "cliente_apellido": "Pérez",
  "empresa_id": 1,
  "empresa_nombre": "Barbería Central",
  "puntuacion": 5,
  "comentario": "Excelente servicio, muy profesional y puntual",
  "respuesta_empresa": null,
  "fecha_calificacion": "2025-01-21T14:30:00",
  "fecha_respuesta": null,
  "puede_responder": false,
  "puede_editar": true
}
```

**Validaciones Automáticas:**
- ✅ Usuario es cliente del turno
- ✅ Turno está en estado `completado`
- ✅ No existe calificación previa para este turno
- ✅ Puntuación entre 1 y 5
- ✅ Comentario máximo 1000 caracteres
- ✅ Actualiza rating_promedio de la empresa

**Errores:**
- `400`: Validaciones fallidas (turno no completado, ya existe calificación)
- `401`: No autenticado
- `403`: No tienes permiso para calificar este turno
- `404`: Turno o empresa no encontrada
- `409`: Ya existe una calificación para este turno

---

### **2. GET `/api/v1/calificaciones/empresa/{empresa_id}`**

Lista todas las calificaciones de una empresa con paginación.

**Sin autenticación requerida** (endpoint público)

**Path Parameters:**
- `empresa_id` (required): ID de la empresa

**Query Parameters:**
- `skip` (optional): Número de registros a saltar, default: 0
- `limit` (optional): Número de registros a retornar, default: 10, max: 50
- `orden` (optional): Ordenamiento (recientes, antiguas, mejor, peor), default: recientes

**Response (200 OK):**
```json
{
  "empresa_id": 1,
  "empresa_nombre": "Barbería Central",
  "rating_promedio": 4.7,
  "total_calificaciones": 127,
  "calificaciones": [
    {
      "calificacion_id": 15,
      "cliente_nombre": "Juan",
      "cliente_apellido": "Pérez",
      "puntuacion": 5,
      "comentario": "Excelente servicio, muy profesional y puntual",
      "respuesta_empresa": "¡Muchas gracias por tu confianza Juan! Nos alegra que hayas disfrutado del servicio.",
      "fecha_calificacion": "2025-01-21T14:30:00",
      "fecha_respuesta": "2025-01-21T16:45:00",
      "servicio_nombre": "Corte de Cabello"
    },
    {
      "calificacion_id": 14,
      "cliente_nombre": "María",
      "cliente_apellido": "González",
      "puntuacion": 4,
      "comentario": "Buen servicio, solo un poco de demora",
      "respuesta_empresa": null,
      "fecha_calificacion": "2025-01-20T11:20:00",
      "fecha_respuesta": null,
      "servicio_nombre": "Corte + Barba"
    }
  ],
  "skip": 0,
  "limit": 10,
  "tiene_siguiente": true,
  "distribucion_puntuaciones": {
    "5_estrellas": 85,
    "4_estrellas": 30,
    "3_estrellas": 8,
    "2_estrellas": 3,
    "1_estrella": 1
  }
}
```

**Errores:**
- `404`: Empresa no encontrada

---

### **3. POST `/api/v1/calificaciones/{calificacion_id}/responder`**

Permite a la empresa responder a una calificación.

**Requiere autenticación:** ✅ (Usuario debe ser de la empresa)

**Path Parameters:**
- `calificacion_id` (required): ID de la calificación

**Request Body:**
```json
{
  "respuesta": "¡Muchas gracias por tu confianza! Nos alegra que hayas disfrutado del servicio."
}
```

**Response (200 OK):**
```json
{
  "calificacion_id": 15,
  "respuesta_empresa": "¡Muchas gracias por tu confianza! Nos alegra que hayas disfrutado del servicio.",
  "fecha_respuesta": "2025-01-21T16:45:00",
  "mensaje": "Respuesta publicada exitosamente"
}
```

**Validaciones:**
- ✅ Usuario pertenece a la empresa calificada
- ✅ Calificación existe y está activa
- ✅ No hay respuesta previa (o se puede editar dentro de 24h)
- ✅ Respuesta máximo 500 caracteres

**Errores:**
- `401`: No autenticado
- `403`: No tienes permiso para responder (no eres de esta empresa)
- `404`: Calificación no encontrada
- `409`: Ya existe una respuesta (fuera del periodo de edición)

---

### **4. GET `/api/v1/calificaciones/mis-calificaciones`**

Lista todas las calificaciones realizadas por el usuario autenticado.

**Requiere autenticación:** ✅

**Query Parameters:**
- `skip` (optional): Número de registros a saltar, default: 0
- `limit` (optional): Número de registros a retornar, default: 10

**Response (200 OK):**
```json
{
  "calificaciones": [
    {
      "calificacion_id": 15,
      "turno_id": 42,
      "empresa_nombre": "Barbería Central",
      "servicio_nombre": "Corte de Cabello",
      "puntuacion": 5,
      "comentario": "Excelente servicio, muy profesional y puntual",
      "respuesta_empresa": "¡Muchas gracias por tu confianza Juan!",
      "fecha_calificacion": "2025-01-21T14:30:00",
      "fecha_turno": "2025-01-20T10:00:00",
      "puede_editar": true
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

**Errores:**
- `401`: No autenticado

---

### **5. GET `/api/v1/calificaciones/empresa/{empresa_id}/estadisticas`**

Obtiene estadísticas detalladas de las calificaciones de una empresa.

**Sin autenticación requerida** (endpoint público)

**Path Parameters:**
- `empresa_id` (required): ID de la empresa

**Response (200 OK):**
```json
{
  "empresa_id": 1,
  "empresa_nombre": "Barbería Central",
  "rating_promedio": 4.7,
  "total_calificaciones": 127,
  "distribucion_puntuaciones": {
    "5_estrellas": 85,
    "4_estrellas": 30,
    "3_estrellas": 8,
    "2_estrellas": 3,
    "1_estrella": 1
  },
  "porcentaje_recomendacion": 90.5,
  "tendencia_ultimo_mes": "positiva"
}
```

**Errores:**
- `404`: Empresa no encontrada

---

## 🔐 **Autenticación**

Endpoints públicos:
- `GET /calificaciones/empresa/{id}`
- `GET /calificaciones/empresa/{id}/estadisticas`

Endpoints protegidos (requieren Bearer token):
- `POST /calificaciones/`
- `POST /calificaciones/{id}/responder`
- `GET /calificaciones/mis-calificaciones`

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📊 **Sistema de Puntuación**

| Estrellas | Descripción | Impacto |
|-----------|-------------|---------|
| ⭐ | Muy malo | Rating bajo |
| ⭐⭐ | Malo | Rating bajo |
| ⭐⭐⭐ | Regular | Rating medio |
| ⭐⭐⭐⭐ | Bueno | Rating alto |
| ⭐⭐⭐⭐⭐ | Excelente | Rating alto |

**Cálculo de Rating Promedio:**
```
rating_promedio = suma_total_puntuaciones / total_calificaciones
```

Se actualiza automáticamente en la tabla `empresa` cada vez que:
- Se crea una calificación
- Se edita una calificación
- Se elimina una calificación

---

## 🧪 **Ejemplos de Uso**

### **Caso 1: Cliente califica después de un turno**

```javascript
// 1. Cliente completa un turno (ID: 42)
// Estado del turno cambia a "completado"

// 2. Cliente deja calificación
const calificacion = await fetch(
  'http://localhost:8000/api/v1/calificaciones/',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      turno_id: 42,
      puntuacion: 5,
      comentario: 'Excelente servicio, muy profesional'
    })
  }
);

const resultado = await calificacion.json();
console.log(`Calificación creada: ID ${resultado.calificacion_id}`);
```

---

### **Caso 2: Empresa responde a calificaciones**

```javascript
// 1. Empresa lista sus calificaciones
const response = await fetch(
  'http://localhost:8000/api/v1/calificaciones/empresa/1',
  {
    headers: { 'Authorization': `Bearer ${empresaToken}` }
  }
);

const { calificaciones } = await response.json();

// 2. Empresa responde a una calificación
const sinResponder = calificaciones.find(c => !c.respuesta_empresa);

if (sinResponder) {
  await fetch(
    `http://localhost:8000/api/v1/calificaciones/${sinResponder.calificacion_id}/responder`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${empresaToken}`
      },
      body: JSON.stringify({
        respuesta: '¡Muchas gracias por tu opinión! Nos alegra que hayas disfrutado.'
      })
    }
  );
}
```

---

### **Caso 3: Usuario ve calificaciones públicas**

```javascript
// Sin autenticación - endpoint público
const response = await fetch(
  'http://localhost:8000/api/v1/calificaciones/empresa/1?orden=mejor&limit=20'
);

const data = await response.json();

console.log(`Rating promedio: ${data.rating_promedio}/5`);
console.log(`Total de calificaciones: ${data.total_calificaciones}`);

// Mostrar distribución
Object.entries(data.distribucion_puntuaciones).forEach(([estrellas, cantidad]) => {
  console.log(`${estrellas}: ${cantidad} calificaciones`);
});
```

---

## 🎨 **Integración con Frontend**

### **React - Componente de Calificaciones**

```jsx
import { useState, useEffect } from 'react';

function CalificacionesEmpresa({ empresaId }) {
  const [calificaciones, setCalificaciones] = useState([]);
  const [ratingPromedio, setRatingPromedio] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarCalificaciones();
  }, [empresaId]);

  const cargarCalificaciones = async () => {
    const response = await fetch(
      `${API_URL}/calificaciones/empresa/${empresaId}/calificaciones?limit=20`
    );
    
    const data = await response.json();
    setCalificaciones(data.calificaciones);
    setRatingPromedio(data.rating_promedio);
    setLoading(false);
  };

  const renderEstrellas = (puntuacion) => {
    return '⭐'.repeat(puntuacion) + '☆'.repeat(5 - puntuacion);
  };

  if (loading) return <p>Cargando calificaciones...</p>;

  return (
    <div className="calificaciones-container">
      <div className="rating-header">
        <h2>Calificaciones</h2>
        <div className="rating-promedio">
          <span className="numero">{ratingPromedio.toFixed(1)}</span>
          <span className="estrellas">{renderEstrellas(Math.round(ratingPromedio))}</span>
        </div>
      </div>

      <div className="calificaciones-lista">
        {calificaciones.map(cal => (
          <div key={cal.calificacion_id} className="calificacion-card">
            <div className="calificacion-header">
              <span className="cliente-nombre">
                {cal.cliente_nombre} {cal.cliente_apellido}
              </span>
              <span className="fecha">
                {new Date(cal.fecha_calificacion).toLocaleDateString()}
              </span>
            </div>
            
            <div className="puntuacion">
              {renderEstrellas(cal.puntuacion)}
            </div>
            
            {cal.comentario && (
              <p className="comentario">{cal.comentario}</p>
            )}
            
            {cal.respuesta_empresa && (
              <div className="respuesta-empresa">
                <strong>Respuesta de la empresa:</strong>
                <p>{cal.respuesta_empresa}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### **React - Formulario de Calificación**

```jsx
function FormularioCalificacion({ turnoId, empresaId, onSuccess }) {
  const [puntuacion, setPuntuacion] = useState(0);
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);

  const enviarCalificacion = async (e) => {
    e.preventDefault();
    setEnviando(true);
    
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(
        `${API_URL}/calificaciones/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            turno_id: turnoId,
            puntuacion,
            comentario
          })
        }
      );
      
      if (response.ok) {
        alert('¡Calificación enviada exitosamente!');
        onSuccess();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      alert('Error al enviar calificación');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={enviarCalificacion} className="form-calificacion">
      <h3>Califica tu experiencia</h3>
      
      <div className="selector-estrellas">
        {[1, 2, 3, 4, 5].map(valor => (
          <button
            key={valor}
            type="button"
            onClick={() => setPuntuacion(valor)}
            className={valor <= puntuacion ? 'activa' : ''}
          >
            ⭐
          </button>
        ))}
      </div>
      
      <textarea
        value={comentario}
        onChange={(e) => setComentario(e.target.value)}
        placeholder="Cuéntanos sobre tu experiencia (opcional)"
        maxLength={1000}
        rows={4}
      />
      
      <button
        type="submit"
        disabled={puntuacion === 0 || enviando}
        className="btn-enviar"
      >
        {enviando ? 'Enviando...' : 'Enviar Calificación'}
      </button>
    </form>
  );
}
```

---

## 🗄️ **Base de Datos**

### **Tabla: calificacion**

```sql
CREATE TABLE calificacion (
    calificacion_id INT PRIMARY KEY AUTO_INCREMENT,
    turno_id INT UNIQUE NOT NULL,
    cliente_id INT NOT NULL,
    empresa_id INT NOT NULL,
    puntuacion TINYINT NOT NULL CHECK (puntuacion BETWEEN 1 AND 5),
    comentario TEXT,
    respuesta_empresa TEXT,
    fecha_calificacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_respuesta DATETIME,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    FOREIGN KEY (turno_id) REFERENCES turno(turno_id) ON DELETE CASCADE,
    FOREIGN KEY (cliente_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id) REFERENCES empresa(empresa_id) ON DELETE CASCADE,
    INDEX idx_empresa (empresa_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_puntuacion (puntuacion),
    INDEX idx_fecha (fecha_calificacion)
);
```

### **Campo en tabla empresa:**

```sql
ALTER TABLE empresa
ADD COLUMN rating_promedio DECIMAL(3,2) DEFAULT 0.00,
ADD INDEX idx_rating (rating_promedio);
```

---

## 🔍 **Troubleshooting**

### **Error 409: "Ya existe una calificación para este turno"**

**Causa:** Solo se permite una calificación por turno.

**Solución:**
- Editar la calificación existente (si tiene menos de 7 días)
- O eliminarla y crear una nueva

---

### **Error 400: "El turno no está completado"**

**Causa:** Solo se puede calificar turnos en estado `completado`.

**Solución:**
- Esperar a que la empresa marque el turno como completado
- Contactar a la empresa si el servicio ya fue realizado

---

### **Error 409: "Ya existe una calificación para este turno"**