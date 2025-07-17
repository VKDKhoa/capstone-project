import sys
import os

CAPSTONE_DIR = os.environ.get("CAPSTONE_DIR", "/home/pi/capstone-project")
sys.path.append(CAPSTONE_DIR)

# import for using API of camera to connect
# from APICamera.ImageConvert import *
# from APICamera.MVSDK import *
#from APICamera.SetUpCREVISCAM import *
from APICamera.Demo_opencv_byCallBack import *

# import for processing
import struct
import time
#import datetime
import numpy as np
import cv2
import gc


def demo():     
    # TO DO #

    #find camera
    cameraCnt, cameraList = enumCameras()
    if cameraCnt is None or cameraCnt < 1:
        print("No camera found.")
        return -1
    camera = cameraList[0]
    
    # connect and check connection to camera
    if openCamera(camera) != 0:
        print("Failed to open camera.")
        return -1
    
    #create stream source object
    streamSourceInfo = GENICAM_StreamSourceInfo()
    streamSourceInfo.channelId = 0
    streamSourceInfo.pCamera = pointer(camera)

    streamSource = pointer(GENICAM_StreamSource())
    if GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource)) != 0:
        print("Failed to create stream source.")
        return -1
    
    # Bước 4: Turn off Trigger (Free run)
    trigModeEnumNode = pointer(GENICAM_EnumNode())
    trigModeEnumNodeInfo = GENICAM_EnumNodeInfo()
    trigModeEnumNodeInfo.pCamera = pointer(camera)
    trigModeEnumNodeInfo.attrName = b"TriggerMode"
    if GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode)) != 0:
        print("Failed to create TriggerMode Node.")
        streamSource.contents.release(streamSource)
        return -1
      
    trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"Off")
    trigModeEnumNode.contents.release(trigModeEnumNode)

    userInfo = b"capstone_demo"
    if streamSource.contents.attachGrabbingEx(streamSource, frameCallbackFuncEx, userInfo) != 0:
        print("Failed to attach frame callback.")
        streamSource.contents.release(streamSource)
        return -1
    
        # Bước 6: Bắt đầu lấy ảnh
    if streamSource.contents.startGrabbing(streamSource, 
                                           c_ulonglong(0), 
                                           c_int(GENICAM_EGrabStrategy.grabStrartegySequential)) != 0:
        print("Failed to start grabbing.")
        streamSource.contents.release(streamSource)
        return -1

    print("Grabbing started. Press Ctrl+C to stop.")
    try:
        time.sleep(g_Image_Grabbing_Timer)
    except KeyboardInterrupt:
        pass

    # Bước 7: Ngắt lấy ảnh, huỷ đăng ký callback
    global g_isStop
    g_isStop = 1
    streamSource.contents.detachGrabbingEx(streamSource, frameCallbackFuncEx, userInfo)
    streamSource.contents.stopGrabbing(streamSource)
    streamSource.contents.release(streamSource)
    
    cv2.destroyAllWindows()

    # Bước 8: Đóng camera
    closeCamera(camera)
    
    return 0
    
if __name__=="__main__": 

    nRet = demo()
    if nRet != 0:
        print("Some Error happend")
    print("--------- Demo end ---------")
    # 3s exit
    time.sleep(0.5)
