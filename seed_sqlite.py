from datetime import date, timedelta
from pathlib import Path
import random
import sqlite3

random.seed(42)

DB_PATH = Path("data") / "shop.db"
DB_PATH.parent.mkdir(exist_ok=True)

customers = [
    (1, "Alex Rivera", "alex@example.com"),
    (2, "Jordan Lee", "jordan@example.com"),
    (3, "Sam Patel", "sam@example.com"),
    (4, "Taylor Brooks", "taylor@example.com"),
    (5, "Casey Morgan", "casey@example.com"),
]

products = [
    (1, "Wireless Headphones", 7999),
    (2, "Mechanical Keyboard", 10900),
    (3, "USB-C Dock", 6499),
    (4, "Webcam", 4999),
    (5, "Laptop Stand", 3299),
]

with sqlite3.connect(DB_PATH) as conn:
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price_cents INTEGER NOT NULL CHECK (price_cents > 0)
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            total_cents INTEGER NOT NULL CHECK (total_cents > 0),
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL UNIQUE,
            amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
            status TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
    """)

    conn.executemany(
        "INSERT OR IGNORE INTO customers VALUES (?, ?, ?)",
        customers,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO products VALUES (?, ?, ?)",
        products,
    )

    for order_id in range(1001, 1051):
        customer_id = random.randint(1, len(customers))
        product_id = random.randint(1, len(products))
        quantity = random.randint(1, 3)
        price_cents = products[product_id - 1][2]
        total_cents = price_cents * quantity
        order_date = (
            date(2026, 1, 1) + timedelta(days=random.randint(0, 240))
        ).isoformat()
        status = random.choice(
            ["delivered", "delivered", "delivered", "shipped", "processing"]
        )

        conn.execute(
            """INSERT OR IGNORE INTO orders
               (order_id, customer_id, product_id, order_date,
                quantity, total_cents, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                order_id, customer_id, product_id, order_date,
                quantity, total_cents, status,
            ),
        )
        conn.execute(
            """INSERT OR IGNORE INTO payments
               (payment_id, order_id, amount_cents, status)
               VALUES (?, ?, ?, ?)""",
            (order_id, order_id, total_cents, "paid"),
        )

    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    sample = conn.execute("""
        SELECT o.order_id, c.name, p.name, o.status, o.total_cents
        FROM orders AS o
        JOIN customers AS c ON c.customer_id = o.customer_id
        JOIN products AS p ON p.product_id = o.product_id
        WHERE o.order_id = 1001
    """).fetchone()

print(f"Created {DB_PATH} with {count} orders")
print(f"Sample order: {sample}")