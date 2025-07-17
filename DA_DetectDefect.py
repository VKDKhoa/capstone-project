import cv2
import numpy as np
#Can be update to detect scratch

def create_Mask(kernel_size,kernel_sizeblur,lower,upper,iteration,area):
    mask = {
        "kernel_size": kernel_size,
        "kernel_blur": (kernel_sizeblur,kernel_sizeblur),
        "lp": lower,
        "up": upper,
        "kernel_matrix": np.ones((kernel_size, kernel_size), np.uint8),
        "iteration": iteration,
        "Area2Detect": area
    }
    return mask

def PreProcess(frame,mask):
    blur = cv2.GaussianBlur(frame,mask['kernel_blur'],0)
    thresh = cv2.inRange(blur,mask['lp'],mask['up'])
    #cv2.imshow("mask",thresh)
    thresh_eroision = cv2.erode(thresh,mask['kernel_matrix'],mask['iteration'])
    #thresh_dialation = cv2.dilate(thresh_eroision,mask['kernel_blur'],mask['iteration'])
    return thresh_eroision

# currently working perfect at record, record1, record3, missing one error at record 2 
def DetectDefection(frame,isDefected):
    #bgr_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    #hsv_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
    
    MASK_LISK = [
         create_Mask(13,3,128,150,1,500),
    #    create_Mask(13,3,[53,7,65],[143,163,138],1,500),
    #    create_Mask(11,3,[53,7,65],[143,163,173],1,500),
    #    create_Mask(11,3,[53,7,65],[143,163,150],1,350),
     ] 
    #applying each mask to detect defect
    for msk in MASK_LISK:
        maskDefection = PreProcess(frame,msk) #edit from frame to hsv_frame
        #find contours for defect area
        contours,_ = cv2.findContours(maskDefection,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        #cv2.imshow("maskDefecttion",maskDefection)
        #cv2.drawContours(frame,contours,-1,(0,0,255),2)
        if not isDefected:
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if msk['Area2Detect'] < area < 10000: #mask[1] fit with 400
                    x,y,w,h = cv2.boundingRect(cnt) #only get the first defect area 
                    cv2.rectangle(frame,(x-10,y-10),(x+w+10,y+h+10),(0,0,255),2) #rectangle for defect area
                    cv2.rectangle(frame,(x-10,y-30),(x+w+40,y-10),(0,0,255),-1) #background for text
                    cv2.putText(frame,"Defected",(x-10,y-15),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2) #text for defect area
                #cv2.drawContours(frame,[cnt],0,(0,0,255),-1)
                    isDefected = True
                #cv2.drawContours(frame,[cnt],-1,(0,0,255),2)    
        if isDefected:
            break
    return isDefected
