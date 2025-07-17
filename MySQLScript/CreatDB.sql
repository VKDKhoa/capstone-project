DROP DATABASE IF EXISTS db_qrproduct;

CREATE DATABASE db_qrproduct
	CHARACTER SET 'utf8mb4'
	COLLATE 'utf8mb4_general_ci';

USE db_qrproduct;

CREATE TABLE qrnotsorted(
 id CHAR(7) PRIMARY KEY,
 type_product CHAR(2),
 product_name VARCHAR(255),
 NSX VARCHAR(20),
 is_sorted CHAR(3) DEFAULT 'NO'
);

CREATE TABLE qrissorted(
 id_sorted CHAR(7) PRIMARY KEY,
 type_product_sorted CHAR(2),
 product_name_sorted VARCHAR(255),
 NSX_sorted VARCHAR(20),
 sortedTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 product_status VARCHAR(20) DEFAULT 'OK'
);

CREATE TABLE IF NOT EXISTS error_id_counter (
    counter INT PRIMARY KEY AUTO_INCREMENT
);

CREATE TABLE IF NOT EXISTS number_of_products (
	numSB INT DEFAULT 0,
	numST INT DEFAULT 0,
	numSF INT DEFAULT 0,
	numER INT DEFAULT 0,
	total_number_of_products INT DEFAULT 0
);
