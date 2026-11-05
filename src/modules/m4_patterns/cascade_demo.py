import json
from collections import Counter
from pathlib import Path

from src.ticketdesk.cascade import Route, cascade
from src.ticketdesk.client import make_client
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.llm import llm_from_env

RUN_PATH = Path(__file__).parent / "runs" / "cascade_hold_out.jsonl"


def main() -> None:
    llm = llm_from_env()
    tickets = load_tickets("hold_out")
    routes: Counter[Route] = Counter()
    correct: Counter[Route] = Counter()
    RUN_PATH.parent.mkdir(exist_ok=True)

    with make_client() as client, RUN_PATH.open("w", encoding="utf-8") as file:
        for ticket in tickets:
            decision = cascade(client, llm, ticket.subject, ticket.body)
            routes[decision.route] += 1
            correct[decision.route] += decision.category == ticket.category
            row = {
                "id": ticket.id,
                "category": ticket.category.value,
                "route": decision.route.value,
                "decided": decision.category.value if decision.category else None,
            }
            file.write(json.dumps(row) + "\n")

    print(f"LLM: {type(llm).__name__}, held-out: {len(tickets)} тикетов")
    for route in Route:
        if route is Route.HUMAN:
            print(f"  {route.value:<6} {routes[route]:3d} тикетов, решает человек")
            continue
        share = correct[route] / routes[route] if routes[route] else 0.0
        print(
            f"  {route.value:<6} {routes[route]:3d} тикетов, верно {correct[route]} ({share:.2f})"
        )


if __name__ == "__main__":
    main()
