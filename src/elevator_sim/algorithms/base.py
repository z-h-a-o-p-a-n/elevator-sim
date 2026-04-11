"""Abstract base class for elevator dispatch algorithms."""

from abc import ABC, abstractmethod

from ..models.elevator import Elevator
from ..models.passenger import Passenger
from ..config import SimConfig


class BaseAlgorithm(ABC):
    def __init__(self, config: SimConfig, algo_config: dict = {}) -> None:
        self._config = config
        self._algo_config = algo_config

    @abstractmethod
    def assign(self, passenger: Passenger, elevators: list[Elevator]) -> Elevator:
        """Assign a passenger to an elevator.

        Called once per new passenger at the tick they submit their request.
        The returned elevator will have the passenger added to its assignment queue.
        """