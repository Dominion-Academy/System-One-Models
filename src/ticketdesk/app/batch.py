import csv
import io
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class TicketInput:
    id: str
    subject: str
    body: str
    expected_category: str | None = None
    expected_urgent: bool | None = None


def parse_flag(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    return None


def parse_tickets(filename: str, data: bytes) -> list[TicketInput]:
    """Читает тикеты из .jsonl или .csv. Обязательные поля: subject и body."""
    text = data.decode("utf-8-sig")
    name = filename.lower()
    if name.endswith(".jsonl"):
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    elif name.endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(text)))
    else:
        raise ValueError("Поддерживаются файлы .jsonl и .csv")

    tickets = []
    for number, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or not row.get("subject") or not row.get("body"):
            raise ValueError(f"Запись {number}: нужны непустые поля subject и body")
        tickets.append(
            TicketInput(
                id=str(row.get("id") or number),
                subject=str(row["subject"]),
                body=str(row["body"]),
                expected_category=row.get("category") or None,
                expected_urgent=parse_flag(row.get("urgent")),
            )
        )
    if not tickets:
        raise ValueError("В файле нет тикетов")
    return tickets
