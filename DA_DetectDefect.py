import cv2
import numpy as np
#Can be update to detect scratch
# Upadte:  06/08/2025
# pass 95% record detect


def create_Mask(kernel_size: int,kernel_sizeblur,lower: int,upper: int,iteration: int,area: float,maxArea: float) -> dict:
    mask = {
        "kernel_size": kernel_size,
        "kernel_blur": (kernel_sizeblur,kernel_sizeblur),
        "lp": np.array(lower),
        "up": np.array(upper),
        "kernel_matrix": np.ones((kernel_size, kernel_size), np.uint8),
        "iteration": iteration,
        "MinArea2Detect": area,
        "MaxAreaDefect": maxArea
    }
    return mask

def PreProcess(frame: np.ndarray, mask: list[int],i: int) -> np.ndarray:
    #cv2.imshow(f"frame before process",cv2.resize(frame,(300,300)))
    
    thresh = cv2.inRange(frame,mask['lp'],mask['up'])
    #_, thresh = cv2.threshold(blur, 40, 255, cv2.THRESH_BINARY)
    #cv2.imshow(f"thresh at mask {i}",cv2.resize(thresh,(300,300)))
    
    thresh_eroision = cv2.erode(thresh,mask['kernel_matrix'],mask['iteration'])
    # cv2.imshow(f"thresh eroision at mask {i}",cv2.resize(thresh_eroision,(300,300)))
    # cv2.waitKey(1)
    #thresh_dialation = cv2.dilate(thresh_eroision,mask['kernel_blur'],mask['iteration'])
    return thresh_eroision

# currently working perfect at record, record1, record3, missing one error at record 2 
def DetectDefection(frame: np.ndarray, isDefected: bool) -> bool:
    
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) if(len(frame.shape) > 2) else frame
    # base on testing, lp = 30, up = 50, size = 11,
    MASK_LISK: list[dict] = [
        create_Mask(11,3,30,70,1,19000,22000),
        create_Mask(21,3,30,70,1,16000,18990),
    ] 
    #applying each mask to detect defect
    for index,msk in enumerate(MASK_LISK):
        maskDefection = PreProcess(frame,msk,index) #edit from frame to hsv_frame
        #find contours for defect area
        contours,_ = cv2.findContours(maskDefection,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"=== mask {index} =====")
        if not isDefected:
            for cnt in contours:
                area = cv2.contourArea(cnt)
                #if area > 3000:
                #    x,y,w,h = cv2.boundingRect(cnt)
                #    cv2.putText(frame,str(area),(x-30,y-15),
                #               cv2.FONT_HERSHEY_SIMPLEX,
                #                fontScale=2.3,
                #               color=255,
                #               thickness=6) #text for defect area
                #print("Area: ",area)
                if (msk['MinArea2Detect'] < area < msk['MaxAreaDefect']): #mask[1] fit with 400
                    #print(f"[DEBUG] Found contour with area = {area}, required ({msk['MinArea2Detect']},{msk['MaxAreaDefect']})")
                    x,y,w,h = cv2.boundingRect(cnt) #only get the first defect area 
                    cv2.rectangle(frame,(x-10,y-10),(x+w+50,y+h+50),0,12) #rectangle for defect area
                    cv2.rectangle(frame,(x-30,y-15),(x+w+90,y-80),0,-1) #background for text
                    cv2.putText(frame,"Defected: " + str(area),(x-30,y-15),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=2.3,
                                color=255,
                                thickness=6) #text for defect area
                    #cv2.drawContours(frame,[cnt],0,0,-1)
                    return True
                #cv2.drawContours(frame,[cnt],-1,(0,0,255),2)    
    isDefected = False
    return isDefected

# test the function
def main():
    import matplotlib.pyplot as plt
    import os

    # Đường dẫn ảnh test
    i = 10
    image_path = f'CREVIS_IMG/extractFrame/QR_Product_num_{i}.jpg' 
    if not os.path.exists(image_path):
        print(f"No img found: {image_path}")
        return

    frame = cv2.imread(image_path)
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) if len(frame.shape) > 2 else frame

    isDefect = False
    isDefect:bool = DetectDefection(frame, isDefect)
    if(isDefect): print("isDefect")
    else: print("not defect")
    cv2.imshow("frame res: ", cv2.resize(frame,(300,300)))
    if(cv2.waitKey(0) == 27): cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
