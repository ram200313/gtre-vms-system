import re
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

boilerplate = [
    "INCOME TAX DEPARTMENT",
    "GOVERNMENT OF INDIA",
    "GOVT OF INDIA",
    "PERMANENT ACCOUNT NUMBER CARD",
    "PERMANENT ACCOUNT NUMBER",
    "SIGNATURE",
    "FATHERS NAME",
    "DATE OF BIRTH",
    "UNIQUE IDENTIFICATION AUTHORITY",
    "ELECTION COMMISSION",
    "MERA AADHAAR",
    "AADMI KA ADHIKAR"
]

candidates = [
    "Fetanen Arcoue Mtet Cud",
    "TiYa Rld YAUAV",
    "ADITYA GANGBOIR",
    "Fe Ciepjg Brie",
    "Ponaarett Accovm MunrCin",
    "IUN AAX DEPARIMENT",
    "Niranjan Kumar"
]

for cand in candidates:
    cand_up = cand.upper()
    max_sim = 0
    best_match = ""
    for b in boilerplate:
        sim = similar(cand_up, b)
        if sim > max_sim:
            max_sim = sim
            best_match = b
            
    print(f"Cand: '{cand}' | Max Sim: {max_sim:.2f} to '{best_match}'")
