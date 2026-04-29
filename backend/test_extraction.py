import json
import re

clean_data = [
    {"text": "Wtur", "upper": "WTUR", "y": 10},
    {"text": "Taant", "upper": "TAANT", "y": 20},
    {"text": "Git iplk", "upper": "GIT IPLK", "y": 30},
    {"text": "NABBTA OMNZT", "upper": "NABBTA OMNZT", "y": 40},
    {"text": "Ciep.97426", "upper": "CIEP.97426", "y": 50},
    {"text": "Wayarah #", "upper": "WAYARAH #", "y": 60},
    {"text": "WOvA ManD YADAV", "upper": "WOVA MAND YADAV", "y": 70}
]

header_keywords = [
    'GOVERNMENT', 'TOFNDI', 'INCOME', 'DIPART', 'TAX', 'GOVT', 'INDIA', 
    'INCO', 'KAX', 'DEPASINENT', 'ENDLA', 'OFINDL', 'INDLA', 'OMNZT'
]

stop_words = [
    'GOVT', 'GOVERNMENT', 'AUTHORITY', 'DEPARTMENT', 'INDIA', 'INCOME', 'TAX', 
    'ELECTION', 'COMMISSION', 'FATHER', 'HUSBAND', 'DOB', 'DATE', 'CARD', 
    'SIGNATURE', 'ACCOUNT', 'IDENTIFICATION', 'NAME', 'PERMANENT', 'DIRECTOR',
    'REPUBLIC', 'UNIQUE', 'OF', 'TAX', 'MERA', 'AADHAAR', 'EPIC',
    'GENDER', 'MALE', 'FEMALE', 'YEAR', 'BIRTH', 'VID',
    'KAX', 'DEPASINENT', 'LACOME', 'NCOVE', 'DIPLRIMEST', 'INDLA', 'OFINDL', 'ENDLA'
]

header_y_limit = 0.0
for item in clean_data:
    if any(h in item["upper"] for h in header_keywords):
        if item["y"] > header_y_limit: 
            header_y_limit = item["y"]

print("Header Y Limit:", header_y_limit)

candidate_names = []
for item in clean_data:
    ln = item["text"]; ln_up = item["upper"]; y_pos = item["y"]
    
    if header_y_limit > 0 and y_pos <= header_y_limit:
        continue
        
    alpha_chars = sum(c.isalpha() for c in ln)
    if alpha_chars >= 3 and (alpha_chars / len(ln)) > 0.5:
        cand_clean = re.sub(r'[^a-zA-Z\s]', '', ln).strip()
        words = cand_clean.split()
        if 1 <= len(words) <= 4 and len(cand_clean) > 3:
            score = 0
            if len(words) == 2 or len(words) == 3: score += 5
            if all(len(w) >= 2 for w in words): score += 3
            if len(cand_clean) < 4: score -= 2
            
            if cand_clean.istitle() or cand_clean.isupper(): score += 2
            
            if score >= 3:
                candidate_names.append((score, cand_clean, y_pos))

print("Candidates:", candidate_names)

extracted_name = ""
if candidate_names:
    candidate_names.sort(key=lambda x: (-x[0], x[2])) # Sort by Score (desc), then Y position (asc)!
    extracted_name = candidate_names[0][1].title()

print("Extracted Name:", extracted_name)
