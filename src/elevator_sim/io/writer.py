"""Output writers for elevator positions log and passenger activity log."""

import csv
from pathlib import Path

from ..models.elevator import Elevator
from ..models.passenger import Passenger


class LogWriter:
    """Writes per-run log files to output_dir.

    Files created:
      <run_id>_positions.csv  — one row per tick, columns: time, E1, E2, ...
      <run_id>_passengers.csv — one row per passenger with timing columns
    """

    def __init__(self, output_dir: str | Path, run_id: str, num_elevators: int) -> None:
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

        self._elevator_ids = [f"E{i + 1}" for i in range(num_elevators)]

        pos_path = self._dir / f"{run_id}_positions.csv"
        self._pos_file = open(pos_path, "w", newline="")
        self._pos_writer = csv.writer(self._pos_file)
        self._pos_writer.writerow(["time", *self._elevator_ids])

        pax_path = self._dir / f"{run_id}_passengers.csv"
        self._pax_file = open(pax_path, "w", newline="")
        self._pax_writer = csv.writer(self._pax_file)
        self._pax_writer.writerow(
            ["passengerId", "source", "dest", "elevator_id", "start_time", "board_elevator_time", "exit_time"]
        )

    def log_tick(self, tick: int, elevators: list[Elevator]) -> None:
        self._pos_writer.writerow([tick, *[e.current_floor for e in elevators]])

    def log_passenger(self, passenger: Passenger) -> None:
        self._pax_writer.writerow([
            passenger.id,
            passenger.origin,
            passenger.destination,
            passenger.assigned_elevator_id,
            passenger.request_time,
            passenger.board_time,
            passenger.arrive_time,
        ])

    def close(self) -> None:
        self._pos_file.close()
        self._pax_file.close()

    def __enter__(self) -> "LogWriter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
