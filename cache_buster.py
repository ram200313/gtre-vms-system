import os
import glob
import re

frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

for file_path in html_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update script tags for visitor_request.js and auth.js
    content = re.sub(r'src="js/visitor_request.js(\?v=\d+)?"', 'src="js/visitor_request.js?v=7"', content)
    content = re.sub(r'src="js/auth.js(\?v=\d+)?"', 'src="js/auth.js?v=7"', content)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Busted cache for {os.path.basename(file_path)}")
