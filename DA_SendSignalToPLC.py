from pymodbus.client import ModbusSerialClient # run modbus version > 3.0.0
import threading

class DA_SendSignal2PLC:
    def __init__(self):
        try:
            self.client = ModbusSerialClient(
                port="/dev/ttyUSB0", #COM4,/dev/ttyUSB0
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1 )
            if self.client.connect():
                print("Connect to PLC board success")
        except Exception as e:
            print("Fail to connect to PLC due to",e)
        finally:
            self.isConnected:bool = self.client.connect()
    
    def SendToPLC(self,data) -> None:
        if self.isConnected:
            signalSend = None
            print("Connect Success")
            print(data)
        #Write the signal to the M3 M4 M5 of PLC
            if data =='SuaBot':
                signalSend = self.client.write_coil(3,True,slave=1) # Write the signal to the PLC, 3 is M3 in the PLC, True mean turn M3 on
                if not signalSend.isError():
                    print("Send to PLC success")
                    threading.Timer(0.2, lambda: self.client.write_coil(3, False, slave=1)).start()
                    data = ''
            elif data =='SuaTuoi':
                signalSend = self.client.write_coil(4,True,slave=1) # Write the signal to the PLC, 4 is M4 in the PLC, True mean turn M4 on
                if not signalSend.isError():
                    print("Send to PLC success")
                    threading.Timer(0.2, lambda: self.client.write_coil(4, False, slave=1)).start()
                    data = ''
            elif data =='SuaTraiCay':   
                signalSend = self.client.write_coil(5,True,slave=1) # Write the signal to the PLC, 5 is M5 in the PLC, True mean turn M5 on
                if not signalSend.isError():
                    signalSend = self.client.write_coil(5,False,slave=1)
                    threading.Timer(0.2, lambda: self.client.write_coil(5, False, slave=1)).start()
                    data = ''
            else:
                signalSend = self.client.write_coil(6,True,slave=1) # Write the signal to the PLC if no data correct, 6 is M6 in the PLC, True mean turn M5 on
                if not signalSend.isError():
                    signalSend = self.client.write_coil(6,False,slave=1)
                    threading.Timer(0.2, lambda: self.client.write_coil(6, False, slave=1)).start()
                    data = ''
        else:
            print("Fail to connect to PLC")
            return
    def closeConnection(self) -> None:
        self.client.close()

def main():
    #test the connection
    PLCconn = DA_SendSignal2PLC()
    if PLCconn.isConnected:
        print("Connection is established")
    else:
        print("Connection is not established")
    PLCconn.closeConnection()
if __name__ == '__main__':
    main()
