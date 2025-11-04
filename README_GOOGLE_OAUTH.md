# 🔐 Sistema de Autenticación - MiTurno API

Sistema completo de autenticación con soporte para login tradicional (email/password), Google OAuth 2.0 y sistema de refresh tokens.

---

## 🎯 **Características**

- ✅ Login tradicional con email y contraseña
- ✅ Registro de nuevos usuarios (Cliente/Empresa)
- ✅ Login con cuenta de Google (Sign in with Google)
- ✅ Sistema de refresh tokens (sesiones largas)
- ✅ Registro automático de usuarios con Google
- ✅ Vinculación de cuentas existentes
- ✅ Asignación automática de roles
- ✅ Generación de JWT tokens propios del sistema
- ✅ Actualización automática de información de perfil
- ✅ Foto de perfil desde Google

---

## 📡 **Endpoints Disponibles**

### **1. POST `/api/auth/login`**

Login tradicional con email y contraseña. Devuelve access token y refresh token.

**Sin autenticación requerida**

**Request Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "miPassword123"
}
```

**Response (200 OK):**
```json
{
  "message": "Login exitoso",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "usuario": {
    "usuario_id": 15,
    "email": "usuario@ejemplo.com",
    "nombre": "Juan",
    "apellido": "Pérez",
    "telefono": "+541123456789",
    "tipo_usuario": "CLIENTE"
  }
}
```

**Validaciones:**
- ✅ Email debe ser válido
- ✅ Password mínimo 8 caracteres
- ✅ Usuario debe estar activo
- ✅ Credenciales correctas

**Errores:**
- `401`: Credenciales inválidas
- `403`: Usuario inactivo
- `422`: Validación de datos fallida

---

### **2. POST `/api/auth/register`**

Registro de nuevo usuario (cliente o empresa).

**Sin autenticación requerida**

**Request Body:**
```json
{
  "email": "nuevo@ejemplo.com",
  "password": "miPassword123",
  "nombre": "María",
  "apellido": "González",
  "telefono": "+541123456789",
  "tipo_usuario": "CLIENTE",
  "categoria_id": 1
}
```

**Campos:**
- `email` (required): Email único en el sistema
- `password` (required): Mínimo 8 caracteres
- `nombre` (required): Nombre del usuario
- `apellido` (required): Apellido del usuario
- `telefono` (optional): Mínimo 10 caracteres
- `tipo_usuario` (optional): "CLIENTE" o "EMPRESA", default: "CLIENTE"
- `categoria_id` (optional): Solo si tipo_usuario es "EMPRESA"

**Response (200 OK):**
```json
{
  "message": "Usuario registrado exitosamente",
  "usuario_id": 20
}
```

**Comportamiento:**
1. **Usuario CLIENTE:**
   - Se crea usuario con rol CLIENTE
   - Acceso inmediato a reservar turnos

2. **Usuario EMPRESA:**
   - Se crea usuario con tipo EMPRESA
   - Requiere `categoria_id` (categoría del negocio)
   - Debe completar información de empresa después del registro

**Errores:**
- `400`: Email ya registrado
- `422`: Validación fallida (password corto, email inválido, etc.)

---

### **3. POST `/api/auth/refresh`**

Obtiene un nuevo access token usando un refresh token válido.

**Sin autenticación requerida** (usa refresh token)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Comportamiento:**
- ✅ Valida refresh token
- ✅ Genera nuevo access token (30 min)
- ✅ Genera nuevo refresh token (7 días)
- ✅ El refresh token anterior queda invalidado

**Errores:**
- `401`: Refresh token inválido o expirado
- `422`: Token malformado

**Uso recomendado:**
```javascript
// Cuando el access token expira (401), usar refresh
const response = await fetch('/api/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    refresh_token: localStorage.getItem('refresh_token')
  })
});

const { access_token, refresh_token } = await response.json();
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);
```

---

## 🔵 **Autenticación con Google OAuth**

### **4. POST `/api/auth/google`**

Autenticación con Google OAuth - Recibe id_token del frontend.

**Sin autenticación requerida**

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFmODNk...",
  "tipo_usuario": "empresa"
}
```

