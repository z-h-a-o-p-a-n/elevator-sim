"""Unit tests for nearest-car and zone-dispatch algorithms."""

import pytest

from elevator_sim.algorithms.nearest_car import NearestCarAlgorithm
from elevator_sim.algorithms.zoned_dispatch import ZonedDispatchAlgorithm
from elevator_sim.config import SimConfig
from elevator_sim.models.elevator import Direction, Elevator
from elevator_sim.models.passenger import Passenger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_elevator(id: int, floor: int, direction: Direction = Direction.IDLE,
                  destinations: set[int] | None = None, passengers: int = 0,
                  assigned: int = 0, capacity: int = 8) -> Elevator:
    e = Elevator(id=id, capacity=capacity, current_floor=floor, direction=direction)
    e.destinations = destinations or set()
    # Stub load counts without real Passenger objects
    e.passengers = [object()] * passengers  # type: ignore[list-item]
    e.assigned = [object()] * assigned  # type: ignore[list-item]
    return e


def make_passenger(origin: int, destination: int = 10) -> Passenger:
    return Passenger(id="p", origin=origin, destination=destination, request_time=0)


def make_config(**kwargs) -> SimConfig:
    return SimConfig(num_floors=20, num_elevators=2, elevator_capacity=8, stop_ticks=0, **kwargs)


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – basic selection
# ---------------------------------------------------------------------------

class TestNearestCarBasic:
    def setup_method(self):
        self.cfg = make_config()
        self.algo = NearestCarAlgorithm(self.cfg)

    def test_picks_closer_elevator(self):
        e1 = make_elevator(1, floor=1)
        e2 = make_elevator(2, floor=8)
        passenger = make_passenger(origin=7)
        assert self.algo.get_elevator(passenger, [e1, e2]) is e2

    def test_single_elevator_always_chosen(self):
        e = make_elevator(1, floor=5)
        passenger = make_passenger(origin=3)
        assert self.algo.get_elevator(passenger, [e]) is e

    def test_tie_broken_by_load(self):
        """Equal distance → elevator with fewer committed passengers wins."""
        e1 = make_elevator(1, floor=3, passengers=2)
        e2 = make_elevator(2, floor=7, passengers=0)  # equidistant from floor 5
        passenger = make_passenger(origin=5)
        assert self.algo.get_elevator(passenger, [e1, e2]) is e2

    def test_elevator_at_origin_floor(self):
        e1 = make_elevator(1, floor=5)
        e2 = make_elevator(2, floor=1)
        passenger = make_passenger(origin=5)
        assert self.algo.get_elevator(passenger, [e1, e2]) is e1


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – effective position (moving away from target)
# ---------------------------------------------------------------------------

class TestNearestCarEffectivePosition:
    def setup_method(self):
        self.cfg = make_config()
        self.algo = NearestCarAlgorithm(self.cfg)

    def test_idle_elevator_uses_current_floor(self):
        e = make_elevator(1, floor=5, direction=Direction.IDLE)
        assert self.algo._effective_position(e, target=3) == 5

    def test_up_elevator_heading_toward_target(self):
        """Elevator going up, target above → no penalty, effective pos = current floor."""
        e = make_elevator(1, floor=3, direction=Direction.UP)
        assert self.algo._effective_position(e, target=8) == 3

    def test_up_elevator_heading_away_from_target(self):
        """Elevator going up, target below → must travel to furthest dest first."""
        e = make_elevator(1, floor=5, direction=Direction.UP, destinations={7, 9})
        assert self.algo._effective_position(e, target=2) == 9

    def test_down_elevator_heading_away_from_target(self):
        """Elevator going down, target above → must travel to lowest dest first."""
        e = make_elevator(1, floor=6, direction=Direction.DOWN, destinations={3, 1})
        assert self.algo._effective_position(e, target=9) == 1

    def test_up_elevator_away_no_destinations(self):
        """No destinations above current floor → fall back to current floor."""
        e = make_elevator(1, floor=5, direction=Direction.UP, destinations=set())
        assert self.algo._effective_position(e, target=2) == 5


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – overshoot
# ---------------------------------------------------------------------------

class TestNearestCarOvershoot:
    def setup_method(self):
        self.cfg = make_config()
        self.algo = NearestCarAlgorithm(self.cfg)

    def test_no_overshoot_idle(self):
        e = make_elevator(1, floor=3, direction=Direction.IDLE)
        assert self.algo._overshoot(e, origin=5) == 0

    def test_no_overshoot_up_no_destinations_beyond(self):
        e = make_elevator(1, floor=2, direction=Direction.UP, destinations={4})
        assert self.algo._overshoot(e, origin=5) == 0  # dest 4 < origin 5

    def test_overshoot_up(self):
        """Elevator going up with destinations beyond origin."""
        e = make_elevator(1, floor=2, direction=Direction.UP, destinations={5, 8})
        # origin=5, beyond = {8}, overshoot = 8-5 = 3
        assert self.algo._overshoot(e, origin=5) == 3

    def test_overshoot_down(self):
        """Elevator going down with destinations below origin."""
        e = make_elevator(1, floor=8, direction=Direction.DOWN, destinations={3, 1})
        # origin=5, beyond = {3, 1}, overshoot = 5-1 = 4
        assert self.algo._overshoot(e, origin=5) == 4

    def test_overshoot_prefers_less_overshoot(self):
        """When equidistant, the elevator with less overshoot wins."""
        # Both are at floor 3 going up, target at floor 5.
        # e1 has no destination beyond 5; e2 has destination at 9.
        e1 = make_elevator(1, floor=3, direction=Direction.UP, destinations={5})
        e2 = make_elevator(2, floor=3, direction=Direction.UP, destinations={5, 9})
        p = make_passenger(origin=5)
        assert self.algo.get_elevator(p, [e1, e2]) is e1


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – direction bonus
# ---------------------------------------------------------------------------

