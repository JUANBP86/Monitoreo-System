-- Script para crear la estructura de la base de datos del Sistema de Monitoreo con Autenticación

-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    correo VARCHAR(100) NOT NULL UNIQUE,
    contraseña VARCHAR(255) NOT NULL,
    nombre VARCHAR(100),
    rol ENUM('admin', 'user') DEFAULT 'user',
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso DATETIME
);

-- Crear tabla de dispositivos
CREATE TABLE IF NOT EXISTS dispositivos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    ip VARCHAR(15) NOT NULL,
    tipo VARCHAR(50),
    ubicacion VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'activo',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_ip (ip)
);

-- Crear tabla de métricas
CREATE TABLE IF NOT EXISTS metricas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dispositivo_id INT NOT NULL,
    cpu DECIMAL(5,2),
    ram DECIMAL(5,2),
    disco DECIMAL(5,2),
    net_bytes_sent BIGINT DEFAULT 0,
    net_bytes_recv BIGINT DEFAULT 0,
    temperatura DECIMAL(5,2),
    procesos_activos INT DEFAULT 0,
    uptime BIGINT DEFAULT 0,
    estado VARCHAR(20),
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id) ON DELETE CASCADE,
    INDEX idx_dispositivo_id (dispositivo_id),
    INDEX idx_fecha (fecha)
);

-- Crear tabla de alertas
CREATE TABLE IF NOT EXISTS alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dispositivo_id INT NOT NULL,
    usuario_id INT NOT NULL,
    tipo VARCHAR(50),
    mensaje TEXT,
    fecha_alerta DATETIME DEFAULT CURRENT_TIMESTAMP,
    resuelta BOOLEAN DEFAULT FALSE,
    fecha_resolucion DATETIME,
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_dispositivo_id (dispositivo_id),
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_fecha_alerta (fecha_alerta)
);

-- Crear tabla de logs de auditoría
CREATE TABLE IF NOT EXISTS logs_auditoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(100),
    detalles TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_fecha (fecha)
);

-- Mostrar tablas creadas
SHOW TABLES;
