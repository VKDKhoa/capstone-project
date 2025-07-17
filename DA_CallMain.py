
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


def RunSystem(label, label_2,MySQLconn, PLCconn)-> None:
    ############### Connect and create Camere #############################
    cameraCnt = None
    CameraList = None
    countFail = 0
    while True:
        if countFail >= 20:
            return
        cameraCnt, cameraList = enumCameras()
        if cameraCnt is None:
            countFail += 1
            continue
        else:
            countFail = 0
            break
    cap = cameraList[0]
    #### open camera ####
    nRet = openCamera(cap)
    if ( nRet != 0 ):
        print("openCamera fail.")
        return;
    #### setting resolution ###########
    #Set Width = 1644
    widthNode = pointer(GENICAM_IntNode())
    widthNodeInfo = GENICAM_IntNodeInfo()
    widthNodeInfo.pCamera = pointer(cap)
    widthNodeInfo.attrName = b"Width"

    nRet = GENICAM_createIntNode(byref(widthNodeInfo), byref(widthNode))
    if nRet == 0:
        widthNode.contents.setValue(widthNode, c_longlong(1644))
        widthNode.contents.release(widthNode)
    
    # Set Height = 1236
    heightNode = pointer(GENICAM_IntNode())
    heightNodeInfo = GENICAM_IntNodeInfo()
    heightNodeInfo.pCamera = pointer(cap)
    heightNodeInfo.attrName = b"Height"

    nRet = GENICAM_createIntNode(byref(heightNodeInfo), byref(heightNode))
    if nRet == 0:
        heightNode.contents.setValue(heightNode, c_longlong(1236))
        heightNode.contents.release(heightNode)
    
    # Set OffsetX
    offsetXNode = pointer(GENICAM_IntNode())
    offsetXNodeInfo = GENICAM_IntNodeInfo()
    offsetXNodeInfo.pCamera = pointer(cap)
    offsetXNodeInfo.attrName = b"OffsetX"

    nRet = GENICAM_createIntNode(byref(offsetXNodeInfo), byref(offsetXNode))
    if nRet == 0:
        offsetXNode.contents.setValue(offsetXNode, c_longlong(0))
        offsetXNode.contents.release(offsetXNode)

    # Set OffsetY
    offsetYNode = pointer(GENICAM_IntNode())
    offsetYNodeInfo = GENICAM_IntNodeInfo()
    offsetYNodeInfo.pCamera = pointer(cap)
    offsetYNodeInfo.attrName = b"OffsetY"

    nRet = GENICAM_createIntNode(byref(offsetYNodeInfo), byref(offsetYNode))
    if nRet == 0:
        offsetYNode.contents.setValue(offsetYNode, c_longlong(0))
        offsetYNode.contents.release(offsetYNode)
    
    # set ExposureTime 
    exposureTimeNode = pointer(GENICAM_DoubleNode())
    exposureTimeNodeInfo = GENICAM_DoubleNodeInfo()
    exposureTimeNodeInfo.pCamera = pointer(cap)
    exposureTimeNodeInfo.attrName = b"ExposureTime"

    nRet = GENICAM_createDoubleNode(byref(exposureTimeNodeInfo), byref(exposureTimeNode))
    if nRet != 0:
        print("create ExposureTime Node fail!")
        return -1
    exposureTimeVal = 0
    nRet = exposureTimeNode.contents.setValue(exposureTimeNode, c_double(exposureTimeVal))
    if nRet != 0:
        print("set ExposureTime value fail!")
    else:
        print(f"Set ExposureTime = {exposureTimeVal}us success.")
    
    # set GainRaw = 450000
    gainNode = pointer(GENICAM_IntNode())
    gainNodeInfo = GENICAM_IntNodeInfo()
    gainNodeInfo.pCamera = pointer(cap)
    gainNodeInfo.attrName = b"GainRaw"

    nRet = GENICAM_createIntNode(byref(gainNodeInfo), byref(gainNode))
    if nRet != 0:
        print("create GainRaw Node fail!")
        return -1
    gainVal = 450000
    nRet = gainNode.contents.setValue(gainNode, c_longlong(gainVal))
    if nRet != 0:
        print("set GainRaw value fail!")
    else:
        print(f"Set GainRaw = {gainVal} success.")
    gainNode.contents.release(gainNode)
    
    #### setting acquisition continous mode ####
    acqCtrlInfo = GENICAM_AcquisitionControlInfo()
    acqCtrlInfo.pCamera = pointer(cap)
    acqCtrl = pointer(GENICAM_AcquisitionControl())

    nRet = GENICAM_createAcquisitionControl(pointer(acqCtrlInfo), byref(acqCtrl))
    if (nRet != 0):
        print("create AcquisitionControl fail!")
        return
    acqModeNode = acqCtrl.contents.acquisitionMode(acqCtrl)
    nRet = acqModeNode.setValueBySymbol(byref(acqModeNode), b"Continuous")
    if (nRet != 0):
        print("set AcquisitionMode [Continuous] fail!")
        acqModeNode.release(byref(acqModeNode))
        acqCtrl.contents.release(acqCtrl)
        return
    # Release nodes acquisition
    acqModeNode.release(byref(acqModeNode))
    acqCtrl.contents.release(acqCtrl)
    print("Set AcquisitionMode = Continuous OK.")

    ########## setting stream for receive image ##############
    streamSourceInfo = GENICAM_StreamSourceInfo()
    streamSourceInfo.channelId = 0
    streamSourceInfo.pCamera = pointer(cap)
      
    streamSource = pointer(GENICAM_StreamSource())
    nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
    if ( nRet != 0 ):
        print("create StreamSource fail!")
        return
    
    ######### turn off trigger mode #################
    trigModeEnumNode = pointer(GENICAM_EnumNode())
    trigModeEnumNodeInfo = GENICAM_EnumNodeInfo() 
    trigModeEnumNodeInfo.pCamera = pointer(cap)
    trigModeEnumNodeInfo.attrName = b"TriggerMode"
    nRet = GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode))
    if ( nRet != 0 ):
        print("create TriggerMode Node fail!")
        streamSource.contents.release(streamSource) 
        return
    nRet = trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"Off")
    if ( nRet != 0 ):
        print("set TriggerMode value [Off] fail!")
        trigModeEnumNode.contents.release(trigModeEnumNode)
        streamSource.contents.release(streamSource) 
        return
    #release trigger node    
    trigModeEnumNode.contents.release(trigModeEnumNode) 
    
    
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
    while run: # loop for stream camera
        # create frame
        raw_frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(raw_frame), c_uint(1000))
        if ( nRet != 0 ):
            print("getFrame fail! Timeout:[500]ms")
            # release 
            streamSource.contents.release(streamSource)   
            return
        
        # pre process frame
        nRet = raw_frame.contents.valid(raw_frame)
        if ( nRet != 0 ):
            print("frame is invalid!")
            # release frame
            frame.contents.release(frame)
            # release stream source
            streamSource.contents.release(streamSource)
            return
        # parameter of frame
        imageParams = IMGCNV_SOpenParam()
        imageParams.dataSize    = raw_frame.contents.getImageSize(raw_frame)
        imageParams.height      = raw_frame.contents.getImageHeight(raw_frame)
        imageParams.width       = raw_frame.contents.getImageWidth(raw_frame)
        imageParams.paddingX    = raw_frame.contents.getImagePaddingX(raw_frame)
        imageParams.paddingY    = raw_frame.contents.getImagePaddingY(raw_frame)
        imageParams.pixelForamt = raw_frame.contents.getImagePixelFormat(raw_frame)
        
        # move data frome driver camera to python
        imageBuff = raw_frame.contents.getImage(raw_frame) #pointer from driver camera contain data raw_frame
        userBuff = c_buffer(b'\0', imageParams.dataSize) # create new memory so that it can be used in Python 
        memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize) # Copy data raw_frame from pointer ImageBuff to userBuff-access by Python
        
        # release frame
        raw_frame.contents.release(raw_frame)
                # Pixel format is Mono8
        if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
            frameData = np.frombuffer(userBuff, dtype=np.uint8)
            expected_size = imageParams.width * imageParams.height
            frameData = frameData[:expected_size]
            frame = frameData.reshape((imageParams.height, imageParams.width))
        
        display_frame = cv2.resize(frame,(500,500), interpolation=cv2.INTER_AREA)
        
        #frame = frame[90:480, 120:510] #y should be first, scale the frame to reduce the size and noise
        show_image_to_label(display_frame, label) #show the frame to label in GUI
        
        #print("Frame size: ",frame.shape) #check the frame size
        #frame testing = [101:476, 101:529], [90:480, 110:510]
        
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
