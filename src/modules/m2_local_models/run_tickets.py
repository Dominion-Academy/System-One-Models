import json
import sys
import time
from pathlib import Path

from typesafe_sdk import TypeSafeClient

from src.modules.m1_system_one.ticket_triage import TICKETS
from src.ticketdesk.triage import triage

RUNS_DIR = Path(__file__).parent / "runs"


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    rows: list[dict[str, object]] = []

    with TypeSafeClient(timeout=60) as client:
        for number, ticket in enumerate(TICKETS, start=1):
            started = time.perf_counter()
            result = triage(client, ticket)
            seconds = time.perf_counter() - started

            rows.append(
                {
                    "ticket": ticket,
                    "category": result.category,
                    "category_probability": result.category_probability,
                    "urgent": result.urgent,
                    "urgent_probability": result.urgent_probability,
                    "seconds": seconds,
                }
            )
            print(
                f"#{number} {result.category} ({result.category_probability:.2f}), "
                f"urgent: {result.urgent} ({result.urgent_probability:.2f}), "
                f"{seconds * 1000:.0f} ms"
            )

    RUNS_DIR.mkdir(exist_ok=True)
    path = RUNS_DIR / f"{label}.json"
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Сохранено: {path}")


if __name__ == "__main__":
    main()
