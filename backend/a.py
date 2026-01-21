import re
from datetime import datetime
from dateutil import parser

def parse_date_value(raw_val, epoch_context):
    context_date = datetime.fromtimestamp(epoch_context)
    if not context_date:
        context_date = datetime.now()
    
    raw_val = raw_val.lower().strip()

    if 'today' in raw_val:
        return context_date.date()
    
    normalized = re.sub(r'[–—\.]', '/', raw_val)
    normalized = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', normalized)
    normalized = re.sub(r'\(.*?\)', '', normalized).strip()

    possibilities = []

    formats_to_try = [
        normalized,
        f"{normalized}/{context_date.year}",
        f"{normalized}/{context_date.year - 1}",
        f"{normalized}/{context_date.year + 1}"
    ]

    for fmt in formats_to_try:
        for df in [True, False]:
            try:
                dt = parser.parse(fmt, dayfirst=df, default=context_date)
                possibilities.append(dt)
            except (ValueError, OverflowError, TypeError):
                continue

    if not possibilities:
        return None
    
    best_match = min(possibilities, key=lambda d: abs((d - context_date).total_seconds()))
    
    return best_match.date()

def decode_text(data):
    data = data.lower()

    patterns = {
        "sender": r"(?:s:|sender:)\s*(.*)",
        "receiver": r"(?:r:|reciever:)\s*(.*)",
        "date": r"(?:d:|date:)\s*(.*)"
    }
    
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, data)
        results[key] = match.group(1).strip() if match else "not found"
        
    return results

raw_text = """
Vesp, Scissors, Bih / RSB
2.428M vs 1.1M (1.328M op)
s: Highly_DeveIoped
r: AnonymizingTheNet
d: today

Chicken vs IV PV 70k robux 
685k vs 630k (55k OP)
s: jbkozz
r: GhstPpI
D: 1/19/26

anc / gcow
105k v 80k (25k op)
Sender: aidliebe
Reciever: LunarHoards
Date: 1/19/26
"""

current_epoch = datetime.now().timestamp()

item = decode_text(raw_text)

print(f"Sender: {item['sender']} | Receiver: {item['receiver']} | Date: {parse_date_value(item['date'], current_epoch)}")