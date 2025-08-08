import cv2
import numpy as np

#Run correctly - complete check at 10/03/2025
class Object:
    def __init__(self,roi: np.ndarray, isObject: bool, isDefected: bool, frame: np.ndarray):
        self.isObject = isObject #boolean to know there is object in frame
        self.roi = roi #ROI of object
        self.isDefected = isDefected #boolean to know the QR label is defected
        self.frame = frame #frame of object

        #frame for display
        self.thresh = None #threshold frame
        self.gray_frame = None
        self.blur_frame = None
        self.dilated_frame = None

    def update_roi(self, roi: np.ndarray) -> np.ndarray: #to upadte roi
        self.roi = roi
        return self.roi
    
    def update_isObject(self, isObject: bool) -> bool: #to update isObject
        self.isObject = isObject
        return self.isObject
    
    def update_isDefect(self, isDefect: bool): #to update isDefect
        self.isDefected = isDefect
        return self.isDefected
    
    #Detect and capture the IMG (as a matrix) of object
    @staticmethod
    def DetectAndCaptureObject(frame: np.ndarray) -> np.ndarray:
        Fy: int = frame.shape[0] #heigh of frame
        #print("Frame shape: ", frame.shape)
        kernel_size: int = 51  
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        # pre process the frame
        gray_frame: np.ndarray = frame
        blur_frame: np.ndarray = cv2.GaussianBlur(gray_frame, (kernel_size, kernel_size), 0)
        _, thresh = cv2.threshold(blur_frame, 40, 255, cv2.THRESH_BINARY)
        dilated_frame: np.ndarray = cv2.dilate(thresh, kernel, iterations=2)
        #cv2.imshow("dialated",cv2.resize(dilated_frame,(500,500)))
        #find contours in the dilated frame
        contours, _ = cv2.findContours(dilated_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #cv2.imshow("Dilated", dilated_frame)
        minArea_ratio: float = 0.550
        maxArea_ratio: float = 0.600
        posMin_ratio: float = 0.958
        posMax_ratio: float = 1.620
        for cnt in contours:
            area: float = cv2.contourArea(cnt)
            #print(area)
            if frame.shape[0]*frame.shape[1]*minArea_ratio < area < frame.shape[0]*frame.shape[1]*maxArea_ratio:
                print("Area ratio available: ",area / (frame.shape[0]*frame.shape[1]))
                M = cv2.moments(cnt)
                Cy: int = int(M['m10'] / M['m00']) #y center of object
                #print("pos ", Cy / (Fy / 2), ",Area ratio = ", area / (frame.shape[0]*frame.shape[1]))
                if 0.958 < Cy / (Fy / 2) <  1.820: # to confrim that object is in the middle of frame
                    #print("pos ", Cy / (Fy / 2), "Area: ", area)
                    x, y, w, h = cv2.boundingRect(cnt) # create rectangle: x,y is first coordinate angle, w and h is width and heigh respectively
                    print("Both Area and pos is available ", Cy / (Fy / 2), ",Area ratio = ", area / (frame.shape[0]*frame.shape[1]))
                    roi: np.ndarray = frame.copy() #create ROI object
                    roi = roi[y:y+h,x:x+w]
                    print("object roi save success")
                    return roi #return the ROI
                else:
                    print(f"pos not available ({posMin_ratio:f},{posMax_ratio:f}): current pos: {Cy / (Fy / 2)}")
            
            elif frame.shape[0]*frame.shape[1]*0.4 < area < frame.shape[0]*frame.shape[1]*0.7:
                cur_ratio: float = area / (frame.shape[0]*frame.shape[1])
                print(f"Area ratio not in range({minArea_ratio:f},{maxArea_ratio:f}), current_ratio = {cur_ratio:f}")

                    # cv2.imwrite(f'IMG/{i}.jpg', roi)
        return np.array([])  # if no object found, return empty array
#test the class
def main():
    import matplotlib.pyplot as plt
    i = 0
    image_path = f'CREVIS_IMG/extractFrame/QR_Product_num_{i}.jpg'
    frame = cv2.imread(image_path)
    #frame = frame[90:480, 120:510]  # Cắt ảnh như hệ thống thực tế

    obj = Object(roi=None, isObject=False, isDefected=False, frame=frame)
    obj.DetectAndCaptureObject()  # Gọi hàm đã có trong class

    # show image
    plt.figure(figsize=(10, 7))  # lớn hơn chút cho 2 hàng
    obj.frame = cv2.cvtColor(obj.frame, cv2.COLOR_BGR2RGB)
    plt.subplot(2, 3, 1)
    plt.title("Ảnh gốc")
    plt.imshow(obj.frame)
    
    plt.subplot(2, 3, 2)
    plt.title("Ảnh xám - Grayscale")
    plt.imshow(obj.gray_frame, cmap='gray')

    plt.subplot(2, 3, 3)
    plt.title("Ảnh mờ Gaussian - Gaussian Blur")
    plt.imshow(obj.blur_frame, cmap='gray')


    plt.subplot(2, 3, 5)
    plt.title("Ảnh giãn nở - Dilated transform")
    plt.imshow(obj.dilated_frame, cmap='gray')

    plt.subplot(2, 3, 4)
    plt.title("Ảnh nhị phân - Threshold")
    plt.imshow(obj.thresh, cmap='gray')

    plt.subplot(2, 3, 6)
    plt.title("Ảnh xử lý - ROI")
    if obj.roi is not None and obj.roi.size > 0:
        roi_resized = cv2.resize(obj.roi, (300, 300))  # Resize ROI for display
        plt.imshow(cv2.cvtColor(roi_resized, cv2.COLOR_BGR2RGB))
    else:
        plt.text(0.5, 0.5, "No ROI", ha="center", va="center")

    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    main()
