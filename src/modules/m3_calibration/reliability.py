import sys
from collections import Counter

from src.modules.m3_calibration.runs_io import load_run
from src.ticketdesk.calibration import print_reliability


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "laya"
    split = sys.argv[2] if len(sys.argv) > 2 else "dev"
    rows = load_run(label, split)

    correct = [row["predicted_category"] == row["category"] for row in rows]
    majority, majority_count = Counter(row["category"] for row in rows).most_common(1)[0]
    print(f"{label}, {split}: {len(rows)} тикетов")
    print(f"Точность категории: {sum(correct) / len(rows):.2f}")
    print(f"База 'всегда {majority}': {majority_count / len(rows):.2f}")
    print()
    print_reliability(
        "Категория: вероятность выбранного варианта против доли верных",
        [row["category_probability"] for row in rows],
        correct,
    )
    print()
    print_reliability(
        "Срочность: вероятность 'да' против доли срочных",
        [row["urgent_probability"] for row in rows],
        [row["urgent"] for row in rows],
    )


if __name__ == "__main__":
    main()
