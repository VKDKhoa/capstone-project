from APICamera.MVSDK import *
from APICamera.ImageConvert import *

def getExposureTime(camera):
    # create node to read ExposureTime
    exposureTimeNode = pointer(GENICAM_DoubleNode())
    exposureTimeNodeInfo = GENICAM_DoubleNodeInfo() 
    exposureTimeNodeInfo.pCamera = pointer(camera)
    exposureTimeNodeInfo.attrName = b"ExposureTime"

    # create node
    nRet = GENICAM_createDoubleNode(byref(exposureTimeNodeInfo), byref(exposureTimeNode))
    if nRet != 0:
        print("create ExposureTime Node fail!")
        return -1

    # get value of ExposureTime
    value = c_double()
    nRet = exposureTimeNode.contents.getValue(exposureTimeNode, byref(value))
    if nRet != 0:
        print("get ExposureTime value fail!")
        exposureTimeNode.contents.release(exposureTimeNode)
        return -1

    # release node
    exposureTimeNode.contents.release(exposureTimeNode)
    return value.value  # return the exposure time value

def getGammaRange(camera):
    gammaNode = pointer(GENICAM_DoubleNode())
    gammaNodeInfo = GENICAM_DoubleNodeInfo()
    gammaNodeInfo.pCamera = pointer(camera)
    gammaNodeInfo.attrName = b"Gamma"

    nRet = GENICAM_createDoubleNode(byref(gammaNodeInfo), byref(gammaNode))
    if nRet != 0:
        print("❌ Failed to create Gamma node.")
        return None

    minVal = c_double()
    maxVal = c_double()
    incVal = c_double()

    if gammaNode.contents.getMinVal(gammaNode, byref(minVal)) != 0:
        print("❌ Failed to get Gamma min value.")
        gammaNode.contents.release(gammaNode)
        return None
    if gammaNode.contents.getMaxVal(gammaNode, byref(maxVal)) != 0:
        print("❌ Failed to get Gamma max value.")
        gammaNode.contents.release(gammaNode)
        return None
    if gammaNode.contents.getIncVal(gammaNode, byref(incVal)) != 0:
        print("❌ Failed to get Gamma increment value.")
        gammaNode.contents.release(gammaNode)
        return None

    gammaNode.contents.release(gammaNode)
    return (minVal.value, maxVal.value, incVal.value)

def getGammaValueOnly(camera):
    gammaNode = pointer(GENICAM_DoubleNode())
    gammaNodeInfo = GENICAM_DoubleNodeInfo()
    gammaNodeInfo.pCamera = pointer(camera)
    gammaNodeInfo.attrName = b"Gamma"

    nRet = GENICAM_createDoubleNode(byref(gammaNodeInfo), byref(gammaNode))
    if nRet != 0:
        print("❌ Gamma node not available.")
        return None

    val = c_double()
    nRet = gammaNode.contents.getValue(gammaNode, byref(val))
    gammaNode.contents.release(gammaNode)
    if nRet != 0:
        print("❌ Failed to read Gamma value.")
        return None
    return val.value
