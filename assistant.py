import re
import sys

from llm import draft_reply
from tools import lookup_order, search_product_reviews


def draft_is_safe(reply: str, order: dict, wants_return: bool) -> bool:
    text = reply.lower()
    order_id = str(order["order_id"])

    if not reply.strip() or order_id not in reply:
        return False

    risky_phrases = [
        "to process a return",
        "process your return",
        "processing your return",
        "return has been started",
        "return has been approved",
        "refund has been approved",
        "refund has been issued",
        "i'll review our return policy",
        "i can guide you through",
        "can provide more specific shipping information",
        "contact them for an update",
        "support team can provide",
        "payment is confirmed",
    ]

    if any(phrase in text for phrase in risky_phrases):
        return False

    order_date = order["order_date"]
    if order_date in reply and re.search(
        r"\b(deliver\w*|arriv\w*)\b.{0,30}" + re.escape(order_date),
        text,
    ):
        return False

    if wants_return and "specialist" not in text and "support team" not in text:
        return False

    return True


def respond(message: str) -> dict:
    match = re.search(r"\b(?:order\s*#?\s*)?(\d{4,})\b", message, re.IGNORECASE)

    if not match:
        return {
            "reply": "Please provide your order number so I can check its status.",
            "order": None,
            "reviews": [],
            "mode": "deterministic",
        }

    order_id = int(match.group(1))
    order = lookup_order(order_id)

    if order is None:
        return {
            "reply": (
                f"I couldn't find order {order_id} in this demo dataset. "
                "Please check the number."
            ),
            "order": None,
            "reviews": [],
            "mode": "deterministic",
        }

    wants_return = bool(re.search(r"\b(return|refund|exchange)\b", message, re.I))
    asks_status = bool(
        re.search(r"\b(where|track|status|shipp?|deliver)\w*\b", message, re.I)
    )

    if wants_return:
        fallback_reply = (
            f"I found order {order_id} for {order['product_name']}. "
            f"Its recorded status is {order['status']}. "
            "I can't verify return eligibility or issue a refund from this demo. "
            "A support specialist should confirm the policy and next steps."
        )
    elif asks_status:
        fallback_reply = (
            f"I found order {order_id} for {order['product_name']}. "
            f"Its recorded status is {order['status']}. "
            "This dataset does not include a carrier tracking link or delivery estimate."
        )
    else:
        fallback_reply = (
            f"I found order {order_id} for {order['product_name']}. "
            f"Its recorded status is {order['status']} and payment is "
            f"{order['payment_status']}. What would you like help with?"
        )

    reviews = search_product_reviews(order["product_id"])

    reply = fallback_reply
    mode = "deterministic"

    try:
        candidate = draft_reply(message, order)
        if draft_is_safe(candidate, order, wants_return):
            reply = candidate
            mode = "claude"
    except Exception:
        pass

    return {
        "reply": reply,
        "order": order,
        "reviews": reviews,
        "mode": mode,
    }


if __name__ == "__main__":
    message = " ".join(sys.argv[1:])
    if not message:
        raise SystemExit('Usage: python assistant.py "I want to return order 1001"')

    result = respond(message)
    print("MODE:", result["mode"])
    print("REPLY:", result["reply"])