"""Nearest-car destination dispatch algorithm."""

from elevator_sim.config import SimConfig

from ..models.elevator import Direction, Elevator
from ..models.passenger import Passenger
from .base import BaseAlgorithm


class NearestCarAlgorithm(BaseAlgorithm):
    """Assigns each passenger to the elevator with the lowest cost score.

    Score approximates total passenger time: wait (to reach pickup) + travel (to destination).
    Lower is better.

      - Wait:    distance from the elevator's effective position to the passenger's origin.
      - Travel:  direct floors from origin to destination, plus 2x any detour floors the
                 elevator must travel past the origin before it can head toward the destination.
                 Each detour floor costs 2 ticks: once going the wrong way, once coming back.
      - Bonus:   optionally subtracted from score when the elevator is already heading toward
                 the origin. Set to 0 (default) to disable.
      - Tie-break: total committed passengers (riding + assigned).

    Args:
        direction_bonus: Amount subtracted from score when elevator is heading toward
            the passenger's origin. Defaults to 0 (disabled).
    """

    def __init__(self, config: SimConfig, algo_config = {}) -> None:
        self._config = config
        self.direction_bonus = algo_config.get("direction_bonus")

    def pick_elevator_for_passenger(self, passenger: Passenger, elevators: list[Elevator]) -> Elevator:
        return min(elevators, key=lambda e: self._score(e, passenger))

    def _score(self, elevator: Elevator, passenger: Passenger) -> tuple[float, int]:
        direct_travel = abs(passenger.origin - passenger.destination)

        if self._projected_load_at(elevator, passenger) >= elevator.capacity:
            # Elevator is full at origin; it must finish its current run before picking up.
            # After the run it will be idle, so no detour after boarding.
            post_trip_pos = self._post_trip_position(elevator)
            wait = abs(elevator.current_floor - post_trip_pos) + abs(post_trip_pos - passenger.origin)
            return (wait + direct_travel, elevator.load + len(elevator.assigned))

        effective_pos = self._effective_position(elevator, passenger.origin)
        wait = abs(effective_pos - passenger.origin)
        bonus = self._direction_bonus(elevator, passenger.origin)
        detour = self._detour(elevator, passenger)
        return (wait + bonus + direct_travel + 2 * detour, elevator.load + len(elevator.assigned))

    def _projected_load_at(self, elevator: Elevator, passenger: Passenger) -> int:
        """Estimate the elevator's load when it reaches the passenger's origin.

        For en-route pickups (elevator already heading toward the origin in its
        current direction), passengers who exit at or before the origin floor
        free up seats before the new passenger boards. For non-en-route cases the
        elevator must reverse first, so we conservatively use the full committed load.
        """
        origin = passenger.origin

        if elevator.direction == Direction.DOWN and origin <= elevator.current_floor:
            exits = sum(1 for p in elevator.passengers if p.destination >= origin)
            boards = sum(1 for p in elevator.assigned if p.origin > origin)
            return elevator.load - exits + boards

        if elevator.direction == Direction.UP and origin >= elevator.current_floor:
            exits = sum(1 for p in elevator.passengers if p.destination <= origin)
            boards = sum(1 for p in elevator.assigned if p.origin < origin)
            return elevator.load - exits + boards

        return elevator.load + len(elevator.assigned)

    def _post_trip_position(self, elevator: Elevator) -> int:
        """Floor the elevator reaches after completing all currently committed stops.

        Used when the elevator is full at the passenger's origin and must finish
        its current run before it can accept a new passenger.
        """
        if elevator.direction == Direction.UP:
            above = [d for d in elevator.destinations if d >= elevator.current_floor]
            return max(above) if above else elevator.current_floor
        if elevator.direction == Direction.DOWN:
            below = [d for d in elevator.destinations if d <= elevator.current_floor]
            return min(below) if below else elevator.current_floor
        return elevator.current_floor

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

    def _detour(self, elevator: Elevator, passenger: Passenger) -> int:
        """Floors traveled past the origin in the wrong direction after pickup.

        When the elevator still has committed stops beyond the origin that are
        opposite to the passenger's destination, the passenger must ride those
        extra floors before the elevator can reverse toward their destination.
        Returns 0 when the elevator and passenger are heading the same way.
        """
        origin = passenger.origin
        passenger_going_up = passenger.destination > passenger.origin

        if elevator.direction == Direction.UP and origin >= elevator.current_floor:
            if passenger_going_up:
                return 0
            beyond = [d for d in elevator.destinations if d > origin]
            return max(beyond) - origin if beyond else 0

        if elevator.direction == Direction.DOWN and origin <= elevator.current_floor:
            if not passenger_going_up:
                return 0
            beyond = [d for d in elevator.destinations if d < origin]
            return origin - min(beyond) if beyond else 0

        return 0

    def _direction_bonus(self, elevator: Elevator, origin: int) -> float:
        """Amount subtracted from score when elevator is heading toward the passenger's origin. Defaults to 0 (disabled)"""
        if self.direction_bonus != None:
            if elevator.direction == Direction.UP and origin > elevator.current_floor:
                return -float(self.direction_bonus)
            elif elevator.direction == Direction.DOWN and origin < elevator.current_floor:
                return -float(self.direction_bonus)
        return 0.0
    
