"""Passenger model."""

from dataclasses import dataclass, field


@dataclass
class Passenger:
    id: str
    origin: int
    destination: int
    request_time: int

    # Set during simulation
    board_time: int | None = None
    arrive_time: int | None = None
    assigned_elevator_id: int | None = None

    @property
    def wait_time(self) -> int | None:
        if self.board_time is None:
            return None
        return self.board_time - self.request_time

    @property
    def total_time(self) -> int | None:
        if self.arrive_time is None:
            return None
        return self.arrive_time - self.request_time

    @property
    def arrived(self) -> bool:
        return self.arrive_time is not None

    def __repr__(self) -> str:
        return f"Passenger({self.id}: {self.origin}->{self.destination})"