**Campos:**
- `id_token` (required): Token de Google obtenido del frontend
- `tipo_usuario` (optional): "cliente" o "empresa", default: "cliente"

**Response (200 OK):**
```json
{
  "message": "Login exitoso con Google",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "usuario_id": 25,
    "email": "usuario@gmail.com",
    "nombre": "Pedro",
    "apellido": "Ramírez",
    "telefono": null,
    "tipo_usuario": "EMPRESA"
  }
}
```

**Comportamiento:**
1. **Usuario nuevo:**
   - Crea usuario automáticamente con datos de Google
   - Asigna rol según `tipo_usuario`
   - Genera contraseña aleatoria (no utilizada)
   - Retorna token inmediatamente

2. **Usuario existente por email:**
   - Vincula cuenta agregando `google_id`
   - Actualiza foto de perfil si no tenía
   - Login directo

3. **Usuario existente por google_id:**
   - Login directo
   - Actualiza información de perfil

**Errores:**
- `400`: Token inválido o ausente
- `401`: Error validando con Google
- `500`: Error interno

---

### **5. GET `/api/auth/google/login`**

Inicia el flujo de autenticación con Google. Redirige al usuario a la página de login de Google.

**Sin autenticación requerida**

**Response (200 OK):**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?client_id=...",
  "message": "Redirige al usuario a esta URL"
}
```

**Uso:**
El frontend debe redirigir al usuario a la `authorization_url` para iniciar el login con Google.

**Errores:**
- `500`: Error generando URL de autorización

---

### **6. GET `/api/auth/google/callback`**

Callback automático de Google después de que el usuario autoriza la aplicación. **No debe ser llamado directamente por el frontend.**

**Query Parameters:**
- `code` (required): Código de autorización de Google
- `state` (optional): Estado para validación

**Response (302 Redirect):**
Redirige al frontend con:
```
http://localhost:3000/auth/success?token=eyJhbGc...&new_user=true
```

**Errores:**
- `400`: Código de autorización inválido o ausente
- `401`: Error validando token de Google
- `500`: Error interno

---

### **7. POST `/api/auth/google/token`**

Valida un ID token de Google y retorna un JWT token del sistema. **Endpoint recomendado para integraciones frontend modernas.**

**Sin autenticación requerida**

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFmODNk...",
  "tipo_usuario": "cliente"
}
```

**Campos:**
- `id_token` (required): Token de Google
- `tipo_usuario` (optional): "cliente" o "empresa", default: "cliente"

**Response (200 OK):**
```json
{
  "message": "Login exitoso con Google",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "usuario_id": 30,
    "email": "usuario@gmail.com",
    "nombre": "Ana",
    "apellido": "Martínez",
    "telefono": null,
    "tipo_usuario": "CLIENTE"
  }
}
```

**Diferencia con `/api/auth/google`:**
- Ambos endpoints hacen lo mismo
- `/api/auth/google/token` sigue la convención RESTful
- `/api/auth/google` es un alias más corto
- Usa el que prefieras, funcionan idénticamente

**Errores:**
- `400`: Token inválido o ausente
- `401`: Error validando con Google
- `500`: Error interno

---

## 🔑 **Sistema de Tokens**

### **Access Token**
- **Duración:** 30 minutos
- **Uso:** Autenticación en endpoints protegidos
- **Almacenamiento:** LocalStorage o memoria (recomendado)

### **Refresh Token**
- **Duración:** 7 días
- **Uso:** Renovar access token sin re-login
- **Almacenamiento:** LocalStorage (secure)
- **Rotación:** Se genera nuevo refresh token en cada renovación

### **Flujo de Renovación Automática:**

