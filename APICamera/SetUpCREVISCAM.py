from APICamera.ImageConvert import *
from APICamera.MVSDK import *
import struct
import time
import datetime
import numpy
import cv2
import gc

g_cameraStatusUserInfo = b"statusInfo"
def deviceLinkNotify(connectArg, linkInfo):
    if ( EVType.offLine == connectArg.contents.m_event ):
        print("camera has off line, userInfo [%s]" %(c_char_p(linkInfo).value))
    elif ( EVType.onLine == connectArg.contents.m_event ):
        print("camera has on line, userInfo [%s]" %(c_char_p(linkInfo).value))

connectCallBackFuncEx = connectCallBackEx(deviceLinkNotify)

def enumCameras():
    # 获取系统单例
    system = pointer(GENICAM_System())
    nRet = GENICAM_getSystemInstance(byref(system))
    if ( nRet != 0 ):
        print("getSystemInstance fail!")
        return None, None

    # 发现相机 
    cameraList = pointer(GENICAM_Camera()) 
    cameraCnt = c_uint()
    nRet = system.contents.discovery(system, byref(cameraList), byref(cameraCnt), c_int(GENICAM_EProtocolType.typeAll));
    if ( nRet != 0 ):
        print("discovery fail!")
        return None, None
    elif cameraCnt.value < 1:
        print("discovery no camera!")
        return None, None
    else:
        print("cameraCnt: " + str(cameraCnt.value))
        return cameraCnt.value, cameraList
    
def subscribeCameraStatus(camera):
    # 注册上下线通知
    eventSubscribe = pointer(GENICAM_EventSubscribe())
    eventSubscribeInfo = GENICAM_EventSubscribeInfo()
    eventSubscribeInfo.pCamera = pointer(camera)
    
    nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
    if ( nRet != 0):
        print("create eventSubscribe fail!")
        return -1
    
    nRet = eventSubscribe.contents.subscribeConnectArgsEx(eventSubscribe, connectCallBackFuncEx, g_cameraStatusUserInfo)
    if ( nRet != 0 ):
        print("subscribeConnectArgsEx fail!")
        # 释放相关资源
        eventSubscribe.contents.release(eventSubscribe)
        return -1  
    
    # 不再使用时，需释放相关资源
    eventSubscribe.contents.release(eventSubscribe) 
    return 0

# 反注册相机连接状态回调
def unsubscribeCameraStatus(camera):
    # 反注册上下线通知
    eventSubscribe = pointer(GENICAM_EventSubscribe())
    eventSubscribeInfo = GENICAM_EventSubscribeInfo()
    eventSubscribeInfo.pCamera = pointer(camera)
    nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
    if ( nRet != 0):
        print("create eventSubscribe fail!")
        return -1
        
    nRet = eventSubscribe.contents.unsubscribeConnectArgsEx(eventSubscribe, connectCallBackFuncEx, g_cameraStatusUserInfo)
    if ( nRet != 0 ):
        print("unsubscribeConnectArgsEx fail!")
        # 释放相关资源
        eventSubscribe.contents.release(eventSubscribe)
        return -1
    
    # 不再使用时，需释放相关资源
    eventSubscribe.contents.release(eventSubscribe)
    return 0   

def openCamera(camera):
    # 连接相机
    nRet = camera.connect(camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl))
    if ( nRet != 0 ):
        print("camera connect fail!")
        return -1
    else:
        print("camera connect success.")
  
    # 注册相机连接状态回调
    nRet = subscribeCameraStatus(camera)
    if ( nRet != 0 ):
        print("subscribeCameraStatus fail!")
        return -1
    return 0

def closeCamera(camera):
    # 反注册相机连接状态回调
    nRet = unsubscribeCameraStatus(camera)
    if ( nRet != 0 ):
        print("unsubscribeCameraStatus fail!")
        return -1
  
    # 断开相机
    nRet = camera.disConnect(byref(camera))
    if ( nRet != 0 ):
        print("disConnect camera fail!")
        return -1
    
    return 0

