"""Abstract base class for elevator dispatch algorithms."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models.elevator import Elevator
from ..models.passenger import Passenger
from ..config import SimConfig


class BaseAlgorithm(ABC):
    def assign(self, passenger: Passenger, elevators: list[Elevator], config: SimConfig) -> Optional[Elevator]:
        """Assign a passenger to an elevator.

        Called once per new passenger at the tick they submit their request.
        The returned elevator will have the passenger added to its assignment queue.
        """
        eligible_elevators = list(filter(lambda e: len(e.assigned) + len(e.passengers) < config.elevator_capacity, elevators))
        if len(eligible_elevators) == 0:
            return None
        return self.get_elevator(passenger, eligible_elevators)

    @abstractmethod
    def get_elevator(self, passenger: Passenger, elevators: list[Elevator]) -> Elevator:
        """Find an assignable elevator."""
