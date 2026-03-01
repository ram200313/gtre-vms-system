import cv2
import numpy as np
def test():
    print('Testing haar faces...')
    img1 = np.ones((300, 300, 3), dtype=np.uint8) * 128
    img1[100:200, 100:200] = 200
    img2 = np.ones((300, 300, 3), dtype=np.uint8) * 128
    img2[100:200, 100:200] = 200
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    f1 = face_cascade.detectMultiScale(img1)
    print('faces:', f1)
test()