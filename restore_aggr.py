import os
import glob
import json
import shutil
from urllib.parse import unquote

history_dir = r"C:\Users\jayram\AppData\Roaming\Code\User\History"
frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"

html_files = [
    "admin_dashboard.html", "admin_login.html", "unauthorized.html"
]

entries_files = glob.glob(os.path.join(history_dir, "*", "entries.json"))
print(f"Found {len(entries_files)} entry files.")

for target in html_files:
    latest_ts = 0
    best_file = None
    
    for ef in entries_files:
        try:
            with open(ef, 'r', encoding='utf-8') as f:
                data = json.load(f)
                res = unquote(data.get("resource", ""))
                # Fuzzy match! Just check if the filename is IN the resource string
                if target in res:
                    for entry in data.get("entries", []):
                        path = os.path.join(os.path.dirname(ef), entry["id"])
                        if os.path.exists(path) and os.path.getsize(path) > 0:
                            if entry["timestamp"] > latest_ts:
                                latest_ts = entry["timestamp"]
                                best_file = path
        except:
            pass
            
    if best_file:
        shutil.copy2(best_file, os.path.join(frontend_dir, target))
        print(f"RESTORED: {target} from {best_file} (ts: {latest_ts})")
    else:
        print(f"NOT FOUND: {target}")
