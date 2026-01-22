from pathlib import Path
import json
import re
from datetime import datetime
from dateutil import parser
import time

def parse_date_value(raw_val, epoch_context):
    context_dt = datetime.fromtimestamp(epoch_context)
    context_date = context_dt.date()

    raw_val = raw_val.lower().strip()

    if "today" in raw_val:
        return context_date
    
    normalized = re.sub(r"[–—\.]", "/", raw_val)
    normalized = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", normalized)
    normalized = re.sub(r"\(.*?\)", "", normalized).strip()

    possibilities = []

    for dayfirst in (True, False):
        try:
            dt = parser.parse(
                normalized,
                dayfirst=dayfirst,
                default=context_dt
            )
        except (ValueError, OverflowError, TypeError):
            continue

        parsed_date = dt.date()

        delta_days = abs((parsed_date - context_date).days)

        if delta_days > 1:
            try:
                parsed_date = parsed_date.replace(year=context_date.year)
            except ValueError:
                parsed_date = parsed_date.replace(
                    year=context_date.year,
                    day=28
                )

        possibilities.append(parsed_date)

    if not possibilities:
        return None
    
    best = min(
        possibilities,
        key=lambda d: abs((d - context_date).days)
    )

    return best

def decode_text(data):
    data = data.lower()

    patterns = {
        "sender": r"(?m)^\s*(?:sender|s)\s*[:\-]?\s*(.*)",
        "receiver": r"(?m)^\s*(?:rece[iv]{2}er|r)\s*[:\-]?\s*(.*)",
        "date": r"(?m)^\s*(?:date|d)\s*[:\-]?\s*(.*)"
    }
    
    results = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, data)
        if matches:
            val = matches[-1].strip().strip('<>').strip()

            if key == "date" and "," in val:
                val = val.split(',')[-1].strip()
                
            results[key] = val
        else:
            results[key] = None
                
    return results

import re

def is_valid_roblox_name(name):
    if not (3 <= len(name) <= 20):
        return False, "Name must be between 3 and 20 characters."
    
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        return False, "Only letters, numbers, and one underscore allowed."
    
    if name.startswith('_') or name.endswith('_'):
        return False, "Underscore cannot be at the start or end."
    
    if "__" in name:
        return False, "Cannot have multiple underscores in a row."
    
    if name.count('_') > 1:
        return False, "Only one underscore is allowed."

    return True, "Valid username."

path = Path("backend/buffers")

messages = []

for file_path in sorted(
    path.glob("*.json"),
    key=lambda p: int(p.stem)
):
    with open(file_path, "r") as f:
        message_buffer = json.load(f)

        messages += message_buffer

n = 0
\
names = set()

for message in messages:
    if len(message[2]) != 1:
        continue

    info = decode_text(message[0])

    if info["date"]:
        info["date"] = parse_date_value(info["date"], message[1])

    b = False

    for pattern, value in info.items():
        if pattern in ["sender", "receiver"] and (value and not is_valid_roblox_name(value)) or value == None:
            #print(pattern, value)
            b = True
            n += 1
            break

    if b and False:
        print(message[0])
        print(info)
        print("\n\n")

        time.sleep(3)
        pass
    elif not b:
        names.add(info["sender"])
        names.add(info["receiver"])

    #time.sleep(.05)

print(len(messages), n)

print(len(names))

import requests

response = requests.post("https://users.roblox.com/v1/usernames/users", json={
  "usernames": list(names)[:200],
  "excludeBannedUsers": False
})

print(json.dumps(response.json(), indent=4))
