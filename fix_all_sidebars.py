import os
import glob
import re

frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

for file_path in html_files:
    filename = os.path.basename(file_path)
    if filename in ["index.html", "admin_login.html", "unauthorized.html"]:
        continue
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    sidebar_match = re.search(r'<nav class="sidebar-nav">.*?</nav>', content, re.DOTALL)
    
    if sidebar_match:
        act_dash = ' active' if filename == 'dashboard.html' else ''
        act_admin = ' active' if filename == 'admin_dashboard.html' else ''
        act_pre_reg = ' active' if filename == 'visitor_request.html' else ''
        act_off_vis = ' active' if filename == 'officer_visitors.html' else ''
        act_rec = ' active' if filename == 'reception_dashboard.html' else ''
        act_todays = ' active' if filename == 'todays_visitors.html' else ''
        act_att = ' active' if filename == 'attendance.html' else ''
        act_gate = ' active' if filename == 'gate_scanners.html' else ''
        
        new_sidebar = f'''<nav class="sidebar-nav">
                <a href="dashboard.html" id="nav-dashboard" class="nav-item{act_dash}">
                    <i class="fa-solid fa-gauge"></i> Dashboard
                </a>
                
                <a href="admin_dashboard.html" id="nav-admin" class="nav-item{act_admin}">
                    <i class="fa-solid fa-users-cog"></i> User Management
                </a>

                <div id="label-officer" class="nav-label" style="padding: 12px 16px 4px; font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">Officer Portal</div>
                <a href="visitor_request.html" id="nav-pre-reg" class="nav-item{act_pre_reg}">
                    <i class="fa-solid fa-user-plus"></i> Pre-Registration
                </a>
                <a href="officer_visitors.html" id="nav-my-visitors" class="nav-item{act_off_vis}">
                    <i class="fa-solid fa-list-check"></i> My Visitors
                </a>

                <div id="label-reception" class="nav-label" style="padding: 12px 16px 4px; font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">Reception & Security</div>
                <a href="reception_dashboard.html" id="nav-reception-dash" class="nav-item{act_rec}">
                    <i class="fa-solid fa-camera"></i> Reception Dashboard
                </a>
                <a href="todays_visitors.html" id="nav-todays-visitors" class="nav-item{act_todays}">
                    <i class="fa-solid fa-users"></i> Today's Visitors
                </a>
                <a href="attendance.html" id="nav-attendance" class="nav-item{act_att}">
                    <i class="fa-solid fa-user-check"></i> Regular Attendance
                </a>
                <a href="gate_scanners.html" id="nav-gate-scanners" class="nav-item{act_gate}">
                    <i class="fa-solid fa-door-open"></i> Gate Scanners
                </a>
            </nav>'''
            
        content = content[:sidebar_match.start()] + new_sidebar + content[sidebar_match.end():]
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filename}")
