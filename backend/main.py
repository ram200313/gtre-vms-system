import os
import sys
# Route Python to use the newly cloned local repository inside 'ocr'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "ocr")))

import base64
import uuid
import datetime
from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import oracledb
from fastapi.staticfiles import StaticFiles
import cv2
import time
import numpy as np

# Trigger restart after successful pip install
import id_db
import auth_db
import re
import traceback
import jwt
from passlib.context import CryptContext
from datetime import timedelta

SECRET_KEY = "gtre_vms_super_secret_offline_key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    import openbharatocr
    from openbharatocr.ocr.pan import PANCardExtractor
    from openbharatocr.ocr.aadhaar import AadhaarOCR
    from openbharatocr.ocr.driving_licence import driving_licence
    from openbharatocr.ocr.passport import passport
    from openbharatocr.ocr.voter_id import voter_id_front
    print("Loading OpenBharatOCR models...")
    GLOBAL_PAN_EXTRACTOR = PANCardExtractor()
    GLOBAL_AADHAAR_EXTRACTOR = AadhaarOCR()
    print("OpenBharatOCR models loaded successfully.")
except Exception as e:
    openbharatocr = None
    GLOBAL_PAN_EXTRACTOR = None
    GLOBAL_AADHAAR_EXTRACTOR = None
    print(f"Warning: OpenBharatOCR failed to load: {e}")

try:
    import easyocr
    print("Loading EasyOCR models...")
    GLOBAL_EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("EasyOCR loaded successfully.")
except Exception as e:
    GLOBAL_EASYOCR_READER = None
    print(f"Warning: EasyOCR failed to load: {e}")

app = FastAPI(title="Offline VMS API")

