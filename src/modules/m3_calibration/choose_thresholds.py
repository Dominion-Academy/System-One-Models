import sys
from typing import Any

from src.modules.m3_calibration.runs_io import load_run

# Условные цены ошибок в долларах. Подставьте свои.
MISSED_URGENT = 50.0  # срочный тикет ждал в общей очереди
FALSE_URGENT = 5.0  # дежурный отвлёкся на несрочный тикет
WRONG_ROUTE = 8.0  # тикет ушёл не в ту команду и вернулся
HUMAN_REVIEW = 2.0  # оператор вручную выбрал категорию

Row = dict[str, Any]


def urgent_cost(rows: list[Row], threshold: float) -> tuple[int, int, float]:
    false_negatives = sum(r["urgent"] and r["urgent_probability"] < threshold for r in rows)
    false_positives = sum(not r["urgent"] and r["urgent_probability"] >= threshold for r in rows)
    cost = false_negatives * MISSED_URGENT + false_positives * FALSE_URGENT
    return false_negatives, false_positives, cost


def category_cost(rows: list[Row], threshold: float) -> tuple[int, int, float]:
    auto = [r for r in rows if r["category_probability"] >= threshold]
    errors = sum(r["predicted_category"] != r["category"] for r in auto)
    escalated = len(rows) - len(auto)
    return escalated, errors, errors * WRONG_ROUTE + escalated * HUMAN_REVIEW


def grid(start: float, stop: float, step: float) -> list[float]:
    count = round((stop - start) / step) + 1
    return [round(start + i * step, 2) for i in range(count)]


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "laya"
    dev, hold_out = load_run(label, "dev"), load_run(label, "hold_out")

    print(f"Срочность ({label}, dev: {len(dev)})")
    print("  порог  пропущено  ложных  цена, $")
    for threshold in grid(0.40, 0.66, 0.02):
        fn, fp, cost = urgent_cost(dev, threshold)
        print(f"  {threshold:.2f}   {fn:9d}  {fp:6d}  {cost:7.0f}")
    urgent_threshold = min(grid(0.30, 0.90, 0.01), key=lambda t: urgent_cost(dev, t)[2])
    fn, fp, cost = urgent_cost(hold_out, urgent_threshold)
    print(f"  Лучший порог на dev: {urgent_threshold:.2f}")
    print(f"  Hold-out: пропущено {fn}, ложных {fp}, цена ${cost:.0f}")
    fn, fp, cost = urgent_cost(hold_out, 0.5)
    print(f"  Hold-out с порогом 0.50: пропущено {fn}, ложных {fp}, цена ${cost:.0f}")

    print()
    print(f"Категория ({label}, dev: {len(dev)})")
    print("  порог  к человеку  ошибок в авто  цена, $")
    for threshold in grid(0.0, 0.9, 0.1):
        escalated, errors, cost = category_cost(dev, threshold)
        print(f"  {threshold:.2f}   {escalated:10d}  {errors:13d}  {cost:7.0f}")
    category_threshold = min(grid(0.0, 1.0, 0.01), key=lambda t: category_cost(dev, t)[2])
    escalated, errors, cost = category_cost(hold_out, category_threshold)
    print(f"  Лучший порог на dev: {category_threshold:.2f}")
    print(
        f"  Hold-out: к человеку {escalated} из {len(hold_out)}, "
        f"ошибок в авто {errors}, цена ${cost:.0f}"
    )
    escalated, errors, cost = category_cost(hold_out, 0.0)
    print(f"  Hold-out без эскалации: ошибок {errors}, цена ${cost:.0f}")


if __name__ == "__main__":
    main()
