USE db_qrproduct;


INSERT IGNORE INTO qrnotsorted(id, type_product, product_name, NSX, is_sorted)
VALUES 
('SB66017', 'SB', 'Optimum Gold', 'Vinamilk', 'NO'),
('ST14479', 'ST', 'TH True Milk', 'TH True Milk', 'NO'),
('SF85747', 'SF', 'Dutch Lady', 'FrieslandCampina', 'NO'),
('SF30841', 'SF', 'Friso Gold', 'Friso', 'NO'),
('ST30477','ST','Vinamilk Sure Prevent','Vinamilk', 'NO'),
('SB84213', 'SB', 'Nutrilon', 'Nutrica', 'NO'),
('SF12948', 'SF', 'Nestle Milo', 'Nestle', 'NO'),
('ST47381', 'ST', 'Fami Dau Nanh', 'Vinamilk', 'NO'),
('ST59420', 'ST', 'Co gai Ha Lan', 'Dutch Lady', 'NO'),
('SB78325', 'SB', 'Ensure Gold', 'Abbott', 'NO');

insert into number_of_products(numSB, numST, numSF, numER, total_number_of_products)
values (0, 0, 0, 0, 0);

SELECT * FROM qrnotsorted;

SELECT * FROM qrissorted;
DELETE FROM qrissorted;

DELETE FROM error_id_counter;
ALTER TABLE error_id_counter AUTO_INCREMENT = 1;

UPDATE qrnotsorted
SET is_sorted = 'NO'
WHERE is_sorted = 'YES';

-- START TRIGGER trg_update_sorted_status
insert into number_of_products(numSB, numST, numSF, numER, total_number_of_products)
values (0, 0, 0, 0, 0);
-- END TRIGGER trg_update_sorted_status

-- START TRIGGER trg_update_number_of_products
DELIMITER $$
CREATE TRIGGER trg_update_number_of_products
AFTER INSERT ON qrissorted
FOR EACH ROW
BEGIN
    IF NEW.type_product_sorted = 'SB' THEN
        UPDATE number_of_products
        SET numSB = numSB + 1,
            total_number_of_products = total_number_of_products + 1;
    ELSEIF NEW.type_product_sorted = 'ST' THEN
        UPDATE number_of_products
        SET numST = numST + 1,
            total_number_of_products = total_number_of_products + 1;
    ELSEIF NEW.type_product_sorted = 'SF' THEN
        UPDATE number_of_products
        SET numSF = numSF + 1,
            total_number_of_products = total_number_of_products + 1;
    ELSEIF NEW.type_product_sorted = 'ER' THEN
        UPDATE number_of_products
        SET numER = numER + 1,
            total_number_of_products = total_number_of_products + 1;
    END IF;
END$$
DELIMITER ;
-- END TRIGGER trg_update_number_of_products

-- START STORE PRODUCE insert_damaged_product
DELIMITER $$
CREATE PROCEDURE insert_damaged_product()
BEGIN -- Start of the procedure

    -- increase the counter to create a new ID
    INSERT INTO error_id_counter VALUES (NULL);
    
    -- Lấy giá trị counter vừa tạo
    SET @cnt := LAST_INSERT_ID(); -- LAST_INSERT_ID() is a MySQL function that returns the last inserted ID
    
    -- create a new ID formatted as 'ER00001'
    SET @new_id := CONCAT('ER', LPAD(@cnt, 5, '0'));

    -- Thêm vào bảng QRissorted
    INSERT INTO qrissorted (
        id_sorted, 
        type_product_sorted, 
        product_name_sorted, 
        NSX_sorted,
        sortedTime,
        product_status
    )
    VALUES (
        @new_id,
        'ER',
        'Unknown',
        'Unknown',
        NOW(),
        'DAMAGED'
    );
END$$ 
-- End of the procedure
DELIMITER ; 
-- return to the default delimiter ;
-- END STORE PRODUCE insert_damaged_product

--START STORE PROCEDURE resetDB
DELIMITER $$
CREATE PROCEDURE resetDB ()
begin
    DELETE FROM error_id_counter;
    ALTER TABLE error_id_counter AUTO_INCREMENT = 1;
    
    delete from qrissorted;
    
    UPDATE qrnotsorted
    SET is_sorted = 'NO'
    WHERE is_sorted = 'YES';

    UPDATE number_of_products
    SET numSB = 0,
        numST = 0,
        numSF = 0,
        numER = 0,
        total_number_of_products = 0;
    -- Reset the auto-increment value of the number_of_products table
end $$
DELIMITER ;
--END STORED PROCEDURE resetDB

--START STORE PROCEDURE showall
DELIMITER $$
CREATE PROCEDURE showall()
begin
    select * from qrissorted;
    select * from qrnotsorted;
end $$
DELIMITER ;
--END STORED PROCEDURE showall

-- START STORE PRODUCE insert_nobody_product
DELIMITER $$
CREATE PROCEDURE insert_nobody_product(IN product_name_sorted VARCHAR(255))
BEGIN -- Start of the procedure

    -- increase the counter to create a new ID
    INSERT INTO error_id_counter VALUES (NULL);
    
    -- Lấy giá trị counter vừa tạo
    SET @cnt := LAST_INSERT_ID(); -- LAST_INSERT_ID() is a MySQL function that returns the last inserted ID
    
    -- create a new ID formatted as 'ER00001'
    SET @new_id := CONCAT('ER', LPAD(@cnt, 5, '0'));

    -- Thêm vào bảng QRissorted
    INSERT INTO qrissorted (
        id_sorted, 
        type_product_sorted, 
        product_name_sorted, 
        NSX_sorted,
        sortedTime,
        product_status
    )
    VALUES (
        @new_id,
        'ER',
        product_name_sorted,
        'Unknown',
        NOW(),
        'NO DATA'
    );
END$$ -- End of the procedure
DELIMITER ; 
-- return to the default delimiter ;
-- END STORE PRODUCE insert_damaged_product

