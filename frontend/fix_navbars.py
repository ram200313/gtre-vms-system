import os
import glob
import re

frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

sidebar_template = """            <nav class="sidebar-nav">
                <a href="dashboard.html" id="nav-dashboard" class="nav-item">
                    <i class="fa-solid fa-gauge"></i> Dashboard
                </a>
                <a href="admin_dashboard.html" id="nav-admin" class="nav-item">
                    <i class="fa-solid fa-users-cog"></i> User Management
                </a>
                <div id="label-officer" class="nav-label"
                    style="padding: 12px 16px 4px; font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">
                    Officer Portal</div>
                <a href="visitor_request.html" id="nav-pre-reg" class="nav-item">
                    <i class="fa-solid fa-user-plus"></i> Pre-Registration
                </a>
                <a href="officer_visitors.html" id="nav-my-visitors" class="nav-item">
                    <i class="fa-solid fa-list-check"></i> My Visitors
                </a>
                <div id="label-reception" class="nav-label"
                    style="padding: 12px 16px 4px; font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">
                    Reception & Security</div>
                <a href="reception_dashboard.html" id="nav-reception-dash" class="nav-item">
                    <i class="fa-solid fa-camera"></i> Reception Dashboard
                </a>
                <a href="todays_visitors.html" id="nav-todays-visitors" class="nav-item">
                    <i class="fa-solid fa-users"></i> Today's Visitors
                </a>
                <a href="attendance.html" id="nav-attendance" class="nav-item">
                    <i class="fa-solid fa-user-check"></i> Regular Attendance
                </a>
                <a href="gate_scanners.html" id="nav-gate-scanners" class="nav-item">
                    <i class="fa-solid fa-door-open"></i> Gate Scanners
                </a>
            </nav>"""

exclude = ['index.html', 'unauthorized.html', 'admin_login.html']
for f in html_files:
    if os.path.basename(f) in exclude:
        continue
    
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Use regex to find and replace the entire sidebar-nav block
    new_content = re.sub(
        r'<nav class="sidebar-nav">.*?</nav>', 
        sidebar_template, 
        content, 
        flags=re.DOTALL
    )

    # Highlight active link by matching filename
    filename = os.path.basename(f)
    if filename == "admin_dashboard.html": # Special case
        new_content = new_content.replace(f'href="{filename}" id="nav-admin" class="nav-item"', f'href="{filename}" id="nav-admin" class="nav-item active"')
    else:
        new_content = new_content.replace(f'href="{filename}"', f'href="{filename}" class="active"')
        # Cleanup class="nav-item active" duplicate if any
        new_content = new_content.replace(' class="active" id="', ' id="').replace(' class="nav-item" class="active"', ' class="nav-item active"')
    
    # Just a simple hack: Replace class="nav-item" with class="nav-item active" for the matching href
    new_content = re.sub(f'href="{filename}" id="(.*?)" class="nav-item"', f'href="{filename}" id="\\1" class="nav-item active"', new_content)

    with open(f, 'w', encoding='utf-8') as file:
        file.write(new_content)

print("Navbars sanitized and standardized!")
