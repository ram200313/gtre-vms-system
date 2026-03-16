import os
import base64
import uuid
import datetime
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import oracledb
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
import time

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
async def search_visitors(q: str):
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
async def get_dashboard_stats():
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
async def get_todays_visitors():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            today_str = f"{datetime.datetime.now().strftime('%Y-%m-%d')}%"
            # Get visitors with passes ready, inside, or exited for today
            cursor.execute("""
                SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, 
                       PHOTO_PATH, PASS_VALID_FROM, PASS_VALID_UNTIL, STATUS, CREATED_BY_OFFICER
                FROM VISITORS 
                WHERE STATUS IN ('PASS_READY', 'VISITOR_INSIDE', 'VISITOR_EXITED') 
                AND PASS_VALID_FROM LIKE :1
                ORDER BY ID DESC
            """, [today_str])
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
    today_str2 = datetime.datetime.now().strftime("%Y-%m-%d")
    todays = [v for v in MOCK_VISITORS_DB if v.get('status') in ['PASS_READY', 'VISITOR_INSIDE', 'VISITOR_EXITED'] and v.get('validFromDate', '').startswith(today_str2)]
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
    validUntilDate: str = Form(...)
):
    try:
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
                    'WAITING_FOR_PHOTO', 'Officer'
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
                'valid_until': validUntilDate
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
                "status": 'WAITING_FOR_PHOTO'
            }
            MOCK_VISITORS_DB.append(mock_visitor)
            MOCK_ID_COUNTER += 1
            return {"status": "success", "message": "Pre-registered locally. Database connection failed."}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visitors/officer/my_visitors")
async def get_my_visitors():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, PASS_VALID_FROM, PASS_VALID_UNTIL, STATUS FROM VISITORS ORDER BY CREATED_AT DESC")
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
                    "status": row[8]
                } for row in rows
            ]
            conn.close()
            return {"status": "success", "data": visitors}
        except Exception as e:
            print("DB Fetch my_visitors error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB
    return {"status": "success", "data": list(reversed(MOCK_VISITORS_DB)), "source": "mock"}

class CapturePhotoRequest(BaseModel):
    photoBase64: str

@app.post("/api/visitors/{visitor_id}/capture_photo")
async def capture_photo(visitor_id: str, req: CapturePhotoRequest):
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

class AdminLogin(BaseModel):
    username: str
    password: str

@app.post("/api/admin/login")
async def admin_login(creds: AdminLogin):
    # Hardcoded Enterprise Demo Credentials
    if creds.username == "admin" and creds.password == "GTRE123":
        return {"status": "success", "token": "mock-jwt-token-7a8b9c", "role": "System Administrator"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def system_login(creds: UserLogin):
    # General system login
    if creds.username == "user" and creds.password == "GTRE123":
        return {"status": "success", "token": "mock-system-token-xyz", "role": "System User"}
    elif creds.username == "admin" and creds.password == "GTRE123":
        return {"status": "success", "token": "mock-system-token-abc", "role": "System Administrator"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

class RecognizeFaceRequest(BaseModel):
    photoBase64: str

# Utility for offline face comparison using OpenCV LBPH Face Recognizer
def compare_faces(base64_img1: str, base64_img2: str) -> float:
    try:
        # Decode base64 strings to bytes
        def decode_base64_to_cv2(b64_str):
            if ',' in b64_str:
                b64_str = b64_str.split(',')[1]
            b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
            img_data = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_data, np.uint8)
            # Read directly as grayscale for face recognition
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            return img

        img1 = decode_base64_to_cv2(base64_img1)
        img2 = decode_base64_to_cv2(base64_img2)

        if img1 is None or img2 is None:
            return 0.0

        # Detect faces using Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces1 = face_cascade.detectMultiScale(img1, scaleFactor=1.1, minNeighbors=4)
        faces2 = face_cascade.detectMultiScale(img2, scaleFactor=1.1, minNeighbors=4)

        # Helper to crop the detected face, or fallback to central crop
        def get_face_crop(img, faces):
            if len(faces) == 0:
                h, w = img.shape
                # Fallback to center 50%
                return img[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
            
            # Use the largest face found
            faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
            x, y, w, h = faces[0]
            # Add slight padding
            pad = int(w * 0.1)
            y1, y2 = max(0, y - pad), min(img.shape[0], y + h + pad)
            x1, x2 = max(0, x - pad), min(img.shape[1], x + w + pad)
            return img[y1:y2, x1:x2]

        face1_crop = get_face_crop(img1, faces1)
        face2_crop = get_face_crop(img2, faces2)

        # Resize for consistent LBPH grid
        face1_resized = cv2.resize(face1_crop, (150, 150))
        face2_resized = cv2.resize(face2_crop, (150, 150))

        # Train an LBPH recognizer on the registered face (img2)
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        # Train with label 1
        recognizer.train([face2_resized], np.array([1]))
        
        # Predict the scanned face (img1)
        label, confidence_dist = recognizer.predict(face1_resized)
        
        # In LBPH, lower confidence = better match (it is a distance metric). 
        # Typically < 50 is a solid match. > 80 is different person.
        # We convert distance to a similarity score 0.0 to 1.0
        # If distance is > 100, similarity is 0. 
        similarity = max(0.0, 1.0 - (confidence_dist / 100.0))
        
        return similarity
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
async def get_attendance_logs():
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
