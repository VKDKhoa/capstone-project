# import for using API of camera to connect
from APICamera.ImageConvert import *
from APICamera.MVSDK import *
from APICamera.SetUpCREVISCAM import *

# import for processing
import struct
import time
import numpy as np
import cv2
import gc
import os

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
    if (nRet != 0):
        print("openCamera fail.")
        return -1

    # Set Width, Height, Offset, Exposure, Gain
    def set_int_node(attrName: bytes, value: int):
        node = pointer(GENICAM_IntNode())
        nodeInfo = GENICAM_IntNodeInfo()
        nodeInfo.pCamera = pointer(cap)
        nodeInfo.attrName = attrName
        nRet = GENICAM_createIntNode(byref(nodeInfo), byref(node))
        if nRet == 0:
            node.contents.setValue(node, c_longlong(value))
            node.contents.release(node)

    def set_double_node(attrName: bytes, value: float):
        node = pointer(GENICAM_DoubleNode())
        nodeInfo = GENICAM_DoubleNodeInfo()
        nodeInfo.pCamera = pointer(cap)
        nodeInfo.attrName = attrName
        nRet = GENICAM_createDoubleNode(byref(nodeInfo), byref(node))
        if nRet == 0:
            node.contents.setValue(node, c_double(value))
            node.contents.release(node)

    set_int_node(b"Width", 1644)
    set_int_node(b"Height", 1236)
    set_int_node(b"OffsetX", 0)
    set_int_node(b"OffsetY", 0)
    set_double_node(b"ExposureTime", 35000.0)
    set_int_node(b"GainRaw", 400000)

    # setting acquisition continous mode
    acqCtrlInfo = GENICAM_AcquisitionControlInfo()
    acqCtrlInfo.pCamera = pointer(cap)
    acqCtrl = pointer(GENICAM_AcquisitionControl())
    GENICAM_createAcquisitionControl(pointer(acqCtrlInfo), byref(acqCtrl))
    acqModeNode = acqCtrl.contents.acquisitionMode(acqCtrl)
    acqModeNode.setValueBySymbol(byref(acqModeNode), b"Continuous")
    acqModeNode.release(byref(acqModeNode))
    acqCtrl.contents.release(acqCtrl)

    # setting stream for receive image
    streamSourceInfo = GENICAM_StreamSourceInfo()
    streamSourceInfo.channelId = 0
    streamSourceInfo.pCamera = pointer(cap)
    streamSource = pointer(GENICAM_StreamSource())
    GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))

    # turn off trigger mode
    trigModeEnumNode = pointer(GENICAM_EnumNode())
    trigModeEnumNodeInfo = GENICAM_EnumNodeInfo()
    trigModeEnumNodeInfo.pCamera = pointer(cap)
    trigModeEnumNodeInfo.attrName = b"TriggerMode"
    GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode))
    trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"Off")
    trigModeEnumNode.contents.release(trigModeEnumNode)

    # start grabbing
    streamSource.contents.startGrabbing(streamSource, c_ulonglong(0),
                                         c_int(GENICAM_EGrabStrategy.grabStrartegySequential))

    isGrab = True

    # ---- Bổ sung thêm để record ----
    recording = False
    out = None
    save_folder = "/home/pi/IMG/Video"
    os.makedirs(save_folder, exist_ok=True)

    print("Press 'C' to start recording, 'Q' to quit.")
    i = 10
    while isGrab:
        raw_frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(raw_frame), c_uint(500))
        if (nRet != 0):
            continue

        if (raw_frame.contents.valid(raw_frame) != 0):
            raw_frame.contents.release(raw_frame)
            continue

        # parameter of frame
        imageParams = IMGCNV_SOpenParam()
        imageParams.dataSize = raw_frame.contents.getImageSize(raw_frame)
        imageParams.height = raw_frame.contents.getImageHeight(raw_frame)
        imageParams.width = raw_frame.contents.getImageWidth(raw_frame)
        imageParams.paddingX = raw_frame.contents.getImagePaddingX(raw_frame)
        imageParams.paddingY = raw_frame.contents.getImagePaddingY(raw_frame)
        imageParams.pixelForamt = raw_frame.contents.getImagePixelFormat(raw_frame)

        imageBuff = raw_frame.contents.getImage(raw_frame)
        userBuff = c_buffer(b'\0', imageParams.dataSize)
        memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)

        frameData = np.frombuffer(userBuff, dtype=np.uint8)
        expected_size = imageParams.width * imageParams.height
        frameData = frameData[:expected_size]
        frame = frameData.reshape((imageParams.height, imageParams.width))

        frame_show = cv2.resize(frame, (500, 500))
        cv2.imshow('myWindow', frame_show)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c') or key == ord('C'):
            if not recording:
                filename = time.strftime("record4") + ".avi"
                save_path = os.path.join(save_folder, filename)
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(save_path, fourcc, 20, (imageParams.width, imageParams.height), isColor=False)
                recording = True
                print(f"Start recording to {save_path}")

        if recording and out is not None:
            out.write(frame)
        if key == ord('s') or key == ord('S'):
            i = i + 1
            cv2.imwrite(f'/home/pi/DA_MAIN/IMG/roiPic/{i}.jpg', frame)
        if key == ord('q') or key == ord('Q'):
            isGrab = False
            break

        raw_frame.contents.release(raw_frame)
        gc.collect()

    # release resource
    if recording and out is not None:
        out.release()

    streamSource.contents.stopGrabbing(streamSource)
    streamSource.contents.release(streamSource)
    closeCamera(cap)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    demo()
