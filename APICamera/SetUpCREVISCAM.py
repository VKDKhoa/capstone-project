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
            
