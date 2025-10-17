# 📍 Sistema de Geolocalización - MiTurno API

Sistema completo de geolocalización para búsqueda de empresas por proximidad y gestión de coordenadas.

---

## 🎯 **Características**

- ✅ Búsqueda de empresas por coordenadas GPS
- ✅ Búsqueda de empresas por dirección
- ✅ Geocodificación automática de direcciones argentinas (API Georef)
- ✅ Actualización manual/automática de coordenadas
- ✅ Filtrado por categoría
- ✅ Radio de búsqueda configurable (hasta 100km)
- ✅ Validaciones robustas y manejo de errores
- ✅ Control de permisos RBAC

---

## 📡 **Endpoints Disponibles**

### **1. GET `/api/v1/geolocalizacion/empresas-cercanas`**

Busca empresas cercanas a coordenadas GPS específicas.

**Query Parameters:**
- `latitud` (required): float, -90 a 90
- `longitud` (required): float, -180 a 180
- `radio_km` (optional): float, 0.1 a 100, default: 10
- `categoria_id` (optional): int

**Ejemplo de Request:**
```bash
GET /api/v1/geolocalizacion/empresas-cercanas?latitud=-34.6037&longitud=-58.3816&radio_km=5&categoria_id=1
Authorization: Bearer {token}
```

**Ejemplo de Response:**
```json
{
  "punto_busqueda": {
    "latitud": -34.6037,
    "longitud": -58.3816
  },
  "radio_km": 5.0,
  "total_encontradas": 3,
  "empresas": [
    {
      "empresa_id": 1,
      "razon_social": "Barbería El Corte",
      "descripcion": "Barbería tradicional",
      "categoria_id": 1,
      "coordenadas": {
        "latitud": -34.6045,
        "longitud": -58.3825
      },
      "distancia_km": 0.12,
      "activa": true
    }
  ]
}
```

**Errores:**
- `400`: Parámetros inválidos o categoría no existe
- `401`: No autenticado
- `500`: Error interno del servidor

---

### **2. GET `/api/v1/geolocalizacion/buscar-por-direccion`**

Busca empresas cercanas a una dirección. Primero geocodifica la dirección y luego busca empresas.

**Query Parameters:**
- `calle` (required): string
- `numero` (optional): string
- `ciudad` (optional): string
- `provincia` (optional): string
- `codigo_postal` (optional): string
- `radio_km` (optional): float, default: 10
- `categoria_id` (optional): int

**Ejemplo de Request:**
```bash
GET /api/v1/geolocalizacion/buscar-por-direccion?calle=Av%20Corrientes&numero=1000&ciudad=CABA&provincia=Buenos%20Aires&radio_km=5
Authorization: Bearer {token}
```

**Ejemplo de Response:**
```json
{
  "punto_busqueda": {
    "latitud": -34.6037,
    "longitud": -58.3816
  },
  "radio_km": 5.0,
  "total_encontradas": 5,
  "empresas": [...]
}
```

**Errores:**
- `400`: Dirección no geocodificable o categoría no existe
- `408`: Timeout del servicio de geocodificación (>10s)
- `500`: Error interno

---

### **3. POST `/api/v1/geolocalizacion/empresas/buscar-por-ubicacion`**

Versión POST de búsqueda por dirección. Mejor para datos estructurados y no expone datos en la URL.

**Request Body:**
```json
{
  "direccion": {
    "calle": "Av Corrientes",
    "numero": "1000",
    "ciudad": "CABA",
    "provincia": "Buenos Aires",
    "codigo_postal": "1043"
  },
  "radio_km": 5.0,
  "categoria_id": 1
}
```

**Ejemplo de Response:**
```json
{
  "punto_busqueda": {
    "latitud": -34.6037,
    "longitud": -58.3816
  },
  "radio_km": 5.0,
  "total_encontradas": 5,
  "empresas": [...]
}
```

**Errores:**
- `400`: Dirección inválida o categoría no existe
- `408`: Timeout de geocodificación
- `422`: Validación de datos fallida

---

### **4. PUT `/api/v1/geolocalizacion/empresas/{empresa_id}/coordenadas`**

Actualiza las coordenadas de una empresa. Soporta actualización manual (desde mapa) o automática (re-geocodificación).

**Permisos requeridos:**
- Usuario debe pertenecer a la empresa
- Permiso: `empresas:actualizar_propia`

**Modo Manual - Request Body:**
```json
{
  "latitud": -34.6537,
  "longitud": -58.3816,
  "corregido_manualmente": true
}
```

**Modo Automático - Request Body:**
```json
{
  "recalcular_desde_direccion": true
}
```

**Ejemplo de Response:**
```json
{
  "success": true,
  "message": "Coordenadas actualizadas exitosamente",
  "empresa_id": 1,
  "coordenadas_anteriores": {
    "latitud": -34.6500,
    "longitud": -58.3800
  },
  "coordenadas_nuevas": {
    "latitud": -34.6537,
    "longitud": -58.3816
  },
  "metodo": "manual"
}
```

**Errores:**
- `400`: Datos inválidos o empresa sin dirección
- `403`: Sin permisos para esta empresa
- `404`: Empresa no encontrada
- `408`: Timeout de geocodificación
- `500`: Error interno

---

## 🔒 **Autenticación**

Todos los endpoints requieren autenticación con Bearer token:
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🧪 **Ejemplos de Uso**