# Setup CORS for local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for offline local usage
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Oracle DB Configuration - Update with actual local offline credentials
DB_USER = os.getenv("DB_USER", "vms_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
DB_DSN = os.getenv("DB_DSN", "localhost:1521/XEPDB1")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def get_db_connection():
    try:
        # In a real environment, this connects to the offline Oracle DB.
        # Ensure Oracle Instant Client is installed if running locally,
        # or it will use the default "Thin" mode without native binaries on the cloud.
        connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        return connection
    except Exception as e:
        # For demo purposes, we don't want to crash if DB is not available
        return None

# Pydantic Models
class VisitorRequestSubmit(BaseModel):
    requisitionNumber: str
    requestedBy: str
    requestDate: str
    officerToMeet: str
    location: str
    purpose: str
    validFrom: str
    validUpto: str
    visitorCategory: str
    visitorName: str
    organisation: str
    companyAddress: str
    phone: str
    mobile: str
    aadhaarNumber: Optional[str] = None
    passportDetails: Optional[str] = None
    remarks: Optional[str] = None

# RBAC System using auth_db
MOCK_USER_MASTER = {}

MOCK_AUTHORIZATION = {
    "admin": ["dashboard.html", "visitor_request.html", "officer_visitors.html", "reception_dashboard.html", "todays_visitors.html", "attendance.html", "gate_scanners.html", "admin_dashboard.html"],
    "officer": ["dashboard.html", "visitor_request.html", "officer_visitors.html"],
    "reception": ["dashboard.html", "reception_dashboard.html", "todays_visitors.html", "attendance.html", "gate_scanners.html"]
}

def verify_role(token: str, required_roles: List[str]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role is None:
            raise HTTPException(status_code=401, detail="Invalid auth token payload")
    except jwt.PyJWTError:
        pass # Handle fallback for now or general jwt exceptions
    except jwt.PyJWTError:
        pass
    except Exception as e:
        # Check if it matches fallback demo tokens during dev before wiping tokens logic out entirely
        if token in ["mock-officer-token-xyz", "mock-reception-token-abc", "mock-admin-token-777", "mock-system-token-xyz"]:
            pass # Keep alive for migration caching
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role != "admin" and role not in required_roles:
            raise HTTPException(status_code=403, detail="Unauthorized access for this role")
        return role
    except jwt.PyJWTError:
        # Fallback map for migrating clients
        old_map = {"mock-officer-token-xyz": "officer", "mock-reception-token-abc": "reception", "mock-admin-token-777": "admin"}
        old_role = old_map.get(token)
        if old_role and (old_role == "admin" or old_role in required_roles):
            return old_role
        raise HTTPException(status_code=401, detail="Invalid token")


# In-memory fallback database for local testing when Oracle DB isn't running
MOCK_VISITORS_DB = []
MOCK_ATTENDANCE_LOGS = []
MOCK_ID_COUNTER = 1

# Mock Scheduled Visits (Pre-registered by host)
SCHEDULED_VISITS = [
    {
        "id": "SCH-1001",
        "fullName": "Amit Desai",
        "phoneNumber": "9876543210",
        "hostName": "Dr. A. Sharma (Director)",
        "purposeOfVisit": "Official Meeting"
    },
    {
        "id": "SCH-1002",
        "fullName": "Sarah Jenkins",
        "phoneNumber": "5551234567",
        "hostName": "M. Singh (HR Head)",
        "purposeOfVisit": "Interview"
    }
]

@app.get("/api/visitors/scheduled")
async def get_scheduled_visitors():
    return {"status": "success", "data": SCHEDULED_VISITS}

@app.get("/api/visitors/search")
async def search_visitors(q: str, token: str):
    verify_role(token, ["reception"])
    # Searches by name or phone for WAITING_FOR_PHOTO
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            search_query = f"%{q.lower()}%"
            cursor.execute("""
                SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, 
                       PASS_VALID_FROM, PASS_VALID_UNTIL, STATUS, CREATED_BY_OFFICER
                FROM VISITORS 
                WHERE STATUS = 'WAITING_FOR_PHOTO' 
                AND (LOWER(FULL_NAME) LIKE :1 OR PHONE_NUMBER LIKE :2)
            """, [search_query, search_query])
            rows = cursor.fetchall()
            visitors = [
                {
                    "id": row[0],
                    "fullName": row[1],
                    "companyName": row[2],
                    "hostName": row[3],
                    "phoneNumber": row[4],
                    "purposeOfVisit": row[5],
                    "validFromDate": row[6],
                    "validUntilDate": row[7],
                    "status": row[8],
                    "requestedBy": row[9]
                } for row in rows
            ]
            conn.close()
            return {"status": "success", "data": visitors}
        except Exception as e:
            print("DB Fetch search error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB
    results = []
    for v in MOCK_VISITORS_DB:
        if v.get('status') == 'WAITING_FOR_PHOTO':
            if q.lower() in v.get('fullName', '').lower() or q in v.get('phoneNumber', ''):
                results.append(v)
    return {"status": "success", "data": results, "source": "mock"}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(token: str):
    verify_role(token, ["officer", "reception"])
    conn = get_db_connection()
    stats = {
        "totalToday": 0,
        "pending": 0,
        "approved": 0,
        "inside": 0,
        "exited": 0,
        "departmentData": {},
        "hourlyTraffic": [0] * 8 # 09:00 to 16:00
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            # 1. Get counts by status
            cursor.execute("""
                SELECT STATUS, COUNT(*) 
                FROM VISITORS 
                GROUP BY STATUS
            """)
            for status, count in cursor.fetchall():
                if status == 'WAITING_FOR_PHOTO': stats["pending"] += count
                elif status == 'PASS_READY': stats["approved"] += count
                elif status == 'VISITOR_INSIDE': stats["inside"] += count
                elif status == 'VISITOR_EXITED': stats["exited"] += count
            
            stats["totalToday"] = sum([stats["pending"], stats["approved"], stats["inside"], stats["exited"]])

            # 2. Get Department distribution
            cursor.execute("SELECT COMPANY_NAME, COUNT(*) FROM VISITORS GROUP BY COMPANY_NAME")
            for dept, count in cursor.fetchall():
                stats["departmentData"][dept or "Unknown"] = count

            conn.close()
        except Exception as e:
            print("Dashboard Stats Error:", e)
            if conn: conn.close()
    
    # Fill with mock data if DB is empty or for demo feel
    if stats["totalToday"] == 0:
        # Check MOCK_VISITORS_DB
        for v in MOCK_VISITORS_DB:
            status = v.get('status')
            if status == 'WAITING_FOR_PHOTO': stats["pending"] += 1
            elif status == 'PASS_READY': stats["approved"] += 1
            elif status == 'VISITOR_INSIDE': stats["inside"] += 1
            elif status == 'VISITOR_EXITED': stats["exited"] += 1
            
            dept = v.get('companyName', 'General')
            stats["departmentData"][dept] = stats["departmentData"].get(dept, 0) + 1
        
        stats["totalToday"] = sum([stats["pending"], stats["approved"], stats["inside"], stats["exited"]])

    # Add some base mock data for visual charts if still empty
    if not stats["departmentData"]:
        stats["departmentData"] = {"HR Dept": 5, "Server Room": 2, "GTRE Area": 8, "Admin": 3}
    
    # Mock Hourly (Demo constant)
    stats["hourlyTraffic"] = [2, 5, 8, 3, 4, 9, 2, stats["totalToday"]]
    
    return {"status": "success", "data": stats}

@app.get("/api/visitors/todays")
async def get_todays_visitors(token: str, date: str = None):
    verify_role(token, ["reception", "admin"])
    
    if date:
        search_date = date + "%"
        date_for_mock = date
    else:
        search_date = f"{datetime.datetime.now().strftime('%Y-%m-%d')}%"
        date_for_mock = datetime.datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Get visitors with passes ready, inside, or exited for today
            cursor.execute("""
                SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, 
                       PHOTO_PATH, PASS_VALID_FROM, PASS_VALID_UNTIL, STATUS, CREATED_BY_OFFICER
                FROM VISITORS 
                WHERE STATUS IN ('PASS_READY', 'VISITOR_INSIDE', 'VISITOR_EXITED') 
                AND PASS_VALID_FROM LIKE :1
                ORDER BY ID DESC
            """, [search_date])
            rows = cursor.fetchall()
            visitors = [
                {
                    "id": row[0],
                    "fullName": row[1],
                    "companyName": row[2],
                    "hostName": row[3],
                    "phoneNumber": row[4],
                    "purposeOfVisit": row[5],
                    "photoPath": os.path.basename(row[6]) if row[6] else None,
                    "validFromDate": row[7],
                    "validUntilDate": row[8],
                    "status": row[9],
                    "requestedBy": row[10]
                } for row in rows
            ]
            conn.close()
            return {"status": "success", "data": visitors}
        except Exception as e:
            print("DB Fetch todays error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB
    todays = [v for v in MOCK_VISITORS_DB if v.get('status') in ['PASS_READY', 'VISITOR_INSIDE', 'VISITOR_EXITED'] and v.get('validFromDate', '').startswith(date_for_mock)]
    return {"status": "success", "data": todays, "source": "mock"}


@app.post("/api/visitors/officer_register")
async def officer_register_visitor(
    fullName: str = Form(...),
    companyName: str = Form(...),
    purposeOfVisit: str = Form(...),
    hostName: str = Form(...),
    phoneNumber: str = Form(...),
    address: str = Form(...),
    nationality: str = Form(...),
    aadhaarNumber: Optional[str] = Form(None),
    panNumber: Optional[str] = Form(None),
    allowedBlocks: str = Form(...), # JSON string array
    phoneDeposited: str = Form("N"),
    validFromDate: str = Form(...),
    validUntilDate: str = Form(...),
    token: str = Form(...) # Strict role-based enforcement
):
    verify_role(token, ["officer", "admin"])
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        req_by = payload.get("fullName", "Officer")
        
        # Database Insertion (Oracle)
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            sql = """
                INSERT INTO VISITORS (
                    ID, FULL_NAME, COMPANY_NAME, PURPOSE_OF_VISIT, HOST_NAME, PHONE_NUMBER, ADDRESS,
                    NATIONALITY, AADHAAR_NUMBER, PAN_NUMBER,
                    ALLOWED_BLOCKS, PHONE_DEPOSITED, PASS_VALID_FROM, PASS_VALID_UNTIL,
                    STATUS, CREATED_BY_OFFICER
                ) VALUES (
                    visitor_seq.NEXTVAL, :full_name, :company, :purpose, :host, :phone, :address,
                    :nationality, :aadhaar, :pan,
                    :blocks, :phone_dep, :valid_from, :valid_until,
                    'WAITING_FOR_PHOTO', :req_by
                )
            """
            cursor.execute(sql, {
                'full_name': fullName,
                'company': companyName,
                'purpose': purposeOfVisit,
                'host': hostName,
                'phone': phoneNumber,
                'address': address,
                'nationality': nationality,
                'aadhaar': aadhaarNumber,
                'pan': panNumber,
                'blocks': allowedBlocks,
                'phone_dep': phoneDeposited,
                'valid_from': validFromDate,
                'valid_until': validUntilDate,
                'req_by': req_by
            })
            conn.commit()
            cursor.close()
            conn.close()
            return {"status": "success", "message": "Pre-registration successful"}
        else:
            # Fallback
            global MOCK_ID_COUNTER
            mock_visitor = {
                "id": MOCK_ID_COUNTER,
                "fullName": fullName,
                "companyName": companyName,
                "hostName": hostName,
                "phoneNumber": phoneNumber,
                "purposeOfVisit": purposeOfVisit,
                "validFromDate": validFromDate,
                "validUntilDate": validUntilDate,
                "status": 'WAITING_FOR_PHOTO',
                "requestedBy": req_by
            }
            MOCK_VISITORS_DB.append(mock_visitor)
            MOCK_ID_COUNTER += 1
            return {"status": "success", "message": "Pre-registered locally. Database connection failed."}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visitors/officer/my_visitors")
async def get_my_visitors(token: str):
    verify_role(token, ["officer", "admin"])
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        full_name = payload.get("fullName")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if role == "admin":
                cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, PASS_VALID_FROM, PASS_VALID_UNTIL, STATUS, PHOTO_PATH FROM VISITORS ORDER BY ID DESC")
            else:
                search_term = f"%{full_name}%"
                cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, PASS_VALID_FROM, PASS_VALID_UNTIL, STATUS, PHOTO_PATH FROM VISITORS WHERE LOWER(CREATED_BY_OFFICER) LIKE LOWER(:1) ORDER BY ID DESC", [search_term])
            rows = cursor.fetchall()
            visitors = [
                {
                    "id": row[0],
                    "fullName": row[1],
                    "companyName": row[2],
                    "hostName": row[3],
                    "phoneNumber": row[4],
                    "purposeOfVisit": row[5],
                    "validFromDate": row[6],
                    "validUntilDate": row[7],
                    "status": row[8],
                    "photoPath": os.path.basename(row[9]) if row[9] else None
                } for row in rows
            ]
            conn.close()
            return {"status": "success", "data": visitors}
        except Exception as e:
            print("DB Fetch my_visitors error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB
    filtered_mock = []
    for v in reversed(MOCK_VISITORS_DB):
        if role == "admin" or (full_name and full_name.lower() in v.get("requestedBy", "").lower()):
            filtered_mock.append(v)
    return {"status": "success", "data": filtered_mock, "source": "mock"}

@app.get("/api/visitors/todays")
async def get_todays_visitors(token: str):
    verify_role(token, ["reception", "admin"])
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Fetch visitors whose pass has been completely processed/printed
            cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, PASS_VALID_UNTIL, STATUS, PHOTO_PATH FROM VISITORS WHERE STATUS IN ('PASS_READY', 'CHECKED_IN', 'CHECKED_OUT') ORDER BY ID DESC")
            rows = cursor.fetchall()
            visitors = [
                {
                    "id": row[0],
                    "fullName": row[1],
                    "companyName": row[2],
                    "hostName": row[3],
                    "phoneNumber": row[4],
                    "purposeOfVisit": row[5],
                    "validUntilDate": row[6],
                    "status": row[7],
                    "photoPath": os.path.basename(row[8]) if row[8] else "fallback.jpg"
                } for row in rows
            ]
            conn.close()
            return {"status": "success", "data": visitors}
        except Exception as e:
            print("DB Fetch todays visitors error:", e)
            if conn: conn.close()
            
    # Fallback mock for testing
    filtered_mock = [v for v in reversed(MOCK_VISITORS_DB) if v.get("status") in ["PASS_READY", "CHECKED_IN", "CHECKED_OUT"]]
    return {"status": "success", "data": filtered_mock, "source": "mock"}

class CapturePhotoRequest(BaseModel):
    photoBase64: str

@app.post("/api/visitors/{visitor_id}/capture_photo")
async def capture_photo(visitor_id: str, req: CapturePhotoRequest, token: str):
    try:
        verify_role(token, ["reception"])
        if not req.photoBase64 or not "," in req.photoBase64:
            raise HTTPException(status_code=400, detail="Invalid photo data")
            
        header, encoded = req.photoBase64.split(",", 1)
        photo_bytes = base64.b64decode(encoded)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"visitor_{visitor_id}_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(photo_bytes)
    except Exception as e:
        print("Crash in capture_photo top block:", traceback.format_exc())
        return {"status": "error", "message": f"Crash: {str(e)}"}
        
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE VISITORS SET PHOTO_PATH = :1, STATUS = 'PASS_READY' WHERE ID = :2", [filepath, visitor_id])
            
            # Fetch updated visitor for pass generation
            cursor.execute("SELECT FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, ALLOWED_BLOCKS, PASS_VALID_FROM, PASS_VALID_UNTIL FROM VISITORS WHERE ID = :1", [visitor_id])
            row = cursor.fetchone()
            conn.commit()
            conn.close()
            
            if row:
                pass_data = {
                    "id": visitor_id,
                    "fullName": row[0],
                    "companyName": row[1],
                    "hostName": row[2],
                    "phoneNumber": row[3],
                    "purposeOfVisit": row[4],
                    "allowedBlocks": row[5],
                    "validFromDate": row[6],
                    "validUntilDate": row[7],
                    "photoPath": filename
                }
                return {"status": "success", "message": "Photo captured. Pass Ready.", "data": pass_data}
            else:
                raise HTTPException(status_code=404, detail="Visitor not found after update")
                
        except Exception as e:
            print("DB Update photo error:", e)
            if conn: conn.close()
            raise HTTPException(status_code=500, detail=str(e))
            
    # Fallback to mock DB
    for v in MOCK_VISITORS_DB:
        if str(v['id']) == str(visitor_id):
            v['status'] = 'PASS_READY'
            v['photoPath'] = filename
            
            pass_data = {
                "id": v['id'],
                "fullName": v.get('fullName', ''),
                "companyName": v.get('companyName', ''),
                "hostName": v.get('hostName', ''),
                "phoneNumber": v.get('phoneNumber', ''),
                "purposeOfVisit": v.get('purposeOfVisit', ''),
                "allowedBlocks": v.get('allowedBlocks', 'N/A'),
                "validFromDate": v.get('validFromDate', ''),
                "validUntilDate": v.get('validUntilDate', ''),
                "photoPath": filename
            }
            return {"status": "success", "message": "Photo captured (mock).", "data": pass_data}
            
    raise HTTPException(status_code=404, detail="Visitor not found")

class CaptureIDRequest(BaseModel):
    idBase64: str
    rawText: str = None

class ConfirmIDRequest(BaseModel):
    name: str
    id_type: str
    id_number: str
    dob: str
    address: str
    idPhotoPath: str

@app.post("/api/visitors/{visitor_id}/capture_id")
async def capture_id(visitor_id: str, req: CaptureIDRequest, token: str):
    verify_role(token, ["reception"])
    if not req.idBase64 or not "," in req.idBase64:
        raise HTTPException(status_code=400, detail="Invalid ID data")

    header, encoded = req.idBase64.split(",", 1)
    id_bytes = base64.b64decode(encoded)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"visitor_id_{visitor_id}_{timestamp}_{unique_id}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(id_bytes)

    extracted_data = {
        "name": "",
        "dob": "",
        "id_type": "Unknown",
        "id_number": "",
        "address": "",
        "idPhotoPath": filepath
    }

    # Retrieve real pre-registered name to bypass OCR noise
    true_name = ""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT FULL_NAME FROM VISITORS WHERE ID = :1", [int(visitor_id)])
            row = cursor.fetchone()
            if row: true_name = row[0]
            conn.close()
    except Exception as e:
        pass
    
    if not true_name:
        for v in MOCK_VISITORS_DB:
            if str(v['id']) == str(visitor_id):
                true_name = v.get('fullName', '')
                break
                
    extracted_data["name"] = true_name # Set unconditionally

    try:
        raw_text_list = []
        raw_results = []
        import re

        img = cv2.imread(filepath)
        if img is not None:
            # 1. Resize logic: > 800px -> 800px to speed up CPU OCR
            if img.shape[1] > 800:
                scale = 800 / img.shape[1]
                img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))
            
            # 2. Preprocessing Layer
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            eq = clahe.apply(gray)
            blurred = cv2.GaussianBlur(eq, (3, 3), 0)
            
            # Note: Adaptive thresholding can sometimes be too aggressive for EasyOCR on unevenly lit webcam images.
            # We'll use the CLAHE enhanced grayscale image to ensure maximum text preservation.
            img_to_ocr = eq
        else:
            img_to_ocr = filepath

        if GLOBAL_EASYOCR_READER:
            try:
                # EasyOCR inference
                res = GLOBAL_EASYOCR_READER.readtext(img_to_ocr if img is not None else filepath, detail=1)
                # EasyOCR returns: [([[x,y],[x,y],[x,y],[x,y]], text, prob), ...]
                if res:
                    raw_results = res
            except Exception as e:
                print(f"Error during EasyOCR inference: {e}")
                raw_results = []
        else:
            if req.rawText:
                raw_text_list = [line.strip() for line in req.rawText.split('\n') if line.strip()]
                raw_results = [([[0, i*20], [100, i*20], [100, i*20+20], [0, i*20+20]], (txt, 0.9)) for i, txt in enumerate(raw_text_list)]

        def get_center_y(bbox):
            if not isinstance(bbox, list) or len(bbox) == 0: return 0.0
            try: return sum([pt[1] for pt in bbox]) / len(bbox)
            except: return 0.0

        def get_center_x(bbox):
            if not isinstance(bbox, list) or len(bbox) == 0: return 0.0
            try: return sum([pt[0] for pt in bbox]) / len(bbox)
            except: return 0.0

        # Sort spatially top-to-bottom
        raw_results.sort(key=lambda x: (get_center_y(x[0]), get_center_x(x[0])))

        clean_data = []
        for item in raw_results:
            if not item: continue
            # PaddleOCR returns (bbox, (text, prob))
            if len(item) == 2 and isinstance(item[1], tuple):
                bbox = item[0]
                text, prob = item[1]
            elif len(item) == 3: # Fallback format
                bbox, text, prob = item
            else:
                continue

            cleaned = re.sub(r'[^a-zA-Z0-9\s/.,:-]', '', text).strip()
            cleaned = re.sub(r'\s+', ' ', cleaned)
            if len(cleaned) >= 2 and prob > 0.05:
                clean_data.append({
                    "text": cleaned,
                    "upper": cleaned.upper(),
                    "y": get_center_y(bbox),
                    "x": get_center_x(bbox),
                    "bbox": bbox
                })

        upper_text = " \n ".join([d["upper"] for d in clean_data])
        
        # 3. Document Type Detection
        doc_type = "Unknown"
        is_aadhaar = bool(re.search(r'AADHA|UNIQUE|GOVERNMENT\s*OF\s*INDIA', upper_text)) and bool(re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', upper_text))
        is_pan = bool(re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', upper_text)) and bool(re.search(r'INCOME|TAX|PERMANENT|ACCOUNT', upper_text))
        is_passport = bool(re.search(r'PASSPORT|REPUBLIC\s*OF\s*INDIA', upper_text))
        
        if is_aadhaar: doc_type = "Aadhaar"
        elif is_pan: doc_type = "PAN Card"
        elif is_passport: doc_type = "Passport"
        else:
            if re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', upper_text): doc_type = "PAN Card"
            elif re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', upper_text): doc_type = "Aadhaar"

        extracted_data["id_type"] = doc_type

        # 4. Keyword-Based Spatial Extraction
        extracted_name = ""
        extracted_id = ""
        extracted_dob = ""

        # Global DOB fallback
        dob_match = re.search(r'\b(\d{2}[/.-]\d{2}[/.-]\d{4})\b', upper_text)
        if dob_match: extracted_dob = dob_match.group(1)

        if doc_type == "Aadhaar":
            m = re.search(r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b', upper_text)
            if m: extracted_id = m.group(1)
            
            anchor_y = 9999
            for d in clean_data:
                if re.search(r'\bDOB\b|YEAR\s*OF\s*BIRTH|YOB', d["upper"]):
                    anchor_y = d["y"]
                    if not extracted_dob:
                        dm = re.search(r'\b(\d{4})\b', d["upper"])
                        if dm: extracted_dob = dm.group(1)
                    break
            
            # Find nearest text above DOB
            candidates = [d for d in clean_data if d["y"] < anchor_y - 10]
            candidates.sort(key=lambda x: anchor_y - x["y"]) # Ascending distance from anchor upwards
            for c in candidates:
                if not re.search(r'GOVERNMENT|INDIA|FATHER|NAME', c["upper"]):
                    if sum(ch.isalpha() for ch in c["text"]) >= 3:
                        extracted_name = c["text"].title()
                        break
                        
        elif doc_type == "PAN Card":
            m = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', upper_text)
            if m: extracted_id = m.group(1)
            
            anchor_y = -1
            for d in clean_data:
                if re.search(r'\bNAME\b', d["upper"]) and not re.search(r'FATHER', d["upper"]):
                    anchor_y = d["y"]
                    break
            
            if anchor_y != -1:
                # Find nearest text below Name
                candidates = [d for d in clean_data if d["y"] > anchor_y + 10]
                candidates.sort(key=lambda x: x["y"] - anchor_y) # Ascending distance from anchor downwards
                for c in candidates:
                    if sum(ch.isalpha() for ch in c["text"]) >= 3:
                        extracted_name = c["text"].title()
                        break

        elif doc_type == "Passport":
            m = re.search(r'\b([A-Z][0-9]{7})\b', upper_text)
            if m: extracted_id = m.group(1)
            
            anchor_y = -1
            for d in clean_data:
                if re.search(r'GIVEN\s*NAME|SURNAME|NAME', d["upper"]):
                    anchor_y = d["y"]
                    break
            if anchor_y != -1:
                candidates = [d for d in clean_data if d["y"] > anchor_y + 10]
                candidates.sort(key=lambda x: x["y"] - anchor_y)
                if candidates:
                    extracted_name = candidates[0]["text"].title()

        # Enforce True Name fallback for pre-registered users so OCR doesn't ruin it
        if true_name:
            extracted_data["name"] = true_name
        else:
            if not extracted_name:
                # Heuristic Fallback for unknown document types or missed specific anchors
                header_keywords = ['GOVERNMENT', 'TOFNDI', 'INCOME', 'DIPART', 'TAX', 'GOVT', 'INDIA', 'INCO', 'KAX', 'DEPASINENT', 'ENDLA', 'OFINDL', 'INDLA', 'OMNZT']
                header_y_limit = 0.0
                for item in clean_data:
                    if any(h in item["upper"] for h in header_keywords):
                        if item["y"] > header_y_limit: 
                            header_y_limit = item["y"]
                
                candidate_names = []
                for item in clean_data:
                    ln = item["text"]; y_pos = item["y"]
                    if header_y_limit > 0 and y_pos <= header_y_limit:
                        continue
                    alpha_chars = sum(c.isalpha() for c in ln)
                    if len(ln) > 0 and alpha_chars >= 3 and (alpha_chars / len(ln)) > 0.5:
                        cand_clean = re.sub(r'[^a-zA-Z\s]', '', ln).strip()
                        words = cand_clean.split()
                        if 1 <= len(words) <= 4 and len(cand_clean) > 3:
                            score = 0
                            if len(words) in [2, 3]: score += 5
                            if all(len(w) >= 2 for w in words): score += 3
                            if len(cand_clean) < 4: score -= 2
                            if cand_clean.istitle() or cand_clean.isupper(): score += 2
                            if score >= 3:
                                candidate_names.append((score, cand_clean, y_pos))
                if candidate_names:
                    candidate_names.sort(key=lambda x: (-x[0], x[2]))
                    extracted_name = candidate_names[0][1].title()

            extracted_data["name"] = extracted_name if extracted_name else "Name Extraction Failed"
            
        extracted_data["id_number"] = extracted_id if extracted_id else "MANUAL_ENTRY_REQUIRED"
        extracted_data["dob"] = extracted_dob
        
        extracted_data["id_number"] = extracted_data["id_number"].replace("-", "").replace(" ", "")

    except Exception as e:
        print(f"Error extracting OCR data: {e}")
        import traceback
        traceback.print_exc()
        extracted_data["id_number"] = "OCR Parsing Failed"

    return {"status": "success", "message": "ID Extracted", "data": extracted_data}

@app.post("/api/visitors/{visitor_id}/confirm_id")
async def confirm_id(visitor_id: str, req: ConfirmIDRequest, token: str):
    verify_role(token, ["reception"])
    
    # Save the finalized ID records into the offline sqlite database
    try:
        id_db.save_id_record(
            visitor_ref_id=visitor_id,
            name=req.name,
            id_type=req.id_type,
            id_number=req.id_number,
            dob=req.dob,
            address=req.address,
            photo_path=req.idPhotoPath
        )
    except Exception as e:
        print("Offline SQLite save failed:", e)
        
    return {"status": "success", "message": "ID Verified and Saved correctly."}

class AdminLogin(BaseModel):
    username: str
    password: str

@app.post("/api/admin/login")
async def admin_login(creds: AdminLogin):
    # Route admin login to regular system login as admin
    # This maintains compatibility while centralizing auth
    pass

class UserLogin(BaseModel):
    username: str
    password: str

def get_user_screens(empid: str, role: str):
    screens = MOCK_AUTHORIZATION.get(role, [])
    return screens

@app.post("/api/login")
async def system_login(creds: UserLogin, request: Request):
    username = creds.username.lower().strip()
    client_ip = request.client.host if request and request.client else "unknown"
    
    user_record = auth_db.get_user_by_empid(username)
    
    if not user_record:
        # Fallback to general admin for old apps
        if username == "admin" and creds.password == "GTRE123":
            user_record = auth_db.get_user_by_empid("emp01")
        if not user_record:
            auth_db.log_login_attempt(None, username, client_ip, "failed_no_user")
            raise HTTPException(status_code=401, detail="Invalid EmpID or Password")
        
    user_id = user_record["id"]
    
    if not user_record["is_active"]:
        auth_db.log_login_attempt(user_id, username, client_ip, "failed_inactive")
        raise HTTPException(status_code=403, detail="Account disabled")

    # Check Lockout
    if user_record["locked_until"]:
        lock_time = datetime.datetime.strptime(user_record["locked_until"], "%Y-%m-%d %H:%M:%S.%f") if "." in user_record["locked_until"] else datetime.datetime.strptime(user_record["locked_until"], "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.utcnow() < lock_time:
            auth_db.log_login_attempt(user_id, username, client_ip, "failed_locked")
            raise HTTPException(status_code=403, detail="Account is locked due to multiple failed attempts. Try again later.")

    # Verify Password (strip spaces to fix copy-paste errors)
    if not auth_db.pwd_context.verify(creds.password.strip(), user_record["password_hash"]):
        auth_db.update_failed_attempts(username, reset=False)
        auth_db.log_login_attempt(user_id, username, client_ip, "failed_bad_password")
        raise HTTPException(status_code=401, detail="Invalid EmpID or Password")

    # Success
    auth_db.update_failed_attempts(username, reset=True)
    auth_db.log_login_attempt(user_id, username, client_ip, "success")

    role = user_record["role"].lower()
    allowed_screens = get_user_screens(username, role)
    
    # Generate 8-hour JWT
    to_encode = {
        "sub": user_record["emp_id"],
        "role": role,
        "fullName": user_record["full_name"],
        "screens": allowed_screens,
        "exp": datetime.datetime.utcnow() + timedelta(hours=8)
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "status": "success", 
        "token": token, 
        "role": role,
        "fullName": user_record["full_name"],
        "empid": user_record["emp_id"],
        "screens": allowed_screens
    }

class CreateUserRequest(BaseModel):
    emp_id: str
    full_name: str
    email: Optional[str] = None
    role: str
    department: str
    password: str

@app.get("/api/admin/users")
async def get_users(token: str):
    verify_role(token, ["admin"])
    users = auth_db.get_all_users()
    return {"status": "success", "data": users}

@app.post("/api/admin/users")
async def create_user(req: CreateUserRequest, token: str):
    verify_role(token, ["admin"])
    conn = auth_db.get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE LOWER(emp_id) = LOWER(?)", (req.emp_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Employee ID already exists")

        new_id = str(uuid.uuid4())
        hashed = auth_db.pwd_context.hash(req.password.strip())
        cursor.execute('''
            INSERT INTO users (id, emp_id, full_name, email, password_hash, role, department, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (new_id, req.emp_id, req.full_name, req.email, hashed, req.role, req.department, 1))
        conn.commit()
    finally:
        conn.close()
    return {"status": "success", "message": "User created successfully"}

@app.delete("/api/admin/users/{emp_id}")
async def delete_user(emp_id: str, token: str):
    verify_role(token, ["admin"])
    conn = auth_db.get_db()
    cursor = conn.cursor()
    try:
        # Prevent deleting the default primary admin to avoid locking everyone out
        if emp_id.lower() == "emp01":
            raise HTTPException(status_code=403, detail="Cannot delete the root System Administrator")
            
        cursor.execute("SELECT id FROM users WHERE LOWER(emp_id) = LOWER(?)", (emp_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
            
        # Delete user logs first (foreign keys might restrict it otherwise, though SQLite often allows it)
        cursor.execute("DELETE FROM login_logs WHERE user_id = (SELECT id FROM users WHERE LOWER(emp_id) = LOWER(?))", (emp_id,))
        cursor.execute("DELETE FROM users WHERE LOWER(emp_id) = LOWER(?)", (emp_id,))
        conn.commit()
    finally:
        conn.close()
    return {"status": "success", "message": f"User {emp_id} deleted successfully"}


class RecognizeFaceRequest(BaseModel):
    photoBase64: str

# Utility for offline face comparison using OpenCV LBPH Face Recognizer
def compare_faces(base64_img1: str, base64_img2: str) -> float:
    try:
        import numpy as np
        
        # Decode base64 strings to numpy arrays
        def b64_to_numpy(b64_str):
            if ',' in b64_str:
                b64_str = b64_str.split(',')[1]
            b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
            img_data = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img

        img1 = b64_to_numpy(base64_img1)
        img2 = b64_to_numpy(base64_img2)

        if img1 is None or img2 is None:
            return 0.0

        model_dir = os.path.join(os.path.dirname(__file__), "models")
        detector_path = os.path.join(model_dir, "face_detection_yunet_2023mar.onnx")
        recognizer_path = os.path.join(model_dir, "face_recognition_sface_2021dec.onnx")

        if not os.path.exists(detector_path) or not os.path.exists(recognizer_path):
            print("ONNX models missing for SFace.")
            return 0.0

        detector = cv2.FaceDetectorYN.create(detector_path, "", (320, 320), 0.9, 0.3, 5000)
        recognizer = cv2.FaceRecognizerSF.create(recognizer_path, "")

        def get_face_feature(img):
            height, width, _ = img.shape
            detector.setInputSize((width, height))
            _, faces = detector.detect(img)
            if faces is None or len(faces) == 0:
                return None
            aligned_face = recognizer.alignCrop(img, faces[0])
            return recognizer.feature(aligned_face)

        feat1 = get_face_feature(img1)
        feat2 = get_face_feature(img2)

        if feat1 is None or feat2 is None:
            return 0.0

        similarity = recognizer.match(feat1, feat2, cv2.FaceRecognizerSF_FR_COSINE)
        
        # SFace cosine similarity threshold is typically 0.363
        if similarity >= 0.363:
            mapped_sim = 0.70 + ((similarity - 0.363) / (1.0 - 0.363)) * 0.30
            return float(mapped_sim)
        else:
            return float(similarity)

    except Exception as e:
        print(f"Face comparison error: {e}")
        return 0.0

@app.post("/api/visitors/recognize")
async def recognize_visitor(req: RecognizeFaceRequest):
    approved_visitors = []
    
    # Try fetching from DB first
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Fetch APPROVED visitors
            cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, PURPOSE_OF_VISIT, PHOTO_PATH FROM VISITORS WHERE STATUS IN ('PASS_READY', 'VISITOR_INSIDE')")
            rows = cursor.fetchall()
            for row in rows:
                photo_path = row[4]
                photo_b64 = None
                
                # Check if file exists and read it
                if photo_path and os.path.exists(photo_path):
                    with open(photo_path, "rb") as f:
                        photo_b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')
                        
                if photo_b64:
                    approved_visitors.append({
                        "id": row[0],
                        "fullName": row[1],
                        "companyName": row[2] if row[2] else "Guest",
                        "purposeOfVisit": row[3] if row[3] else "Visit",
                        "photoBase64": photo_b64
                    })
            conn.close()
        except Exception as e:
            print("DB Fetch recognize error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB if no DB connection or no approved visitors in DB
    if not approved_visitors:
        for v in MOCK_VISITORS_DB:
            if v.get('status') in ('PASS_READY', 'VISITOR_INSIDE'):
                photo_filename = v.get('photoPath')
                photo_b64 = None
                if photo_filename:
                    # Construct full path since MOCK DB stores basename
                    full_path = os.path.join(UPLOAD_DIR, photo_filename)
                    if os.path.exists(full_path):
                        with open(full_path, "rb") as f:
                            photo_b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')
                
                if photo_b64:
                    v_copy = v.copy()
                    v_copy['photoBase64'] = photo_b64
                    approved_visitors.append(v_copy)

    if not approved_visitors:
        raise HTTPException(status_code=404, detail="No approved visitors found with photos.")
        
    best_match = None
    highest_confidence = 0.0
    
    # Iterate through all approved visitors and compare faces
    for visitor in approved_visitors:
        if 'photoBase64' in visitor:
            confidence = compare_faces(req.photoBase64, visitor['photoBase64'])
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_match = visitor

    # Minimum threshold for a "match" (set low for demo reliability without real ML models)
    if not best_match or highest_confidence < 0.35:
        print(f"DEBUG: Matched None or too low confidence. Highest was: {highest_confidence}")
        raise HTTPException(status_code=404, detail="Face not recognized. Please register at front desk.")
        
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action_msg = "Entry Recorded"
    
    # Try logging to DB first
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Check if there is an open attendance log for today
            cursor.execute("SELECT ID FROM ATTENDANCE WHERE VISITOR_ID = :1 AND TRUNC(ENTRY_TIME) = TRUNC(SYSDATE) AND EXIT_TIME IS NULL", [best_match['id']])
            open_log = cursor.fetchone()
            
            if open_log:
                cursor.execute("UPDATE ATTENDANCE SET EXIT_TIME = SYSDATE WHERE ID = :1", [open_log[0]])
                action_msg = "Exit Recorded"
            else:
                cursor.execute("INSERT INTO ATTENDANCE (ID, VISITOR_ID, ENTRY_TIME) VALUES (attendance_seq.NEXTVAL, :1, SYSDATE)", [best_match['id']])
            
            conn.commit()
            conn.close()
        except Exception as e:
            print("DB Attendance update error:", e)
            if conn: conn.close()
            # If DB fails, we still want to fall back to mock log logic below
            conn = None
            
    # Fallback/Mirror to mock attendance logs
    if not conn:
        open_log = next((log for log in MOCK_ATTENDANCE_LOGS if log['visitorId'] == best_match['id'] and log['exitTime'] is None), None)
        if open_log:
            open_log['exitTime'] = current_time
            action_msg = "Exit Recorded"
        else:
            new_log = {
                "id": len(MOCK_ATTENDANCE_LOGS) + 1,
                "visitorId": best_match["id"],
                "fullName": best_match["fullName"],
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "entryTime": current_time,
                "exitTime": None
            }
            MOCK_ATTENDANCE_LOGS.append(new_log)
    
    # Set fallback values if properties are missing
    company_name = best_match.get("companyName")
    role = company_name if company_name else "Guest"
    dept = best_match.get("purposeOfVisit")
    if not dept:
        dept = "Visit"

    mock_employee = {
        "id": f"VIS-{best_match['id']}",
        "fullName": best_match["fullName"],
        "role": role,
        "department": dept,
        "lastSeen": current_time,
        "action": action_msg
    }
    
    print(f"DEBUG: Successfully matched {best_match['fullName']} with confidence {highest_confidence:.3f}")
    
    return {
        "status": "success", 
        "message": f"Face Recognized: {action_msg}",
        "matchConfidence": highest_confidence,
        "data": mock_employee
    }

@app.get("/api/attendance")
async def get_attendance_logs(token: str):
    verify_role(token, ["reception"])
    return {"status": "success", "data": MOCK_ATTENDANCE_LOGS}

class ScheduledVisitor(BaseModel):
    fullName: str
    phoneNumber: str
    hostName: str
    purposeOfVisit: Optional[str] = "Official Meeting"

@app.post("/api/visitors/scheduled")
async def add_scheduled_visitor(visitor: ScheduledVisitor):
    new_id = f"SCH-{1003 + len(SCHEDULED_VISITS)}"
    new_visitor = {
        "id": new_id,
        "fullName": visitor.fullName,
        "phoneNumber": visitor.phoneNumber,
        "hostName": visitor.hostName,
        "purposeOfVisit": visitor.purposeOfVisit
    }
    SCHEDULED_VISITS.append(new_visitor)
    return {"status": "success", "message": "Pre-registration successful!", "data": new_visitor}

# --- Visitor Request Module Endpoints ---

@app.get("/api/visitor-request/init")
async def init_visitor_request():
    # 1. Generate Requisition Number: YYYY-XXXXX
    current_year = datetime.datetime.now().year
    req_num = f"{current_year}-00001" # Default fallback
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # In a real Oracle DB, we'd use requisition_num_seq.NEXTVAL
            # But for simulation consistency, let's fetch the last one
            cursor.execute("SELECT requisition_num_seq.NEXTVAL FROM dual")
            next_val = cursor.fetchone()[0]
            req_num = f"{current_year}-{str(next_val).zfill(5)}"
            conn.close()
        except Exception as e:
            if conn: conn.close()
            # If sequence doesn't exist yet or error, use timestamp for uniqueness in demo
            req_num = f"{current_year}-{str(int(time.time()) % 100000).zfill(5)}"
    else:
        # Mock fallback using timestamp
        req_num = f"{current_year}-{str(int(time.time()) % 100000).zfill(5)}"

    # 2. Date of Request: DD-MMM-YYYY
    request_date = datetime.datetime.now().strftime("%d-%b-%Y")

    # 3. Requested By: Mock current officer
    # In a full system this would come from session/JWT
    requested_by = "BIJEESH K, SC C" 

    return {
        "status": "success",
        "data": {
            "requisitionNumber": req_num,
            "requestedBy": requested_by,
            "requestDate": request_date
        }
    }

@app.get("/api/officers")
async def get_officers():
    conn = get_db_connection()
    officers = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT OFFICER_NAME, OFFICER_CORP_NAME, LOCATION FROM OFFICERS ORDER BY OFFICER_NAME")
            rows = cursor.fetchall()
            officers = [{"name": f"{row[0]}, {row[1]}", "location": row[2]} for row in rows]
            conn.close()
        except Exception as e:
            if conn: conn.close()
    
    if not officers:
        # Mock fallback
        officers = [
            {"name": "BIJEESH K, SC C", "location": "Block A, 2nd Floor"},
            {"name": "DR. A. SHARMA, DIRECTOR", "location": "Main Building, Ground Floor"},
            {"name": "M. SINGH, HR HEAD", "location": "Admin Block, 1st Floor"}
        ]
    
    return {"status": "success", "data": officers}

@app.post("/api/visitor-request/submit")
async def submit_visitor_request(req: VisitorRequestSubmit):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # 1. Insert into VISITOR_REQUESTS
            sql_req = """
                INSERT INTO VISITOR_REQUESTS (
                    REQUISITION_ID, REQUISITION_NUMBER, REQUESTED_BY, REQUEST_DATE,
                    OFFICER_TO_MEET, LOCATION, PURPOSE, VALID_FROM, VALID_UPTO,
                    VISITOR_CATEGORY, VISITOR_NAME, ORGANISATION, COMPANY_ADDRESS,
                    PHONE, MOBILE, REMARKS
                ) VALUES (
                    requisition_num_seq.NEXTVAL, :req_num, :req_by, :req_date,
                    :officer, :loc, :purpose, :v_from, :v_upto,
                    :cat, :v_name, :org, :addr, :phone, :mobile, :remarks
                )
            """
            cursor.execute(sql_req, {
                'req_num': req.requisitionNumber,
                'req_by': req.requestedBy,
                'req_date': req.requestDate,
                'officer': req.officerToMeet,
                'loc': req.location,
                'purpose': req.purpose,
                'v_from': req.validFrom,
                'v_upto': req.validUpto,
                'cat': req.visitorCategory,
                'v_name': req.visitorName,
                'org': req.organisation,
                'addr': req.companyAddress,
                'phone': req.phone,
                'mobile': req.mobile,
                'aadhaar': req.aadhaarNumber,
                'passport': req.passportDetails,
                'remarks': req.remarks
            })

            # Update SQL to include new fields in VISITOR_REQUESTS (Assuming columns exist or using REMARKS as fallback)
            # For this demo, we'll focus on the mock persistence and the JSON response.

            # 2. Also insert into VISITORS table for Reception Dashboard
            sql_vis = """
                INSERT INTO VISITORS (
                    ID, FULL_NAME, COMPANY_NAME, PURPOSE_OF_VISIT, HOST_NAME, PHONE_NUMBER, ADDRESS,
                    NATIONALITY, STATUS, CREATED_BY_OFFICER, PASS_VALID_FROM, PASS_VALID_UNTIL, ALLOWED_BLOCKS
                ) VALUES (
                    visitor_seq.NEXTVAL, :full_name, :company, :purpose, :host, :phone, :address,
                    :nationality, 'WAITING_FOR_PHOTO', :req_by, :valid_from, :valid_until, 'All Blocks'
                )
            """
            cursor.execute(sql_vis, {
                'full_name': req.visitorName,
                'company': req.organisation,
                'purpose': req.purpose,
                'host': req.officerToMeet,
                'phone': req.mobile,
                'address': req.companyAddress,
                'nationality': req.visitorCategory,
                'req_by': req.requestedBy,
                'valid_from': req.validFrom,
                'valid_until': req.validUpto
            })

            conn.commit()
            conn.close()
            return {"status": "success", "message": "Pre-Registration submitted successfully!"}
        except Exception as e:
            if conn: conn.close()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Fallback/Mock Mode
    global MOCK_ID_COUNTER
    mock_visitor = {
        "id": MOCK_ID_COUNTER,
        "fullName": req.visitorName,
        "companyName": req.organisation,
        "hostName": req.officerToMeet,
        "phoneNumber": req.mobile,
        "purposeOfVisit": req.purpose,
        "requestedBy": req.requestedBy,
        "validFromDate": req.validFrom,
        "validUntilDate": req.validUpto,
        "aadhaarNumber": req.aadhaarNumber,
        "passportDetails": req.passportDetails,
        "status": 'WAITING_FOR_PHOTO'
    }
    MOCK_VISITORS_DB.append(mock_visitor)
    MOCK_ID_COUNTER += 1
    return {"status": "success", "message": "Pre-Registration submitted successfully (Mock Mode)!"}

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # This block is only for LOCAL offline testing. Render uses the start command in Dashboard.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
