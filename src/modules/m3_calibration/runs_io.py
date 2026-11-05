import json
from pathlib import Path
from typing import Any

RUNS_DIR = Path(__file__).parent / "runs"


def load_run(label: str, split: str | None = None) -> list[dict[str, Any]]:
    rows = []
    path = RUNS_DIR / f"{label}.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if split is None or row["split"] == split:
            rows.append(row)
    return rows
