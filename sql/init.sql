-- MySQL初始化脚本
-- 创建各微服务数据库

-- 创建订单服务数据库
CREATE DATABASE IF NOT EXISTS cfmp_order CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建支付服务数据库
CREATE DATABASE IF NOT EXISTS cfmp_payment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建通知服务数据库
CREATE DATABASE IF NOT EXISTS cfmp_notification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 为各服务创建用户并授权（可选，也可以直接使用root）
-- 为了简化，我们直接使用root用户

-- 显示创建的数据库
SHOW DATABASES;
