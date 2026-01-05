import proofreader
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

path = Path("backend/buffers")

messages = []

for file_path in path.glob('*.json'):
    with open(file_path, 'r') as f:
        message_buffer = json.load(f)

        messages += message_buffer

validation_queue = []

for message in messages:
    if len(message[2]) == 1 :
        file_path = Path(f"backend/media/{message[2][0]}")

        if file_path.exists() and file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            message[2] = message[2][0]
            validation_queue.append(message)

app = FastAPI()

@app.get("/next")
def get_next():
    if len(validation_queue) > 0:
        message = validation_queue[0]
        validation_queue[0] = validation_queue[-1]
        validation_queue.pop()

        data = proofreader.get_trade_data(f"backend/media/{message[2]}")

        return {
            "message": message,
            "data": data
        }
    
    raise HTTPException(status_code=404, detail="No more items!")
