import json
import sys
import time
from pathlib import Path

from src.ticketdesk.client import make_client
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.typed import typed_triage

RUNS_DIR = Path(__file__).parent / "runs"


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    RUNS_DIR.mkdir(exist_ok=True)
    path = RUNS_DIR / f"{label}.jsonl"

    with make_client() as client, path.open("w", encoding="utf-8") as file:
        for ticket in load_tickets():
            started = time.perf_counter()
            result = typed_triage(client, ticket.subject, ticket.body)
            row = {
                "id": ticket.id,
                "split": ticket.split,
                "category": ticket.category.value,
                "urgent": ticket.urgent,
                "predicted_category": result.category.value,
                "category_probability": result.category_probability,
                "urgent_probability": result.urgent_probability,
                "seconds": time.perf_counter() - started,
            }
            file.write(json.dumps(row) + "\n")
            mark = "ok " if result.category == ticket.category else "ERR"
            print(
                f"{ticket.id} {mark} {result.category.value:<9} "
                f"p={result.category_probability:.2f} urgent={result.urgent_probability:.2f}"
            )
    print(f"Сохранено: {path}")


if __name__ == "__main__":
    main()
