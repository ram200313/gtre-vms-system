import jwt
import time
import requests
import base64

SECRET_KEY = "gtre_vms_super_secret_offline_key"
ALGORITHM = "HS256"

token = jwt.encode({"role": "reception", "exp": int(time.time()) + 3600}, SECRET_KEY, algorithm=ALGORITHM)

with open("backend/lena.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "idBase64": "data:image/jpeg;base64," + img_b64,
    "rawText": ""
}

start = time.time()
r = requests.post(f"http://127.0.0.1:8000/api/visitors/123/capture_id?token={token}", json=payload)
print(f"Status Code: {r.status_code}")
print(f"Time taken: {time.time() - start:.2f}s")
try:
    print(r.json())
except Exception as e:
    print("Response text:", r.text)
