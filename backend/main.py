import proofreader
import json
import bisect
import re
from datetime import datetime
from dateutil import parser
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import random

path = Path("buffers")

messages = []

for file_path in sorted(
    path.glob("*.json"),
    key=lambda p: int(p.stem)
):
    with open(file_path, "r") as f:
        message_buffer = json.load(f)

        messages += message_buffer

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for message in messages:
    message.append(random.random() > .5)

messages = messages[::-1]

def find_before_index(target: float):
    keys = [m[1] for m in messages]
    return bisect.bisect_left(keys, target)

def find_equal_index(target: float):
    keys = [m[1] for m in messages]
    i = bisect.bisect_left(keys, target)
    if i != len(keys) and keys[i] == target:
        return i
    return -1

def parse_date(text, epoch_context):
    context_date = datetime.fromtimestamp(epoch_context)

    if context_date is None:
        context_date = datetime.now()
    
    match = re.search(r'(?:d|date)\s*[:\-]\s*(.*)', text, re.IGNORECASE)
    if not match:
        return None
    
    raw_val = match.group(1).split('\n')[0].lower().strip()

    if 'today' in raw_val:
        return context_date.date()
    
    normalized = re.sub(r'[–—\.]', '/', raw_val)

    normalized = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', normalized)

    normalized = re.sub(r'\(.*?\)', '', normalized).strip()

    possibilities = []
    
    try:
        possibilities.append(parser.parse(normalized, dayfirst=True, yearfirst=False))
    except (ValueError, OverflowError):
        pass
        
    try:
        possibilities.append(parser.parse(normalized, dayfirst=False, yearfirst=False))
    except (ValueError, OverflowError):
        pass

    if not possibilities:
        return None
    
    best_match = min(possibilities, key=lambda d: abs((d - context_date).total_seconds()))
    
    return best_match.date()

@app.get("/messages")
def get_next(before: float = 2000000000, limit: int = 10, passed: str = "none"):
    index = find_before_index(before)
    result = []

    for i in range(index - 1, -1, -1):
        m = messages[i]
        m_passed = m[3]

        should_append = False
        if passed == "none":
            should_append = True
        elif passed == "true" and m_passed is True:
            should_append = True
        elif passed == "false" and m_passed is False:
            should_append = True

        if should_append:
            result.append(m)
            if len(result) == limit:
                break
    
    return result

@app.get("/media/{file_name}")
def get_next(file_name: str):
    file_path = Path("media") / file_name

    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="No media found!")

@app.get("/autofill/{timestamp}")   
def get_next(timestamp: float):
    index = find_equal_index(timestamp)

    print(index, timestamp)

    if index > -1:
        print(index)
        message = messages[index]

        file_path = Path("media") / message[2][0]

        if file_path.exists() and file_path.is_file():
            data = proofreader.get_trade_data(str(file_path))

            date = parse_date(message[0], message[1])

            return {
                "trade": data,
                "date": date
            }
    
    raise HTTPException(status_code=404, detail="No media found!")

@app.get("/thumbnail/{file_name}")
def get_next(file_name: str):
    file_path = Path("thumbnails") / file_name

    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="No media found!")

@app.post("/tag/{file_name}")
def get_next(file_name: str, data: dict = Body(...)):
    file_path = tags_dir / f"{file_name}.json"

    try:
        with open(file_path, "w") as f:
            f.write(json.dumps(data, separators=(',', ':')))
        return {"message": "Tag saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
