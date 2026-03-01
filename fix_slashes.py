import os
import glob
import re

frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"
files = glob.glob(os.path.join(frontend_dir, "*.html")) + glob.glob(os.path.join(frontend_dir, "js", "*.js"))

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # We stripped "http://localhost:8000" earlier, which turned things like:
    # fetch('http://localhost:8000/api/visitors/approved')
    # into:
    # fetch('/api/visitors/approved')
    # Which is exactly what we want! Let's just make sure there are no missing slashes.
    
    modified = False
    
    # Fix paths that might have become relative e.g., fetch('api/visitors
    # and change them to fetch('/api/visitors
    content = re.sub(r"fetch\('api/", "fetch('/api/", content)
    content = re.sub(r"fetch\(`api/", "fetch(`/api/", content)
    
    # Same for uploads
    content = re.sub(r"src\s*=\s*['\"]uploads/", "src='/uploads/", content)
    content = re.sub(r"src\s*=\s*`uploads/", "src=`/uploads/", content)
    
    if "api/" in content or "uploads/" in content:
        # Just rewrite to be safe
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Verified slashes in {os.path.basename(f)}")
