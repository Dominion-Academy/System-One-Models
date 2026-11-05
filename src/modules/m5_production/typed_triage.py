from typesafe_sdk import TypeSafeClient

from src.ticketdesk.typed import Category, typed_triage

LAYA_URL = "http://localhost:5000"

TICKETS = [
    (
        "Charged twice",
        (
            "I was charged twice for my annual subscription this month. "
            "I asked for a refund two weeks ago and nobody has replied. This is unacceptable!"
        ),
    ),
    (
        "API returns 500",
        (
            "Our API integration started returning 500 errors on every request 20 minutes ago. "
            "We can't process any customer orders until this is fixed."
        ),
    ),
    (
        "Dark theme?",
        "Hi! Do you have a dark theme for the dashboard? It would be a nice feature to have.",
    ),
]


def route(category: Category) -> str:
    match category:
        case Category.BILLING:
            return "billing-team"
        case Category.TECHNICAL:
            return "engineering"
        case Category.ACCOUNT:
            return "account-support"
        case Category.OTHER:
            return "general-queue"


def main() -> None:
    with TypeSafeClient(base_url=LAYA_URL, api_key="local", model="jev-latest") as client:
        for subject, body in TICKETS:
            result = typed_triage(client, subject, body)
            print(f"{subject}: {result}")
            print(f"    route: {route(result.category)}, angry: {result.frustration.name}")


if __name__ == "__main__":
    main()
