import cv2
import numpy as np

def test_orb():
    # Create two random noisy images to represent different faces/noise
    img1 = np.random.randint(0, 256, (300, 300), dtype=np.uint8)
    img2 = np.random.randint(0, 256, (300, 300), dtype=np.uint8)

    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    
    if des1 is None or des2 is None:
        print("no descriptors")
        return

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    print("Total matches without distance filter:", len(matches))
    score_unfiltered = len(matches) / max(len(kp1), len(kp2), 1)
    print("Unfiltered naive score:", score_unfiltered)
    
    good_matches = [m for m in matches if m.distance < 60]
    print("Good matches (<60):", len(good_matches))
    score_filtered = len(good_matches) / max(len(kp1), len(kp2), 1)
    print("Filtered score:", score_filtered)
    
    # Let's test two identical images translated slightly
    img3 = np.roll(img1, shift=(5, 5), axis=(0, 1))
    kp3, des3 = orb.detectAndCompute(img3, None)
    matches3 = bf.match(des1, des3)
    good_matches3 = [m for m in matches3 if m.distance < 60]
    score_filtered3 = len(good_matches3) / max(len(kp1), len(kp3), 1)
    print("Filtered score (translated same image):", score_filtered3)

test_orb()
