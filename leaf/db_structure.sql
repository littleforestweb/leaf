-- leaf.account definition

CREATE TABLE IF NOT EXISTS `account` (
  `id` int NOT NULL AUTO_INCREMENT,
  `logo` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `theme` int DEFAULT NULL,
  `version` int DEFAULT NULL,
  `active` int DEFAULT '1',
  `is_super` int DEFAULT '0',
  `created` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.asset_type definition

CREATE TABLE IF NOT EXISTS `asset_type` (
  `asset_type_id` int NOT NULL AUTO_INCREMENT,
  `asset_type_name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `asset_table` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `asset_table_column` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`asset_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.deployments definition

CREATE TABLE IF NOT EXISTS `deployments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `deployment_number` int NOT NULL DEFAULT '0',
  `deployment_user` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `user_email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `deployment_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `submitted_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `submitted_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `source_server_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'localhost',
  `source_server_ip` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '127.0.0.1',
  `source_files` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `source_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `destination_username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'rsync_user',
  `destination_server_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `destination_server_ip` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `destination_location` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `transfer_method` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'rsync',
  `completed_datetime` datetime DEFAULT NULL,
  `completed_timestamp` timestamp NULL DEFAULT NULL,
  `status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'pending',
  `deployment_log` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `accountId` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.lists definition

CREATE TABLE IF NOT EXISTS `lists` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reference` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `accountId` int DEFAULT NULL,
  `user_with_access` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.menus definition

CREATE TABLE IF NOT EXISTS `menus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reference` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `accountId` int DEFAULT NULL,
  `user_with_access` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.sites definition

CREATE TABLE IF NOT EXISTS `sites` (
  `id` int NOT NULL AUTO_INCREMENT,
  `base_url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `base_folder` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `submitted_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `accountId` int DEFAULT NULL,
  `site_ignore_robots` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `site_max_urls` int DEFAULT NULL,
  `userId` int NOT NULL,
  `gen_screenshots` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.workflow definition

CREATE TABLE IF NOT EXISTS `workflow` (
  `id` int NOT NULL AUTO_INCREMENT,
  `startUser` int DEFAULT NULL,
  `assignEditor` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dueDate` datetime DEFAULT NULL,
  `tags` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `comments` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `submittedDate` datetime DEFAULT NULL,
  `siteIds` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `status` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `accountId` int DEFAULT NULL,
  `listName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `attachments` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `priority` int DEFAULT '1',
  `type` int DEFAULT '1',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `lastEdited` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.site_assets definition

CREATE TABLE IF NOT EXISTS `site_assets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `site_id` int NOT NULL,
  `path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `filename` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `status` int NOT NULL,
  `mimeType` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `site_assets_FK` (`site_id`),
  CONSTRAINT `site_assets_FK` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.site_meta definition

CREATE TABLE IF NOT EXISTS `site_meta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `site_id` int DEFAULT NULL,
  `url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `status` int DEFAULT NULL,
  `title` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `mimeType` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `HTMLpath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `screenshotPath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `modified_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `add_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_site_id` (`site_id`),
  CONSTRAINT `FK_site_id` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.`user` definition

CREATE TABLE IF NOT EXISTS `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `account_id` int NOT NULL DEFAULT '0',
  `is_admin` int NOT NULL DEFAULT '0',
  `is_manager` int NOT NULL DEFAULT '0',
  `created` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  KEY `fk_user_account1_idx` (`account_id`),
  CONSTRAINT `fk_user_account1` FOREIGN KEY (`account_id`) REFERENCES `account` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.user_groups definition

CREATE TABLE IF NOT EXISTS `user_groups` (
  `group_id` int NOT NULL AUTO_INCREMENT,
  `group_name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `created_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `modified_by` int NOT NULL,
  `account_id` int NOT NULL,
  `created_by` int NOT NULL,
  PRIMARY KEY (`group_id`),
  KEY `account_id_FK` (`account_id`),
  KEY `modified_by_FK` (`modified_by`),
  KEY `created_by_FK` (`created_by`),
  CONSTRAINT `account_id_FK` FOREIGN KEY (`account_id`) REFERENCES `account` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `created_by_FK` FOREIGN KEY (`created_by`) REFERENCES `user` (`id`),
  CONSTRAINT `modified_by_FK` FOREIGN KEY (`modified_by`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.user_image definition

CREATE TABLE IF NOT EXISTS `user_image` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `color` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `first_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `last_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_user_image_userId` (`user_id`),
  CONSTRAINT `fk_user_image_userId` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.group_member definition

CREATE TABLE IF NOT EXISTS `group_member` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `user_id` int NOT NULL,
  `joined_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_group_user` (`group_id`,`user_id`),
  KEY `user_FK` (`user_id`),
  CONSTRAINT `group_id_FK` FOREIGN KEY (`group_id`) REFERENCES `user_groups` (`group_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `user_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- leaf.user_access definition

CREATE TABLE IF NOT EXISTS `user_access` (
  `access_id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `asset_type_id` int NOT NULL,
  `asset_id` int DEFAULT NULL,
  `folder_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `permission_level` int NOT NULL,
  PRIMARY KEY (`access_id`),
  KEY `asset_type_id_FK` (`asset_type_id`),
  KEY `groupewe_FK` (`group_id`),
  CONSTRAINT `asset_type_id_FK` FOREIGN KEY (`asset_type_id`) REFERENCES `asset_type` (`asset_type_id`),
  CONSTRAINT `group_FK` FOREIGN KEY (`group_id`) REFERENCES `user_groups` (`group_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;