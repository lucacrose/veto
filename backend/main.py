import json
import proofreader
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
ANNOTATED_DIR = Path("annotated")
MEDIA_DIR = Path("media")
THUMBNAILS_DIR = Path("thumbnails")
BUFFERS_DIR = Path("buffers")

for d in [ANNOTATED_DIR, MEDIA_DIR, THUMBNAILS_DIR]: d.mkdir(exist_ok=True)

# Static Serving
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
app.mount("/thumbnails", StaticFiles(directory=THUMBNAILS_DIR), name="thumbnails")

# Load Messages once on startup
MESSAGES = []
if BUFFERS_DIR.exists():
    for file_path in sorted(BUFFERS_DIR.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
        with open(file_path, "r") as f:
            MESSAGES += json.load(f)

class ActionRequest(BaseModel):
    filename: str
    message_index: int
    action: str 
    metadata: Optional[dict] = None

def get_status(filename: str) -> str:
    if (ANNOTATED_DIR / f"{filename}.json").exists(): return "accepted"
    if (ANNOTATED_DIR / f"{filename}.skipped").exists(): return "rejected"
    return "pending"

@app.get("/stats")
def get_stats():
    accepted = len(list(ANNOTATED_DIR.glob("*.json")))
    rejected = len(list(ANNOTATED_DIR.glob("*.skipped")))
    total = len([m for m in MESSAGES if m[2]])
    return {"accepted": accepted, "rejected": rejected, "remaining": total - (accepted + rejected)}

@app.get("/next")
def get_next_trade(exclude: List[str] = Query([])):
    """Finds next trade not in 'exclude' list and not already on disk."""
    for i, msg in enumerate(MESSAGES):
        if not msg[2]: continue
        filename = msg[2][0]
        
        # Skip if finished or currently in frontend buffer
        if get_status(filename) == "pending" and filename not in exclude:
            try:
                img_path = MEDIA_DIR / filename
                # Heavy CV Operation
                metadata = proofreader.get_trade_data(str(img_path))
                return {"message_index": i, "filename": filename, "metadata": metadata}
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
    return None

@app.post("/action")
def perform_action(req: ActionRequest):
    if req.action == "accept":
        with open(ANNOTATED_DIR / f"{req.filename}.json", "w") as f:
            json.dump(req.metadata, f, indent=2)
    else:
        (ANNOTATED_DIR / f"{req.filename}.skipped").touch()
    return {"status": "ok"}