import datetime
import requests
import os
import json

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
READER_KEY = os.environ.get("READER_KEY", "reader-key-123")
WRITER_KEY = os.environ.get("WRITER_KEY", "writer-key-456")

def post(path, payload, key):
    r = requests.post(f"{BASE}{path}", json=payload, headers={"X-API-Key": key})
    print(f"POST {path} status={r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)

def main():
    now = datetime.datetime.utcnow().isoformat()

    # 1) read
    post("/actions/get_top_customers", {"limit": 5}, READER_KEY)
    # 2) paginated read
    post("/actions/find_orders", {"customer_id": 3, "limit": 3}, READER_KEY)
    post("/actions/find_orders", {"customer_id": 3, "limit": 3, "cursor": 3}, READER_KEY)
    # 3) safe write (dry run)
    post("/actions/update_customer_tier", {"customer_id": 3, "tier": "gold", "dry_run": True}, WRITER_KEY)
    # 4) commit write
    post("/actions/update_customer_tier", {"customer_id": 3, "tier": "gold", "dry_run": False}, WRITER_KEY)
    # 5) read
    post("/actions/get_top_customers", {"limit": 1, "since": now}, READER_KEY)

if __name__ == "__main__":
    main()
