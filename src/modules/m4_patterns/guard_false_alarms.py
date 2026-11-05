from src.ticketdesk.client import make_client
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.guards import INPUT_GUARD, check_input

THRESHOLDS = (0.5, 0.6, 0.7, 0.8)


def main() -> None:
    # Все тикеты выборки написаны настоящими клиентами: любое срабатывание Guardrail ложное.
    tickets = load_tickets("dev")
    scores: dict[str, list[float]] = {name: [] for name in INPUT_GUARD}
    with make_client() as client:
        for ticket in tickets:
            result = check_input(client, ticket.subject, ticket.body)
            for name, p in result.probabilities.items():
                scores[name].append(p)

    print(f"Ложные срабатывания на {len(tickets)} настоящих тикетах (dev)")
    print("проверка    max   " + "  ".join(f">={t}" for t in THRESHOLDS))
    for name, values in scores.items():
        counts = "  ".join(f"{sum(p >= t for p in values):5d}" for t in THRESHOLDS)
        print(f"{name:<10} {max(values):.2f}  {counts}")


if __name__ == "__main__":
    main()
