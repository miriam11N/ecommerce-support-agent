import os
import random
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
if not uri:
    raise SystemExit("MONGODB_URI is missing from .env")

sql_path = Path("data") / "shop.db"
if not sql_path.exists():
    raise SystemExit("data/shop.db is missing. Run python seed_sqlite.py first.")

with sqlite3.connect(sql_path) as sql:
    orders = sql.execute("""
        SELECT o.order_id, o.customer_id, o.product_id,
               o.status, p.name
        FROM orders AS o
        JOIN products AS p ON p.product_id = o.product_id
        ORDER BY o.order_id
    """).fetchall()

review_templates = [
    (5, "The {product} works well and arrived as expected.", "positive"),
    (4, "Happy with the {product}. Setup was straightforward.", "positive"),
    (3, "The {product} is okay, but delivery took longer than expected.", "neutral"),
    (2, "The {product} did not meet my expectations.", "negative"),
    (1, "My {product} arrived damaged. I need help with a replacement.", "negative"),
]

ticket_templates = {
    "delivered": [
        ("return", "I want to return the {product} from order {order_id}."),
        ("product_issue", "The {product} in order {order_id} is not working properly."),
        ("billing", "I have a billing question about order {order_id}."),
    ],
    "shipped": [
        ("shipping", "Where is my {product}? My order number is {order_id}."),
        ("delivery", "The tracking for order {order_id} has not updated."),
    ],
    "processing": [
        ("status", "Can you check the status of order {order_id}?"),
        ("cancel", "Can I cancel order {order_id} before it ships?"),
    ],
}

rng = random.Random(42)
client = MongoClient(uri, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")
    db = client["ecommerce_support"]
    reviews = db["reviews"]
    tickets = db["tickets"]

    for order_id, customer_id, product_id, status, product_name in orders:
        if status == "delivered":
            rating, template, sentiment = rng.choice(review_templates)
            review = {
                "_id": f"review-{order_id}",
                "order_id": order_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "product_name": product_name,
                "rating": rating,
                "sentiment": sentiment,
                "text": template.format(product=product_name),
            }
            reviews.update_one(
                {"_id": review["_id"]},
                {"$set": review},
                upsert=True,
            )

        category, template = rng.choice(ticket_templates[status])
        ticket = {
            "_id": f"ticket-{order_id}",
            "order_id": order_id,
            "customer_id": customer_id,
            "product_id": product_id,
            "category": category,
            "status": "open",
            "text": template.format(
                product=product_name,
                order_id=order_id,
            ),
        }
        tickets.update_one(
            {"_id": ticket["_id"]},
            {"$set": ticket},
            upsert=True,
        )

    reviews.create_index("product_id")
    tickets.create_index("order_id")

    print(f"SQLite orders: {len(orders)}")
    print(f"MongoDB reviews: {reviews.count_documents({})}")
    print(f"MongoDB tickets: {tickets.count_documents({})}")
    print("Sample ticket:", tickets.find_one(
        {"order_id": 1001},
        {"_id": 0, "order_id": 1, "category": 1, "text": 1},
    ))
finally:
    client.close()