import cv2
import os

base_path = os.environ['CAPSTONE_DIR'] # /home/picapstone-project
img_path = os.path.join(base_path,'IMG/roiPic/1.jpg')

img = cv2.imread(img_path,1)
cv2.imshow('img',img)

key = cv2.waitKey(0)
if key == 27:
	cv2.destroyAllWindows()

