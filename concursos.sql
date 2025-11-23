-- Esquema de base de datos para el Bot de Empleos Públicos (Chile)
-- Este archivo define SOLO la estructura. No incluye datos de ejemplo.

-- 1) (Opcional) Crear la base de datos.
--    Puedes cambiar "bot_empleos" por el nombre que prefieras.
CREATE DATABASE IF NOT EXISTS `bot_empleos`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `bot_empleos`;

-- 2) Eliminar la tabla si existe (útil para recrear el esquema desde cero)
DROP TABLE IF EXISTS `concursos`;

-- 3) Crear tabla principal de concursos
CREATE TABLE IF NOT EXISTS `concursos` (
  `id`                INT NOT NULL AUTO_INCREMENT,
  `guid`              VARCHAR(255) NOT NULL,
  `titulo`            VARCHAR(500) NOT NULL,
  `link`              VARCHAR(500) NOT NULL,
  `fecha_publicacion` DATETIME DEFAULT NULL,
  `ministerio`        VARCHAR(255) DEFAULT NULL,
  `comuna`            VARCHAR(255) DEFAULT NULL,
  `fecha_cierre`      DATETIME DEFAULT NULL,

  -- Timestamps de trazabilidad
  `creado_en`         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `guid` (`guid`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;
