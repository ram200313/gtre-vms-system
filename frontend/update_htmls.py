import os
import glob

frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

# We renamed index.html to new_visitor.html
html_files = [f for f in html_files if not f.endswith('index.html')]

script_tag = '    <script src="js/auth.js"></script>\n</head>'

logout_button = """
                    <button onclick="systemLogout()" class="btn btn-secondary" style="margin-left: 15px; padding: 8px 12px; background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1;">
                        <i class="fa-solid fa-sign-out-alt"></i> Logout
                    </button>
                </div>"""

for f in html_files:
    fname = os.path.basename(f)
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Update index.html links to new_visitor.html
    if 'index.html' in content:
        content = content.replace('"index.html"', '"new_visitor.html"')
        
    # 2. Add auth.js to protect pages (except admin_login)
    if fname != 'admin_login.html' and 'auth.js' not in content:
        content = content.replace('</head>', script_tag)
        
    # 3. Add Logout button to the header-user div if not already present
    if fname != 'admin_login.html' and 'systemLogout()' not in content:
        # The header-user closing div is usually right after <div class="avatar">...</div>
        content = content.replace('                </div>\n            </header>', logout_button + '\n            </header>')
        
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