```javascript
// Interceptor de axios para renovación automática
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        });
        
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        // Reintentar request original con nuevo token
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh falló, redirigir a login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

---

## 🔒 **Autenticación de Requests**

Todos los endpoints protegidos requieren Bearer token:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Ejemplo de Request Autenticado:**

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('/api/v1/mis-turnos', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

---

## 🧪 **Ejemplos de Uso**

### **Caso 1: Login tradicional**

```javascript
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) {
    throw new Error('Credenciales inválidas');
  }
  
  const data = await response.json();
  
  // Guardar tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('usuario', JSON.stringify(data.usuario));
  
  return data.usuario;
};
```

---

### **Caso 2: Registro de nuevo usuario**

```javascript
const registrar = async (datos) => {
  const response = await fetch('http://localhost:8000/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: datos.email,
      password: datos.password,
      nombre: datos.nombre,
      apellido: datos.apellido,
      telefono: datos.telefono,
      tipo_usuario: 'CLIENTE'
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error en el registro');
  }
  
  const result = await response.json();
  console.log(`Usuario registrado con ID: ${result.usuario_id}`);
  
  // Hacer login automáticamente
  return await login(datos.email, datos.password);
};
```

---

### **Caso 3: Login con Google (Flujo Completo)**

```javascript
import { GoogleLogin } from '@react-oauth/google';

function LoginPage() {
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_token: credentialResponse.credential,
          tipo_usuario: 'cliente'
        })
      });
      
      if (!response.ok) throw new Error('Login failed');
      
      const data = await response.json();
      
      // Guardar token
      localStorage.setItem('access_token', data.token);
      localStorage.setItem('usuario', JSON.stringify(data.usuario));
      
      // Redirigir
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Error:', error);
      alert('Error al iniciar sesión con Google');
    }
  };
  
  return (
    <GoogleLogin
      onSuccess={handleGoogleSuccess}
      onError={() => alert('Error al conectar con Google')}
      useOneTap
    />
  );
}
```

---

### **Caso 4: Renovación automática de token**

```javascript
// Hook personalizado para auto-refresh
const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  useEffect(() => {
    // Verificar token cada 25 minutos
    const interval = setInterval(async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        try {
          const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
          });
          
          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
          } else {
            // Token expiró, hacer logout
            localStorage.clear();
            window.location.href = '/login';
          }
        } catch (error) {
          console.error('Error renovando token:', error);
        }
      }
    }, 25 * 60 * 1000); // 25 minutos
    
    return () => clearInterval(interval);
  }, []);
  
  return { isAuthenticated };
};
```

---

## ⚙️ **Configuración**

### **Variables de Entorno**

```env
# JWT Configuration
SECRET_KEY=tu_secret_key_super_segura_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=123456789-abcdefgh.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Solo para desarrollo local (permite HTTP)
OAUTHLIB_INSECURE_TRANSPORT=1
```

**Producción (Railway/Fly.io):**
```bash
# NO configurar OAUTHLIB_INSECURE_TRANSPORT en producción
# Usar siempre HTTPS
```

---

## 🛠️ **Configuración de Google Cloud Console**

### **Paso 1: Crear Proyecto**
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Click en "Nuevo Proyecto"
3. Nombre: "MiTurno Auth"
4. Crear

### **Paso 2: Configurar Pantalla de Consentimiento**
1. APIs y servicios → Pantalla de consentimiento de OAuth
2. Tipo de usuario: **Usuarios externos**
3. Información de la aplicación:
   - Nombre: **MiTurno**
   - Correo de asistencia: tu email
   - Logotipo: (opcional)
4. Alcances: Agregar los siguientes scopes
   - `openid`
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`

### **Paso 3: Crear Credenciales OAuth**
```
Tipo de aplicación: Aplicación web
Nombre: MiTurno Backend API

Orígenes de JavaScript autorizados:
   http://localhost:3000
   https://tu-frontend.vercel.app

URIs de redireccionamiento autorizados:
   http://localhost:8000/api/auth/google/callback
   https://tu-api.railway.app/api/auth/google/callback
```

---

## 🗄️ **Base de Datos**

### **Campos en Usuario**

```sql
ALTER TABLE usuario
ADD COLUMN google_id VARCHAR(255) UNIQUE NULL,
ADD COLUMN picture_url VARCHAR(500) NULL,
ADD INDEX idx_google_id (google_id);
```

