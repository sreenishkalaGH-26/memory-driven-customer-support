"""Synthetic (clearly fake) CRM profiles and past tickets for the demo.

CUSTOMERS is ordinary CRM data (name, ID, platform). It is NOT the memory layer.
SEED_HISTORY is pushed into Hindsight through retain() when you click "Load demo history".
Priya Sharma has no seeded history on purpose: she is the fresh customer in the main demo.
"""
from datetime import datetime, timedelta

_now = datetime.now()


def _days_ago(n: int, hour: int = 11) -> datetime:
    return (_now - timedelta(days=n)).replace(hour=hour, minute=15, second=0, microsecond=0)


CUSTOMERS = {
    "CUST-1001": {"name": "Priya Sharma", "platform": "Android app", "plan": "Premium"},
    "CUST-1002": {"name": "Rahul Verma", "platform": "Web (Chrome on Windows)", "plan": "Standard"},
    "CUST-1003": {"name": "Ananya Iyer", "platform": "iOS app", "plan": "Premium"},
    "CUST-1004": {"name": "Vikram Nair", "platform": "Android app", "plan": "Standard"},
}

SEED_HISTORY = {
    "CUST-1002": [
        {
            "when": _days_ago(21),
            "content": (
                "Support ticket T-4821 (login issue). Customer Rahul Verma on Web (Chrome, Windows) could not log in "
                "after a password reset; reset emails were arriving in his spam folder. Resolution that worked: "
                "whitelisted the sender domain, requested a new reset link, and cleared browser cookies. "
                "Customer prefers email over phone. He was mildly frustrated about having to reset twice."
            ),
        },
    ],
    "CUST-1003": [
        {
            "when": _days_ago(9),
            "content": (
                "Support ticket T-5010 (delivery issue). Customer Ananya Iyer on the iOS app reported order #88213 "
                "marked delivered but not received. Resolution: courier contacted, package found at the building "
                "reception, redelivered next day. Customer asked to always be updated by in-app notification, "
                "not SMS. She was quite frustrated as this was her second delivery problem this quarter."
            ),
        },
    ],
    "CUST-1004": [
        {
            "when": _days_ago(35),
            "content": (
                "Support ticket T-3990 (refund). Customer Vikram Nair on the Android app (v5.2) asked about a "
                "duplicate charge for order #77120. Resolution: duplicate charge refunded to the original "
                "payment method within 5 business days. Customer was calm and prefers short answers."
            ),
        },
    ],
}
