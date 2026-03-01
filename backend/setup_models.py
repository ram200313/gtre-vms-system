import os
import urllib.request

os.makedirs('models', exist_ok=True)

openface_url = "https://storage.cmusatyalab.org/openface-models/nn4.small2.v1.t7"
openface_path = "models/nn4.small2.v1.t7"

if not os.path.exists(openface_path):
    print(f"Downloading OpenFace model to {openface_path}...")
    try:
        urllib.request.urlretrieve(openface_url, openface_path)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download: {e}")
else:
    print("OpenFace model already exists.")
