import urllib.request
import os

os.makedirs('frontend/js/tesseract', exist_ok=True)
files = {
    'tesseract.min.js': 'https://unpkg.com/tesseract.js@v5.1.1/dist/tesseract.min.js',
    'worker.min.js': 'https://unpkg.com/tesseract.js@v5.1.1/dist/worker.min.js',
    'tesseract-core-simd.wasm.js': 'https://unpkg.com/tesseract.js-core@v5.0.0/tesseract-core-simd.wasm.js',
    'eng.traineddata.gz': 'https://raw.githubusercontent.com/naptha/tessdata/gh-pages/4.0.0/eng.traineddata.gz'
}

for name, url in files.items():
    path = f"frontend/js/tesseract/{name}"
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        urllib.request.urlretrieve(url, path)
    else:
        print(f"Already have {name}")
print("Done!")
