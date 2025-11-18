-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1:3306
-- Tiempo de generación: 15-11-2025 a las 15:59:07
-- Versión del servidor: 8.3.0
-- Versión de PHP: 8.2.18

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `bot_empleos`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `concursos`
--

DROP TABLE IF EXISTS `concursos`;
CREATE TABLE IF NOT EXISTS `concursos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `guid` varchar(255) NOT NULL,
  `titulo` varchar(500) NOT NULL,
  `link` varchar(500) NOT NULL,
  `fecha_publicacion` datetime DEFAULT NULL,
  `ministerio` varchar(255) DEFAULT NULL,
  `comuna` varchar(255) DEFAULT NULL,
  `fecha_cierre` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL,
  `actualizado_en` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `guid` (`guid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
