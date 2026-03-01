import cv2
import numpy as np
import urllib.request
import os

try:
    urllib.request.urlretrieve("https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg", "lena.jpg")
    urllib.request.urlretrieve("https://raw.githubusercontent.com/opencv/opencv/master/samples/data/messi5.jpg", "messi.jpg")
except:
    pass

if os.path.exists("lena.jpg") and os.path.exists("messi.jpg"):
    img1 = cv2.imread("lena.jpg", cv2.IMREAD_COLOR)
    img2 = cv2.imread("messi.jpg", cv2.IMREAD_COLOR)

    img1 = cv2.resize(img1, (300, 300))
    img2 = cv2.resize(img2, (300, 300))
    
    # Same person translated slightly
    img3 = np.roll(img1, shift=(15, 15), axis=(0, 1))

    def compare_hists(i1, i2):
        i1_f = i1[60:240, 60:240]
        i2_f = i2[60:240, 60:240]
        
        h1 = cv2.cvtColor(i1_f, cv2.COLOR_BGR2HSV)
        h2 = cv2.cvtColor(i2_f, cv2.COLOR_BGR2HSV)
        
        hist1 = cv2.calcHist([h1], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        
        hist2 = cv2.calcHist([h2], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        
        dist = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
        return 1.0 - dist

    print(f"Diff person score: {compare_hists(img1, img2)}")
    print(f"Same person score: {compare_hists(img1, img3)}")
    print(f"Exact same score: {compare_hists(img1, img1)}")
else:
    print("No images downloaded")