### **Caso 1: Cliente busca peluquerías cercanas a su ubicación**
```javascript
// 1. Obtener ubicación del cliente (GPS del navegador)
navigator.geolocation.getCurrentPosition(async (position) => {
  const { latitude, longitude } = position.coords;
  
  // 2. Buscar empresas cercanas
  const response = await fetch(
    `${API_URL}/geolocalizacion/empresas-cercanas?` +
    `latitud=${latitude}&longitud=${longitude}&radio_km=10&categoria_id=1`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const resultado = await response.json();
  console.log(`Encontradas ${resultado.total_encontradas} peluquerías`);
});
```

---

### **Caso 2: Buscar empresas cerca de una dirección específica**
```javascript
const direccion = {
  calle: "Av Corrientes",
  numero: "1000",
  ciudad: "CABA",
  provincia: "Buenos Aires"
};

const response = await fetch(
  `${API_URL}/geolocalizacion/empresas/buscar-por-ubicacion`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      direccion,
      radio_km: 5,
      categoria_id: 2
    })
  }
);

const resultado = await response.json();
```

---

### **Caso 3: Empresa corrige su ubicación desde mapa interactivo**
```javascript
// Usuario arrastra el pin en el mapa a la ubicación correcta
const nuevaUbicacion = {
  lat: -34.6537,
  lng: -58.3816
};

const response = await fetch(
  `${API_URL}/geolocalizacion/empresas/${empresaId}/coordenadas`,
  {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      latitud: nuevaUbicacion.lat,
      longitud: nuevaUbicacion.lng,
      corregido_manualmente: true
    })
  }
);

const resultado = await response.json();
console.log(resultado.message); // "Coordenadas actualizadas exitosamente"
```

---

## 🗺️ **Integración con Mapas**

### **Leaflet.js**
```javascript
// Crear mapa centrado en Buenos Aires
const map = L.map('map').setView([-34.6037, -58.3816], 13);

// Agregar capa de OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Agregar marcadores de empresas encontradas
resultado.empresas.forEach(empresa => {
  const marker = L.marker([
    empresa.coordenadas.latitud,
    empresa.coordenadas.longitud
  ]).addTo(map);
  
  marker.bindPopup(`
    <b>${empresa.razon_social}</b><br>
    Distancia: ${empresa.distancia_km.toFixed(2)} km
  `);
});
```

---

## ⚙️ **Configuración**

### **Variables de Entorno**
```bash
# API de Geocodificación (Georef Argentina)
GEOREF_API_URL=https://apis.datos.gob.ar/georef/api

# Límites de Argentina (validación)
ARGENTINA_LAT_MIN=-55.0
ARGENTINA_LAT_MAX=-21.0
ARGENTINA_LNG_MIN=-73.5
ARGENTINA_LNG_MAX=-53.0
```

---

## 📊 **Límites y Validaciones**

| Parámetro | Mínimo | Máximo | Default |
|-----------|--------|--------|---------|
| `radio_km` | 0.1 | 100 | 10 |
| `latitud` | -90 | 90 | - |
| `longitud` | -180 | 180 | - |
| Timeout geocodificación | - | 10s | - |
| Resultados por búsqueda | - | 50 | - |

**Coordenadas válidas para Argentina:**
- Latitud: -55.0 a -21.0
- Longitud: -73.5 a -53.0

---

## 🔍 **Troubleshooting**

### **Error 408: Timeout de geocodificación**

**Causa:** El servicio de Georef tardó más de 10 segundos.

**Solución:**
- Reintentar la petición
- Usar modo manual con coordenadas específicas
- Verificar conectividad con API Georef

---

### **Error 400: Dirección no geocodificable**

**Causa:** La dirección no existe o está mal escrita.

**Solución:**
- Verificar ortografía de calle, ciudad y provincia
- Usar nombres oficiales de localidades
- Probar sin número de calle
- Usar modo manual si persiste el error

---

### **Coordenadas fuera de Argentina**

**Causa:** Las coordenadas proporcionadas no están dentro del territorio argentino.

**Solución:**
- Verificar que latitud esté entre -55.0 y -21.0
- Verificar que longitud esté entre -73.5 y -53.0
- Revisar el orden (latitud, longitud) no al revés

---

## 🚀 **Performance**

- **Geocodificación:** ~500-2000ms (depende de API Georef)
- **Búsqueda por coordenadas:** <100ms (con índices optimizados)
- **Radio <10km:** ~50-100ms
- **Radio >50km:** ~200-500ms

**Optimizaciones implementadas:**
- ✅ Índice compuesto en `(latitud, longitud)`
- ✅ Límite de 50 resultados por búsqueda
- ✅ Timeout de 10s para geocodificación
- ✅ Cache de direcciones frecuentes (futuro)

---

## 📚 **Referencias**

- [API Georef Argentina](https://datosgobar.github.io/georef-ar-api/)
- [Fórmula de Haversine](https://en.wikipedia.org/wiki/Haversine_formula) - Cálculo de distancias
- [Leaflet.js](https://leafletjs.com/) - Librería de mapas recomendada

---

## 🎯 **Roadmap**

- [ ] Cache de geocodificación en Redis
- [ ] Búsqueda por múltiples categorías
- [ ] Ordenamiento personalizado (rating, distancia, etc.)
- [ ] Exportar resultados a CSV/JSON
- [ ] Heatmap de densidad de empresas
- [ ] Sugerencias de direcciones (autocomplete)

---

**Última actualización:** 17/10/2025  
**Versión:** 1.0.0