class TestNearestCarDirectionBonus:
    def test_direction_bonus_applied_upward(self):
        cfg = make_config()
        algo = NearestCarAlgorithm(cfg, algo_config={"direction_bonus": 10})
        # e1 idle at floor 5, distance=3 → score (3, 0)
        # e2 going UP at floor 3, same distance=3, but gets bonus → score (3-10, 0) = (-7, 0) → wins
        e1 = make_elevator(1, floor=5, direction=Direction.IDLE)
        e2 = make_elevator(2, floor=3, direction=Direction.UP)
        p = make_passenger(origin=6)
        assert algo.get_elevator(p, [e1, e2]) is e2

    def test_direction_bonus_not_applied_when_wrong_direction(self):
        cfg = make_config()
        algo = NearestCarAlgorithm(cfg, algo_config={"direction_bonus": 10})
        # e1 idle at floor 5, distance=3
        # e2 going DOWN at floor 8 (moving away from origin=6 if origin < floor… wait floor=8>origin=6 means heading away)
        # Actually DOWN from 8 toward target 6 is heading toward it: direction DOWN, origin < current_floor → bonus applied
        # Use UP elevator heading away to confirm no bonus
        e1 = make_elevator(1, floor=5, direction=Direction.IDLE)
        e2 = make_elevator(2, floor=8, direction=Direction.UP)  # going UP, origin=6 < 8, no bonus
        p = make_passenger(origin=6)
        # e2 distance = |8-6| = 2, e1 distance = |5-6| = 1 → e1 wins (closer, no bonus changes that)
        assert algo.get_elevator(p, [e1, e2]) is e1

    def test_no_direction_bonus_when_not_configured(self):
        cfg = make_config()
        algo = NearestCarAlgorithm(cfg)  # no direction_bonus
        e1 = make_elevator(1, floor=5, direction=Direction.IDLE)
        e2 = make_elevator(2, floor=3, direction=Direction.UP)
        p = make_passenger(origin=6)
        # e1 distance=1, e2 distance=3 → e1 wins regardless
        assert algo.get_elevator(p, [e1, e2]) is e1


# ---------------------------------------------------------------------------
# ZonedDispatchAlgorithm
# ---------------------------------------------------------------------------

ZONE_CONFIG = {
    "sub_algorithm": "nearest_car",
    "zones": [
        {"floors": [1, 10], "elevator_ids": [1, 2]},
        {"floors": [11, 20], "elevator_ids": [3, 4]},
    ],
}


def make_zone_algo(sub_algorithm: str = "nearest_car") -> ZonedDispatchAlgorithm:
    cfg = SimConfig(num_floors=20, num_elevators=4, elevator_capacity=4, stop_ticks=0)
    algo_config = dict(ZONE_CONFIG, sub_algorithm=sub_algorithm)
    return ZonedDispatchAlgorithm(cfg, algo_config=algo_config)


def make_zone_elevators() -> list[Elevator]:
    return [
        make_elevator(1, floor=1, capacity=4),
        make_elevator(2, floor=5, capacity=4),
        make_elevator(3, floor=11, capacity=4),
        make_elevator(4, floor=15, capacity=4),
    ]


class TestZonedDispatchZoneRouting:
    def test_low_zone_passenger_gets_low_zone_elevator(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=4, destination=8)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id in {1, 2}

    def test_high_zone_passenger_gets_high_zone_elevator(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=15, destination=18)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id in {3, 4}

    def test_origin_at_zone_boundary_low(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=10, destination=5)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id in {1, 2}

    def test_origin_at_zone_boundary_high(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=11, destination=18)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id in {3, 4}

    def test_origin_outside_all_zones_returns_none(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=25, destination=30)
        result = algo.assign(p, elevators)
        assert result is None


class TestZonedDispatchCapacity:
    def test_returns_none_when_zone_elevators_full(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        # Fill zone 1 elevators to capacity (capacity=4)
        for e in elevators:
            if e.id in {1, 2}:
                e.passengers = [object()] * 4  # type: ignore[list-item]
        p = make_passenger(origin=5, destination=9)
        result = algo.assign(p, elevators)
        assert result is None

    def test_skips_full_elevator_in_zone(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        # Fill elevator 1 to capacity, elevator 2 has space
        for e in elevators:
            if e.id == 1:
                e.passengers = [object()] * 4  # type: ignore[list-item]
        p = make_passenger(origin=3, destination=7)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id == 2


class TestZonedDispatchSubAlgorithms:
    def test_nearest_car_sub_algo_picks_closest(self):
        algo = make_zone_algo(sub_algorithm="nearest_car")
        elevators = make_zone_elevators()
        # Within zone 1: e1 at floor 1, e2 at floor 5; passenger at floor 4 → e2 is closer
        p = make_passenger(origin=4, destination=8)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id == 2  # closest to floor 4

    def test_round_robin_sub_algo_returns_valid_elevator(self):
        algo = make_zone_algo(sub_algorithm="round_robin")
        elevators = make_zone_elevators()
        p = make_passenger(origin=4, destination=8)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id in {1, 2}

    def test_random_sub_algo_returns_valid_elevator(self):
        algo = make_zone_algo(sub_algorithm="random")
        elevators = make_zone_elevators()
        p = make_passenger(origin=15, destination=18)
        result = algo.assign(p, elevators)
        assert result is not None
        assert result.id in {3, 4}

    def test_get_elevator_raises(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=5)
        with pytest.raises(NotImplementedError):
            algo.get_elevator(p, elevators)
