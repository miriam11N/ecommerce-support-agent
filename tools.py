import sqlite3
from pathlib import Path
import os

from dotenv import load_dotenv
from pymongo import MongoClient
DB_PATH = Path(__file__).resolve().parent / "data" / "shop.db"


def lookup_order(order_id: int) -> dict | None:
    """Return one order with its customer, product, and payment details."""
    if not isinstance(order_id, int) or order_id < 1:
        raise ValueError("order_id must be a positive integer")

    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")

    with sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT o.order_id, o.order_date, o.quantity, o.status,
                   o.total_cents, o.customer_id, o.product_id,
                   c.name AS customer_name, p.name AS product_name,
                   pay.status AS payment_status
            FROM orders AS o
            JOIN customers AS c ON c.customer_id = o.customer_id
            JOIN products AS p ON p.product_id = o.product_id
            LEFT JOIN payments AS pay ON pay.order_id = o.order_id
            WHERE o.order_id = ?
            """,
            (order_id,),
        ).fetchone()

    if row is None:
        return None

    order = dict(row)
    order["total_usd"] = f"${order.pop('total_cents') / 100:.2f}"
    return order

def search_product_reviews(product_id: int, limit: int = 3) -> list[dict]:
    """Return a few reviews for a product, without inventing review content."""
    if not isinstance(product_id, int) or product_id < 1:
        raise ValueError("product_id must be a positive integer")
    if not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")

    load_dotenv(Path(__file__).resolve().parent / ".env")
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is missing.")

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    try:
        cursor = (
            client["ecommerce_support"]["reviews"]
            .find(
                {"product_id": product_id},
                {
                    "_id": 0,
                    "order_id": 1,
                    "rating": 1,
                    "sentiment": 1,
                    "text": 1,
                },
            )
            .sort("order_id", 1)
            .limit(limit)
        )
        return list(cursor)
    finally:
        client.close()