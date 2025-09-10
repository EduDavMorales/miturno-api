-- Base de datos: Sistema de Gestión de Turnos
-- MySQL compatible con phpMyAdmin

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS sistema_turnos
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE sistema_turnos;

-- =============================================
-- TABLA: USUARIO
-- Base para clientes y empresas
-- =============================================
CREATE TABLE usuario (
    usuario_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    tipo_usuario ENUM('cliente', 'empresa') NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_tipo_usuario (tipo_usuario),
    INDEX idx_fecha_creacion (fecha_creacion)
) ENGINE=InnoDB;

-- =============================================
-- TABLA: CATEGORIA
-- =============================================
CREATE TABLE categoria (
    categoria_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    activa BOOLEAN DEFAULT TRUE,
    
    INDEX idx_nombre (nombre),
    INDEX idx_activa (activa)
) ENGINE=InnoDB;

-- =============================================
-- TABLA: EMPRESA
-- =============================================
CREATE TABLE empresa (
    empresa_id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT UNIQUE NOT NULL,
    categoria_id INT NOT NULL,
    razon_social VARCHAR(200) NOT NULL,
    cuit VARCHAR(13) UNIQUE,
    direccion VARCHAR(300) NOT NULL,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    descripcion TEXT,
    horario_apertura TIME NOT NULL,
    horario_cierre TIME NOT NULL,
    duracion_turno_minutos INT DEFAULT 60,
    logo_url VARCHAR(500),
    activa BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categoria(categoria_id) ON DELETE RESTRICT,
    
    INDEX idx_categoria (categoria_id),
    INDEX idx_ubicacion (latitud, longitud),
    INDEX idx_activa (activa),
    INDEX idx_horarios (horario_apertura, horario_cierre)
) ENGINE=InnoDB;

-- =============================================
-- TABLA: SERVICIO
-- =============================================
CREATE TABLE servicio (
    servicio_id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    duracion_minutos INT DEFAULT 60,
    precio DECIMAL(10, 2) DEFAULT 0.00,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresa(empresa_id) ON DELETE CASCADE,
    
    INDEX idx_empresa (empresa_id),
    INDEX idx_activo (activo),
    INDEX idx_precio (precio)
) ENGINE=InnoDB;

-- =============================================
-- TABLA: TURNO
-- =============================================
CREATE TABLE turno (
    turno_id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    cliente_id INT NOT NULL,
    servicio_id INT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado ENUM('pendiente', 'confirmado', 'cancelado', 'completado') DEFAULT 'pendiente',
    notas_cliente TEXT,
    notas_empresa TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fecha_cancelacion TIMESTAMP NULL,
    
    FOREIGN KEY (empresa_id) REFERENCES empresa(empresa_id) ON DELETE CASCADE,
    FOREIGN KEY (cliente_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (servicio_id) REFERENCES servicio(servicio_id) ON DELETE SET NULL,
    
    INDEX idx_empresa_fecha (empresa_id, fecha, hora),
    INDEX idx_cliente (cliente_id),
    INDEX idx_fecha_hora (fecha, hora),
    INDEX idx_estado (estado),
    INDEX idx_servicio (servicio_id),
    
    UNIQUE KEY unique_empresa_fecha_hora (empresa_id, fecha, hora)
) ENGINE=InnoDB;

-- =============================================
-- TABLA: HORARIO_EMPRESA
-- =============================================
CREATE TABLE horario_empresa (
    horario_id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    dia_semana ENUM('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo') NOT NULL,
    hora_apertura TIME NOT NULL,
    hora_cierre TIME NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (empresa_id) REFERENCES empresa(empresa_id) ON DELETE CASCADE,
    
    INDEX idx_empresa_dia (empresa_id, dia_semana),
    INDEX idx_activo (activo),
    
    UNIQUE KEY unique_empresa_dia (empresa_id, dia_semana)
) ENGINE=InnoDB;

-- =============================================
-- TABLA: BLOQUEO_HORARIO
-- =============================================
CREATE TABLE bloqueo_horario (
    bloqueo_id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    hora_inicio TIME,
    hora_fin TIME,
    motivo VARCHAR(255),
    tipo ENUM('feriado', 'vacaciones', 'mantenimiento', 'otro') DEFAULT 'otro',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresa(empresa_id) ON DELETE CASCADE,
    
    INDEX idx_empresa_fechas (empresa_id, fecha_inicio, fecha_fin),
    INDEX idx_tipo (tipo),
    INDEX idx_fechas (fecha_inicio, fecha_fin)
) ENGINE=InnoDB;

-- =============================================
-- TABLA: NOTIFICACION
-- =============================================
CREATE TABLE notificacion (
    notificacion_id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    turno_id INT,
    tipo ENUM('recordatorio', 'confirmacion', 'cancelacion') NOT NULL,
    mensaje TEXT NOT NULL,
    canal ENUM('email', 'whatsapp', 'push') DEFAULT 'email',
    enviada BOOLEAN DEFAULT FALSE,
    fecha_programada TIMESTAMP NOT NULL,
    fecha_enviada TIMESTAMP NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (turno_id) REFERENCES turno(turno_id) ON DELETE CASCADE,
    
    INDEX idx_usuario (usuario_id),
    INDEX idx_turno (turno_id),
    INDEX idx_fecha_programada (fecha_programada),
    INDEX idx_enviada (enviada),
    INDEX idx_tipo_canal (tipo, canal)
) ENGINE=InnoDB;

-- =============================================
-- DATOS INICIALES
-- =============================================
INSERT INTO categoria (nombre, descripcion) VALUES 
('Salud y Belleza', 'Peluquerías, spas, salones de uñas, maquillaje, barberías'),
('Servicios Médicos', 'Consultorios médicos, dentistas, psicólogos, nutricionistas'),
('Servicios Profesionales', 'Abogados, contadores, escribanos, consultores'),
('Servicios Técnicos', 'Reparaciones, mantenimiento, instalaciones, soporte técnico'),
('Educación y Capacitación', 'Clases particulares, cursos, talleres, entrenamientos'),
('Servicios Domésticos', 'Limpieza, jardinería, plomería, electricidad'),
('Bienestar y Fitness', 'Gimnasios, entrenadores personales, terapias, masajes'),
('Servicios Creativos', 'Fotografía, diseño, eventos, música, arte'),
('Servicios Automotrices', 'Mecánica, lavadero, inspecciones, seguros'),
('Servicios Inmobiliarios', 'Tasaciones, asesoría, gestiones, mudanzas');