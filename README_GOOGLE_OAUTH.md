# 🔐 Sistema de Google OAuth - MiTurno API

Sistema completo de autenticación con Google OAuth 2.0 para registro y login simplificado de usuarios.

---

## 🎯 **Características**

- ✅ Login con cuenta de Google (Sign in with Google)
- ✅ Registro automático de nuevos usuarios
- ✅ Vinculación de cuentas existentes
- ✅ Asignación automática de rol CLIENTE
- ✅ Generación de JWT token propio del sistema
- ✅ Actualización automática de información de perfil
- ✅ Foto de perfil desde Google

---

## 📡 **Endpoints Disponibles**

### **1. GET `/api/auth/google/login`**

Inicia el flujo de autenticación con Google. Redirige al usuario a la página de login de Google.

**Sin parámetros requeridos**

**Response (200 OK):**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?client_id=..."
}
```

**Uso:**
El frontend debe redirigir al usuario a esta URL para iniciar el login con Google.

**Errores:**
- `500`: Error generando URL de autorización

---

### **2. GET `/api/auth/google/callback`**

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

### **3. POST `/api/auth/google/token`**

Valida un ID token de Google y retorna un JWT token del sistema. **Endpoint recomendado para integraciones frontend modernas.**

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFmODNk..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "usuario": {
    "usuario_id": 15,
    "email": "usuario@gmail.com",
    "nombre": "Juan",
    "apellido": "Pérez",
    "google_id": "105847362947284756391",
    "picture_url": "https://lh3.googleusercontent.com/a/...",
    "tipo_usuario": "CLIENTE",
    "activo": true
  },
  "es_nuevo_usuario": true
}
```

**Comportamiento:**
1. **Usuario nuevo:**
   - Crea usuario en BD con datos de Google
   - Asigna rol CLIENTE automáticamente
   - Genera contraseña aleatoria (no utilizada)
   - Retorna `es_nuevo_usuario: true`

2. **Usuario existente por email:**
   - Vincula cuenta agregando `google_id`
   - Actualiza foto de perfil si no tenía
   - Retorna `es_nuevo_usuario: false`

3. **Usuario existente por google_id:**
   - Login directo
   - Actualiza información de perfil
   - Retorna `es_nuevo_usuario: false`

**Errores:**
- `400`: Token inválido o ausente
- `401`: Error validando con Google
- `500`: Error interno

---

## 🔐 **Configuración**

### **Variables de Entorno**

Agrega estas variables a tu `.env`:

```env
# Google OAuth
GOOGLE_CLIENT_ID=123456789-abcdefgh.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Solo para desarrollo local (permite HTTP)
OAUTHLIB_INSECURE_TRANSPORT=1
```

**Producción (Fly.io):**
```bash
fly secrets set GOOGLE_CLIENT_ID="tu_client_id.apps.googleusercontent.com"
fly secrets set GOOGLE_CLIENT_SECRET="GOCSPX-tu_secret"
fly secrets set GOOGLE_REDIRECT_URI="https://turnos-api.fly.dev/api/auth/google/callback"

# NO configurar OAUTHLIB_INSECURE_TRANSPORT en producción
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
   - Información de contacto: tu email
4. Alcances: Agregar los siguientes scopes
   - `openid`
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
5. Usuarios de prueba: Agregar tu email (para modo Testing)

### **Paso 3: Crear Credenciales OAuth**

1. APIs y servicios → Credenciales
2. Crear credenciales → ID de cliente de OAuth 2.0
3. Configuración:

```
Tipo de aplicación: Aplicación web
Nombre: MiTurno Backend API

Orígenes de JavaScript autorizados (opcional para backend):
   http://localhost:3000
   https://tu-frontend.vercel.app

URIs de redireccionamiento autorizados (importante):
   http://localhost:8000/api/auth/google/callback
   https://turnos-api.fly.dev/api/auth/google/callback
