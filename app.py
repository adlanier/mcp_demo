from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sqlite3
import os
from datetime import datetime
import json

DB_PATH = os.environ.get("DB_PATH", "demo.db")

# --- Simple RBAC via API keys ---
API_KEYS = {
    # key: role
    "reader-key-123": "reader",
    "writer-key-456": "writer",
}

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_auth(x_api_key: Optional[str] = Header(default=None)) -> str:
    role = API_KEYS.get(x_api_key or "", None)
    if not role:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    return role

def require(role_needed: str):
    def _check(role: str = Depends(ensure_auth)) -> str:
        order = {"reader": 1, "writer": 2}
        if order.get(role, 0) < order.get(role_needed, 0):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return role
    return _check

def audit(conn: sqlite3.Connection, actor: str, action: str, params: Dict[str, Any], row_count: int = 0, dry_run: bool = False):
    conn.execute(
        "INSERT INTO audit_log(ts, actor, action, params_json, row_count, dry_run) VALUES (?,?,?,?,?,?)",
        (datetime.utcnow().isoformat(), actor, action, json.dumps(params, separators=(',',':')), row_count, 1 if dry_run else 0),
    )
    conn.commit()

app = FastAPI(title="MCP DB Demo", version="1.0.0")

# --- Models ---
class GetTopCustomersParams(BaseModel):
    limit: int = Field(5, ge=1, le=100)
    since: Optional[str] = None  # ISO timestamp filter on updated_at

class FindOrdersParams(BaseModel):
    customer_id: int
    since: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    cursor: Optional[int] = Field(None, description="Offset-based cursor")

class UpdateCustomerTierParams(BaseModel):
    customer_id: int
    tier: str = Field(pattern="^(bronze|silver|gold)$")
    dry_run: bool = True

# --- Actions ---
@app.post("/actions/get_top_customers")
def get_top_customers(params: GetTopCustomersParams, role: str = Depends(require("reader"))):
    conn = get_conn()
    sql = "SELECT id, name, revenue, tier, updated_at FROM customers"
    args: List[Any] = []
    if params.since:
        sql += " WHERE updated_at >= ?"
        args.append(params.since)
    sql += " ORDER BY revenue DESC LIMIT ?"
    args.append(params.limit)
    rows = conn.execute(sql, args).fetchall()
    out = [dict(r) for r in rows]
    audit(conn, actor=role, action="get_top_customers", params=params.model_dump(), row_count=len(out))
    return {"ok": True, "rows": out, "row_count": len(out), "cursor": None}

@app.post("/actions/find_orders")
def find_orders(params: FindOrdersParams, role: str = Depends(require("reader"))):
    conn = get_conn()
    offset = params.cursor or 0
    sql = "SELECT id, customer_id, amount, created_at FROM orders WHERE customer_id = ?"
    args: List[Any] = [params.customer_id]
    if params.since:
        sql += " AND created_at >= ?"
        args.append(params.since)
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    args += [params.limit, offset]
    rows = conn.execute(sql, args).fetchall()
    out = [dict(r) for r in rows]
    next_cursor = None if len(out) < params.limit else offset + params.limit
    audit(conn, actor=role, action="find_orders", params=params.model_dump(), row_count=len(out))
    return {"ok": True, "rows": out, "row_count": len(out), "cursor": next_cursor}

@app.post("/actions/update_customer_tier")
def update_customer_tier(params: UpdateCustomerTierParams, role: str = Depends(require("writer"))):
    conn = get_conn()
    # Validate tier enum via regex in Pydantic; ensure customer exists
    existing = conn.execute("SELECT id, tier FROM customers WHERE id = ?", (params.customer_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="customer_id not found")

    if params.dry_run:
        audit(conn, actor=role, action="update_customer_tier", params=params.model_dump(), row_count=0, dry_run=True)
        return {"ok": True, "row_count": 0, "dry_run": True, "hint": "Set dry_run=false to commit"}

    cur = conn.execute("UPDATE customers SET tier = ?, updated_at = ? WHERE id = ?", (params.tier, datetime.utcnow().isoformat(), params.customer_id))
    conn.commit()
    row_count = cur.rowcount
    audit(conn, actor=role, action="update_customer_tier", params=params.model_dump(), row_count=row_count, dry_run=False)
    return {"ok": True, "row_count": row_count, "dry_run": False}

@app.get("/healthz")
def healthz():
    return {"ok": True}
