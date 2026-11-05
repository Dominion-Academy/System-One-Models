import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DecisionRecord:
    ticket_id: str
    model: str
    thresholds_version: str
    route: str
    predicted_category: str | None
    category_probability: float
    urgent_probability: float
    latency_ms: float
    error: str | None = None


def log_decision(path: Path, record: DecisionRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), **asdict(record)}
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(line) + "\n")


def read_log(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
