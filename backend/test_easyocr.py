import sys
sys.path.insert(0, './ocr')
import easyocr
import os
import glob

# Get the latest image in uploads
list_of_files = glob.glob('../uploads/*.jpg')
latest_file = max(list_of_files, key=os.path.getctime)

print(f"Reading {latest_file}...")
reader = easyocr.Reader(['en'], gpu=False, verbose=False)
res = reader.readtext(latest_file, detail=1)

for bbox, text, prob in res:
    y_center = sum([pt[1] for pt in bbox]) / len(bbox)
    print(f"Y: {y_center:.1f} | Text: {text} | Prob: {prob:.2f}")

