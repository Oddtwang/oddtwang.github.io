-- MySQL dump 10.13  Distrib 5.7.40, for Linux (x86_64)
--
-- Host: mysql.idioms.harishtayyarmadabushi.com    Database: idioms_harish
-- ------------------------------------------------------
-- Server version	8.0.29-0ubuntu0.20.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `allocations`
--

DROP TABLE IF EXISTS `allocations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `allocations` (
  `allocation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `idiom_id` int NOT NULL,
  PRIMARY KEY (`allocation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `allocations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `allocations_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=660 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `allocations_p2`
--

DROP TABLE IF EXISTS `allocations_p2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `allocations_p2` (
  `allocation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `idiom_id` int NOT NULL,
  PRIMARY KEY (`allocation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `allocations_p2_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `allocations_p2_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1916 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `allocations_p3`
--

DROP TABLE IF EXISTS `allocations_p3`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `allocations_p3` (
  `allocation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `idiom_id` int NOT NULL,
  PRIMARY KEY (`allocation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `allocations_p3_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `allocations_p3_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1010 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `allocations_p4`
--

DROP TABLE IF EXISTS `allocations_p4`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `allocations_p4` (
  `allocation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `idiom_id` int NOT NULL,
  PRIMARY KEY (`allocation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `allocations_p4_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `allocations_p4_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=832 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `annotations`
--

DROP TABLE IF EXISTS `annotations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `annotations` (
  `annotation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `idiom_id` int NOT NULL,
  `data` text NOT NULL,
  PRIMARY KEY (`annotation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `annotations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `annotations_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=527 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `annotations_p2`
--

DROP TABLE IF EXISTS `annotations_p2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `annotations_p2` (
  `annotation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `idiom_id` int NOT NULL,
  `data` text NOT NULL,
  PRIMARY KEY (`annotation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `annotations_p2_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `annotations_p2_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=851 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `annotations_p3`
--

DROP TABLE IF EXISTS `annotations_p3`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `annotations_p3` (
  `annotation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `idiom_id` int NOT NULL,
  `data` text NOT NULL,
  PRIMARY KEY (`annotation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `annotations_p3_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `annotations_p3_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=505 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `annotations_p4`
--

DROP TABLE IF EXISTS `annotations_p4`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `annotations_p4` (
  `annotation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `idiom_id` int NOT NULL,
  `data` text NOT NULL,
  PRIMARY KEY (`annotation_id`),
  KEY `user_id` (`user_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `annotations_p4_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `annotations_p4_ibfk_2` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `idioms`
--

DROP TABLE IF EXISTS `idioms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `idioms` (
  `idiom_id` int NOT NULL AUTO_INCREMENT,
  `idiom` varchar(100) NOT NULL,
  `language` varchar(5) NOT NULL,
  PRIMARY KEY (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=563 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `meanings`
--

DROP TABLE IF EXISTS `meanings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meanings` (
  `meaning_id` int NOT NULL AUTO_INCREMENT,
  `idiom_id` int NOT NULL,
  `meaning` varchar(100) NOT NULL,
  PRIMARY KEY (`meaning_id`),
  KEY `idiom_id` (`idiom_id`),
  CONSTRAINT `meanings_ibfk_1` FOREIGN KEY (`idiom_id`) REFERENCES `idioms` (`idiom_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2792 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-10-30 16:12:34
