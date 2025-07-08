
DROP TABLE IF EXISTS `article_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `article_info` (
                                `account_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
                                `account_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
                                `review_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
                                `type` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
                                `title` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
                                `avatar` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
                                `time` int DEFAULT NULL,
                                `pic_url` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
                                `doc_url` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
                                `author` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
                                `read_status` tinyint(1) unsigned zerofill DEFAULT NULL,
                                `favorite` tinyint(1) unsigned zerofill DEFAULT NULL,
                                KEY `title_index` (`title`(10)) USING BTREE,
                                KEY `review_index` (`review_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
/*!40101 SET character_set_client = @saved_cs_client */;


DROP TABLE IF EXISTS `crawl_time`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crawl_time` (
                              `account_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
                              `account_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
                              `crawl_time` int(10) unsigned zerofill DEFAULT '0000000000'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
