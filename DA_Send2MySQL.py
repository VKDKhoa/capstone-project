import mysql.connector
from datetime import datetime

class DA_Send2MySQL:
#create connection to mysql
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='1234',
                database='db_qrproduct',
                charset='utf8mb4'
                )
            self.cursor = self.conn.cursor(buffered=True)
            self.isConnect = self.conn.is_connected()
            if self.isConnect:
                print("Connected to MySQL success")
        except mysql.connector.Error as e:
            print("Fail to Connect MySQL DB due to",e)
            self.conn = None
            self.cursor = None
            self.isConnect = False

    def getStatusConnection(self) -> bool:
        return self.isConnect
    
    #check if the data is already exist in the database qrnotsorted
    def checkDataExist(self,data: str) -> bool:
            # Clean input data
        data = str(data).strip().upper()
        print(f"[DEBUG] Cleaned data to check: '{data}' (length: {len(data)})")
    
        try:
            # Use TRIM and UPPER for comparison to handle whitespace and case issues
            query = "SELECT 1 FROM qrnotsorted WHERE TRIM(UPPER(id)) = %s LIMIT 1"
            self.cursor.execute(query, (data,))
            result = self.cursor.fetchone()
        
            found = result is not None
            print(f"[DEBUG] Query result: {found}")
        
            if not found:
                # Additional debug: show similar IDs
                debug_query = "SELECT id FROM qrnotsorted WHERE id LIKE %s LIMIT 5"
                self.cursor.execute(debug_query, (f"%{data[:2]}%",))
                similar_ids = self.cursor.fetchall()
                print(f"[DEBUG] Similar IDs found: {[row[0] for row in similar_ids]}")
        
            return found
        
        except Exception as e:
            print(f"[ERROR] Database query failed: {e}")
            return False
        #self.cursor.execute(query, (data,))
        #result = self.cursor.fetchone()
        #return result is not None #true if data is exist, false if data is not exist
    
    # Show the data in the table qrissorted
    def showTableQRisSorted(self):
        query = """
                    SELECT id_sorted, type_product_sorted, product_name_sorted, NSX_sorted, sortedTime, product_status 
                    FROM qrissorted 
                    ORDER BY sortedTime DESC"""
        self.cursor.execute(query) # Execute the query
        results = self.cursor.fetchall() #save the result of query to results as a list of tuples
        return results #return the result of query
    
    #Show data in the table qrnotsorted
    def showTableQRnotSorted(self):
        query = """
                    SELECT id, type_product, product_name, NSX, is_sorted
                    FROM qrnotsorted """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return results #return the result of query
    
    # Show number of products
    def showNumberOfProducts(self):
        """ Number of product on GUI in PyQT5 """
        query = """
                    SELECT numSB, numST, numSF, numER, total_number_of_products 
                    FROM number_of_products """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return results #return the result of query
        
    #send data to mysql server
    #data is a tuple with 4 elements: id_sorted, type_product_sorted, product_name_sorted, NSX_sorted, sortedTime
    def handleWithDamagedData(self) -> None:
        self.cursor.callproc("insert_damaged_product")
        self.conn.commit()

    def handleWithNoData(self,data) -> None:
        """ Process when data not found in data base """
        try:
            self.cursor.callproc("insert_Nobody_product",[data])
            self.conn.commit()
            print(f"[MySQL] Saved '{data}' to qrnodata")
        except mysql.connector.Error as e:
            print("[MySQL] Error in handleWithNoData:", e)

    def sendData2mysql(self,data) -> None:
        """ Send data QR to MySQL database"""
        print(f"[DEBUG] === sendData2mysql called with: '{data}' ===")
    
        try:
            # Clean input data - same as checkDataExist
            clean_data = str(data).strip().upper()
            print(f"[DEBUG] Cleaned data: '{clean_data}'")
        
            # Select information from qrnotsorted where id == data
            # Use TRIM and UPPER for consistency with checkDataExist
            query_check = """
            SELECT id, type_product, product_name, NSX
            FROM qrnotsorted
            WHERE TRIM(UPPER(id)) = %s
            """
            print(f"[DEBUG] Executing query: {query_check}")
            print(f"[DEBUG] Query parameter: '{clean_data}'")
        
            self.cursor.execute(query_check, (clean_data,))
            result = self.cursor.fetchone()
        
            print(f"[DEBUG] Query result: {result}")
        
            if not result:
                print(f"[ERROR] ID {data} not found in qrnotsorted after cleaning.")
                self.handleWithNoData(data)  
                return
        
            print(f"[SUCCESS] Found data in qrnotsorted: {result}")
        
            # Add time data was added into qrissorted
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            handleData = result + (timestamp,)
        
            print(f"[DEBUG] Data to insert: {handleData}")
        
            # add inform mapping from qrnotsorted to qrissorted
            column = "(id_sorted, type_product_sorted, product_name_sorted, NSX_sorted, sortedTime)"
            query_insert = f"INSERT IGNORE INTO qrissorted {column} VALUES (%s, %s, %s, %s, %s)"
        
            print(f"[DEBUG] Insert query: {query_insert}")
        
            self.cursor.execute(query_insert, handleData)
            self.conn.commit()
            print("[SUCCESS] Data inserted successfully into qrissorted")
        
        except mysql.connector.Error as e:
            print(f"[ERROR] MySQL Error in sendData2mysql: {e}")
        except Exception as e:
            print(f"[ERROR] General Error in sendData2mysql: {e}")
    
        print(f"[DEBUG] === sendData2mysql finished ===")
    
    def resetDB(self) -> None:
        self.cursor.callproc("resetDB")
        self.conn.commit()
    #reset the database to initial state
    
    def closeConnection(self) -> None:
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def main():
    #test the connection
    MySQLconn = DA_Send2MySQL()
    if MySQLconn.getStatusConnection():
        print("Connection is established")
    else:
        print("Connection is not established")
    MySQLconn.closeConnection()
if __name__ == '__main__':
    main()
