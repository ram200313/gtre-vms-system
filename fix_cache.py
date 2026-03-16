import glob
import os

files = glob.glob('frontend/**/*.html', recursive=True)
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Simple replace to break cache
    content = content.replace('js/auth.js', 'js/auth.js?v=6')
    content = content.replace('js/auth.js?v=2', 'js/auth.js?v=6')
    content = content.replace('js/auth.js?v=3', 'js/auth.js?v=6')
    content = content.replace('js/auth.js?v=4', 'js/auth.js?v=6')
    content = content.replace('js/auth.js?v=5', 'js/auth.js?v=6')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print("Cache bust applied to all HTML files successfully.")
