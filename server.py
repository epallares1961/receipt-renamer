import os, re
from decimal import Decimal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import dropbox

app = FastAPI(title="Receipt Renamer")

class RenameRequest(BaseModel):
    dropbox_path: str
    vendor: str
    amount: float
    date_mmddyyyy: str  # MMDDYYYY

def clean_vendor(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"

def get_dbx():
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("DROPBOX_ACCESS_TOKEN is missing in Render env vars")
    return dropbox.Dropbox(token)

def get_secret():
    secret = os.environ.get("RENAMER_SECRET")
    if not secret:
        raise RuntimeError("RENAMER_SECRET is missing in Render env vars")
    return secret

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/rename")
def rename_receipt(payload: RenameRequest, x_renamer_secret: str = Header(default="")):
    if x_renamer_secret != get_secret():
        raise HTTPException(status_code=401, detail="Unauthorized")

    dbx = get_dbx()

    vendor = clean_vendor(payload.vendor)
    amount = f"${Decimal(str(payload.amount)):.2f}"
    new_name = f"{vendor}_{amount}_{payload.date_mmddyyyy}.pdf"

    folder = payload.dropbox_path.rsplit("/", 1)[0]
    new_path = f"{folder}/{new_name}"

    dbx.files_move_v2(payload.dropbox_path, new_path, autorename=True)

    return {"status": "ok", "new_name": new_name, "new_path": new_path}