Los campos agregados:
- `google_id`: ID único del usuario en Google
- `picture_url`: URL de la foto de perfil de Google

---

## 🔍 **Troubleshooting**

### **Error 401: "Credenciales inválidas"**

**Causa:** Email o password incorrectos.

**Solución:**
- Verificar email y password
- Intentar recuperación de contraseña
- Verificar que el usuario esté activo

---

### **Error 401: "Token expirado"**

**Causa:** El access token expiró (30 minutos).

**Solución:**
```javascript
// Usar refresh token para obtener nuevo access token
const response = await fetch('/api/auth/refresh', {
  method: 'POST',
  body: JSON.stringify({
    refresh_token: localStorage.getItem('refresh_token')
  })
});
```

---

### **Error: "Refresh token inválido"**

**Causa:** El refresh token expiró (7 días) o fue invalidado.

**Solución:**
- Usuario debe hacer login nuevamente
- Implementar detección automática y redirigir a login

---

### **Error: "redirect_uri_mismatch" (Google)**

**Causa:** La URI de redirección no coincide con la configurada en Google Cloud Console.

**Solución:**
1. Ve a Google Cloud Console → Credenciales
2. Edita tu cliente OAuth
3. Verifica que las URIs sean exactamente:
   - `http://localhost:8000/api/auth/google/callback` (local)
   - `https://tu-api.com/api/auth/google/callback` (producción)

---

## 📊 **Comparación de Métodos de Autenticación**

| Característica | Email/Password | Google OAuth | Refresh Token |
|----------------|----------------|--------------|---------------|
| **Registro rápido** | ❌ Formulario completo | ✅ 1 click | N/A |
| **Seguridad** | ⚠️ Depende de password | ✅ Alta | ✅ Alta |
| **Sesión larga** | ✅ Con refresh token | ⚠️ Sin refresh | ✅ 7 días |
| **Recuperación** | ✅ Email recovery | ✅ Automática | ✅ Auto-renovación |
| **Sin internet** | ✅ Funciona | ❌ Requiere conexión | ✅ Funciona |

---

## 🎯 **Mejores Prácticas**

### **Seguridad**

1. **Nunca expongas tokens en URLs**
   ```javascript
   // ❌ MAL
   window.location.href = `/dashboard?token=${token}`;
   
   // ✅ BIEN
   localStorage.setItem('access_token', token);
   window.location.href = '/dashboard';
   ```

2. **Usa refresh tokens correctamente**
   - Guarda access token en memoria cuando sea posible
   - Guarda refresh token en localStorage/httpOnly cookie
   - Renueva automáticamente antes de expiración

3. **Logout seguro**
   ```javascript
   const logout = () => {
     localStorage.removeItem('access_token');
     localStorage.removeItem('refresh_token');
     localStorage.removeItem('usuario');
     window.location.href = '/login';
   };
   ```

### **UX**

1. **Manejo de errores claro**
   ```javascript
   try {
     await login(email, password);
   } catch (error) {
     if (error.status === 401) {
       toast.error('Email o contraseña incorrectos');
     } else if (error.status === 403) {
       toast.error('Tu cuenta está inactiva. Contacta soporte.');
     } else {
       toast.error('Error al iniciar sesión');
     }
   }
   ```

2. **Indicadores de carga**
   ```jsx
   {loading && <Spinner />}
   ```

3. **Recordar sesión**
   ```javascript
   if (localStorage.getItem('refresh_token')) {
     // Usuario tiene sesión activa
     redirectToDashboard();
   }
   ```

---

## 🚀 **Roadmap**

- [ ] Autenticación con Apple Sign-In
- [ ] Autenticación con Microsoft Account  
- [ ] Two-Factor Authentication (2FA)
- [ ] Desvinculación de cuenta Google
- [ ] Login con múltiples métodos simultáneos
- [ ] Rate limiting en endpoints de auth
- [ ] Logs de seguridad (intentos fallidos)

---

**Última actualización:** Octubre 2025  
**Versión:** 2.0.0  
**Estado:** ✅ Productivo y funcional