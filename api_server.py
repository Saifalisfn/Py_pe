import threading
import time
import json
import urllib.parse
import requests as http_requests
import re

import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from database import db

app = FastAPI(title="BharatPe Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for pending OTP sessions (mobile -> {requests.Session, csrf_token, uuid})
_pending_logins: dict = {}

# Watcher state
_watcher_thread: Optional[threading.Thread] = None
_watcher_stop = threading.Event()


# ─── Models ──────────────────────────────────────────────────────────────────

class OtpRequest(BaseModel):
    mobile: str

class OtpVerify(BaseModel):
    mobile: str
    otp: str

class ConfigUpdate(BaseModel):
    polling_interval: Optional[int] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    webhook_enabled: Optional[bool] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: Optional[bool] = None


# ─── Auth ────────────────────────────────────────────────────────────────────

@app.post("/auth/request-otp")
def request_otp(body: OtpRequest):
    mobile = body.mobile.strip()
    session = http_requests.Session()

    try:
        home_res = session.get("https://enterprise.bharatpe.in/", timeout=15)
    except Exception as e:
        raise HTTPException(502, f"BharatPe unreachable: {e}")

    match = re.search(r'name="_token"\s+value="([^"]+)"', home_res.text)
    if not match:
        raise HTTPException(502, "CSRF token not found")

    csrf_token = match.group(1)
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://enterprise.bharatpe.in/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
    }

    res = session.post(
        "https://enterprise.bharatpe.in/v1/api/user/requestotp",
        data={"mobile": mobile, "_token": csrf_token},
        headers=headers,
        timeout=15
    )

    uuid = ""
    try:
        otp_json = res.json()
        uuid = otp_json.get("data", {}).get("uuid") or otp_json.get("uuid", "")
    except Exception:
        pass

    _pending_logins[mobile] = {"session": session, "csrf_token": csrf_token, "uuid": uuid, "headers": headers}
    return {"message": f"OTP sent to {mobile}", "uuid": uuid}


@app.post("/auth/verify-otp")
def verify_otp(body: OtpVerify):
    mobile = body.mobile.strip()
    pending = _pending_logins.get(mobile)
    if not pending:
        raise HTTPException(400, "No pending OTP request for this mobile. Call /auth/request-otp first.")

    session = pending["session"]
    csrf_token = pending["csrf_token"]
    uuid = pending["uuid"]
    headers = pending["headers"]

    res = session.post(
        "https://enterprise.bharatpe.in/v1/api/user/verifyotp",
        data={"mobile": mobile, "uuid": uuid, "otp": body.otp, "_token": csrf_token},
        headers=headers,
        timeout=15
    )

    if res.status_code != 200:
        raise HTTPException(401, f"OTP verification failed: {res.text}")

    verify_data = res.json()
    token = (verify_data.get("data", {}).get("token") or
             verify_data.get("token") or
             verify_data.get("data", {}).get("accessToken") or
             verify_data.get("access_token"))

    if not token:
        raise HTTPException(502, "Token not found in response")

    auth_headers = {**headers, "Authorization": f"Bearer {token}", "token": token}
    session.get("https://enterprise.bharatpe.in/dashboard", headers=auth_headers, allow_redirects=False, timeout=15)
    profile_res = session.get("https://enterprise.bharatpe.in/api/v1/merchant/profile", headers=auth_headers, allow_redirects=False, timeout=15)

    merchant_id = "unknown"
    if profile_res.status_code == 200:
        try:
            m_data = profile_res.json().get("data", {})
            merchant_id = (m_data.get("merchant", {}).get("id") or
                           m_data.get("merchantId") or
                           m_data.get("id") or merchant_id)
        except Exception:
            pass

    db.save_session(
        mobile=mobile,
        token=token,
        merchant_id=str(merchant_id),
        csrf_token=csrf_token,
        cookies=session.cookies.get_dict(),
        user_agent=headers["User-Agent"]
    )

    _pending_logins.pop(mobile, None)
    return {"message": f"Login complete for {mobile}", "merchant_id": merchant_id}


# ─── Sessions ────────────────────────────────────────────────────────────────

@app.get("/sessions")
def list_sessions():
    sessions = db.get_all_sessions()
    # Strip sensitive fields
    safe = [{"mobile": s["mobile"], "merchant_id": s["merchant_id"], "updated_at": str(s.get("updated_at", ""))} for s in sessions]
    return {"count": len(safe), "sessions": safe}


