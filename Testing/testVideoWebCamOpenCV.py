import cv2

def initFrame():
    cap = cv2.VideoCapture('IMG/Video/record.mp4') # 0 is the camera number, is the camera API of linux - using when running on RASPBERRY PI
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) #resolution
    return cap

def main():
	cap = initFrame()
	if not cap.isOpened():
		print("Error: Unable to open video source.")
		return
	
	while True:
		ret, frame = cap.read()  # Corrected indentation with spaces
		cv2.imshow("Frame", frame)
		if cv2.waitKey(1) & 0xFF == 27:
			break
	
	cap.release()
	cv2.destroyAllWindows()
		
if __name__ == "__main__":
	main()
	
