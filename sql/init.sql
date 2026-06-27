-- ============================================================
-- Parking System - Database Initialization
-- Version: v1.0
-- Date: 2026-06-24
-- ============================================================

CREATE DATABASE IF NOT EXISTS `parking_system`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `parking_system`;

-- Parking Record Table
CREATE TABLE IF NOT EXISTS `parking_record` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `plate_number`  VARCHAR(20)     NOT NULL,
    `plate_image`   VARCHAR(500)    NULL,
    `entry_time`    DATETIME        NOT NULL,
    `exit_time`     DATETIME        NULL,
    `status`        ENUM('parking','paid','exited') NOT NULL DEFAULT 'parking',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_plate_number` (`plate_number`),
    INDEX `idx_status` (`status`),
    INDEX `idx_entry_time` (`entry_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payment Record Table
CREATE TABLE IF NOT EXISTS `payment_record` (
    `id`                 INT             NOT NULL AUTO_INCREMENT,
    `parking_record_id`  INT             NOT NULL,
    `plate_number`       VARCHAR(20)     NOT NULL,
    `amount`             DECIMAL(10,2)   NOT NULL,
    `park_hours`         INT             NOT NULL,
    `status`             ENUM('valid','expired') NOT NULL DEFAULT 'valid',
    `pay_time`           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_parking_record_id` (`parking_record_id`),
    INDEX `idx_plate_number` (`plate_number`),
    INDEX `idx_pay_time` (`pay_time`),
    CONSTRAINT `fk_payment_parking`
        FOREIGN KEY (`parking_record_id`) REFERENCES `parking_record` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
