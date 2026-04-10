"""Elevator model."""

from dataclasses import dataclass, field
from enum import Enum, auto

from .passenger import Passenger


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    IDLE = auto()


class ElevatorState(Enum):
    MOVING = auto()
    STOPPED = auto()  # stopped at a floor during stop_ticks countdown
    IDLE = auto()


@dataclass
class Elevator:
    id: int
    capacity: int
    current_floor: int = 1
    direction: Direction = Direction.IDLE
    state: ElevatorState = ElevatorState.IDLE

    # Passengers currently riding
    passengers: list[Passenger] = field(default_factory=list)

    # Floors this elevator must visit (destinations of aboard passengers + assigned pickups)
    destinations: set[int] = field(default_factory=set)

    # Passengers assigned to this elevator but not yet boarded
    assigned: list[Passenger] = field(default_factory=list)

    # Countdown ticks remaining while stopped after a boarding/exiting event
    stop_ticks_remaining: int = 0

    # Ticks spent in a non-idle state (moving or stopped at a floor)
    active_ticks: int = 0

    # Total floors traveled (incremented each time the elevator moves one floor)
    floors_traveled: int = 0

    @property
    def is_full(self) -> bool:
        return len(self.passengers) >= self.capacity

    @property
    def load(self) -> int:
        return len(self.passengers)

    @property
    def is_stopped(self) -> bool:
        return self.stop_ticks_remaining > 0

    def assign(self, passenger: Passenger) -> None:
        """Assign a passenger to this elevator (not yet boarded)."""
        passenger.assigned_elevator_id = self.id
        self.assigned.append(passenger)
        self.destinations.add(passenger.origin)

    def exit(self, tick: int) -> list[Passenger]:
        """Remove passengers whose destination is current floor."""
        arrived = [p for p in self.passengers if p.destination == self.current_floor]
        for p in arrived:
            self.passengers.remove(p)
            p.arrive_time = tick
        self.destinations.discard(self.current_floor)
        return arrived

    def board(self, tick: int) -> list[Passenger]:
        """Board assigned passengers waiting at current floor."""
        to_board = [
            p for p in self.assigned
            if p.origin == self.current_floor and not self.is_full
        ]
        # Respect capacity
        boarders: list[Passenger] = []
        for p in to_board:
            if self.is_full:
                break
            boarders.append(p)

        for p in boarders:
            self.assigned.remove(p)
            self.passengers.append(p)
            self.destinations.add(p.destination)
            p.board_time = tick

        # Remove origin from destinations only if no more assigned passengers waiting here
        remaining_at_floor = [p for p in self.assigned if p.origin == self.current_floor]
        if not remaining_at_floor:
            self.destinations.discard(self.current_floor)

        return boarders

    def move(self) -> None:
        """Advance elevator one floor in its current direction."""
        if self.direction == Direction.UP:
            self.current_floor += 1
            self.floors_traveled += 1
            self.state = ElevatorState.MOVING
        elif self.direction == Direction.DOWN:
            self.current_floor -= 1
            self.floors_traveled += 1
            self.state = ElevatorState.MOVING
        else:
            self.state = ElevatorState.IDLE

    def __repr__(self) -> str:
        return (
            f"Elevator({self.id} @ floor {self.current_floor}, state={self.state.name}, "
            f"direction={self.direction.name}, load={self.load}/{self.capacity}, "
            f"passengers: {", ".join(map(lambda p: p.id, self.passengers))})"
        )
