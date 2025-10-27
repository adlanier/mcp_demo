import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.environ.get("DB_PATH", "demo.db")

schema = """
PRAGMA foreign_keys=ON;

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS audit_log;

CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  revenue REAL NOT NULL,
  tier TEXT NOT NULL CHECK (tier IN ('bronze','silver','gold')),
  updated_at TEXT NOT NULL
);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  params_json TEXT NOT NULL,
  row_count INTEGER,
  dry_run INTEGER NOT NULL DEFAULT 0
);
"""

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(schema)

    now = datetime.utcnow()
    customers = [
        (1, "Acme Corp", 125000.0, "gold", now.isoformat()),
        (2, "Globex", 78000.0, "silver", (now).isoformat()),
        (3, "Initech", 54000.0, "silver", (now).isoformat()),
        (4, "Umbrella Co", 22000.0, "bronze", (now).isoformat()),
        (5, "Soylent", 94000.0, "gold", (now).isoformat()),
        (6, "Hooli", 150000.0, "gold", (now).isoformat()),
    ]
    cur.executemany("INSERT INTO customers(id,name,revenue,tier,updated_at) VALUES (?,?,?,?,?)", customers)

    orders = []
    oid = 1
    for cid in range(1, 7):
        for k in range(5):
            orders.append((oid, cid, 1000 * (cid + k), (now - timedelta(days=cid*k+1)).isoformat()))
            oid += 1
    cur.executemany("INSERT INTO orders(id,customer_id,amount,created_at) VALUES (?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print(f"Initialized DB at {DB_PATH} with {len(customers)} customers and {len(orders)} orders.")

if __name__ == "__main__":
    main()
