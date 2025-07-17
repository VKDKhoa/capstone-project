from DA_SendSignalToPLC import DA_SendSignal2PLC
from DA_Send2MySQL import DA_Send2MySQL
import time

def create_mysql_connection():
    return DA_Send2MySQL()

def create_plc_connection():
    return DA_SendSignal2PLC()
    
if __name__ == "__main__":
    plc = create_plc_connection()
    if plc.isConnected:
        print ("Connect 2 PLC success")
    else:
        print("false to connect")
    time.sleep(2)
    try:
        plc.closeConnection()
        print("close connect to PLC")
    except:
        print("could not be close")
    
