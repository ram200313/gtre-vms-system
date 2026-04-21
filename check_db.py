import sqlite3
import pprint

conn = sqlite3.connect("offline_auth.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("== USERS ==")
cursor.execute("SELECT emp_id, failed_attempts, is_active, locked_until FROM users")
for r in cursor.fetchall():
    print(dict(r))

print("\n== LOGS (Last 10) ==")
cursor.execute("SELECT emp_id, status, login_time FROM login_logs ORDER BY id DESC LIMIT 10")
for r in cursor.fetchall():
    print(dict(r))

conn.close()
