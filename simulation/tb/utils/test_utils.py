import json
from pathlib import Path


def count_errors(path: Path) -> int:
    errors = 0

    if not path.is_file():
        raise FileNotFoundError(f"Log file does not exist: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry["Level"] == "ERROR":
                errors += 1

    return errors
