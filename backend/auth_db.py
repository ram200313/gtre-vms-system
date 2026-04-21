import sqlite3
import os
import uuid
import datetime
from passlib.context import CryptContext

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "offline_auth.db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            emp_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            is_active BOOLEAN DEFAULT 1,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Login Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            emp_id TEXT,
            ip_address TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT
        )
    ''')
    
    # Check if admin exists, if not, create default users
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()['cnt'] == 0:
        default_users = [
            (str(uuid.uuid4()), "EMP01", "System Administrator", "admin@gtre.gov", pwd_context.hash("Admin@123"), "admin", "IT", 1),
            (str(uuid.uuid4()), "EMP02", "Security Officer", "security@gtre.gov", pwd_context.hash("GTRE123"), "officer", "Security", 1),
            (str(uuid.uuid4()), "EMP03", "Front Desk Reception", "reception@gtre.gov", pwd_context.hash("GTRE123"), "reception", "Front Desk", 1)
        ]
        cursor.executemany('''
            INSERT INTO users (id, emp_id, full_name, email, password_hash, role, department, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_users)
        
    conn.commit()
    conn.close()

def log_login_attempt(user_id, emp_id, ip_address, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO login_logs (user_id, emp_id, ip_address, status)
        VALUES (?, ?, ?, ?)
    ''', (user_id, emp_id, ip_address, status))
    conn.commit()
    conn.close()

def get_user_by_empid(emp_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(emp_id) = LOWER(?)", (emp_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_failed_attempts(emp_id, reset=False):
    conn = get_db()
    cursor = conn.cursor()
    try:
        if reset:
            cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP WHERE LOWER(emp_id) = LOWER(?)", (emp_id,))
        else:
            # Increment and check if lock needed
            cursor.execute("SELECT failed_attempts FROM users WHERE LOWER(emp_id) = LOWER(?)", (emp_id,))
            row = cursor.fetchone()
            if row:
                attempts = row['failed_attempts'] + 1
                if attempts >= 5:
                    lock_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
                    cursor.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE LOWER(emp_id) = LOWER(?)", 
                                   (attempts, lock_time, emp_id))
                else:
                    cursor.execute("UPDATE users SET failed_attempts = ? WHERE LOWER(emp_id) = LOWER(?)", 
                                   (attempts, emp_id))
        conn.commit()
    finally:
        conn.close()

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, emp_id, full_name, email, role, department, is_active, last_login, created_at FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

# Run init on import
init_db()
