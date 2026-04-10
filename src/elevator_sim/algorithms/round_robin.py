"""Round-robin destination dispatch algorithm."""

from elevator_sim.config import SimConfig

from ..models.elevator import Elevator
from ..models.passenger import Passenger
from .base import BaseAlgorithm


class RoundRobinAlgorithm(BaseAlgorithm):
    """Assigns the nth passenger to elevator (n mod m), where m is the number of elevators.

    The counter is global across all passengers ever assigned, regardless of capacity
    filtering. If the selected elevator is at capacity, the base class will return None.
    """

    def __init__(self, config: SimConfig, algo_config: dict = {}) -> None:
        self._counter = 0
        self._config = config

    # def assign(self, passenger: Passenger, elevators: list[Elevator], config) -> Elevator | None:
    #     if not elevators:
    #         return None
    #     return self.get_elevator(passenger, elevators)

    def get_elevator(self, passenger: Passenger, elevators: list[Elevator]) -> Elevator:
        m = len(elevators)
        selected = elevators[self._counter % m]
        self._counter += 1
        if len(selected.assigned) + len(selected.passengers) >= self._config.elevator_capacity:
            return None
        return selected
