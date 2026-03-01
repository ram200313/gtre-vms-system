import os
import sys
from main import MOCK_VISITORS_DB, UPLOAD_DIR, compare_faces
import base64
print('Mock DB:', len([v for v in MOCK_VISITORS_DB if v.get('status') == 'APPROVED']))
x = os.listdir(UPLOAD_DIR)
print('Uploads:', len(x))
if len(x) > 0:
    with open(os.path.join(UPLOAD_DIR, x[-1]), 'rb') as f:
        b64 = 'data:image/jpeg;base64,' + base64.b64encode(f.read()).decode('utf-8')
    sim = compare_faces(b64, b64)
    print('Self-similarity:', sim)
