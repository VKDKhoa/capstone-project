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
                database='db_qrproduct'
                )
            self.cursor = self.conn.cursor()
            self.isConnect = self.conn.is_connected()
            print("Connected to MySQL")
        except mysql.connector.Error as e:
            print("Fail to Connect MySQL DB due to",e)
            self.isConnect = False

    def getStatusConnection(self) -> bool:
        return self.isConnect
    
    #check if the data is already exist in the database qrnotsorted
    def checkDataExist(self,data: str) -> bool:
        print("Data to check: ",data)
        query = "SELECT 1 FROM qrnotsorted WHERE id = %s" #query to check if the data is exist
        self.cursor.execute(query, (data,))
        result = self.cursor.fetchone()
        return result is not None #true if data is exist, false if data is not exist
    
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
        self.cursor.callproc("insert_Nobody_product",[data])
        self.conn.commit()

    def sendData2mysql(self,data) -> None:
        def splitData(data:str) -> tuple:
            if '-' not in data:
                return (data,)
            return tuple(data.split('-'))
    
        handleData = splitData(data) #convert to tuple for add to db

        #take current time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        handleData = handleData + (timestamp,)
    
        column = "(id_sorted, type_product_sorted, product_name_sorted, NSX_sorted, sortedTime)"
        query = f"INSERT IGNORE INTO qrissorted {column} VALUES (%s, %s, %s, %s, %s)"
    #insert data to db    
        try:
            self.cursor.execute(query,handleData)
            self.conn.commit()
            print("Data inserted successfully")
        except mysql.connector.Error as e: #catch the error
            print(e)
        finally:
            data = ''
    
    def resetDB(self) -> None:
        self.cursor.callproc("resetDB")
        self.conn.commit()
    #reset the database to initial state
    
    def closeConnection(self) -> None:
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
