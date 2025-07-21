from DA_SendSignalToPLC import DA_SendSignal2PLC
from DA_Send2MySQL import DA_Send2MySQL
import time

#import module for APICamera
from APICamera.MVSDK import *
from APICamera.ImageConvert import *
from APICamera.SetUpCREVISCAM import *

def create_mysql_connection():
    return DA_Send2MySQL()

def create_plc_connection():
    return DA_SendSignal2PLC()

def create_camera_connection():
    cameraCnt, cameraList = enumCameras()
    if cameraCnt is None or cameraCnt < 1:
        print("No camera found.")
        return -1
    # connect and check connection to camera
    camera = cameraList[0]
    if openCamera(camera) != 0:
        print("Failed to open camera.")
        return -1
    return camera

def set_camera_settings(camera, width=1644, height=1236, offsetX=0, offsetY=0,
                        exposureTimeVal=0, gainVal=300000, acqMode=b"Continuous"):
    
    # Set ROI
    if setROI(camera, offsetX, offsetY, width, height) != 0:
        print("Set ROI failed.")
        return None
    
    # Set Exposure
    if setExposureTime(camera, exposureTimeVal) != 0:
        print("Set exposure failed.")
        return None
    
    # Set Gain
    if setGain(camera, gainVal) != 0:
        print("Set gain failed.")
        return None
    
    # Set acquisition mode
    if setAcquisitionMode(camera, acqMode) != 0:
        print("Set acquisition mode failed.")
        return None

    # Create stream source
    streamSourceInfo = GENICAM_StreamSourceInfo()
    streamSourceInfo.channelId = 0
    streamSourceInfo.pCamera = pointer(camera)

    streamSource = pointer(GENICAM_StreamSource())
    nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
    if nRet != 0:
        print("Create StreamSource failed!")
        return None
    print("Stream source created successfully.")
    # Turn off trigger mode before streaming
    if setTriggerModeOff(camera, streamSource) != 0:
        print("Set trigger mode off failed.")
        streamSource.contents.release(streamSource)
        return None

    return streamSource


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
    