def setExposureTime(camera, dVal):
    # 通用属性设置:设置曝光 --根据属性类型，直接构造属性节点。如曝光是 double类型，构造doubleNode节点
    exposureTimeNode = pointer(GENICAM_DoubleNode())
    exposureTimeNodeInfo = GENICAM_DoubleNodeInfo() 
    exposureTimeNodeInfo.pCamera = pointer(camera)
    exposureTimeNodeInfo.attrName = b"ExposureTime"
    
    nRet = GENICAM_createDoubleNode(byref(exposureTimeNodeInfo), byref(exposureTimeNode))
    if ( nRet != 0 ):
        print("create ExposureTime Node fail!")
        return -1
      
    # 设置曝光时间
    nRet = exposureTimeNode.contents.setValue(exposureTimeNode, c_double(dVal))  
    if ( nRet != 0 ):
        print("set ExposureTime value [%f]us fail!"  % (dVal))
        # 释放相关资源
        exposureTimeNode.contents.release(exposureTimeNode)
        return -1
    else:
        print("set ExposureTime value [%f]us success." % (dVal))
            
    # 释放节点资源     
    exposureTimeNode.contents.release(exposureTimeNode)    
    return 0

def setGain(camera, gainVal):
    # set GainRaw = gainVal
    gainNode = pointer(GENICAM_IntNode())
    gainNodeInfo = GENICAM_IntNodeInfo()
    gainNodeInfo.pCamera = pointer(camera)
    gainNodeInfo.attrName = b"GainRaw"

    nRet = GENICAM_createIntNode(byref(gainNodeInfo), byref(gainNode))
    if nRet != 0:
        print("create GainRaw Node fail!")
        return -1
    nRet = gainNode.contents.setValue(gainNode, c_longlong(gainVal))
    if nRet != 0:
        print("set GainRaw value fail!")
        return -1
    else:
        print(f"Set GainRaw = {gainVal} success.")
    
    gainNode.contents.release(gainNode)
    return 0

def setAcquisitionMode(camera, acqMode):
    #### setting acquisition continous mode ####
    acqCtrlInfo = GENICAM_AcquisitionControlInfo()
    acqCtrlInfo.pCamera = pointer(camera)
    acqCtrl = pointer(GENICAM_AcquisitionControl())

    nRet = GENICAM_createAcquisitionControl(pointer(acqCtrlInfo), byref(acqCtrl))
    if (nRet != 0):
        print("create AcquisitionControl fail!")
        return -1
    
    acqModeNode = acqCtrl.contents.acquisitionMode(acqCtrl)
    nRet = acqModeNode.setValueBySymbol(byref(acqModeNode), acqMode)
    if (nRet != 0):
        print("set AcquisitionMode [Continuous] fail!")
        acqModeNode.release(byref(acqModeNode))
        acqCtrl.contents.release(acqCtrl)
        return -1
    
    # Release nodes acquisition
    acqModeNode.release(byref(acqModeNode))
    acqCtrl.contents.release(acqCtrl)
    print("Set AcquisitionMode = Continuous OK.")
    return 0

def setTriggerModeOff(camera, streamSource):
    ######### turn off trigger mode #################
    trigModeEnumNode = pointer(GENICAM_EnumNode())
    trigModeEnumNodeInfo = GENICAM_EnumNodeInfo() 
    trigModeEnumNodeInfo.pCamera = pointer(camera)
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
    return 0 

