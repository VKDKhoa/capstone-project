
############### START IMPORT #################

# neccessary module
import cv2
import time
import gc 
import struct
import threading
import queue
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
def show_image_to_label(cv_img: np.ndarray, label: QPixmap) -> None:
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB) if(len(cv_img.shape) > 2) else cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB) #convert the image to RGB format
    resize_img = cv2.resize(rgb_image, (label.width(), label.height())) #resize the image to fit the label size
    
    h, w, ch = resize_img.shape #get the height, width and channel of the image
    bytes_per_line = ch * w # number of bytes per line, using to convert to QImage

    qt_image = QImage(resize_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(qt_image)

    label.setPixmap(pixmap.scaled(label.width(), label.height(), Qt.KeepAspectRatio))


######## FUNCTION FOR IMAGE PROCESSING IN THREAD #######################
processing_queue = queue.Queue()
display_queue = queue.Queue()
stop_event = threading.Event()
""" PROCESSING EACH OF IMAGE PRODUCT """
def process_img(Product: Object,MySQLconn, PLCconn) -> None:
    
    Product.isDefected = DetectDefection(Product.roi, Product.isDefected)
    if Product.isDefected:
        display_queue.put(("Damage", Product.roi))
        return

    isQrProduct = ReadAndDecodeQR(Product.roi, MySQLconn, PLCconn)
    display_queue.put(("OK", Product.roi))

def processing_worker(MySQLconn, PLCconn):
    """Worker thread run continously"""
    while not stop_event.is_set():  
        try:
            product = processing_queue.get(timeout=1)
            if product is None: 
                break
            
            # call fuction for img process
            process_img(product,MySQLconn, PLCconn)
            processing_queue.task_done()
        except queue.Empty:
            continue

"""MAIN SOURCE FOR RUNNING SYSTEM"""
def RunSystem(label, label_2,MySQLconn, PLCconn)-> None:
    
    ############### Connect and create Camera #############################
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
                        width=1644,
                        height=1236,
                        offsetX= 0,
                        offsetY=0,
                        exposureTimeVal= 250, #250
                        gainVal= 250000, #250000
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
    
    IMG_LIST: list[Object] = [] #list of object being detected and still not processed
    ROI: np.ndarray = np.array([]) # to contain the ROI of object being detected
    FRAME_LIST: list[np.ndarray] = [] #list of ROI being detected
    
    isDefected: bool = False #Check if the QR label is defected
    isObject: bool = False #Check if the object is detected

    n:int = 0 #Count the number of objetc
    i:int = 20 #To store the img that can not be Decode or dectect
    
    ################ start stream camera #####################
    global run
    run = True
    TimeoutValue = 1000 #timeout value for getFrame
    t_prev = time.time()
    
    #Create thread for porcess img extract from camera while camera still stream
    worker_thread = threading.Thread(target=processing_worker,args=(MySQLconn, PLCconn), daemon=True)
    worker_thread.start()
    
    # loop for stream camera
    while run: 
        # create frame
        """ READ FRAME FROM CREVIS CAMERA AND CONVERT INTO OPENCV FORAMT"""
        raw_frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(raw_frame), c_uint(TimeoutValue))
        if ( nRet != 0 ):
            print("getFrame fail! Timeout:%d ms", TimeoutValue)
            # release if getFrame fail
            streamSource.contents.release(streamSource)
            stop_event.set()   
            return
        
        # convert frame to OpenCV format
        frame = convertOpenCV(raw_frame) #convert the frame to OpenCV format
        if frame is None:
            print("convertOpenCV fail!")
            # release frame
            raw_frame.contents.release(raw_frame)
            stop_event.set()
            # release stream source
            streamSource.contents.release(streamSource)
            return
        
        """ START PROCESSING AFTER CONVERT OPENCV """
        #frame = frame[90:480, 120:510] 
        display_frame: np.ndarray = frame.copy() #copy the frame for display purpose
        display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2GRAY) if(len(display_frame.shape) > 2) else display_frame
        if label is not None:
            show_image_to_label(display_frame,label)
        else:
            cv2.imshow("display frame", cv2.resize(display_frame,(500,500))) #show the frame in window
        
        # display image from camera extract
        try:
            while True:
                tag, img = display_queue.get_nowait()
                if tag == "Damage":
                    if MySQLconn is not None:
                        MySQLconn.handleWithDamagedData() 
                    if PLCconn is not None:
                        PLCconn.SendToPLC("Damaged")
                    
                    if label_2 is None:
                        cv2.imshow("Damage Product", cv2.resize(img, (300, 300)))
                    else:
                        show_image_to_label(img,label_2)
                
                elif tag == "OK":
                    if label_2 is None:
                        cv2.imshow("ROI processes", cv2.resize(img, (300, 300)))
                    else:
                        show_image_to_label(img,label_2)
                display_queue.task_done()
        except queue.Empty:
            pass
        #Write the code here
        frame: np.ndarray = cv2.cvtColor(raw_frame.copy(),cv2.COLOR_BGR2GRAY) if(len(frame.shape) > 2) else frame  #resize the frame to fit the label size
        
        #cv2.imshow("frame for processing", cv2.resize(frame,(500,500))) #show the frame in window
        FRAME_LIST.append(frame) #add the frame to the list of frame
        
        #t_prev = time.time()
        while len(FRAME_LIST) > 0:
            if isObject is True:
                # print("list of frame",len(FRAME_LIST)) 
                FRAME_LIST.pop(0)# skip to avoid reading many time
                isObject = False
                continue
            else:
                ROI = Object.DetectAndCaptureObject(FRAME_LIST[0])#detect and capture the object in the frame
            #cv2.imwrite(f'extractFrame/QR_Product_num_{i}.jpg',FRAME_LIST[0]) #save the frame to file
            
            if ROI.size > 0: #if the ROI is not empty
                t_current = time.time()
                print("====================== Object time detect ==========================")
                print(f"detect object at time: {t_current}")
                print(f"previous time detect object: {t_prev}")
                print(f"t_prev memory address: {id(t_prev)}")  # Kiểm tra biến
                print(f"time space = {(t_current - t_prev)}")
                if((t_current - t_prev) < 0.5):
                    print("time space too small: time space = ", (t_current - t_prev))
                    FRAME_LIST.pop(0)
                    continue
                print(f"time space available = {(t_current - t_prev)}")
                print(f"BEFORE UPDATE - t_prev = {t_prev}")
                t_prev = t_current
                print(f"AFTER UPDATE - t_prev = {t_prev}")
                isObject = True
                
                #cv2.imshow("frame contain QR product", cv2.resize(FRAME_LIST[0],(300,300),cv2.INTER_AREA))
                
                #cv2.imwrite(f'CREVIS_IMG/extractFrame/QR_Product_num_{i}.jpg',FRAME_LIST[0]) #save the frame to file
                
                print("Object detected, ROI size: ", ROI.size)
                QR_Object: Object = Object(ROI,isObject,isDefected,FRAME_LIST[0]) # if object detect in frame, creat Object name QR_Object
                QR_Object.update_isObject(isObject) #update status of detect object
                #QR_Object.update_roi(ROI) #save the ROI to object
                IMG_LIST.append(QR_Object)
                
                if(len(IMG_LIST) > 0): 
                    """ THRESH FOR PROCESSCING IMAGE"""
                    current_object: np.ndarray = IMG_LIST[0]
                    
                    #cv2.imwrite(f'CREVIS_IMG/extractFrame/DetectFail_num_{i}.jpg',current_object.roi) #save the frame to file
                    i += 1 #increase the number of object
                    processing_queue.put(current_object)
                    print("Object sent to processing queue")
                    IMG_LIST.pop(0)
                
                #cv2.imshow("ROI", cv2.resize(ROI,(300,300),cv2.INTER_CUBIC)) #show the current object in processing
                
                #IMG_LIST.append(QR_Object)
            
            FRAME_LIST.pop(0) #remove the first frame in the list
            
        key = cv2.waitKey(30) & 0xFF
        if key == 27 or run == False:  # ESC để thoát
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
    stop_event.set()  
    
    return
    

def StopSystem() -> None:
    global run
    run = False


def main():
    RunSystem(None,None,None,None) #run the system
if __name__ == '__main__':
    main()
