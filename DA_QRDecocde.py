import cv2
import pyzbar.pyzbar as pyzbar
import re
import numpy as np



def show(nameWindow:str,img) -> None:
    cv2.imshow(nameWindow,img)
    key = cv2.waitKey(0)
    if key == 27:
        cv2.destroyAllWindows()
        return

class QRcodeRead:
    def __init__(self,frame):
        self.frame: np.ndarray = frame
        self.data: str = ''
        self.gamma: float = 1.5
        self.angle: float = 0
        self.QR_info = []
        self.pattern = r"^(SB|ST|SF)\d{5}$" #pattern of data
    
    def Sharpen(self,img) -> np.ndarray:
        blur = cv2.GaussianBlur(img, (3,3), 0)
        #matrix to sharpen
        sharp = np.array([[-1,-1,-1],
                        [-1,9,-1],
                        [-1,-1,-1]
                        ])
        #convolution to make img sharpen
        img = cv2.filter2D(blur,-1,sharp)
        return img
    
    def gamma_correction(self,img) -> np.ndarray:
        inv_gamma = 1.0 / self.gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(img, table)
    
    def Rot(self,img) -> np.ndarray :
        (h, w) = img.shape[:2]
        scale = 1.0  #
        center = (w // 2, h // 2)  # Center img
    
        M = cv2.getRotationMatrix2D(center, self.angle, scale)
        rotated_img = cv2.warpAffine(img, M, (w, h))
        return rotated_img

    def findAngle(self,img) -> float:
        thresh = cv2.inRange(img,50,128) #pic 4 is best with 140
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
    
    def decodeQRdata(self,img) -> str:
        #show('img will be decode',img)
        self.QR_info = pyzbar.decode(img)
        if not self.QR_info:
            return ''
        self.data = self.QR_info[0].data.decode("utf-8")
        x,y,w,h = self.QR_info[0].rect
        cv2.rectangle(self.frame,(x,y),(x+w,y+h),(255,0,255),2) #drawing rectangle around QR
        return self.data 
    
    def CheckingAndSendData(self,data,MySQLconn,PLCconn) -> None:
        if len(data) <= 0:
            return
        self.data = data.replace(" ","") #clean the data with leftover space
        #print(self.data)
        IDProduct:str = self.data[:7] if len(self.data) >= 7 else self.data
        if re.match(self.pattern, IDProduct):
            isExist = MySQLconn.checkDataExist(IDProduct)
            if not isExist:
                print("Data is not exist")
                MySQLconn.handleWithNoData(self.data)
                PLCconn.SendToPLC("No data in DB")
                return  
            MySQLconn.sendData2mysql(self.data)
            type_product = IDProduct[:2]
            productName:str = 'SuaBot' if type_product == 'SB' else ('SuaTuoi' if type_product == 'ST' else 'SuaTraiCay')
            print(productName)
            PLCconn.SendToPLC(productName)
        else:
            print(self.data)
            PLCconn.SendToPLC("No data in DB")

def improveIMG(QRobject,img) -> np.ndarray:
    img = QRobject.gamma_correction(QRobject.frame) #improve contrast
    img = QRobject.Sharpen(img) #improve sharpen
    return img

def Tranform2Thresh(img,thresh_Val:int,equal:bool) -> np.ndarray:
    gray = img
    if equal:
        gray = cv2.equalizeHist(gray)
    _,thresh = cv2.threshold(gray,thresh_Val,255,cv2.THRESH_BINARY)
    return thresh

def ReadAndDecodeQR(frame,MySQLconn,PLCconn) -> bool:
    # First attempt to decode the QR code
    QRobject = QRcodeRead(frame)
    gray = frame
    #gray = cv2.cvtColor(QRobject.frame,cv2.COLOR_BGR2GRAY)
    #show('img in First attemp to decode',gray)
    data = QRobject.decodeQRdata(gray)
    
    if len(data) > 0:  # Successfully detected QR code
        QRobject.CheckingAndSendData(data,MySQLconn, PLCconn)
        return True
            
    
    #Second Attemp, will imporve the contrast and make edge more sharpen for easier decode
    img = QRobject.frame
    img = improveIMG(QRobject,img)
    thresh_Val = np.array([128,140,160,180])
    for th in thresh_Val :
        thresh = Tranform2Thresh(img,th,False)
        #show('img in Seccon attemp to decode',thresh)
        data = QRobject.decodeQRdata(thresh)
        if len(data) > 0:  # Successfully detected QR code
            break
    
    if len(data) > 0:
        QRobject.CheckingAndSendData(data,MySQLconn, PLCconn)
        return True
    
    ## Final attempt to decode the QR code
    QRobject.angle = QRobject.findAngle(img)
    angle2Rot = QRobject.angle if 30 < QRobject.angle < 80 else (135 - QRobject.angle if 80 < QRobject.angle <= 90 else 0)
    QRobject.angle = -angle2Rot
    img = QRobject.Rot(img)
    thresh = Tranform2Thresh(img,128,True)
    
    data = QRobject.decodeQRdata(thresh)
    #show('img in last attemp to decode',thresh)
    if len(data) > 0:  # Successfully detected QR code
        QRobject.CheckingAndSendData(data,MySQLconn, PLCconn)
        return True
    else:
        return False

         
def main():
    img_path = f'IMG/IDK{0}.jpg'
    img = cv2.imread(img_path)
    if img is None:
        print(f"Lỗi: Không thể đọc ảnh từ {img_path}")
    else:
        isSuccess = ReadAndDecodeQR(img)
        if isSuccess:
            print("Decode success")
        else:
            print("Decode Fail")

if __name__ == '__main__':
    main()
