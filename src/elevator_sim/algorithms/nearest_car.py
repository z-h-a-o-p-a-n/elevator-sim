"""Nearest-car destination dispatch algorithm."""

from elevator_sim.config import SimConfig

from ..models.elevator import Direction, Elevator
from ..models.passenger import Passenger
from .base import BaseAlgorithm


class NearestCarAlgorithm(BaseAlgorithm):
    """Assigns each passenger to the elevator with the lowest cost score.

    Scoring per elevator (lower is better):
      - Base cost: distance from elevator's effective position to passenger's origin.
      - Direction bonus: subtracted from score if elevator is already heading toward
        the origin. Set to 0 (default) to disable.
      - Overshoot penalty: 2x floors the elevator travels past the origin before reversing.
      - Tie-break: total committed passengers (riding + assigned).

    Args:
        direction_bonus: Amount subtracted from score when elevator is heading toward
            the passenger's origin. Defaults to 0 (disabled).
    """

    def __init__(self, config: SimConfig, algo_config = {}) -> None:
        self._config = config
        self.direction_bonus = algo_config.get("direction_bonus")

    def get_elevator(self, passenger: Passenger, elevators: list[Elevator]) -> Elevator:
        return min(elevators, key=lambda e: self._score(e, passenger))

    def _score(self, elevator: Elevator, passenger: Passenger) -> tuple[float, int]:
        effective_pos = self._effective_position(elevator, passenger.origin)
        distance = abs(effective_pos - passenger.origin)

        bonus = self._direction_bonus(elevator, passenger.origin)

        overshoot = self._overshoot(elevator, passenger.origin)

        return (distance + bonus + 2 * overshoot, elevator.load + len(elevator.assigned))

    def _effective_position(self, elevator: Elevator, target: int) -> int:
        """Return the number of floors the elevator still need to travel reach before it could turn toward target.

        For an elevator moving away from the target, the effective position is
        its furthest destination in the current direction, because it must
        travel there before reversing.
        """
        if elevator.direction == Direction.UP and target < elevator.current_floor:
            above = [d for d in elevator.destinations if d >= elevator.current_floor]
            return max(above) if above else elevator.current_floor
        if elevator.direction == Direction.DOWN and target > elevator.current_floor:
            below = [d for d in elevator.destinations if d <= elevator.current_floor]
            return min(below) if below else elevator.current_floor
        return elevator.current_floor

    def _direction_bonus(self, elevator: Elevator, origin: int) -> float:
        """Amount subtracted from score when elevator is heading toward the passenger's origin. Defaults to 0 (disabled)"""
        if self.direction_bonus != None:
            if elevator.direction == Direction.UP and origin > elevator.current_floor:
                return -float(self.direction_bonus)
            elif elevator.direction == Direction.DOWN and origin < elevator.current_floor:
                return -float(self.direction_bonus)
        return 0.0
    
    def _overshoot(self, elevator: Elevator, origin: int) -> int:
        """Extra floors the elevator must travel past the origin before it can reverse.

        When two elevators are equidistant from the origin, prefer the one whose
        furthest committed destination is closer to the origin — it will reach
        the origin sooner in practice and cause less unnecessary riding.
        """
        if elevator.direction == Direction.UP and origin >= elevator.current_floor:
            beyond = [d for d in elevator.destinations if d > origin]
            return max(beyond) - origin if beyond else 0
        if elevator.direction == Direction.DOWN and origin <= elevator.current_floor:
            beyond = [d for d in elevator.destinations if d < origin]
            return origin - min(beyond) if beyond else 0
        return 0
