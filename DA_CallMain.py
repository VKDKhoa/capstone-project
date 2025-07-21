
############### START IMPORT #################

# neccessary module
import cv2
import time
import gc 
import struct
import numpy as np

# import the packages for detection object in camera
from DA_ObjectDetection import Object

# import the packages for detect defection
from DA_DetectDefect import DetectDefection

#from DA_QRDecocde import ReadAndDecodeQR
from DA_QRDecocde import ReadAndDecodeQR

# import the packages for MySQL, PLC connection and camera setting && connection
from DA_Connection import *

# import PyQt5 for GUI
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

#import module for APICamera
from APICamera.MVSDK import *
from APICamera.ImageConvert import *
from APICamera.SetUpCREVISCAM import *

############### END IMPORT #################

VideoPath = [0,1,'IMG/Video/record.mp4']
#print("Status of connect to MySQL",MySQLconn.getStatusConnection()) #connect to MySQL
#print("Status of connect to PLC",PLCconn.isConnected) #connect to PLC

#init the frame
global run
run = False

#show image from camera openCV to label in GUI, for display purpose
def show_image_to_label(cv_img, label) -> None:
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB) #convert the image to RGB format
    resize_img = cv2.resize(rgb_image, (label.width(), label.height())) #resize the image to fit the label size
    
    h, w, ch = resize_img.shape #get the height, width and channel of the image
    bytes_per_line = ch * w # number of bytes per line, using to convert to QImage

    qt_image = QImage(resize_img.data, w, h, bytes_per_line, QImage.Format_RGB888) #
    pixmap = QPixmap.fromImage(qt_image)

    label.setPixmap(pixmap.scaled(label.width(), label.height(), Qt.KeepAspectRatio))

def onGetFrameEx(frame):
    pass
def RunSystem(label, label_2,MySQLconn, PLCconn)-> None:
    ############### Connect and create Camere #############################
    countFail = 0
    cap = -1 #initialize camera
    cap = create_camera_connection()
    while cap == -1: #if camera is not connected, try to connect again
        countFail += 1
        if countFail >= 20:
            return
        cap = create_camera_connection()
    
    #### setting camera ###########
    streamSource = set_camera_settings(cap,
                        width=1000,
                        height=1000,
                        offsetX= 1644//2 -500,
                        offsetY=1236//2 -500,
                        exposureTimeVal=30000,
                        gainVal=300000,
                        acqMode = b"Continuous") #set the camera settings
    
    if streamSource is None:
        print("Failed to set camera settings.")
        return
    
    # start grabbing 
    nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), \
                                               c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
    if( nRet != 0):
        print("startGrabbing fail!")
        # realease if grabing fail
        streamSource.contents.release(streamSource)   
        return
    
    ################ parameter for system processing #####################
    IMG_LIST = [] #list of object being detected and still not processed
    ROI = [] #list to contain the ROI matrix of objectS
    
    isDefected: bool = False #Check if the QR label is defected
    isObject: bool = False #Check if the object is detected
    
    n:int = 0 #Count the number of objetc
    i:int = 0 #To store the img that can not be Decode or dectect
    
     ################ start stream camera #####################
    global run
    run = True
    TimeoutValue = 1000 #timeout value for getFrame
    while run: # loop for stream camera
        # create frame
        raw_frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(raw_frame), c_uint(TimeoutValue))
        if ( nRet != 0 ):
            print("getFrame fail! Timeout:%d ms", TimeoutValue)
            # release if getFrame fail
            streamSource.contents.release(streamSource)   
            return
        
        # convert frame to OpenCV format
        frame = convertOpenCV(raw_frame) #convert the frame to OpenCV format
        if frame is None:
            print("convertOpenCV fail!")
            # release frame
            raw_frame.contents.release(raw_frame)
            # release stream source
            streamSource.contents.release(streamSource)
            return
        
        # display the frame
        copyForDisplay = frame.copy() #copy the frame for display
        display_frame = cv2.resize(copyForDisplay,(500,500), interpolation=cv2.INTER_AREA)
        
        #show the frame to label in GUI
        show_image_to_label(display_frame, label) #show the frame to label in GUI
        
        #Write the code here
        if ROI is not None and len(ROI) > 0:
            QR_Object.update_isObject(True) #update status of detect object
            QR_Object.update_roi(ROI) #save the ROI to object
            n += 1 #increase the number of object
            if len(QR_Object.roi) > 0:
                IMG_LIST.append(QR_Object)
            ROI = [] # reset ROI after add it to list
        else:
            QR_Object = Object(ROI,isObject,isDefected,frame) # if object detect in frame, creat Object name QR_Object
            ROI = QR_Object.DetectAndCaptureObject() #continue to scan for object
        
        #print("ROI LENGHT: ",len(IMG_LIST))
        
        if IMG_LIST != [] and len(IMG_LIST[0].roi) > 0:
            #Start Detect the defection
            #cv2.imshow("current_img",IMG_LIST[0].roi)
            isCurrentObjectDefect = DetectDefection(IMG_LIST[0].roi,IMG_LIST[0].isDefected)
            IMG_LIST[0].update_isDefect(isCurrentObjectDefect)
            
            if IMG_LIST[0].isDefected:#if not defected, check the angle
                PLCconn.SendToPLC("Damaged")
                MySQLconn.handleWithDamagedData()
                print("Defected")
            else:
                isSuccess:bool = ReadAndDecodeQR(IMG_LIST[0].frame,MySQLconn, PLCconn) #decode the QR code and save the data to MySQL
                if not isSuccess:
                    cv2.imwrite(f'IMG/IDK{i}.jpg',IMG_LIST[0].frame)
                    i += 1
            
            current_roi = cv2.resize(IMG_LIST[0].roi,(300,300), interpolation=cv2.INTER_AREA) #to showing the current object in processing
            show_image_to_label(current_roi, label_2)
            #print("Current object: ",IMG_LIST[0].roi.shape) #check the current object size
            #cv2.imshow("Current Object",current_roi)
            IMG_LIST.pop(0)
            gc.collect()
            if (cv2.waitKey(1) & 0xFF == 27) or run == False: 
                break
    # --- end while ---
    print("Stop camera")
    cv2.destroyAllWindows()

    # release resource after stop grab
    nRet = streamSource.contents.stopGrabbing(streamSource)
    if ( nRet != 0 ):
        print("stopGrabbing fail!")
        # release if stop fail
        streamSource.contents.release(streamSource)  
        return

    # close camera
    nRet = closeCamera(cap)
    if ( nRet != 0 ):
        print("closeCamera fail")
        #release
        streamSource.contents.release(streamSource)   
        return
    # release stream
    streamSource.contents.release(streamSource)  
    return

def StopSystem() -> None:
    global run
    run = False

def main():
    RunSystem(None,None,None,None) #run the system
if __name__ == '__main__':
    main()