@app.delete("/sessions/{mobile}")
def delete_session(mobile: str):
    db.delete_session(mobile)
    return {"message": f"Session for {mobile} deactivated"}


# ─── Transactions ────────────────────────────────────────────────────────────

@app.get("/transactions")
def get_transactions(mobile: Optional[str] = None, limit: int = 50):
    if mobile:
        rows = db.get_transactions_by_mobile(mobile, limit)
    else:
        rows = db.fetchall(
            "SELECT session_mobile, transaction_id, utr, amount, status, payer_name, payer_vpa, transaction_date "
            "FROM transactions ORDER BY transaction_date DESC LIMIT %s",
            (limit,)
        )
    return {"count": len(rows), "transactions": [dict(r) for r in rows]}


@app.post("/transactions/fetch")
def fetch_transactions(mobile: Optional[str] = None):
    """Trigger live fetch from BharatPe API for all or one account."""
    from api import fetch_bharatpe_data
    try:
        fetch_bharatpe_data(mobile=mobile, save_to_db=True)
        return {"message": "Fetch complete"}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── UTR ─────────────────────────────────────────────────────────────────────

@app.get("/utr/{utr_number}")
def search_utr(utr_number: str):
    from utr_finder import find_utr
    found, data = find_utr(utr_number)
    if not found:
        return {"found": False, "data": None}
    return {"found": True, "data": data}


@app.get("/utr/{utr_number}/history")
def utr_history(utr_number: str, limit: int = 20):
    logs = db.get_utr_search_history(utr=utr_number, limit=limit)
    return {"utr": utr_number, "history": [dict(r) for r in logs]}


# ─── Stats ───────────────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats():
    sessions = db.get_all_sessions()
    txn_count = db.fetchall("SELECT COUNT(*) as c FROM transactions")[0]["c"]
    notif_count = db.fetchall("SELECT COUNT(*) as c FROM notifications")[0]["c"]
    utr_count = db.fetchall("SELECT COUNT(*) as c FROM utr_logs")[0]["c"]
    recent_searches = db.get_utr_search_history(limit=5)
    return {
        "active_sessions": len(sessions),
        "total_transactions": txn_count,
        "total_notifications": notif_count,
        "utr_searches": utr_count,
        "recent_utr_searches": [dict(r) for r in recent_searches]
    }


# ─── Config ──────────────────────────────────────────────────────────────────

@app.get("/config")
def get_config():
    cfg = db.get_config()
    # Strip sensitive fields from response
    safe_fields = ["polling_interval", "webhook_url", "webhook_enabled", "telegram_enabled", "telegram_chat_id", "updated_at"]
    return {k: str(v) if v is not None else None for k, v in dict(cfg).items() if k in safe_fields}


@app.put("/config")
def update_config(body: ConfigUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    db.update_config(**updates)
    return {"message": "Config updated", "updated": list(updates.keys())}


# ─── Watcher ─────────────────────────────────────────────────────────────────

def _watcher_loop():
    import watcher
    while not _watcher_stop.is_set():
        watcher.check_for_updates()
        cfg = db.get_config()
        interval = cfg.get("polling_interval", 120)
        _watcher_stop.wait(timeout=interval)


@app.get("/watcher/status")
def watcher_status():
    running = _watcher_thread is not None and _watcher_thread.is_alive()
    return {"running": running}


@app.post("/watcher/start")
def start_watcher():
    global _watcher_thread, _watcher_stop
    if _watcher_thread and _watcher_thread.is_alive():
        return {"message": "Watcher already running"}
    _watcher_stop.clear()
    _watcher_thread = threading.Thread(target=_watcher_loop, daemon=True)
    _watcher_thread.start()
    return {"message": "Watcher started"}


@app.post("/watcher/stop")
def stop_watcher():
    global _watcher_thread
    if not _watcher_thread or not _watcher_thread.is_alive():
        return {"message": "Watcher not running"}
    _watcher_stop.set()
    _watcher_thread.join(timeout=5)
    return {"message": "Watcher stopped"}


# ─── Static / SPA ────────────────────────────────────────────────────────────

_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        return FileResponse(os.path.join(_DIST, "index.html"))


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
