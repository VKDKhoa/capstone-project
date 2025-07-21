#import module for APICamera
from APICamera.MVSDK import *
from APICamera.ImageConvert import *
from APICamera.SetUpCREVISCAM import *

import cv2
from DA_Connection import *

def turnOnCamera():
    countFail = 0
    cap = -1 #initialize camera
    cap = create_camera_connection()
    while cap == -1: #if camera is not connected, try to connect again
        countFail += 1
        if countFail >= 20:
            return
        cap = create_camera_connection()
    
    #### open camera ####
    
    
    #### setting camera ###########
    print("create stream source")
    streamSource = set_camera_settings(cap,
                        width=1644,
                        height=1236,
                        offsetX=0,
                        offsetY=0,
                        exposureTimeVal=35000,
                        gainVal=300000,
                        acqMode = b"Continuous") #set the camera settings
    
    print("start grabbing")
    # start grabbing 
    nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), \
                                               c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
    if( nRet != 0):
        print("startGrabbing fail!")
        # realease if grabing fail
        streamSource.contents.release(streamSource)   
        return -1
    
    TimeoutValue = 1000 #timeout value for getFrame
    while True: # loop for stream camera
         # create frame
        raw_frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(raw_frame), c_uint(TimeoutValue))
        if ( nRet != 0 ):
            print("getFrame fail! Timeout:%d ms", TimeoutValue)
            # release if getFrame fail
            streamSource.contents.release(streamSource)   
            return
        
        # pre process frame
        nRet = raw_frame.contents.valid(raw_frame)
        if ( nRet != 0 ):
            print("frame is invalid!")
            # release frame
            raw_frame.contents.release(raw_frame)
            streamSource.contents.release(streamSource)
            return -1
        
        # convert frame to OpenCV format
        frame = convertOpenCV(raw_frame) #convert the frame to OpenCV format
        if frame is None:
            print("convertOpenCV fail!")
            # release frame
            raw_frame.contents.release(raw_frame)
            # release stream source
            streamSource.contents.release(streamSource)
            return -1
        
        # display the frame
        copyForDisplay = frame.copy() #copy the frame for display
        display_frame = cv2.resize(copyForDisplay,(500,500), interpolation=cv2.INTER_AREA)
        
        cv2.imshow("Camera Stream", display_frame)
        gc.collect()
        
        if (cv2.waitKey(1) & 0xFF == 27):  # Press 'ESC' to exit
            break
    # release stream source
    return turnOffCamera(cap, streamSource)


def turnOffCamera(cap, streamSource):
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
    print("Camera closed successfully")
    return 0

if __name__=="__main__": 
    nRet = turnOnCamera()
    if nRet != 0:
        print("Some Error happend")
    print("--------- Demo end ---------")
    # 3s exit
    time.sleep(0.2) 	
