# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
# Python deps
pip install -r requirements.txt

# Initialize database (run once)
python setup_database.py

# Run CLI
python main.py

# Run API server (serves dashboard + REST API)
python api_server.py
# Dashboard → http://localhost:8000
# API docs  → http://localhost:8000/docs
```

### Frontend (dev mode)
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 — proxies /api → :8000
npm run build      # outputs to frontend/dist/, served by FastAPI
```

## Architecture

CLI tool for managing multiple BharatPe merchant accounts. Polls the BharatPe enterprise API and persists data to a remote MySQL database.

**Data flow:**
1. `login.py` — authenticates via BharatPe web (OTP flow), harvests bearer token + merchant ID + cookies, saves session to `sessions` table
2. `api.py` — uses saved sessions to fetch transactions from `payments-tesseract.bharatpe.in`, saves to `transactions` table
3. `utr_finder.py` — searches UTR via `enterprise.bharatpe.in/v1/api/transaction/recon`; hits DB cache first, then live API
4. `watcher.py` — polling loop (default 120s interval); detects new transactions by comparing latest UTR against last known; fires webhook + Telegram alerts
5. `database.py` — singleton `db` object used by all modules; handles reconnection automatically
6. `main.py` — interactive menu tying all modules together
7. `api_server.py` — FastAPI server; all endpoints import the same modules above. Serves React SPA from `frontend/dist/` in production. OTP login is split into `/auth/request-otp` + `/auth/verify-otp`, with pending state held in `_pending_logins` dict (in-memory, single process)

**Database tables:** `sessions`, `transactions`, `utr_logs`, `notifications`, `config`

**Config** (webhook URL, Telegram token, polling interval) lives in the `config` table (single row, id=1), not in `.env`. Update via `db.update_config(...)`.

## Environment

`.env` holds only MySQL connection settings (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_POOL_SIZE`). All runtime config (webhooks, Telegram, polling) is stored in the `config` DB table.

## Key behaviors

- Sessions soft-deleted (not dropped) when API returns 401/302 — `is_active = FALSE`
- Transactions upserted by `(session_mobile, transaction_id)` unique key — safe to re-fetch
- `watcher.py` detects new payments by comparing latest transaction UTR against last entry in `notifications` table, not by timestamp
