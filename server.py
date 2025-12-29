import os, re
from decimal import Decimal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import dropbox

app = FastAPI()

def get_dbx():
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("DROPBOX_ACCESS_TOKEN is missing")
    return dropbox.Dropbox(token)

def get_secret():
    secret = os.environ.get("RENAMER_SECRET")
    if not secret:
        raise RuntimeError("RENAMER_SECRET is missing")
    return secret


class Rename(BaseModel):
    dropbox_path: str
    vendor: str
    amount: float
    date_mmddyyyy: str

def clean(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"

    secret = get_secret()
    if x_renamer_secret != secret:
        raise HTTPException(401)

    dbx = get_dbx()


    vendor = clean(r.vendor)
    amount = f"${Decimal(str(r.amount)):.2f}"
    new_name = f"{vendor}_{amount}_{r.date_mmddyyyy}.pdf"

    folder = r.dropbox_path.rsplit("/", 1)[0]
    new_path = f"{folder}/{new_name}"

    dbx.files_move_v2(r.dropbox_path, new_path, autorename=True)

    return {"status": "ok", "new_name": new_name}
