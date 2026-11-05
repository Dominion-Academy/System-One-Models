import json
from dataclasses import dataclass
from pathlib import Path

from src.ticketdesk.typed import Category

DATA_PATH = Path(__file__).parent / "data" / "tickets.jsonl"


@dataclass(frozen=True)
class LabeledTicket:
    id: str
    split: str
    subject: str
    body: str
    category: Category
    urgent: bool


def load_tickets(split: str | None = None) -> list[LabeledTicket]:
    tickets = []
    for line in DATA_PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if split is not None and row["split"] != split:
            continue
        tickets.append(
            LabeledTicket(
                id=row["id"],
                split=row["split"],
                subject=row["subject"],
                body=row["body"],
                category=Category(row["category"]),
                urgent=row["urgent"],
            )
        )
    return tickets
