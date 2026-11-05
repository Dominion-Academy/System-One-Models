import os
import time
from pathlib import Path

from src.ticketdesk import thresholds
from src.ticketdesk.cascade import cascade
from src.ticketdesk.client import make_client
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.decision_log import DecisionRecord, log_decision
from src.ticketdesk.llm import llm_from_env

LOG_PATH = Path(__file__).parent / "logs" / "decisions.jsonl"


def main() -> None:
    LOG_PATH.unlink(missing_ok=True)
    llm = llm_from_env()
    model = os.environ.get("TYPESAFE_DEFAULT_MODEL", "unknown")
    with make_client() as client:
        for ticket in load_tickets():
            started = time.perf_counter()
            decision = cascade(client, llm, ticket.subject, ticket.body)
            record = DecisionRecord(
                ticket_id=ticket.id,
                model=model,
                thresholds_version=thresholds.VERSION,
                route=decision.route.value,
                predicted_category=decision.triage.category.value,
                category_probability=decision.triage.category_probability,
                urgent_probability=decision.triage.urgent_probability,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            log_decision(LOG_PATH, record)
    print(f"Записано решений: {len(load_tickets())} в {LOG_PATH}")
    print(LOG_PATH.read_text(encoding="utf-8").splitlines()[0])


if __name__ == "__main__":
    main()
