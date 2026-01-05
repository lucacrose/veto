import proofreader
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

path = Path("buffers")

messages = []

for file_path in path.glob('*.json'):
    with open(file_path, 'r') as f:
        message_buffer = json.load(f)

        messages += message_buffer

validation_queue = []

for message in messages:
    if len(message[2]) == 1 :
        file_path = Path("media") / message[2][0]

        if file_path.exists() and file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            message[2] = message[2][0]
            validation_queue.append(message)

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

@app.get("/next")
def get_next():
    if len(validation_queue) > 0:
        message = validation_queue[0]
        validation_queue[0] = validation_queue[-1]
        validation_queue.pop()

        data = proofreader.get_trade_data(f"media/{message[2]}")

        return {
            "message": message,
            "data": data
        }
    
    raise HTTPException(status_code=404, detail="No more items!")

@app.get("/media/{file_name}")
def get_next(file_name: str):
    file_path = Path("media") / file_name

    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="No media found!")

@app.get("/thumbnail/{file_name}")
def get_next(file_name: str):
    file_path = Path("thumbnails") / file_name

    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="No media found!")
