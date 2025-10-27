# MCP DB Demo (FastAPI + SQLite)

A minimal demo that shows how an AI client could send structured **actions** to an **MCP-like server** which safely queries/updates a database with guardrails (RBAC, parameter binding, and audit logging).

## Files
- `requirements.txt` – Python deps
- `db_init.py` – creates and seeds `demo.db`
- `app.py` – FastAPI server exposing 3 actions
- `client.py` – simple script that calls the actions
- `demo.db` – created by `db_init.py`

## Quick Start

```bash
# 1) Create a virtual environment (optional but recommended)
python3 -m venv .venv && source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Initialize the database
python db_init.py

# 4) Start the server
uvicorn app:app --reload --port 8000
```

In another terminal, test with the client:

```bash
python client.py
```

Or use `curl`:

```bash
# Health
curl -s http://127.0.0.1:8000/healthz | jq

# Read (top customers)
curl -s -X POST http://127.0.0.1:8000/actions/get_top_customers  -H "X-API-Key: reader-key-123"  -H "Content-Type: application/json"  -d '{"limit":5}' | jq

# Paginated read
curl -s -X POST http://127.0.0.1:8000/actions/find_orders  -H "X-API-Key: reader-key-123"  -H "Content-Type: application/json"  -d '{"customer_id":3,"limit":3}' | jq

# Next page (cursor=3)
curl -s -X POST http://127.0.0.1:8000/actions/find_orders  -H "X-API-Key: reader-key-123"  -H "Content-Type: application/json"  -d '{"customer_id":3,"limit":3,"cursor":3}' | jq

# Dry-run write
curl -s -X POST http://127.0.0.1:8000/actions/update_customer_tier  -H "X-API-Key: writer-key-456"  -H "Content-Type: application/json"  -d '{"customer_id":3,"tier":"gold","dry_run":true}' | jq

# Commit write
curl -s -X POST http://127.0.0.1:8000/actions/update_customer_tier  -H "X-API-Key: writer-key-456"  -H "Content-Type: application/json"  -d '{"customer_id":3,"tier":"gold","dry_run":false}' | jq
```

## RBAC Keys
- **Reader:** `X-API-Key: reader-key-123`
- **Writer:** `X-API-Key: writer-key-456`

## Notes
- All SQL uses **parameter binding** (no string concatenation).
- The server writes an **audit log** into `audit_log` table for every action.
- `find_orders` shows **cursor-based pagination** via an offset token.
- This is a minimal MCP-like pattern for demo purposes; in a real MCP server you'd also publish **capabilities** and follow the formal protocol framing.
# mcp_demo # Adds a simple title to README
# mcp_demo
