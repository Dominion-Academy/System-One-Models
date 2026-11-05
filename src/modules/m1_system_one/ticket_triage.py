from typesafe_sdk import TypeSafeClient

from src.ticketdesk.triage import triage

LAYA_URL = "http://localhost:5000"

TICKETS = [
    (
        "I was charged twice for my annual subscription this month. "
        "I asked for a refund two weeks ago and nobody has replied."
    ),
    (
        "Our API integration started returning 500 errors on every request 20 minutes ago. "
        "We can't process any customer orders until this is fixed."
    ),
    "How do I change the email address on my account? No rush, just curious.",
    "Hi! Do you have a dark theme for the dashboard? It would be a nice feature to have.",
    (
        "I can't log in: the password reset email never arrives, "
        "and I have a demo for investors in one hour."
    ),
]


def main() -> None:
    with TypeSafeClient(base_url=LAYA_URL, api_key="local", model="jev-latest") as client:
        for number, ticket in enumerate(TICKETS, start=1):
            result = triage(client, ticket)
            print(f"#{number} {ticket[:60]}...")
            print(
                f"    category: {result.category} "
                f"({result.category_probability:.2f}), "
                f"urgent: {result.urgent} ({result.urgent_probability:.2f})"
            )


if __name__ == "__main__":
    main()
