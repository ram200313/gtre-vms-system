import sqlite3
import os
import datetime

# By default, creates an sqlite database in the same directory as this file
DB_PATH = os.path.join(os.path.dirname(__file__), "offline_id_scans.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitor_id_records (
            visitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_ref_id VARCHAR(50),
            name VARCHAR(100),
            id_type VARCHAR(50),
            id_number VARCHAR(100),
            dob VARCHAR(50),
            address TEXT,
            photo_path VARCHAR(255),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_id_record(visitor_ref_id, name, id_type, id_number, dob, address, photo_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO visitor_id_records (visitor_ref_id, name, id_type, id_number, dob, address, photo_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (str(visitor_ref_id), name, id_type, id_number, dob, address, photo_path))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def get_id_record(visitor_ref_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM visitor_id_records WHERE visitor_ref_id = ? ORDER BY timestamp DESC LIMIT 1', (str(visitor_ref_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Initialize on import
init_db()
