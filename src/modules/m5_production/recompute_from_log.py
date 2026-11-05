from collections import Counter
from statistics import median

from src.modules.m3_calibration.choose_thresholds import category_cost, grid
from src.modules.m7_production.log_decisions import LOG_PATH
from src.ticketdesk.calibration import print_reliability
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.decision_log import read_log


def main() -> None:
    # Метки здесь заменяют исход, который в продакшене пришёл бы от оператора.
    labels = {ticket.id: ticket.category.value for ticket in load_tickets()}
    rows = read_log(LOG_PATH)
    for row in rows:
        row["category"] = labels[row["ticket_id"]]

    versions = Counter(row["thresholds_version"] for row in rows)
    latencies = [row["latency_ms"] for row in rows]
    print(f"Решений: {len(rows)}, версии порогов: {dict(versions)}")
    print(f"Задержка: медиана {median(latencies):.0f} мс, максимум {max(latencies):.0f} мс")
    print(f"Маршруты: {dict(Counter(row['route'] for row in rows))}")
    print()
    print_reliability(
        "Категория по логу",
        [row["category_probability"] for row in rows],
        [row["predicted_category"] == row["category"] for row in rows],
    )
    best = min(grid(0.0, 1.0, 0.01), key=lambda t: category_cost(rows, t)[2])
    escalated, errors, _ = category_cost(rows, best)
    print(f"Порог категории по логу: {best:.2f} (к человеку {escalated}, ошибок {errors})")


if __name__ == "__main__":
    main()
