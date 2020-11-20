import cv2
import numpy as np

qr_detector = cv2.QRCodeDetector()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 10)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
cap.set(cv2.CAP_PROP_FOCUS, 128)
cap.set(cv2.CAP_PROP_EXPOSURE, 128)
#cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc('M','J','P','G'))
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)


print("Starting Camera")
i = 0
focus = 128
exposure = 128
toggle_qr = False

def draw_qr_detection(img, pts, data):
    pts = np.int32(pts).reshape(-1,2)
    
    for j in range(pts.shape[0]):
        cv2.line(img, tuple(pts[j]), tuple(pts[(j+1) % pts.shape[0]]), (0, 255, 0), 5)
    
    for j in range(pts.shape[0]):
        cv2.circle(img, tuple(pts[j]), 10, (0, 0, 255), -1)
        
    image = cv2.putText(img, data, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   1, (255, 0, 0), 2, cv2.LINE_AA)

def read_qr(image):
    data, bbox, qr_code = qr_detector.detectAndDecode(image)

    if len(data) > 0:
        draw_qr_detection(image, bbox, data)
    
    

while True:
    ret, frame = cap.read()
    
    if toggle_qr:
        read_qr(frame)
    
    cv2.imshow('frame', frame)
    key = cv2.waitKey(1)
        
    if key == ord('q'):
        break
    
    if key == ord('s'):
        print('Frame {0:05d} saved'.format(i))
        cv2.imwrite('./frames/frame{0:05d}.jpg'.format(i), frame)
        i += 1
    
    if key == ord('t'):
        toggle_qr = not toggle_qr
    
    if key == ord('d'):
        if focus - 5 > 0:
            focus = focus - 5
            cap.set(cv2.CAP_PROP_FOCUS, focus)
        print('Focus: ' + str(focus))
    
    if key == ord('f'):
        if focus + 5 < 255:
            focus = focus + 5
            cap.set(cv2.CAP_PROP_FOCUS, focus)
        print('Focus: ' + str(focus))
    
    if key == ord('w'):
        if exposure - 5 > 0:
            exposure = exposure - 5
            cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        print('Exposure: ' + str(exposure))
    
    if key == ord('e'):
        if exposure + 5 < 255:
            exposure = exposure + 5
            cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        print('Exposure: ' + str(exposure))
        
    if key == ord('i'):
        print('Shape: ' + str(frame.shape))
    

print("Terminating Program!")
cap.release()
cv2.destroyAllWindows()