import cv2
import numpy as np
def test():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    img1 = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    img2 = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    recognizer.train([img1], np.array([1]))
    label, confidence = recognizer.predict(img2)
    print('Diff images:', label, confidence)
    label, confidence = recognizer.predict(img1)
    print('Same image:', label, confidence)
test()