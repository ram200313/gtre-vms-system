import os
import base64
import uuid
import datetime
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import cx_Oracle
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np

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
        # Ensure Oracle Instant Client is installed if running locally.
        connection = cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

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

@app.get("/api/visitors/pending")
async def get_pending_visitors():
    # If DB is connected, fetch from DB. Otherwise from MOCK_VISITORS_DB
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, PHOTO_PATH, VISIT_DATE, EXPECTED_EXIT_TIME, STATUS FROM VISITORS WHERE STATUS = 'PENDING'")
            rows = cursor.fetchall()
            visitors = [
                {
                    "id": row[0],
                    "fullName": row[1],
                    "companyName": row[2],
                    "hostName": row[3],
                    "phoneNumber": row[4],
                    "purposeOfVisit": row[5],
                    "photoPath": os.path.basename(row[6]),
                    "visitDate": row[7].strftime("%Y-%m-%d") if row[7] else None,
                    "expectedExitTime": row[8],
                    "status": row[9]
                } for row in rows
            ]
            conn.close()
            return {"status": "success", "data": visitors}
        except Exception as e:
            print("DB Fetch pending error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB
    pending = [v for v in MOCK_VISITORS_DB if v['status'] == 'PENDING']
    return {"status": "success", "data": pending, "source": "mock"}

@app.get("/api/visitors/approved")
async def get_approved_visitors():
    # If DB is connected, fetch from DB. Otherwise from MOCK_VISITORS_DB
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, HOST_NAME, PHONE_NUMBER, PURPOSE_OF_VISIT, PHOTO_PATH, VISIT_DATE, EXPECTED_EXIT_TIME, STATUS FROM VISITORS WHERE STATUS = 'APPROVED' AND TRUNC(VISIT_DATE) = TRUNC(SYSDATE)")
            rows = cursor.fetchall()
            visitors = [
                {
                    "id": row[0],
                    "fullName": row[1],
                    "companyName": row[2],
                    "hostName": row[3],
                    "phoneNumber": row[4],
                    "purposeOfVisit": row[5],
                    "photoPath": os.path.basename(row[6]),
                    "visitDate": row[7].strftime("%Y-%m-%d") if row[7] else None,
                    "expectedExitTime": row[8],
                    "status": row[9]
                } for row in rows
            ]
            conn.close()
            return {"status": "success", "data": visitors}
        except Exception as e:
            print("DB Fetch approved error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB
    approved = [v for v in MOCK_VISITORS_DB if v['status'] == 'APPROVED']
    return {"status": "success", "data": approved, "source": "mock"}

@app.post("/api/visitors/{visitor_id}/status")
async def update_visitor_status(visitor_id: str, status_update: dict):
    new_status = status_update.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE VISITORS SET STATUS = :1 WHERE ID = :2", [new_status, visitor_id])
            conn.commit()
            conn.close()
            return {"status": "success", "message": f"Visitor {new_status.lower()} successfully."}
        except Exception as e:
            print("DB Update status error:", e)
            if conn: conn.close()
            
    # Fallback to mock DB
    for v in MOCK_VISITORS_DB:
        if str(v['id']) == str(visitor_id):
            v['status'] = new_status
            return {"status": "success", "message": f"Visitor {new_status.lower()} successfully (mock)."}
            
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
            cursor.execute("SELECT ID, FULL_NAME, COMPANY_NAME, PURPOSE_OF_VISIT, PHOTO_PATH FROM VISITORS WHERE STATUS = 'APPROVED'")
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
            if v.get('status') == 'APPROVED':
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


@app.post("/api/visitors/register")
async def register_visitor(
    # Section 1
    fullName: str = Form(...),
    companyName: str = Form(...),
    purposeOfVisit: str = Form(...),
    hostName: str = Form(...),
    phoneNumber: str = Form(...),
    address: str = Form(...),
    
    # Section 2
    nationality: str = Form(...),
    aadhaarNumber: Optional[str] = Form(None),
    panNumber: Optional[str] = Form(None),
    passportNumber: Optional[str] = Form(None),
    visaNumber: Optional[str] = Form(None),
    countryDropdown: Optional[str] = Form(None),
    docVerified: str = Form("N"),
    
    # Section 3
    photoBase64: str = Form(...), # expecting data:image/jpeg;base64,...
    
    # Section 4
    allowedBlocks: str = Form(...), # JSON string array
    
    # Section 5
    phoneDeposited: str = Form("N"),
    lockerNumber: Optional[str] = Form(None),
    
    # Section 6
    visitDate: str = Form(...),
    expectedExitTime: str = Form(...),
    multiEntryAllowed: str = Form("N"),
    
    # Status
    actionStatus: str = Form("PENDING")
):
    try:
        # 1. Process and save the offline photo
        if not photoBase64 or not "," in photoBase64:
            raise HTTPException(status_code=400, detail="Invalid photo data")
            
        header, encoded = photoBase64.split(",", 1)
        photo_bytes = base64.b64decode(encoded)
        
        # Give the file a unique offline safe name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"visitor_{phoneNumber}_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(photo_bytes)
            
        # 2. Database Insertion (Oracle)
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Check for existing pending today
            check_sql = """
                SELECT ID FROM VISITORS 
                WHERE PHONE_NUMBER = :1 AND TRUNC(VISIT_DATE) = TRUNC(SYSDATE) AND STATUS IN ('PENDING', 'APPROVED')
            """
            cursor.execute(check_sql, [phoneNumber])
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return {"status": "error", "message": "Visitor already exists for today. Reactivating visit...", "existing_id": existing[0]}

            sql = """
                INSERT INTO VISITORS (
                    ID, FULL_NAME, COMPANY_NAME, PURPOSE_OF_VISIT, HOST_NAME, PHONE_NUMBER, ADDRESS,
                    NATIONALITY, AADHAAR_NUMBER, PAN_NUMBER, PASSPORT_NUMBER, VISA_NUMBER, COUNTRY, DOC_VERIFIED,
                    PHOTO_PATH, ALLOWED_BLOCKS, PHONE_DEPOSITED, LOCKER_NUMBER, VISIT_DATE, EXPECTED_EXIT_TIME, 
                    MULTI_ENTRY_ALLOWED, STATUS
                ) VALUES (
                    visitor_seq.NEXTVAL, :full_name, :company, :purpose, :host, :phone, :address,
                    :nationality, :aadhaar, :pan, :passport, :visa, :country, :doc_verified,
                    :photo_path, :blocks, :phone_dep, :locker, TO_DATE(:visit_date, 'YYYY-MM-DD'), :exit_time,
                    :multi_entry, :status
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
                'passport': passportNumber,
                'visa': visaNumber,
                'country': countryDropdown,
                'doc_verified': docVerified,
                'photo_path': filepath,
                'blocks': allowedBlocks,
                'phone_dep': phoneDeposited,
                'locker': lockerNumber,
                'visit_date': visitDate,
                'exit_time': expectedExitTime,
                'multi_entry': multiEntryAllowed,
                'status': actionStatus
            })
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "status": "success", 
                "message": f"Visitor {actionStatus.lower()} successfully", 
                "photo_path": filepath
            }
        else:
            # Fallback if DB isn't running in this local test env
            # Still return success so the UI can demonstrate functionality
            global MOCK_ID_COUNTER
            mock_visitor = {
                "id": MOCK_ID_COUNTER,
                "fullName": fullName,
                "companyName": companyName,
                "hostName": hostName,
                "phoneNumber": phoneNumber,
                "purposeOfVisit": purposeOfVisit,
                "photoPath": os.path.basename(filepath),
                "visitDate": visitDate,
                "expectedExitTime": expectedExitTime,
                "status": actionStatus
            }
            MOCK_VISITORS_DB.append(mock_visitor)
            MOCK_ID_COUNTER += 1
            
            return {
                "status": "warning", 
                "message": "Saved photo locally. Database connection failed, but form processed.", 
                "photo_path": filepath
            }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # This block is only for LOCAL offline testing. Render uses the start command in Dashboard.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
