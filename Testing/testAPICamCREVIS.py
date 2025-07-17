import sys
import os

CAPSTONE_DIR = os.environ.get("CAPSTONE_DIR", "/home/pi/capstone-project")
sys.path.append(CAPSTONE_DIR)

# import for using API of camera to connect
from APICamera.ImageConvert import *
from APICamera.MVSDK import *
from APICamera.SetUpCREVISCAM import *

# import for processing
import struct
import time
#import datetime
import numpy as np
import cv2
import gc


def demo():    
    # check camera is connect
    cameraCnt = None
    CameraList = None
    countFail = 0
    while True:
        if countFail >= 20:
            return -1
        cameraCnt, cameraList = enumCameras()
        if cameraCnt is None:
            countFail += 1
            continue
        else:
            countFail = 0
            break
    
    # show inform of connected camera
    for index in range(0, cameraCnt):
        camera = cameraList[index]
        print("\nCamera Id = " + str(index))
        print("Key           = " + str(camera.getKey(camera)))
        print("vendor name   = " + str(camera.getVendorName(camera)))
        print("Model  name   = " + str(camera.getModelName(camera)))
        print("Serial number = " + str(camera.getSerialNumber(camera)))
        
    cap = cameraList[0]

    # open camera
    nRet = openCamera(cap)
    if ( nRet != 0 ):
        print("openCamera fail.")
        return -1;
    
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
    
    # Set OffsetX = 0
    offsetXNode = pointer(GENICAM_IntNode())
    offsetXNodeInfo = GENICAM_IntNodeInfo()
    offsetXNodeInfo.pCamera = pointer(cap)
    offsetXNodeInfo.attrName = b"OffsetX"

    nRet = GENICAM_createIntNode(byref(offsetXNodeInfo), byref(offsetXNode))
    if nRet == 0:
        offsetXNode.contents.setValue(offsetXNode, c_longlong(0))
        offsetXNode.contents.release(offsetXNode)

    # Set OffsetY = 0
    offsetYNode = pointer(GENICAM_IntNode())
    offsetYNodeInfo = GENICAM_IntNodeInfo()
    offsetYNodeInfo.pCamera = pointer(cap)
    offsetYNodeInfo.attrName = b"OffsetY"

    nRet = GENICAM_createIntNode(byref(offsetYNodeInfo), byref(offsetYNode))
    if nRet == 0:
        offsetYNode.contents.setValue(offsetYNode, c_longlong(0))
        offsetYNode.contents.release(offsetYNode)
    
    # set ExposureTime = 35000 us
    exposureTimeNode = pointer(GENICAM_DoubleNode())
    exposureTimeNodeInfo = GENICAM_DoubleNodeInfo()
    exposureTimeNodeInfo.pCamera = pointer(cap)
    exposureTimeNodeInfo.attrName = b"ExposureTime"

    nRet = GENICAM_createDoubleNode(byref(exposureTimeNodeInfo), byref(exposureTimeNode))
    if nRet != 0:
        print("create ExposureTime Node fail!")
        return -1

    nRet = exposureTimeNode.contents.setValue(exposureTimeNode, c_double(0))
    if nRet != 0:
        print("set ExposureTime value fail!")
    else:
        print("Set ExposureTime = 35000us success.")
    
    # set GainRaw = 500000
    gainNode = pointer(GENICAM_IntNode())
    gainNodeInfo = GENICAM_IntNodeInfo()
    gainNodeInfo.pCamera = pointer(cap)
    gainNodeInfo.attrName = b"GainRaw"

    nRet = GENICAM_createIntNode(byref(gainNodeInfo), byref(gainNode))
    if nRet != 0:
        print("create GainRaw Node fail!")
        return -1

    nRet = gainNode.contents.setValue(gainNode, c_longlong(400000))
    if nRet != 0:
        print("set GainRaw value fail!")
    else:
        print("Set GainRaw = 120000 success.")
    gainNode.contents.release(gainNode)
    
    # setting acquisition continous mode
    acqCtrlInfo = GENICAM_AcquisitionControlInfo()
    acqCtrlInfo.pCamera = pointer(cap)
    acqCtrl = pointer(GENICAM_AcquisitionControl())

    nRet = GENICAM_createAcquisitionControl(pointer(acqCtrlInfo), byref(acqCtrl))
    if (nRet != 0):
        print("create AcquisitionControl fail!")
        return -1
    acqModeNode = acqCtrl.contents.acquisitionMode(acqCtrl)
    nRet = acqModeNode.setValueBySymbol(byref(acqModeNode), b"Continuous")
    if (nRet != 0):
        print("set AcquisitionMode [Continuous] fail!")
        acqModeNode.release(byref(acqModeNode))
        acqCtrl.contents.release(acqCtrl)
        return -1
    # Release nodes acquisition
    acqModeNode.release(byref(acqModeNode))
    acqCtrl.contents.release(acqCtrl)
    print("Set AcquisitionMode = Continuous OK.")
    
    # setting stream for receive image
    streamSourceInfo = GENICAM_StreamSourceInfo()
    streamSourceInfo.channelId = 0
    streamSourceInfo.pCamera = pointer(cap)
      
    streamSource = pointer(GENICAM_StreamSource())
    nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
    if ( nRet != 0 ):
        print("create StreamSource fail!")
        return -1
    
    # turn off trigger mode
    trigModeEnumNode = pointer(GENICAM_EnumNode())
    trigModeEnumNodeInfo = GENICAM_EnumNodeInfo() 
    trigModeEnumNodeInfo.pCamera = pointer(cap)
    trigModeEnumNodeInfo.attrName = b"TriggerMode"
    nRet = GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode))
    if ( nRet != 0 ):
        print("create TriggerMode Node fail!")
        streamSource.contents.release(streamSource) 
        return -1
    nRet = trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"Off")
    if ( nRet != 0 ):
        print("set TriggerMode value [Off] fail!")
        trigModeEnumNode.contents.release(trigModeEnumNode)
        streamSource.contents.release(streamSource) 
        return -1
    
    #release trigger node    
    trigModeEnumNode.contents.release(trigModeEnumNode) 

    # start grabbing 
    nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), \
                                               c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
    if( nRet != 0):
        print("startGrabbing fail!")
        # realease if grabing fail
        streamSource.contents.release(streamSource)   
        return -1

    isGrab = True

    while isGrab :
        # create frame
        raw_frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(raw_frame), c_uint(500))
        if ( nRet != 0 ):
            print("getFrame fail! Timeout:[1000]ms")
            # release 
            streamSource.contents.release(streamSource)   
            return -1 
        #else:
            #inform of success frame
        #   print("getFrame success BlockId = [" + str(frame.contents.getBlockId(frame)) + "], get frame time: " + str(datetime.datetime.now()))
        
        
        nRet = raw_frame.contents.valid(raw_frame)
        if ( nRet != 0 ):
            print("frame is invalid!")
            # release frame
            frame.contents.release(frame)
            # release stream source
            streamSource.contents.release(streamSource)
            return -1 

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
        userBuff = c_buffer(b'\0',imageParams.dataSize) # create new memory so that it can be used in Python 
        memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize) # Copy data raw_frame from pointer ImageBuff to userBuff-access by Python

        # release frame
        raw_frame.contents.release(raw_frame)

        # Pixel format is Mono8
        if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
            frameData = np.frombuffer(userBuff, dtype=np.uint8)
            expected_size = imageParams.width * imageParams.height
            frameData = frameData[:expected_size]  # C?t n?u du
            frame = frameData.reshape((imageParams.height, imageParams.width))
        
        frame = cv2.resize(frame,(500,500))
            
    

        cv2.imshow('myWindow', frame)
        gc.collect()
        if (cv2.waitKey(1) >= 0):
            isGrab = False
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
        return -1

    # close camera
    nRet = closeCamera(cap)
    if ( nRet != 0 ):
        print("closeCamera fail")
        #release
        streamSource.contents.release(streamSource)   
        return
     
    # release stream
    streamSource.contents.release(streamSource)    
    
    return 0
    
if __name__=="__main__": 

    nRet = demo()
    if nRet != 0:
        print("Some Error happend")
    print("--------- Demo end ---------")
    # 3s exit
    time.sleep(0.5)
