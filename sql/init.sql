-- ============================================================
-- Parking System - Database Initialization
-- Version: v2.0
-- Date: 2026-06-27
-- ============================================================

CREATE DATABASE IF NOT EXISTS `parking_system`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `parking_system`;

-- ============================================================
-- 1. Users
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
    `id`                INT             NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `username`          VARCHAR(50)     NOT NULL                 COMMENT '用户名',
    `password_hash`     VARCHAR(255)    NOT NULL                 COMMENT 'bcrypt哈希密码',
    `role`              VARCHAR(20)     NOT NULL DEFAULT 'user'  COMMENT '角色：admin/user',
    `phone`             VARCHAR(20)     DEFAULT NULL             COMMENT '手机号',
    `membership_expire` DATETIME        DEFAULT NULL             COMMENT '会员到期时间',
    `wallet_balance`    DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '钱包余额',
    `is_active`         TINYINT(1)      NOT NULL DEFAULT 1       COMMENT '是否启用',
    `created_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 2. Parking Record
-- ============================================================
CREATE TABLE IF NOT EXISTS `parking_record` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `plate_number`  VARCHAR(20)     NOT NULL                 COMMENT '车牌号',
    `plate_image`   VARCHAR(500)    DEFAULT NULL             COMMENT '入场车牌图片路径',
    `entry_time`    DATETIME        NOT NULL                 COMMENT '入场时间',
    `exit_time`     DATETIME        DEFAULT NULL             COMMENT '出场时间',
    `status`        ENUM('parking','paid','exited') NOT NULL DEFAULT 'parking' COMMENT '状态',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_plate_number` (`plate_number`),
    INDEX `idx_status` (`status`),
    INDEX `idx_entry_time` (`entry_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='停车记录表';

-- ============================================================
-- 3. Payment Record
-- ============================================================
CREATE TABLE IF NOT EXISTS `payment_record` (
    `id`                 INT             NOT NULL AUTO_INCREMENT,
    `parking_record_id`  INT             NOT NULL                 COMMENT '关联停车记录ID',
    `plate_number`       VARCHAR(20)     NOT NULL                 COMMENT '车牌号（冗余）',
    `amount`             DECIMAL(10,2)   NOT NULL                 COMMENT '缴费金额',
    `park_hours`         INT             NOT NULL                 COMMENT '计费小时数',
    `status`             ENUM('valid','expired') NOT NULL DEFAULT 'valid' COMMENT '状态',
    `pay_time`           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '缴费时间',
    PRIMARY KEY (`id`),
    INDEX `idx_parking_record_id` (`parking_record_id`),
    INDEX `idx_plate_number` (`plate_number`),
    INDEX `idx_pay_time` (`pay_time`),
    CONSTRAINT `fk_payment_parking`
        FOREIGN KEY (`parking_record_id`) REFERENCES `parking_record` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='缴费记录表';

-- ============================================================
-- 4. User Cars
-- ============================================================
CREATE TABLE IF NOT EXISTS `user_cars` (
    `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `user_id`       INT             NOT NULL                 COMMENT '用户ID',
    `plate_number`  VARCHAR(20)     NOT NULL                 COMMENT '车牌号',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_plate_number` (`plate_number`),
    CONSTRAINT `fk_user_cars_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户车辆绑定';

-- ============================================================
-- 5. Wallet Transaction
-- ============================================================
CREATE TABLE IF NOT EXISTS `wallet_transaction` (
    `id`             INT             NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `user_id`        INT             NOT NULL                 COMMENT '用户ID',
    `type`           VARCHAR(20)     NOT NULL                 COMMENT '交易类型：recharge/payment',
    `amount`         DECIMAL(10,2)   NOT NULL                 COMMENT '金额（充值正/消费负）',
    `balance_after`  DECIMAL(10,2)   NOT NULL                 COMMENT '交易后余额',
    `related_id`     INT             DEFAULT NULL             COMMENT '关联记录ID',
    `created_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '交易时间',
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`),
    CONSTRAINT `fk_wallet_tx_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='钱包交易流水';

-- ============================================================
-- 6. Blacklist
-- ============================================================
CREATE TABLE IF NOT EXISTS `blacklist` (
    `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '主键',
    `plate_number`  VARCHAR(20)     NOT NULL                 COMMENT '车牌号',
    `reason`        VARCHAR(255)    NOT NULL                 COMMENT '拉黑原因',
    `black_type`    VARCHAR(20)     NOT NULL DEFAULT 'permanent' COMMENT '类型：permanent/temporary',
    `expire_at`     DATETIME        DEFAULT NULL             COMMENT '限时到期时间',
    `status`        VARCHAR(20)     NOT NULL DEFAULT 'active' COMMENT '状态：active/removed',
    `created_by`    INT             NOT NULL                 COMMENT '操作管理员ID',
    `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    INDEX `idx_plate_number` (`plate_number`),
    INDEX `idx_status` (`status`),
    CONSTRAINT `fk_blacklist_user` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='黑名单表';

-- ============================================================
-- Default Data
-- ============================================================
-- Default admin account (password: admin123)
INSERT IGNORE INTO `users` (`username`, `password_hash`, `role`, `wallet_balance`) VALUES
    ('admin', '$2b$12$LJ3m4ys3LkBCVxJGqOjpHuP9Y0T5mMOTmNWZNvJkKZMqOBvRFZPzK', 'admin', 200.00);

-- Default test user (password: test123)
INSERT IGNORE INTO `users` (`username`, `password_hash`, `role`, `wallet_balance`) VALUES
    ('user001', '$2b$12$LJ3m4ys3LkBCVxJGqOjpHuP9Y0T5mMOTmNWZNvJkKZMqOBvRFZPzK', 'user', 100.00);