def setROI(camera, OffsetX, OffsetY, nWidth, nHeight):
    #获取原始的宽度
    widthMaxNode = pointer(GENICAM_IntNode())
    widthMaxNodeInfo = GENICAM_IntNodeInfo() 
    widthMaxNodeInfo.pCamera = pointer(camera)
    widthMaxNodeInfo.attrName = b"WidthMax"
    nRet = GENICAM_createIntNode(byref(widthMaxNodeInfo), byref(widthMaxNode))
    if ( nRet != 0 ):
        print("create WidthMax Node fail!")
        return -1
    
    oriWidth = c_longlong()
    nRet = widthMaxNode.contents.getValue(widthMaxNode, byref(oriWidth))
    if ( nRet != 0 ):
        print("widthMaxNode getValue fail!")
        # 释放相关资源
        widthMaxNode.contents.release(widthMaxNode)
        return -1  
    
    # 释放相关资源
    widthMaxNode.contents.release(widthMaxNode)
    
    # 获取原始的高度
    heightMaxNode = pointer(GENICAM_IntNode())
    heightMaxNodeInfo = GENICAM_IntNodeInfo() 
    heightMaxNodeInfo.pCamera = pointer(camera)
    heightMaxNodeInfo.attrName = b"HeightMax"
    nRet = GENICAM_createIntNode(byref(heightMaxNodeInfo), byref(heightMaxNode))
    if ( nRet != 0 ):
        print("create HeightMax Node fail!")
        return -1
    
    oriHeight = c_longlong()
    nRet = heightMaxNode.contents.getValue(heightMaxNode, byref(oriHeight))
    if ( nRet != 0 ):
        print("heightMaxNode getValue fail!")
        # 释放相关资源
        heightMaxNode.contents.release(heightMaxNode)
        return -1
    
    # 释放相关资源
    heightMaxNode.contents.release(heightMaxNode)
        
    # 检验参数
    if ( ( oriWidth.value < (OffsetX + nWidth)) or ( oriHeight.value < (OffsetY + nHeight)) ):
        print("please check input param!")
        return -1
    
    # 设置宽度
    widthNode = pointer(GENICAM_IntNode())
    widthNodeInfo = GENICAM_IntNodeInfo() 
    widthNodeInfo.pCamera = pointer(camera)
    widthNodeInfo.attrName = b"Width"
    nRet = GENICAM_createIntNode(byref(widthNodeInfo), byref(widthNode))
    if ( nRet != 0 ):
        print("create Width Node fail!") 
        return -1
    
    nRet = widthNode.contents.setValue(widthNode, c_longlong(nWidth))
    if ( nRet != 0 ):
        print("widthNode setValue [%d] fail!" % (nWidth))
        # 释放相关资源
        widthNode.contents.release(widthNode)
        return -1  
    
    # 释放相关资源
    widthNode.contents.release(widthNode)
    
    # 设置高度
    heightNode = pointer(GENICAM_IntNode())
    heightNodeInfo = GENICAM_IntNodeInfo() 
    heightNodeInfo.pCamera = pointer(camera)
    heightNodeInfo.attrName = b"Height"
    nRet = GENICAM_createIntNode(byref(heightNodeInfo), byref(heightNode))
    if ( nRet != 0 ):
        print("create Height Node fail!")
        return -1
    
    nRet = heightNode.contents.setValue(heightNode, c_longlong(nHeight))
    if ( nRet != 0 ):
        print("heightNode setValue [%d] fail!" % (nHeight))
        # 释放相关资源
        heightNode.contents.release(heightNode)
        return -1    
    
    # 释放相关资源
    heightNode.contents.release(heightNode)    
    
    # 设置OffsetX
    OffsetXNode = pointer(GENICAM_IntNode())
    OffsetXNodeInfo = GENICAM_IntNodeInfo() 
    OffsetXNodeInfo.pCamera = pointer(camera)
    OffsetXNodeInfo.attrName = b"OffsetX"
    nRet = GENICAM_createIntNode(byref(OffsetXNodeInfo), byref(OffsetXNode))
    if ( nRet != 0 ):
        print("create OffsetX Node fail!")
        return -1
    
    nRet = OffsetXNode.contents.setValue(OffsetXNode, c_longlong(OffsetX))
    if ( nRet != 0 ):
        print("OffsetX setValue [%d] fail!" % (OffsetX))
        # 释放相关资源
        OffsetXNode.contents.release(OffsetXNode)
        return -1    
    
    # 释放相关资源
    OffsetXNode.contents.release(OffsetXNode)  
    
    # 设置OffsetY
    OffsetYNode = pointer(GENICAM_IntNode())
    OffsetYNodeInfo = GENICAM_IntNodeInfo() 
    OffsetYNodeInfo.pCamera = pointer(camera)
    OffsetYNodeInfo.attrName = b"OffsetY"
    nRet = GENICAM_createIntNode(byref(OffsetYNodeInfo), byref(OffsetYNode))
    if ( nRet != 0 ):
        print("create OffsetY Node fail!")
        return -1
    
    nRet = OffsetYNode.contents.setValue(OffsetYNode, c_longlong(OffsetY))
    if ( nRet != 0 ):
        print("OffsetY setValue [%d] fail!" % (OffsetY))
        # 释放相关资源
        OffsetYNode.contents.release(OffsetYNode)
        return -1    
    
    # 释放相关资源
    OffsetYNode.contents.release(OffsetYNode)   
    return 0
            
