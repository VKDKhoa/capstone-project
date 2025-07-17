use db_qrproduct;
-- TRIGGER FOR UPDATE PRODUCT STATUS
DELIMITER $$
CREATE TRIGGER trg_update_sorted_status -- Trigger name is trg-update-sorted-status
AFTER INSERT ON qrissorted -- Trigger is activated after inserting a new row into the QRissorted table
FOR EACH ROW -- Trigger is activated for each row
BEGIN
IF EXISTS 
( SELECT 1 FROM qrnotsorted WHERE id = NEW.id_sorted) -- Check if the id_sorted exists in the qrnotsorted table) 
	THEN
        UPDATE qrnotsorted 
        SET is_sorted = 'YES'
        WHERE id = NEW.id_sorted;
	END IF;
END$$
DELIMITER ;
