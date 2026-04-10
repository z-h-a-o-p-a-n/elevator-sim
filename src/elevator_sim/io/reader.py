"""Input parsing for elevator requests."""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Request:
    time: int
    id: str
    source: int
    dest: int


def parse_csv(path: str | Path) -> list[Request]:
    """Parse a CSV file into a list of Requests, sorted by time."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return _parse_rows(reader)


def parse_records(records: list[dict[str, str | int]]) -> list[Request]:
    """Parse a list of dicts (each with keys: time, id, source, dest) into Requests."""
    return _parse_rows(records)  # type: ignore[arg-type]


def _parse_rows(rows: object) -> list[Request]:
    requests = [
        Request(
            time=int(row["time"]),  # type: ignore[index]
            id=str(row["id"]),  # type: ignore[index]
            source=int(row["source"]),  # type: ignore[index]
            dest=int(row["dest"]),  # type: ignore[index]
        )
        for row in rows  # type: ignore[union-attr]
    ]
    return sorted(requests, key=lambda r: r.time)