```

4. Crear y **guardar** Client ID y Client Secret

---

## 🧪 **Testing**

### **Opción 1: Flujo Completo (Redirect)**

1. **Iniciar login:**
   ```bash
   GET http://localhost:8000/api/auth/google/login
   ```

2. **Copiar `authorization_url` del response**

3. **Abrir URL en navegador:** Se abrirá página de login de Google

4. **Autorizar la aplicación**

5. **Serás redirigido al callback** con el token:
   ```
   http://localhost:3000/auth/success?token=eyJhbGc...&new_user=true
   ```

### **Opción 2: Validación de Token (Recomendado)**

**Desde Frontend:**
```javascript
// 1. Usuario hace click en "Sign in with Google"
import { GoogleLogin } from '@react-oauth/google';

<GoogleLogin
  onSuccess={(credentialResponse) => {
    // 2. Enviar token a tu backend
    fetch('http://localhost:8000/api/auth/google/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_token: credentialResponse.credential
      })
    })
    .then(res => res.json())
    .then(data => {
      // 3. Guardar token y redirigir
      localStorage.setItem('token', data.access_token);
      if (data.es_nuevo_usuario) {
        window.location.href = '/onboarding';
      } else {
        window.location.href = '/dashboard';
      }
    });
  }}
  onError={() => {
    console.log('Login Failed');
  }}
/>
```

**Testing Manual en Swagger:**
1. Ve a `/docs`
2. Endpoint: `POST /api/auth/google/token`
3. Obtén un `id_token` válido desde:
   - Herramienta: [Google OAuth Playground](https://developers.google.com/oauthplayground)
   - O desde tu frontend con `@react-oauth/google`
4. Pega el token en el body
5. Execute

---

## 🎨 **Integración con Frontend**

### **React con @react-oauth/google**

**1. Instalación:**
```bash
npm install @react-oauth/google
```

**2. Configuración en App.js:**
```jsx
import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  return (
    <GoogleOAuthProvider clientId="tu_client_id.apps.googleusercontent.com">
      <YourApp />
    </GoogleOAuthProvider>
  );
}
```

**3. Componente de Login:**
```jsx
import { GoogleLogin } from '@react-oauth/google';
import { useState } from 'react';

function LoginPage() {
  const [loading, setLoading] = useState(false);

  const handleGoogleSuccess = async (credentialResponse) => {
    setLoading(true);
    
    try {
      const response = await fetch('https://turnos-api.fly.dev/api/auth/google/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_token: credentialResponse.credential
        })
      });

      if (!response.ok) throw new Error('Login failed');

      const data = await response.json();
      
      // Guardar token
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('usuario', JSON.stringify(data.usuario));

      // Redirigir según tipo de usuario
      if (data.es_nuevo_usuario) {
        window.location.href = '/bienvenida';
      } else {
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error al iniciar sesión con Google');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h1>Iniciar Sesión</h1>
      
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={() => alert('Error al conectar con Google')}
        useOneTap
        text="signin_with"
        shape="rectangular"
        size="large"
      />
      
      {loading && <p>Iniciando sesión...</p>}
    </div>
  );
}
```

### **Vue 3**

```vue
<template>
  <div class="login">
    <h1>Iniciar Sesión</h1>
    <div id="g_id_onload"
         :data-client_id="clientId"
         data-callback="handleGoogleLogin">
    </div>
    <div class="g_id_signin" data-type="standard"></div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

onMounted(() => {
  // Cargar script de Google
  const script = document.createElement('script');
  script.src = 'https://accounts.google.com/gsi/client';
  script.async = true;
  document.head.appendChild(script);
  
  // Callback global
  window.handleGoogleLogin = async (response) => {
    try {
      const res = await fetch('https://turnos-api.fly.dev/api/auth/google/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: response.credential })
      });
      
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Error:', error);
    }
  };
});
</script>
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
- `google_id`: ID único del usuario en Google (ej: "105847362947284756391")
- `picture_url`: URL de la foto de perfil de Google

---

## 🔍 **Troubleshooting**

### **Error: "redirect_uri_mismatch"**

**Causa:** La URI de redirección no coincide con la configurada en Google Cloud Console.

