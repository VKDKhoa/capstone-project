#import module for APICamera
from APICamera.MVSDK import *
from APICamera.ImageConvert import *
from APICamera.SetUpCREVISCAM import *
from APICamera.GetValueCREVISCAM import *

import cv2
import numpy as np
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
                        exposureTimeVal=250,
                        gainVal=250000,
                        acqMode = b"Continuous") #set the camera settings
    
    if streamSource is None:
        print("Failed to set camera settings.")
        return -1
    print("start grabbing")
    # start grabbing 
    
    nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), 
                                               c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
    if( nRet != 0):
        print("startGrabbing fail!")
        # realease if grabing fail
        streamSource.contents.release(streamSource)   
        return -1
    
    TimeoutValue = 500 #timeout value for getFrame
    # varibale for record video
    recording = False
    video_writer = None
    while True: # loop for stream camera
         # create frame
        raw_frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(raw_frame), c_uint(TimeoutValue))
        if ( nRet != 0 ):
            print(f"getFrame fail! Timeout:%d ms", TimeoutValue)
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
        #print("Frame shape:", frame.shape)

        if frame is None:
            print("convertOpenCV fail!")
            # release frame
            raw_frame.contents.release(raw_frame)
            # release stream source
            streamSource.contents.release(streamSource)
            return -1
        
        # display the frame
        copyForDisplay = frame.copy() #copy the frame for display
        display_frame = cv2.resize(copyForDisplay,(600,600), interpolation=cv2.INTER_AREA)
        
        cv2.imshow("Camera Stream", display_frame)
        key = cv2.waitKey(1) & 0xFF
        # record if press "s"
        if key == ord('s'):
            recording = not recording
            if recording:
                print("Started recording...")
                filename = f"/home/pi/capstone-project/CREVIS_IMG/Video/record5-Te250.avi"
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]),isColor = False)
            else:
                print("Stopped recording.")
                if video_writer:
                    video_writer.release()
                    video_writer = None

        if recording and video_writer:
            video_writer.write(frame)

        gc.collect()

        if key == 27:  # ESC
            break
        # release video writer if still open
        if video_writer:
            video_writer.release()

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
