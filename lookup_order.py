import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

db_path = Path("data") / "shop.db"
uri = os.getenv("MONGODB_URI")

if not db_path.exists():
    raise SystemExit("Missing data/shop.db. Run python seed_sqlite.py.")
if not uri:
    raise SystemExit("Missing MONGODB_URI in .env.")
if len(sys.argv) != 2 or not sys.argv[1].isdigit():
    raise SystemExit("Usage: python lookup_order.py 1001")

order_id = int(sys.argv[1])

with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as sql:
    sql.row_factory = sqlite3.Row
    row = sql.execute(
        """
        SELECT o.order_id, o.order_date, o.quantity, o.status,
               o.total_cents, c.name AS customer_name,
               p.name AS product_name, pay.status AS payment_status
        FROM orders AS o
        JOIN customers AS c ON c.customer_id = o.customer_id
        JOIN products AS p ON p.product_id = o.product_id
        LEFT JOIN payments AS pay ON pay.order_id = o.order_id
        WHERE o.order_id = ?
        """,
        (order_id,),
    ).fetchone()

if row is None:
    raise SystemExit(f"Order {order_id} not found.")

order = dict(row)
order["total_usd"] = f"${order.pop('total_cents') / 100:.2f}"

client = MongoClient(uri, serverSelectionTimeoutMS=10000)
try:
    db = client["ecommerce_support"]
    ticket = db["tickets"].find_one(
        {"order_id": order_id},
        {"_id": 0, "category": 1, "status": 1, "text": 1},
    )
    review = db["reviews"].find_one(
        {"order_id": order_id},
        {"_id": 0, "rating": 1, "sentiment": 1, "text": 1},
    )
finally:
    client.close()

print("ORDER:", order)
print("TICKET:", ticket)
print("REVIEW:", review)