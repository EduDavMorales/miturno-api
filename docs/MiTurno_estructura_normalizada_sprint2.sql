CREATE DATABASE  IF NOT EXISTS `sistema_turnos` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `sistema_turnos`;
-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: sistema_turnos
-- ------------------------------------------------------
-- Server version	8.4.6

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('9e275309deea');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auditoria_detalle`
--

DROP TABLE IF EXISTS `auditoria_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auditoria_detalle` (
  `detalle_id` bigint NOT NULL AUTO_INCREMENT,
  `auditoria_id` bigint NOT NULL,
  `tipo_dato` enum('anterior','nuevo','metadata') NOT NULL,
  `campo_nombre` varchar(100) NOT NULL,
  `campo_valor` text,
  `campo_tipo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`detalle_id`),
  KEY `auditoria_id` (`auditoria_id`),
  KEY `ix_auditoria_detalle_detalle_id` (`detalle_id`),
  CONSTRAINT `auditoria_detalle_ibfk_1` FOREIGN KEY (`auditoria_id`) REFERENCES `auditoria_sistema` (`auditoria_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auditoria_detalle`
--

LOCK TABLES `auditoria_detalle` WRITE;
/*!40000 ALTER TABLE `auditoria_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `auditoria_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auditoria_sistema`
--

DROP TABLE IF EXISTS `auditoria_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auditoria_sistema` (
  `auditoria_id` bigint NOT NULL AUTO_INCREMENT,
  `tabla_afectada` varchar(50) NOT NULL,
  `registro_id` int NOT NULL,
  `accion` varchar(50) NOT NULL,
  `usuario_id` int NOT NULL,
  `empresa_id` int DEFAULT NULL,
  `datos_anteriores` json DEFAULT NULL,
  `datos_nuevos` json DEFAULT NULL,
  `campos_modificados` text,
  `motivo` varchar(255) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `fecha_cambio` datetime DEFAULT CURRENT_TIMESTAMP,
  `metadatos` json DEFAULT NULL,
  PRIMARY KEY (`auditoria_id`),
  KEY `ix_auditoria_sistema_fecha_cambio` (`fecha_cambio`),
  KEY `ix_auditoria_sistema_usuario_id` (`usuario_id`),
  KEY `ix_auditoria_sistema_accion` (`accion`),
  KEY `ix_auditoria_sistema_tabla_afectada` (`tabla_afectada`),
  KEY `ix_auditoria_sistema_auditoria_id` (`auditoria_id`),
  KEY `ix_auditoria_sistema_empresa_id` (`empresa_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auditoria_sistema`
--

LOCK TABLES `auditoria_sistema` WRITE;
/*!40000 ALTER TABLE `auditoria_sistema` DISABLE KEYS */;
/*!40000 ALTER TABLE `auditoria_sistema` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autorizacion_soporte`
--

DROP TABLE IF EXISTS `autorizacion_soporte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `autorizacion_soporte` (
  `autorizacion_id` int NOT NULL AUTO_INCREMENT,
  `usuario_solicitante_id` int NOT NULL,
  `usuario_autorizado_id` int NOT NULL,
  `empresa_id` int DEFAULT NULL,
  `nivel_acceso` varchar(20) NOT NULL,
  `motivo` text NOT NULL,
  `fecha_solicitud` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_autorizacion` datetime DEFAULT NULL,
  `fecha_vencimiento` datetime NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `token_acceso` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`autorizacion_id`),
  UNIQUE KEY `token_acceso` (`token_acceso`),
  KEY `usuario_solicitante_id` (`usuario_solicitante_id`),
  KEY `usuario_autorizado_id` (`usuario_autorizado_id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `ix_autorizacion_soporte_autorizacion_id` (`autorizacion_id`),
  CONSTRAINT `autorizacion_soporte_ibfk_1` FOREIGN KEY (`usuario_solicitante_id`) REFERENCES `usuario` (`usuario_id`),
  CONSTRAINT `autorizacion_soporte_ibfk_2` FOREIGN KEY (`usuario_autorizado_id`) REFERENCES `usuario` (`usuario_id`),
  CONSTRAINT `autorizacion_soporte_ibfk_3` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autorizacion_soporte`
--

LOCK TABLES `autorizacion_soporte` WRITE;
/*!40000 ALTER TABLE `autorizacion_soporte` DISABLE KEYS */;
/*!40000 ALTER TABLE `autorizacion_soporte` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bloqueo_horario`
--

DROP TABLE IF EXISTS `bloqueo_horario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bloqueo_horario` (
  `bloqueo_id` int NOT NULL AUTO_INCREMENT,
  `empresa_id` int NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `hora_inicio` time DEFAULT NULL,
  `hora_fin` time DEFAULT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `tipo` enum('FERIADO','VACACIONES','MANTENIMIENTO','OTRO') DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`bloqueo_id`),
  KEY `empresa_id` (`empresa_id`),
  CONSTRAINT `bloqueo_horario_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bloqueo_horario`
--

LOCK TABLES `bloqueo_horario` WRITE;
/*!40000 ALTER TABLE `bloqueo_horario` DISABLE KEYS */;
/*!40000 ALTER TABLE `bloqueo_horario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `categoria_id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(500) DEFAULT NULL,
  `activa` tinyint(1) NOT NULL,
  PRIMARY KEY (`categoria_id`),
  UNIQUE KEY `ix_categoria_nombre` (`nombre`),
  KEY `ix_categoria_categoria_id` (`categoria_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categoria`
--

LOCK TABLES `categoria` WRITE;
/*!40000 ALTER TABLE `categoria` DISABLE KEYS */;
/*!40000 ALTER TABLE `categoria` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `direccion`
--

DROP TABLE IF EXISTS `direccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `direccion` (
  `direccion_id` int NOT NULL AUTO_INCREMENT,
  `calle` varchar(100) NOT NULL,
  `numero` varchar(10) DEFAULT NULL,
  `ciudad` varchar(50) NOT NULL,
  `provincia` varchar(50) NOT NULL,
  `codigo_postal` varchar(10) DEFAULT NULL,
  `pais` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`direccion_id`),
  KEY `ix_direccion_direccion_id` (`direccion_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `direccion`
--

LOCK TABLES `direccion` WRITE;
/*!40000 ALTER TABLE `direccion` DISABLE KEYS */;
/*!40000 ALTER TABLE `direccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `empresa`
--

DROP TABLE IF EXISTS `empresa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empresa` (
  `empresa_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `categoria_id` int NOT NULL,
  `razon_social` varchar(200) NOT NULL,
  `cuit` varchar(13) DEFAULT NULL,
  `latitud` decimal(10,8) DEFAULT NULL,
  `longitud` decimal(11,8) DEFAULT NULL,
  `descripcion` text,
  `duracion_turno_minutos` int DEFAULT NULL,
  `logo_url` varchar(500) DEFAULT NULL,
  `activa` tinyint(1) NOT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `direccion_id` int DEFAULT NULL,
  `geocoding_confidence` varchar(50) DEFAULT NULL,
  `geocoding_warning` text,
  `requires_verification` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`empresa_id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  UNIQUE KEY `cuit` (`cuit`),
  KEY `categoria_id` (`categoria_id`),
  KEY `direccion_id` (`direccion_id`),
  KEY `ix_empresa_empresa_id` (`empresa_id`),
  KEY `idx_empresa_coordenadas` (`latitud`,`longitud`),
  CONSTRAINT `empresa_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`),
  CONSTRAINT `empresa_ibfk_2` FOREIGN KEY (`categoria_id`) REFERENCES `categoria` (`categoria_id`),
  CONSTRAINT `empresa_ibfk_3` FOREIGN KEY (`direccion_id`) REFERENCES `direccion` (`direccion_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `empresa`
--

LOCK TABLES `empresa` WRITE;
/*!40000 ALTER TABLE `empresa` DISABLE KEYS */;
/*!40000 ALTER TABLE `empresa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `horario_empresa`
--

DROP TABLE IF EXISTS `horario_empresa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `horario_empresa` (
  `horario_id` int NOT NULL AUTO_INCREMENT,
  `empresa_id` int NOT NULL,
  `dia_semana` enum('lunes','martes','miercoles','jueves','viernes','sabado','domingo') NOT NULL,
  `hora_apertura` time NOT NULL,
  `hora_cierre` time NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`horario_id`),
  KEY `empresa_id` (`empresa_id`),
  CONSTRAINT `horario_empresa_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `horario_empresa`
--

LOCK TABLES `horario_empresa` WRITE;
/*!40000 ALTER TABLE `horario_empresa` DISABLE KEYS */;
/*!40000 ALTER TABLE `horario_empresa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mensaje`
--

DROP TABLE IF EXISTS `mensaje`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mensaje` (
  `mensaje_id` int NOT NULL AUTO_INCREMENT,
  `turno_id` int NOT NULL,
  `emisor_id` int NOT NULL,
  `contenido` text NOT NULL,
  `fecha_envio` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `leido` tinyint(1) NOT NULL,
  PRIMARY KEY (`mensaje_id`),
  KEY `turno_id` (`turno_id`),
  KEY `emisor_id` (`emisor_id`),
  KEY `ix_mensaje_mensaje_id` (`mensaje_id`),
  CONSTRAINT `mensaje_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turno` (`turno_id`),
  CONSTRAINT `mensaje_ibfk_2` FOREIGN KEY (`emisor_id`) REFERENCES `usuario` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mensaje`
--

LOCK TABLES `mensaje` WRITE;
/*!40000 ALTER TABLE `mensaje` DISABLE KEYS */;
/*!40000 ALTER TABLE `mensaje` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permiso`
--

DROP TABLE IF EXISTS `permiso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permiso` (
  `permiso_id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(100) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `categoria` varchar(50) NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`permiso_id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `ix_permiso_permiso_id` (`permiso_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permiso`
--

LOCK TABLES `permiso` WRITE;
/*!40000 ALTER TABLE `permiso` DISABLE KEYS */;
/*!40000 ALTER TABLE `permiso` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rol`
--

DROP TABLE IF EXISTS `rol`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol` (
  `rol_id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `descripcion` text,
  `tipo` varchar(20) NOT NULL,
  `nivel` int NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rol_id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `ix_rol_rol_id` (`rol_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rol`
--

LOCK TABLES `rol` WRITE;
/*!40000 ALTER TABLE `rol` DISABLE KEYS */;
/*!40000 ALTER TABLE `rol` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rol_permiso`
--

DROP TABLE IF EXISTS `rol_permiso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol_permiso` (
  `rol_permiso_id` int NOT NULL AUTO_INCREMENT,
  `rol_id` int NOT NULL,
  `permiso_id` int NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_asignado` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rol_permiso_id`),
  KEY `rol_id` (`rol_id`),
  KEY `permiso_id` (`permiso_id`),
  KEY `ix_rol_permiso_rol_permiso_id` (`rol_permiso_id`),
  CONSTRAINT `rol_permiso_ibfk_1` FOREIGN KEY (`rol_id`) REFERENCES `rol` (`rol_id`),
  CONSTRAINT `rol_permiso_ibfk_2` FOREIGN KEY (`permiso_id`) REFERENCES `permiso` (`permiso_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rol_permiso`
--

LOCK TABLES `rol_permiso` WRITE;
/*!40000 ALTER TABLE `rol_permiso` DISABLE KEYS */;
/*!40000 ALTER TABLE `rol_permiso` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servicio`
--

DROP TABLE IF EXISTS `servicio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servicio` (
  `servicio_id` int NOT NULL AUTO_INCREMENT,
  `empresa_id` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `duracion_minutos` int DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`servicio_id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `ix_servicio_servicio_id` (`servicio_id`),
  CONSTRAINT `servicio_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servicio`
--

LOCK TABLES `servicio` WRITE;
/*!40000 ALTER TABLE `servicio` DISABLE KEYS */;
/*!40000 ALTER TABLE `servicio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `turno`
--

DROP TABLE IF EXISTS `turno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `turno` (
  `turno_id` int NOT NULL AUTO_INCREMENT,
  `empresa_id` int NOT NULL,
  `cliente_id` int NOT NULL,
  `servicio_id` int DEFAULT NULL,
  `fecha` date NOT NULL,
  `hora` time NOT NULL,
  `estado` enum('pendiente','confirmado','cancelado','completado') NOT NULL,
  `notas_cliente` text,
  `notas_empresa` text,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_cancelacion` datetime DEFAULT NULL,
  `cancelado_por` enum('cliente','empresa') DEFAULT NULL,
  `motivo_cancelacion` text,
  PRIMARY KEY (`turno_id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `servicio_id` (`servicio_id`),
  KEY `ix_turno_turno_id` (`turno_id`),
  KEY `ix_turno_hora` (`hora`),
  KEY `ix_turno_fecha` (`fecha`),
  CONSTRAINT `turno_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`),
  CONSTRAINT `turno_ibfk_2` FOREIGN KEY (`cliente_id`) REFERENCES `usuario` (`usuario_id`),
  CONSTRAINT `turno_ibfk_3` FOREIGN KEY (`servicio_id`) REFERENCES `servicio` (`servicio_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `turno`
--

LOCK TABLES `turno` WRITE;
/*!40000 ALTER TABLE `turno` DISABLE KEYS */;
/*!40000 ALTER TABLE `turno` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `usuario_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `telefono` varchar(15) NOT NULL,
  `tipo_usuario` enum('CLIENTE','EMPRESA') NOT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario_id`),
  UNIQUE KEY `ix_usuario_email` (`email`),
  KEY `ix_usuario_usuario_id` (`usuario_id`),
  KEY `ix_usuario_tipo_usuario` (`tipo_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario_rol`
--

DROP TABLE IF EXISTS `usuario_rol`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario_rol` (
  `usuario_rol_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `rol_id` int NOT NULL,
  `empresa_id` int DEFAULT NULL,
  `asignado_por` int DEFAULT NULL,
  `fecha_asignado` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_vencimiento` datetime DEFAULT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `motivo_inactivacion` text,
  PRIMARY KEY (`usuario_rol_id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `rol_id` (`rol_id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `asignado_por` (`asignado_por`),
  KEY `ix_usuario_rol_usuario_rol_id` (`usuario_rol_id`),
  CONSTRAINT `usuario_rol_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`),
  CONSTRAINT `usuario_rol_ibfk_2` FOREIGN KEY (`rol_id`) REFERENCES `rol` (`rol_id`),
  CONSTRAINT `usuario_rol_ibfk_3` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`),
  CONSTRAINT `usuario_rol_ibfk_4` FOREIGN KEY (`asignado_por`) REFERENCES `usuario` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario_rol`
--

LOCK TABLES `usuario_rol` WRITE;
/*!40000 ALTER TABLE `usuario_rol` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuario_rol` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-30  1:10:44
