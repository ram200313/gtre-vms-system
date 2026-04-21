import requests

url = "http://localhost:8000/api/login"
payload = {"username": "EMP02", "password": "GTRE123"}
r = requests.post(url, json=payload)
print(r.status_code, r.text)

payload2 = {"username": "1234", "password": "123"} # assuming password was 123... wait, they didn't specify. but let's test EMP02 first.
