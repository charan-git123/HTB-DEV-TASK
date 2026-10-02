-- Run this as a MySQL administrator, then configure an application user.
CREATE DATABASE IF NOT EXISTS netflix_clone
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE netflix_clone;

CREATE TABLE IF NOT EXISTS users (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(80) NOT NULL,
 email VARCHAR(254) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 created_at BIGINT NOT NULL
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS login_sessions (
 token_hash VARCHAR(64) PRIMARY KEY,
 user_id INT NOT NULL,
 expires_at BIGINT NOT NULL,
 INDEX ix_login_sessions_user_id (user_id),
 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS watchlist (
 user_id INT NOT NULL,
 movie_id INT NOT NULL,
 watched BOOLEAN NOT NULL DEFAULT FALSE,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (user_id, movie_id),
 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS auth_attempts (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 bucket VARCHAR(64) NOT NULL,
 created_at BIGINT NOT NULL,
 INDEX ix_auth_attempts_bucket (bucket),
 INDEX ix_auth_attempts_created_at (created_at)
) ENGINE=InnoDB;
