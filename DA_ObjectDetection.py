import cv2
import numpy as np
import threading
class ContourProcessor(threading.Thread):
    def __init__(self, contours, frame):
        super().__init__()
        self.contours = contours
        self.frame = frame
        self.result_roi = None
        self.found = False

    def run(self):
        for cnt in self.contours:
            area = cv2.contourArea(cnt)
            print("Contour area:", area)

            if self.found:
                break

            if area > 1010000:
                self.result_roi = self.frame.copy()
                self.found = True
                break

#Run correctly - complete check at 10/03/2025
class Object:
    def __init__(self,roi, isObject, isDefected, frame):
        self.isObject = isObject #boolean to know there is object in frame
        self.roi = roi #ROI of object
        self.isDefected = isDefected #boolean to know the QR label is defected
        self.frame = frame #frame of object
    
    def update_roi(self, roi): #to upadte roi
        self.roi = roi
        return self.roi
    
    def update_isObject(self, isObject): #to update isObject
        self.isObject = isObject
        return self.isObject
    
    def update_isDefect(self, isDefect): #to update isDefect
        self.isDefected = isDefect
        return self.isDefected
    #Detect and capture the IMG (as a matrix) of object
    #### old code ######
    def DetectAndCaptureObject(self):
        Fx, Fy = self.frame.shape #heigh of frame
        #print('y:', Fy)
        kernel_size = 21  # best with frame[90:480, 110:510]
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        gray_frame = self.frame
    #    display_gray_frame = cv2.resize(gray_frame,(300,300),interpolation=cv2.INTER_AREA)
    #    cv2.imshow("gray", display_gray_frame)
    #    blur_frame = cv2.GaussianBlur(gray_frame, (kernel_size, kernel_size), 0)
        _, thresh = cv2.threshold(gray_frame, 120, 255, cv2.THRESH_BINARY)
    #    thresh = cv2.inRange(gray_frame,128,255)
        dilated_frame = cv2.dilate(thresh, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        contour_thread = ContourProcessor(contours, self.frame)
        contour_thread.start()
        contour_thread.join(timeout=0.01) 
        
        if contour_thread.found:
            self.roi = contour_thread.result_roi
            self.isObject = True
    #   display_dialate_frame = cv2.resize(dilated_frame,(300,300),interpolation=cv2.INTER_AREA)
    #    cv2.imshow("Dilated", display_dialate_frame)
    #    #print(len(contours))
    #    i = 0
    #    cv2.drawContours(display_gray_frame, contours, -1, (255,255,255), -1)
    #   for cnt in contours:
    #       area = cv2.contourArea(cnt)
    #       print(area)
    #        if self.isObject:
    #            break
    #        if area > 1009000:
    #          print(area)
    #            self.roi = self.frame
    #            self.isObject = True
    #            break
    #               # cv2.imwrite(f'IMG/{i}.jpg', roi)
            return self.roi