**Solución:**
1. Ve a Google Cloud Console → Credenciales
2. Edita tu cliente OAuth
3. Verifica que las URIs sean exactamente:
   - `http://localhost:8000/api/auth/google/callback` (local)
   - `https://turnos-api.fly.dev/api/auth/google/callback` (producción)

---

### **Error: "invalid_grant"**

**Causa:** El código de autorización expiró o ya fue usado.

**Solución:**
- Los códigos de Google expiran en ~10 minutos
- Reinicia el flujo de login
- No reutilices códigos/tokens

---

### **Error: "OAUTHLIB_INSECURE_TRANSPORT"**

**Causa:** Intentando usar HTTP en lugar de HTTPS.

**Solución para desarrollo local:**
```env
OAUTHLIB_INSECURE_TRANSPORT=1
```

**Para producción:** NO agregues esta variable, usa HTTPS siempre.

---

### **Usuario creado pero sin rol**

**Causa:** Tabla `rol` vacía o rol CLIENTE no existe.

**Solución:**
```sql
-- Verificar que existe el rol CLIENTE
SELECT * FROM rol WHERE nombre = 'CLIENTE';

-- Si no existe, crearlo
INSERT INTO rol (nombre, descripcion, tipo, nivel, activo)
VALUES ('CLIENTE', 'Usuario cliente del sistema', 'SISTEMA', 1, true);
```

---

### **Error: "User not found" después de login**

**Causa:** El usuario se creó pero no se retornó correctamente.

**Solución:**
```python
# Verificar en el código que después de crear usuario se haga:
db.commit()
db.refresh(usuario)  # ← Importante para obtener el ID
```

---

## 📊 **Flujo Completo del Sistema**

```
┌─────────────┐
│   USUARIO   │
│  (Frontend) │
└──────┬──────┘
       │
       │ 1. Click "Sign in with Google"
       ▼
┌──────────────────┐
│  Google Login    │
│  Popup/Redirect  │
└──────┬───────────┘
       │
       │ 2. Usuario autoriza
       ▼
┌──────────────────┐
│  Google OAuth    │
│  id_token        │
└──────┬───────────┘
       │
       │ 3. POST /api/auth/google/token
       ▼
┌──────────────────────────┐
│  MiTurno Backend (FastAPI)│
│  - Valida token           │
│  - Busca/crea usuario     │
│  - Asigna rol CLIENTE     │
│  - Genera JWT propio      │
└──────┬───────────────────┘
       │
       │ 4. Response con JWT
       ▼
┌─────────────┐
│  Frontend   │
│  - Guarda   │
│    token    │
│  - Redirige │
└─────────────┘
```

---

## 🎯 **Mejores Prácticas**

### **Seguridad**

1. **Nunca expongas el Client Secret en el frontend**
   - Solo debe estar en el backend
   - Usa variables de entorno

2. **Valida siempre el token en el backend**
   - No confíes solo en el frontend
   - Verifica con la API de Google

3. **Usa HTTPS en producción**
   - Nunca uses `OAUTHLIB_INSECURE_TRANSPORT=1` en prod
   - Google rechazará conexiones inseguras

### **UX**

1. **Muestra estados de carga**
   ```jsx
   {loading && <Spinner />}
   ```

2. **Maneja errores gracefully**
   ```jsx
   onError={() => {
     toast.error('No se pudo conectar con Google. Intenta nuevamente.');
   }}
   ```

3. **Diferencia usuarios nuevos de existentes**
   ```jsx
   if (data.es_nuevo_usuario) {
     // Mostrar tutorial o bienvenida
   } else {
     // Ir directo al dashboard
   }
   ```

---

## 📚 **Referencias**

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/gsi/web)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
- [@react-oauth/google](https://www.npmjs.com/package/@react-oauth/google)

---

## 🚀 **Roadmap**

- [ ] Soporte para Apple Sign-In
- [ ] Soporte para Microsoft Account
- [ ] Refresh token para sesiones largas
- [ ] Desvinculación de cuenta Google
- [ ] Login con múltiples métodos (email + Google)

---

**Última actualización:** 20 de Octubre 2025  
**Versión:** 1.0.0  
**Estado:** ✅ Productivo y funcional