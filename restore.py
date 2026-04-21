import os
import glob
import shutil
import json

history_dir = r"C:\Users\jayram\AppData\Roaming\Code\User\History"
frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"

html_files = [
    "admin_dashboard.html", "admin_login.html", "attendance.html", 
    "dashboard.html", "gate_scanners.html", "index.html", 
    "officer_visitors.html", "reception_dashboard.html", "scanner.html", 
    "todays_visitors.html", "unauthorized.html", "visitor_request.html"
]

def restore_latest_backup():
    # Find all entries.json
    entries_files = glob.glob(os.path.join(history_dir, "*", "entries.json"))
    
    restored_count = 0
    for file_name in html_files:
        best_time = 0
        best_file = None
        
        # Searching through all history folders to find matching resource
        for entries_file in entries_files:
            try:
                with open(entries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    resource = data.get("resource", "")
                    # Match by basename
                    if resource.endswith(f"frontend/{file_name}") or resource.endswith(f"frontend\\{file_name}"):
                        # Find the entries array
                        entries = data.get("entries", [])
                        for entry in entries:
                            ts = entry.get("timestamp", 0)
                            file_id = entry.get("id")
                            history_path = os.path.join(os.path.dirname(entries_file), file_id)
                            # Check size to ensure not 0 bytes
                            if os.path.exists(history_path) and os.path.getsize(history_path) > 0:
                                if ts > best_time:
                                    best_time = ts
                                    best_file = history_path
            except Exception as e:
                pass
                
        if best_file:
            target = os.path.join(frontend_dir, file_name)
            shutil.copy2(best_file, target)
            print(f"Restored {file_name} from VS Code History ({best_time})")
            restored_count += 1
        else:
            print(f"COULD NOT FIND HISTORY FOR {file_name}")
            
    print(f"Total restored: {restored_count}")

restore_latest_backup()