def convertOpenCV(frame) -> numpy.ndarray:
    nRet = frame.contents.valid(frame)
    if ( nRet != 0):
        print("frame is invalid!")
        # 释放驱动图像缓存资源
        frame.contents.release(frame)
        return None        
 
    #print("BlockId = %d userInfo = %s"  %(frame.contents.getBlockId(frame), c_char_p(userInfo).value))

    #此处客户应用程序应将图像拷贝出使用
    
    # parameter of frame
    imageParams = IMGCNV_SOpenParam()
    imageParams.dataSize    = frame.contents.getImageSize(frame)
    imageParams.height      = frame.contents.getImageHeight(frame)
    imageParams.width       = frame.contents.getImageWidth(frame)
    imageParams.paddingX    = frame.contents.getImagePaddingX(frame)
    imageParams.paddingY    = frame.contents.getImagePaddingY(frame)
    imageParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

    # move data frome driver camera to python
    imageBuff = frame.contents.getImage(frame)
    userBuff = c_buffer(b'\0', imageParams.dataSize)
    memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)

    # 释放驱动图像缓存资源
    frame.contents.release(frame)

    # 如果图像格式是 Mono8 直接使用
    if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
        # grayByteArray = bytearray(userBuff)
        # cvImage = numpy.array(grayByteArray).reshape(imageParams.height, imageParams.width)
        frameData = numpy.frombuffer(userBuff, dtype=numpy.uint8)
        expected_size = imageParams.width * imageParams.height
        frameData = frameData[:expected_size]  # C?t n?u du
        cvImage = frameData.reshape((imageParams.height, imageParams.width))
    
    return cvImage

def isGammaSupported(camera):
    gammaNode = pointer(GENICAM_DoubleNode())
    gammaNodeInfo = GENICAM_DoubleNodeInfo()
    gammaNodeInfo.pCamera = pointer(camera)
    gammaNodeInfo.attrName = b"Gamma"

    nRet = GENICAM_createDoubleNode(byref(gammaNodeInfo), byref(gammaNode))
    if nRet != 0:
        return False
    gammaNode.contents.release(gammaNode)
    return True

def setGamma(camera, gammaVal):
    # Create a pointer to the Gamma node
    
    gammaNode = pointer(GENICAM_DoubleNode())
    gammaNodeInfo = GENICAM_DoubleNodeInfo()
    gammaNodeInfo.pCamera = pointer(camera)
    gammaNodeInfo.attrName = b"Gamma"

    # Initialize the Gamma node
    nRet = GENICAM_createDoubleNode(byref(gammaNodeInfo), byref(gammaNode))
    if nRet != 0:
        print("Failed to create Gamma node.")
        return -1

    # Set the gamma value
    nRet = gammaNode.contents.setValue(gammaNode, c_double(gammaVal))
    if nRet != 0:
        print("Failed to set Gamma value.")
        gammaNode.contents.release(gammaNode)
        return -1

    # Release the node after use
    gammaNode.contents.release(gammaNode)
    print(f"Gamma value set to: {gammaVal}")
    return 0
