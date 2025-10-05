import cv2
import pyzbar.pyzbar as pyzbar
import re
import numpy as np

from DA_Send2MySQL import *
from DA_SendSignalToPLC import *

def show(nameWindow:str,img) -> None:
    cv2.imshow(nameWindow,img)
    key = cv2.waitKey(0)
    if key == 27:
        cv2.destroyAllWindows()
        return

class QRcodeRead:
    def __init__(self,frame: np.ndarray):
        self.frame: np.ndarray = frame
        self.data: str = ''
        self.gamma: float = 1.5
        self.angle: float = 0
        self.QR_info = []
        self.pattern = r"^(SB|ST|SF)\d{5}$" #pattern of data
    
    def Sharpen(self,img: np.ndarray) -> np.ndarray:
        blur = cv2.GaussianBlur(img, (3,3), 0)
        #matrix to sharpen
        sharp = np.array([[-1,-1,-1],
                        [-1,9,-1],
                        [-1,-1,-1]
                        ])
        #convolution to make img sharpen
        img = cv2.filter2D(blur,-1,sharp)
        return img
    
    def gamma_correction(self,img: np.ndarray) -> np.ndarray:
        inv_gamma = 1.0 / self.gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(img, table)
    
    def Rot(self,img: np.ndarray) -> np.ndarray :
        (h, w) = img.shape[:2]
        scale = 1.0  #
        center = (w // 2, h // 2)  # Center img
    
        M = cv2.getRotationMatrix2D(center, self.angle, scale)
        rotated_img = cv2.warpAffine(img, M, (w, h))
        return rotated_img

    def findAngle(self,img: np.ndarray) -> float:
        thresh = cv2.inRange(img,50,70) #pic 4 is best with 140
        kernel = np.ones((3,3), np.uint8)
        dialation = cv2.dilate(thresh, kernel, iterations=1)
        contours, _ = cv2.findContours(dialation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
        #cv.drawContours(img,contours,-1,(0,255,0),2)
        for cnt in contours:
            area = cv2.contourArea(cnt)
        
            if 800 < area < 1200 :
                #print(angle)
                rect = cv2.minAreaRect(cnt)
                #cv2.drawContours(img,[cnt],-1,(0,255,0),2)
                self.angle = rect[2]
            if 40 < self.angle < 50:
                return self.angle
        return self.angle
    
    def decodeQRdata(self,img: np.ndarray) -> str:
        #show('img will be decode',img)
        self.QR_info = pyzbar.decode(img)
        if not self.QR_info:
            return ''
        self.data = self.QR_info[0].data.decode("utf-8")
        x,y,w,h = self.QR_info[0].rect
        cv2.rectangle(self.frame,(x,y),(x+w+50,y+h+50),0,12) #drawing rectangle around QR
        return self.data 
    
    def CheckingAndSendData(self, data: str, MySQLconn: DA_Send2MySQL, PLCconn: DA_SendSignal2PLC) -> None:
        print(f"[DEBUG] === START CheckingAndSendData ===")
        print(f"[DEBUG] Input data: '{data}'")
    
        if len(data) <= 0:
            print(f"[DEBUG] Empty data, returning")
            return
        
        self.data = data.replace(" ", "")
        print(f"[DEBUG] Cleaned data: '{self.data}'")
    
        IDProduct: str = self.data[:7] if len(self.data) >= 7 else self.data
        print(f"[DEBUG] IDProduct: '{IDProduct}' (length: {len(IDProduct)})")
    
        if re.match(self.pattern, IDProduct):
            print(f"[DEBUG] Pattern MATCHED for: '{IDProduct}'")
        
            isExist = MySQLconn.checkDataExist(IDProduct)
            print(f"[DEBUG] checkDataExist() returned: {isExist} (type: {type(isExist)})")
        
            if not isExist:
                print(f"[ERROR] Data '{IDProduct}' NOT FOUND in database")
                MySQLconn.handleWithNoData(self.data)
                PLCconn.SendToPLC("No data in DB")
                return
            else:
                print(f"[SUCCESS] Data '{IDProduct}' FOUND in database")
            
        # Tiếp tục xử lý...
            MySQLconn.sendData2mysql(self.data)
            type_product = IDProduct[:2]
            productName: str = 'SuaBot' if type_product == 'SB' else ('SuaTuoi' if type_product == 'ST' else 'SuaTraiCay')
            print(f"[SUCCESS] Product: {productName}")
            PLCconn.SendToPLC(productName)
        else:
            print(f"[ERROR] Pattern NOT MATCHED for: '{IDProduct}'")
            PLCconn.SendToPLC("No data in DB")
        
    print(f"[DEBUG] === END CheckingAndSendData ===")

def improveIMG(QRobject: QRcodeRead,img: np.ndarray) -> np.ndarray:
    img = QRobject.gamma_correction(QRobject.frame) #improve contrast
    img = QRobject.Sharpen(img) #improve sharpen
    return img

def Tranform2Thresh(img: np.ndarray, thresh_Val:int, equal:bool) -> np.ndarray:
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) if(len(img.shape)) > 2 else img
    if equal:
        gray = cv2.equalizeHist(gray)
    _,thresh = cv2.threshold(gray,thresh_Val,255,cv2.THRESH_BINARY)
    return thresh

def ReadAndDecodeQR(frame: np.ndarray, MySQLconn: DA_Send2MySQL,PLCconn: DA_SendSignal2PLC) -> bool:
    # First attempt to decode the QR code
    QRobject = QRcodeRead(frame)
    #gray = cv2.cvtColor(QRobject.frame,cv2.COLOR_BGR2GRAY) if len(QRobject.frame.shape) > 2 else QRobject.frame
    #show('img in First attemp to decode',gray)
    #cv2.imshow("img for first attemp ",cv2.resize(gray,(300,300)))
    #data = QRobject.decodeQRdata(gray)
    
    #if len(data) > 0:  # Successfully detected QR code
    #   QRobject.CheckingAndSendData(data,MySQLconn, PLCconn) if MySQLconn is not None and PLCconn is not None else None
    #    #print("success at first attemp")
    #    print("QR code data:", data)
    #    return True
    #else: 
    #    print("first attemp false");      
    
    #Second Attemp, will imporve the contrast and make edge more sharpen for easier decode
    img = QRobject.frame
    img = cv2.cvtColor(QRobject.frame,cv2.COLOR_BGR2GRAY) if len(img.shape) > 2 else img
    data = QRobject.decodeQRdata(img)
    if len(data) > 0:  # Successfully detected QR code
        print(f"success at first attempt")
        QRobject.CheckingAndSendData(data,MySQLconn, PLCconn) if MySQLconn is not None and PLCconn is not None else None
        print("QR code data:", data)
        return True
    #img = improveIMG(QRobject,img)
    thresh_Val = np.array([30,35,40,45,50,55,60,70,80])
    for th in thresh_Val :
        thresh = Tranform2Thresh(img,th,False)
        #cv2.imshow(f"thresh val = {th} for second attemp ",cv2.resize(thresh,(300,300)))
        #show('img in Seccon attemp to decode',thresh)
        data = QRobject.decodeQRdata(thresh)
        if len(data) > 0:  # Successfully detected QR code
            print(f"success at second attempt at thresh val = {th}")
            QRobject.CheckingAndSendData(data,MySQLconn, PLCconn) if MySQLconn is not None and PLCconn is not None else None
            print("QR code data:", data)
            return True
    print("second attemp false"); 
    
    ## Final attempt to decode the QR code
    #QRobject.angle = QRobject.findAngle(img)
    #angle2Rot = QRobject.angle if 30 < QRobject.angle < 80 else (135 - QRobject.angle if 80 < QRobject.angle <= 90 else 0)
    #QRobject.angle = -angle2Rot
    #img = QRobject.Rot(img)
    #thresh = Tranform2Thresh(img,128,True)
    #cv2.imshow("img in final attemp ",cv2.resize(thresh,(300,300)))
    #data = QRobject.decodeQRdata(thresh)
    #show('img in last attemp to decode',thresh)
    #if len(data) > 0:  # Successfully detected QR code
    #    QRobject.CheckingAndSendData(data,MySQLconn, PLCconn) if MySQLconn is not None and PLCconn is not None else None
    #    #print("success at last attempt")
    #    print("QR code data:", data)
    #   return True
    #else:
    #    print("final attemp false"); 
    return False

         
def main():
    i = 9 # index of img
    img_path = f'CREVIS_IMG/extractFrame/QR_Product_num_{i}.jpg'
    img = cv2.imread(img_path)
    if img is None:
        print(f"Can not read img from {img_path}")
    else:
        isSuccess = ReadAndDecodeQR(img,None,None)
        if isSuccess:
            print("Decode success")
        else:
            print("Decode Fail")
    if(cv2.waitKey(0) == 27): cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
