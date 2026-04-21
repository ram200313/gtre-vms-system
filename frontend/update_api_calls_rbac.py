import os
import glob
import re

frontend_dir = r"c:\Users\jayram\OneDrive\Desktop\GTRE..VMS\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

# Patterns to match and replace
# 1. fetchAPI('/api/...') -> fetchAPI('/api/...?token=' + sessionStorage.getItem('systemToken'))
# 2. fetchAPI('/api/visitor-request/submit', { ... }) needs token in JSON body

for f in html_files:
    fname = os.path.basename(f)
    print(f"Checking {fname}...")
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    changed = False

    # Skip files that don't use fetchAPI
    if 'fetchAPI' not in content:
        continue

    # Update simple GET requests in fetchAPI
    # Find fetchAPI('/api/endpoint') and change to fetchAPI('/api/endpoint?token=' + sessionStorage.getItem('systemToken'))
    # This regex looks for fetchAPI calls with a string argument that doesn't already have 'token='
    get_pattern = r"fetchAPI\(['\"](/api/[^'\"?]+)['\"]\)"
    def replace_get(match):
        endpoint = match.group(1)
        return f"fetchAPI(`${{endpoint}}?token=${{sessionStorage.getItem('systemToken')}}`)"
    
    new_content = re.sub(get_pattern, replace_get, content)
    if new_content != content:
        content = new_content
        changed = True

    # Update template literal fetchAPI calls if any
    get_pattern_tl = r"fetchAPI\(`(/api/[^`?]+)\`\)"
    def replace_get_tl(match):
        endpoint = match.group(1)
        return f"fetchAPI(`${{endpoint}}?token=${{sessionStorage.getItem('systemToken')}}`)"
        
    new_content = re.sub(get_pattern_tl, replace_get_tl, content)
    if new_content != content:
        content = new_content
        changed = True

    if changed:
        print(f"Updated API calls in {fname}")
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)

print("Done!")
