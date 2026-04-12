"""Round-robin destination dispatch algorithm."""

from elevator_sim.config import SimConfig

from ..models.elevator import Elevator
from ..models.passenger import Passenger
from .base import BaseAlgorithm


class RoundRobinAlgorithm(BaseAlgorithm):
    """Assigns the nth passenger to elevator (n mod m), where m is the number of elevators.

    The counter is global across all passengers ever assigned.
    """

    def __init__(self, config: SimConfig, algo_config: dict = {}) -> None:
        self._counter = 0
        self._config = config

    def pick_elevator_for_passenger(self, passenger: Passenger, elevators: list[Elevator]) -> Elevator:
        m = len(elevators)
        selected = elevators[self._counter % m]
        self._counter += 1
        return selected        
