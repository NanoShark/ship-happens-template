-- Active: 1743506400227@@127.0.0.1@3306
-- Create user database
CREATE DATABASE IF NOT EXISTS users_db;
USE users_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Insert sample data
INSERT INTO users (name, email) VALUES 
('John Doe', 'john@example.com'),
('Jane Smith', 'jane@example.com');

-- Create auth database
CREATE DATABASE IF NOT EXISTS auth_db;
USE auth_db;

CREATE TABLE IF NOT EXISTS auth (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL
);