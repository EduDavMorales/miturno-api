-- MySQL dump 10.13  Distrib 8.4.6, for Linux (x86_64)
--
-- Host: localhost    Database: sistema_turnos
-- ------------------------------------------------------
-- Server version	8.4.6

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `autorizacion_soporte`
--

DROP TABLE IF EXISTS `autorizacion_soporte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `autorizacion_soporte` (
  `autorizacion_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `admin_id` int NOT NULL,
  `recurso_tipo` enum('turno','usuario','empresa') NOT NULL,
  `recurso_id` int NOT NULL,
  `motivo` text NOT NULL,
  `autorizado` tinyint(1) DEFAULT '0',
  `fecha_solicitud` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_autorizacion` timestamp NULL DEFAULT NULL,
  `fecha_vencimiento` timestamp NOT NULL,
  `utilizado` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`autorizacion_id`),
  KEY `admin_id` (`admin_id`),
  KEY `idx_usuario_recurso` (`usuario_id`,`recurso_tipo`,`recurso_id`),
  KEY `idx_fecha_vencimiento` (`fecha_vencimiento`),
  KEY `idx_autorizado` (`autorizado`),
  CONSTRAINT `autorizacion_soporte_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`),
  CONSTRAINT `autorizacion_soporte_ibfk_2` FOREIGN KEY (`admin_id`) REFERENCES `usuario` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `tipo` enum('feriado','vacaciones','mantenimiento','otro') DEFAULT 'otro',
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`bloqueo_id`),
  KEY `idx_empresa_fechas` (`empresa_id`,`fecha_inicio`,`fecha_fin`),
  KEY `idx_tipo` (`tipo`),
  KEY `idx_fechas` (`fecha_inicio`,`fecha_fin`),
  CONSTRAINT `bloqueo_horario_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `categoria_id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `activa` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`categoria_id`),
  UNIQUE KEY `nombre` (`nombre`),
  KEY `idx_nombre` (`nombre`),
  KEY `idx_activa` (`activa`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `direccion` varchar(300) NOT NULL,
  `latitud` decimal(10,8) DEFAULT NULL,
  `longitud` decimal(11,8) DEFAULT NULL,
  `descripcion` text,
  `horario_apertura` time NOT NULL,
  `horario_cierre` time NOT NULL,
  `duracion_turno_minutos` int DEFAULT '60',
  `logo_url` varchar(500) DEFAULT NULL,
  `activa` tinyint(1) DEFAULT '1',
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`empresa_id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  UNIQUE KEY `cuit` (`cuit`),
  KEY `idx_categoria` (`categoria_id`),
  KEY `idx_ubicacion` (`latitud`,`longitud`),
  KEY `idx_activa` (`activa`),
  KEY `idx_horarios` (`horario_apertura`,`horario_cierre`),
  CONSTRAINT `empresa_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`) ON DELETE CASCADE,
  CONSTRAINT `empresa_ibfk_2` FOREIGN KEY (`categoria_id`) REFERENCES `categoria` (`categoria_id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`horario_id`),
  UNIQUE KEY `unique_empresa_dia` (`empresa_id`,`dia_semana`),
  KEY `idx_empresa_dia` (`empresa_id`,`dia_semana`),
  KEY `idx_activo` (`activo`),
  CONSTRAINT `horario_empresa_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `notificacion`
--

DROP TABLE IF EXISTS `notificacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notificacion` (
  `notificacion_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `turno_id` int DEFAULT NULL,
  `tipo` enum('recordatorio','confirmacion','cancelacion') NOT NULL,
  `mensaje` text NOT NULL,
  `canal` enum('email','whatsapp','push') DEFAULT 'email',
  `enviada` tinyint(1) DEFAULT '0',
  `fecha_programada` timestamp NOT NULL,
  `fecha_enviada` timestamp NULL DEFAULT NULL,
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`notificacion_id`),
  KEY `idx_usuario` (`usuario_id`),
  KEY `idx_turno` (`turno_id`),
  KEY `idx_fecha_programada` (`fecha_programada`),
  KEY `idx_enviada` (`enviada`),
  KEY `idx_tipo_canal` (`tipo`,`canal`),
  CONSTRAINT `notificacion_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`) ON DELETE CASCADE,
  CONSTRAINT `notificacion_ibfk_2` FOREIGN KEY (`turno_id`) REFERENCES `turno` (`turno_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `permiso`
--

DROP TABLE IF EXISTS `permiso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permiso` (
  `permiso_id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `codigo` varchar(100) NOT NULL,
  `descripcion` text,
  `recurso` varchar(50) NOT NULL,
  `accion` varchar(50) NOT NULL,
  `requiere_contexto` tinyint(1) DEFAULT '0',
  `requiere_consentimiento` tinyint(1) DEFAULT '0',
  `activo` tinyint(1) DEFAULT '1',
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`permiso_id`),
  UNIQUE KEY `nombre` (`nombre`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `idx_recurso_accion` (`recurso`,`accion`),
  KEY `idx_activo` (`activo`),
  KEY `idx_requiere_contexto` (`requiere_contexto`),
  KEY `idx_requiere_consentimiento` (`requiere_consentimiento`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `tipo` enum('global','empresa') NOT NULL,
  `nivel` int NOT NULL DEFAULT '1',
  `activo` tinyint(1) DEFAULT '1',
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`rol_id`),
  UNIQUE KEY `nombre` (`nombre`),
  UNIQUE KEY `slug` (`slug`),
  KEY `idx_tipo` (`tipo`),
  KEY `idx_activo` (`activo`),
  KEY `idx_nivel` (`nivel`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rol_permiso`
--

DROP TABLE IF EXISTS `rol_permiso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol_permiso` (
  `rol_id` int NOT NULL,
  `permiso_id` int NOT NULL,
  `fecha_asignado` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `asignado_por` int DEFAULT NULL,
  PRIMARY KEY (`rol_id`,`permiso_id`),
  KEY `permiso_id` (`permiso_id`),
  KEY `asignado_por` (`asignado_por`),
  KEY `idx_fecha_asignado` (`fecha_asignado`),
  CONSTRAINT `rol_permiso_ibfk_1` FOREIGN KEY (`rol_id`) REFERENCES `rol` (`rol_id`) ON DELETE CASCADE,
  CONSTRAINT `rol_permiso_ibfk_2` FOREIGN KEY (`permiso_id`) REFERENCES `permiso` (`permiso_id`) ON DELETE CASCADE,
  CONSTRAINT `rol_permiso_ibfk_3` FOREIGN KEY (`asignado_por`) REFERENCES `usuario` (`usuario_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `duracion_minutos` int DEFAULT '60',
  `precio` decimal(10,2) DEFAULT '0.00',
  `activo` tinyint(1) DEFAULT '1',
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`servicio_id`),
  KEY `idx_empresa` (`empresa_id`),
  KEY `idx_activo` (`activo`),
  KEY `idx_precio` (`precio`),
  CONSTRAINT `servicio_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `estado` enum('pendiente','confirmado','cancelado','completado') DEFAULT 'pendiente',
  `notas_cliente` text,
  `notas_empresa` text,
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `fecha_cancelacion` timestamp NULL DEFAULT NULL,
  `cancelado_por` enum('cliente','empresa') DEFAULT NULL,
  `motivo_cancelacion` text,
  PRIMARY KEY (`turno_id`),
  UNIQUE KEY `unique_empresa_fecha_hora` (`empresa_id`,`fecha`,`hora`),
  KEY `idx_empresa_fecha` (`empresa_id`,`fecha`,`hora`),
  KEY `idx_cliente` (`cliente_id`),
  KEY `idx_fecha_hora` (`fecha`,`hora`),
  KEY `idx_estado` (`estado`),
  KEY `idx_servicio` (`servicio_id`),
  CONSTRAINT `turno_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`) ON DELETE CASCADE,
  CONSTRAINT `turno_ibfk_2` FOREIGN KEY (`cliente_id`) REFERENCES `usuario` (`usuario_id`) ON DELETE CASCADE,
  CONSTRAINT `turno_ibfk_3` FOREIGN KEY (`servicio_id`) REFERENCES `servicio` (`servicio_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `fecha_creacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`),
  KEY `idx_tipo_usuario` (`tipo_usuario`),
  KEY `idx_fecha_creacion` (`fecha_creacion`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `usuario_permisos_activos`
--

DROP TABLE IF EXISTS `usuario_permisos_activos`;
/*!50001 DROP VIEW IF EXISTS `usuario_permisos_activos`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `usuario_permisos_activos` AS SELECT 
 1 AS `usuario_id`,
 1 AS `empresa_id`,
 1 AS `permiso_codigo`,
 1 AS `permiso_nombre`,
 1 AS `recurso`,
 1 AS `accion`,
 1 AS `requiere_contexto`,
 1 AS `requiere_consentimiento`,
 1 AS `rol_nombre`,
 1 AS `rol_tipo`,
 1 AS `rol_nivel`*/;
SET character_set_client = @saved_cs_client;

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
  `fecha_asignado` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_vencimiento` date DEFAULT NULL,
  `activo` tinyint(1) DEFAULT '1',
  `motivo_inactivacion` text,
  PRIMARY KEY (`usuario_rol_id`),
  UNIQUE KEY `unique_usuario_rol_empresa` (`usuario_id`,`rol_id`,`empresa_id`),
  KEY `asignado_por` (`asignado_por`),
  KEY `idx_usuario` (`usuario_id`),
  KEY `idx_rol` (`rol_id`),
  KEY `idx_empresa` (`empresa_id`),
  KEY `idx_activo` (`activo`),
  KEY `idx_fecha_vencimiento` (`fecha_vencimiento`),
  CONSTRAINT `usuario_rol_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`usuario_id`) ON DELETE CASCADE,
  CONSTRAINT `usuario_rol_ibfk_2` FOREIGN KEY (`rol_id`) REFERENCES `rol` (`rol_id`) ON DELETE CASCADE,
  CONSTRAINT `usuario_rol_ibfk_3` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`) ON DELETE CASCADE,
  CONSTRAINT `usuario_rol_ibfk_4` FOREIGN KEY (`asignado_por`) REFERENCES `usuario` (`usuario_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'sistema_turnos'
--
/*!50003 DROP FUNCTION IF EXISTS `usuario_tiene_permiso` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `usuario_tiene_permiso`(
    p_usuario_id INT,
    p_permiso_codigo VARCHAR(100), 
    p_empresa_id INT
) RETURNS tinyint(1)
    READS SQL DATA
    DETERMINISTIC
BEGIN
    DECLARE permiso_count INT DEFAULT 0;
    
    SELECT COUNT(*) INTO permiso_count
    FROM usuario_permisos_activos
    WHERE usuario_id = p_usuario_id
      AND permiso_codigo = p_permiso_codigo
      AND (empresa_id = p_empresa_id OR empresa_id IS NULL OR p_empresa_id IS NULL);
    
    RETURN permiso_count > 0;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Final view structure for view `usuario_permisos_activos`
--

/*!50001 DROP VIEW IF EXISTS `usuario_permisos_activos`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `usuario_permisos_activos` AS select distinct `ur`.`usuario_id` AS `usuario_id`,`ur`.`empresa_id` AS `empresa_id`,`p`.`codigo` AS `permiso_codigo`,`p`.`nombre` AS `permiso_nombre`,`p`.`recurso` AS `recurso`,`p`.`accion` AS `accion`,`p`.`requiere_contexto` AS `requiere_contexto`,`p`.`requiere_consentimiento` AS `requiere_consentimiento`,`r`.`nombre` AS `rol_nombre`,`r`.`tipo` AS `rol_tipo`,`r`.`nivel` AS `rol_nivel` from (((`usuario_rol` `ur` join `rol` `r` on((`ur`.`rol_id` = `r`.`rol_id`))) join `rol_permiso` `rp` on((`r`.`rol_id` = `rp`.`rol_id`))) join `permiso` `p` on((`rp`.`permiso_id` = `p`.`permiso_id`))) where ((`ur`.`activo` = true) and (`r`.`activo` = true) and (`p`.`activo` = true) and ((`ur`.`fecha_vencimiento` is null) or (`ur`.`fecha_vencimiento` > curdate()))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-17  0:46:09
