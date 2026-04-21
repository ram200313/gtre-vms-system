import os
import glob

frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

# Exclude login and unauthorized pages that don't have the sidebar
exclude = ['index.html', 'admin_login.html', 'unauthorized.html']
html_files = [f for f in html_files if os.path.basename(f) not in exclude]

# Sidebar replacements
replacements = {
    'href="dashboard.html"': 'href="dashboard.html" id="nav-dashboard"',
    'href="visitor_request.html"': 'href="visitor_request.html" id="nav-pre-reg"',
    'href="officer_visitors.html"': 'href="officer_visitors.html" id="nav-my-visitors"',
    'href="reception_dashboard.html"': 'href="reception_dashboard.html" id="nav-reception-dash"',
    'href="todays_visitors.html"': 'href="todays_visitors.html" id="nav-todays-visitors"',
    'href="attendance.html"': 'href="attendance.html" id="nav-attendance"',
    'href="gate_scanners.html"': 'href="gate_scanners.html" id="nav-gate-scanners"',
}

# Labels need more specific replacement to avoid duplicates or misplacements
officer_label_old = 'Officer Portal</div>'
officer_label_new = 'Officer Portal</div>' # We'll find the div before it

reception_label_old = 'Reception & Security</div>'
reception_label_new = 'Reception & Security</div>'

for f in html_files:
    print(f"Updating {os.path.basename(f)}...")
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Update links if ID not already present
    for old, new in replacements.items():
        if f' id="' not in new.split('id=')[-1]: # Simple check
             content = content.replace(old, new)
    
    # 2. Add IDs to labels if not present
    if 'id="label-officer"' not in content:
        content = content.replace('<div class="nav-label"', '<div id="label-officer" class="nav-label"', 1)
    if 'id="label-reception"' not in content:
        content = content.replace('<div class="nav-label"', '<div id="label-reception" class="nav-label"', 1)

    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Done!")
