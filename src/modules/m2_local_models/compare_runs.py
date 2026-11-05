import json
import sys
from pathlib import Path
from typing import Any

RUNS_DIR = Path(__file__).parent / "runs"


def load(label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = json.loads(
        (RUNS_DIR / f"{label}.json").read_text(encoding="utf-8")
    )
    return rows


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Использование: python -m src.modules.m2_local_models.compare_runs A B")
    label_a, label_b = sys.argv[1], sys.argv[2]
    rows_a, rows_b = load(label_a), load(label_b)

    category_matches = 0
    urgent_matches = 0
    print(f"{'#':<3}{'категория ' + label_a:<28}{'категория ' + label_b:<28}срочность (P да)")
    for number, (a, b) in enumerate(zip(rows_a, rows_b, strict=True), start=1):
        category_matches += a["category"] == b["category"]
        urgent_matches += a["urgent"] == b["urgent"]
        category_a = f"{a['category']} {a['category_probability']:.2f}"
        category_b = f"{b['category']} {b['category_probability']:.2f}"
        print(
            f"{number:<3}{category_a:<28}{category_b:<28}"
            f"{a['urgent_probability']:.2f} / {b['urgent_probability']:.2f}"
        )

    total = len(rows_a)
    print()
    print(f"Совпадений категорий: {category_matches} из {total}")
    print(f"Совпадений решений о срочности: {urgent_matches} из {total}")
    for label, rows in ((label_a, rows_a), (label_b, rows_b)):
        mean_ms = sum(row["seconds"] for row in rows) / len(rows) * 1000
        print(f"{label}: в среднем {mean_ms:.0f} мс на тикет")


if __name__ == "__main__":
    main()
