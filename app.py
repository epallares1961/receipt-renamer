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
    date_mmddyyyy: str

def clean(text):
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"

def get_dbx():
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("Missing DROPBOX_ACCESS_TOKEN")
    return dropbox.Dropbox(token)

def get_secret():
    secret = os.environ.get("RENAMER_SECRET")
    if not secret:
        raise RuntimeError("Missing RENAMER_SECRET")
    return secret

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/rename")
def rename_receipt(r: RenameRequest, x_renamer_secret: str = Header("")):
    if x_renamer_secret != get_secret():
        raise HTTPException(status_code=401, detail="Unauthorized")

    dbx = get_dbx()

    vendor = clean(r.vendor)
    amount = f"${Decimal(str(r.amount)):.2f}"
    new_name = f"{vendor}_{amount}_{r.date_mmddyyyy}.pdf"

    folder = r.dropbox_path.rsplit("/", 1)[0]
    new_path = f"{folder}/{new_name}"

    dbx.files_move_v2(r.dropbox_path, new_path, autorename=True)
    return {"status": "ok", "new_name": new_name}
@app.get("/list_pdfs")
def list_pdfs(folder: str, x_renamer_secret: str = Header("")):
    if x_renamer_secret != get_secret():
        raise HTTPException(status_code=401, detail="Unauthorized")

    dbx = get_dbx()

    result = dbx.files_list_folder(folder)
    pdfs = []

    for entry in result.entries:
        if entry.name.lower().endswith(".pdf"):
            pdfs.append(entry.path_display)

    return {"pdf_files": pdfs}
