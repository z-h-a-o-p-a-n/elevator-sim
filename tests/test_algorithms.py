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
        assert self.algo.pick_elevator_for_passenger(passenger, [e1, e2]) is e2

    def test_single_elevator_always_chosen(self):
        e = make_elevator(1, floor=5)
        passenger = make_passenger(origin=3)
        assert self.algo.pick_elevator_for_passenger(passenger, [e]) is e

    def test_tie_broken_by_load(self):
        """Equal distance -> elevator with fewer committed passengers wins."""
        e1 = make_elevator(1, floor=3, passengers=2)
        e2 = make_elevator(2, floor=7, passengers=0)  # equidistant from floor 5
        passenger = make_passenger(origin=5)
        assert self.algo.pick_elevator_for_passenger(passenger, [e1, e2]) is e2

    def test_elevator_at_origin_floor(self):
        e1 = make_elevator(1, floor=5)
        e2 = make_elevator(2, floor=1)
        passenger = make_passenger(origin=5)
        assert self.algo.pick_elevator_for_passenger(passenger, [e1, e2]) is e1


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – projected load at pickup
# ---------------------------------------------------------------------------

class TestNearestCarProjectedLoad:
    def setup_method(self):
        self.cfg = make_config()
        self.algo = NearestCarAlgorithm(self.cfg)

    def test_en_route_down_exits_free_capacity(self):
        """Passengers exiting at or above origin reduce the projected load."""
        # 8-capacity elevator at floor 8 going DOWN, full with passengers exiting at floors 9, 7, 6
        e = make_elevator(1, floor=8, direction=Direction.DOWN, capacity=3)
        p_riding = [
            Passenger(id="r1", origin=10, destination=9, request_time=0),  # exits at 9 (above origin 6)
            Passenger(id="r2", origin=10, destination=7, request_time=0),  # exits at 7 (above origin 6)
            Passenger(id="r3", origin=10, destination=3, request_time=0),  # exits at 3 (below origin 6)
        ]
        e.passengers = p_riding
        new_passenger = make_passenger(origin=6, destination=1)
        # At floor 6: r1 and r2 have already exited, only r3 remains → projected load = 1
        assert self.algo._projected_load_at(e, new_passenger) == 1

    def test_en_route_down_full_elevator_considered_available(self):
        """A full elevator that will have space by the origin is still chosen when it's the best option."""
        # e1: full, but passenger exiting before origin frees a seat
        e1 = make_elevator(1, floor=8, direction=Direction.DOWN, capacity=1, destinations={7})
        r = Passenger(id="r1", origin=10, destination=7, request_time=0)  # exits at 7, above origin 6
        e1.passengers = [r]
        # e2: idle, far away
        e2 = make_elevator(2, floor=1, direction=Direction.IDLE, capacity=1)
        p = make_passenger(origin=6, destination=1)
        assert self.algo.pick_elevator_for_passenger(p, [e1, e2]) is e1

    def test_post_trip_includes_travel_to_end_of_run(self):
        """Post-trip score includes travel from current floor to end of run, then to origin."""
        # e1: full, both going to floor 8; new passenger at floor 6 going UP to 9
        # Post-trip distance = |3→8| + |8→6| = 5 + 2 = 7
        e1 = make_elevator(1, floor=3, direction=Direction.UP, capacity=2, destinations={8})
        e1.passengers = [
            Passenger(id="r1", origin=1, destination=8, request_time=0),
            Passenger(id="r2", origin=1, destination=8, request_time=0),
        ]
        # e2: projected load=1 at floor 6; wait=1, direct=3, detour=6-4=2 → score=1+3+4=8
        e2 = make_elevator(2, floor=7, direction=Direction.DOWN, capacity=2, destinations={6, 4})
        e2.passengers = [
            Passenger(id="r3", origin=9, destination=6, request_time=0),
            Passenger(id="r4", origin=9, destination=4, request_time=0),
        ]
        p = make_passenger(origin=6, destination=9)  # going UP
        # e1 score (7+3=10) > e2 score (8) → e2 wins
        assert self.algo.pick_elevator_for_passenger(p, [e1, e2]) is e2

    def test_non_en_route_uses_conservative_load(self):
        """Elevator moving away uses load + assigned without exit credit."""
        e = make_elevator(1, floor=3, direction=Direction.UP, capacity=8)
        p_riding = [Passenger(id="r1", origin=1, destination=10, request_time=0)]
        e.passengers = p_riding
        new_passenger = make_passenger(origin=1, destination=5)  # below current floor, not en-route
        # Elevator going UP, origin 1 < current_floor 3 → not en-route → load + assigned = 1 + 0
        assert self.algo._projected_load_at(e, new_passenger) == 1


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
        """Elevator going up, target above -> no penalty, effective pos = current floor."""
        e = make_elevator(1, floor=3, direction=Direction.UP)
        assert self.algo._effective_position(e, target=8) == 3

    def test_up_elevator_heading_away_from_target(self):
        """Elevator going up, target below -> must travel to furthest dest first."""
        e = make_elevator(1, floor=5, direction=Direction.UP, destinations={7, 9})
        assert self.algo._effective_position(e, target=2) == 9

    def test_down_elevator_heading_away_from_target(self):
        """Elevator going down, target above -> must travel to lowest dest first."""
        e = make_elevator(1, floor=6, direction=Direction.DOWN, destinations={3, 1})
        assert self.algo._effective_position(e, target=9) == 1

    def test_up_elevator_away_no_destinations(self):
        """No destinations above current floor -> fall back to current floor."""
        e = make_elevator(1, floor=5, direction=Direction.UP, destinations=set())
        assert self.algo._effective_position(e, target=2) == 5


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – en-route scoring
# ---------------------------------------------------------------------------

class TestNearestCarEnRoute:
    def setup_method(self):
        self.cfg = make_config()
        self.algo = NearestCarAlgorithm(self.cfg)

    def test_en_route_same_direction_score(self):
        """DOWN elevator, DOWN passenger: wait + direct travel, no detour."""
        e = make_elevator(1, floor=7, direction=Direction.DOWN, destinations={4})
        p = make_passenger(origin=6, destination=1)
        # wait=1, direct=5, detour=0 → score=6
        assert self.algo._score(e, p) == (6, 0)

    def test_en_route_opposite_direction_score(self):
        """DOWN elevator, UP passenger: wait + direct travel + 2x detour floors."""
        e = make_elevator(1, floor=7, direction=Direction.DOWN, destinations={4})
        p = make_passenger(origin=6, destination=9)
        # wait=1, direct=3, detour=6-4=2 → score = 1+3+4 = 8
        assert self.algo._score(e, p) == (8, 0)


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – detour
# ---------------------------------------------------------------------------

class TestNearestCarDetour:
    def setup_method(self):
        self.cfg = make_config()
        self.algo = NearestCarAlgorithm(self.cfg)

    def test_no_detour_same_direction_up(self):
        e = make_elevator(1, floor=2, direction=Direction.UP, destinations={5, 8})
        p = make_passenger(origin=5, destination=10)
        assert self.algo._detour(e, p) == 0

    def test_no_detour_same_direction_down(self):
        e = make_elevator(1, floor=8, direction=Direction.DOWN, destinations={3, 1})
        p = make_passenger(origin=5, destination=1)
        assert self.algo._detour(e, p) == 0

    def test_detour_up_elevator_down_passenger(self):
        e = make_elevator(1, floor=2, direction=Direction.UP, destinations={5, 8})
        p = make_passenger(origin=5, destination=1)
        # beyond={8}, detour=8-5=3
        assert self.algo._detour(e, p) == 3

    def test_detour_down_elevator_up_passenger(self):
        e = make_elevator(1, floor=8, direction=Direction.DOWN, destinations={3, 1})
        p = make_passenger(origin=5, destination=10)
        # beyond={3,1}, detour=5-1=4
        assert self.algo._detour(e, p) == 4


# ---------------------------------------------------------------------------
# NearestCarAlgorithm – direction bonus
# ---------------------------------------------------------------------------

class TestNearestCarDirectionBonus:
    def test_direction_bonus_applied_upward(self):
        cfg = make_config()
        algo = NearestCarAlgorithm(cfg, algo_config={"direction_bonus": 10})
        # e1 idle at floor 5, distance=3 -> score (3, 0)
        # e2 going UP at floor 3, same distance=3, but gets bonus -> score (3-10, 0) = (-7, 0) -> wins
        e1 = make_elevator(1, floor=5, direction=Direction.IDLE)
        e2 = make_elevator(2, floor=3, direction=Direction.UP)
        p = make_passenger(origin=6)
        assert algo.pick_elevator_for_passenger(p, [e1, e2]) is e2

    def test_direction_bonus_not_applied_when_wrong_direction(self):
        cfg = make_config()
        algo = NearestCarAlgorithm(cfg, algo_config={"direction_bonus": 10})
        # e1 idle at floor 5, distance=3
        # e2 going DOWN at floor 8 (moving away from origin=6 if origin < floor… wait floor=8>origin=6 means heading away)
        # Actually DOWN from 8 toward target 6 is heading toward it: direction DOWN, origin < current_floor -> bonus applied
        # Use UP elevator heading away to confirm no bonus
        e1 = make_elevator(1, floor=5, direction=Direction.IDLE)
        e2 = make_elevator(2, floor=8, direction=Direction.UP)  # going UP, origin=6 < 8, no bonus
        p = make_passenger(origin=6)
        # e2 distance = |8-6| = 2, e1 distance = |5-6| = 1 -> e1 wins (closer, no bonus changes that)
        assert algo.pick_elevator_for_passenger(p, [e1, e2]) is e1

    def test_no_direction_bonus_when_not_configured(self):
        cfg = make_config()
        algo = NearestCarAlgorithm(cfg)  # no direction_bonus
        e1 = make_elevator(1, floor=5, direction=Direction.IDLE)
        e2 = make_elevator(2, floor=3, direction=Direction.UP)
        p = make_passenger(origin=6)
        # e1 distance=1, e2 distance=3 -> e1 wins regardless
        assert algo.pick_elevator_for_passenger(p, [e1, e2]) is e1


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
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id in {1, 2}

    def test_high_zone_passenger_gets_high_zone_elevator(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=15, destination=18)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id in {3, 4}

    def test_origin_at_zone_boundary_low(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=10, destination=5)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id in {1, 2}

    def test_origin_at_zone_boundary_high(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        p = make_passenger(origin=11, destination=18)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id in {3, 4}


class TestZonedDispatchCapacity:
    def test_skips_full_elevator_in_zone(self):
        algo = make_zone_algo()
        elevators = make_zone_elevators()
        # Fill elevator 1 to capacity, elevator 2 has space
        for e in elevators:
            if e.id == 1:
                e.passengers = [object()] * 4  # type: ignore[list-item]
        p = make_passenger(origin=3, destination=7)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id == 2


class TestZonedDispatchSubAlgorithms:
    def test_nearest_car_sub_algo_picks_closest(self):
        algo = make_zone_algo(sub_algorithm="nearest_car")
        elevators = make_zone_elevators()
        # Within zone 1: e1 at floor 1, e2 at floor 5; passenger at floor 4 -> e2 is closer
        p = make_passenger(origin=4, destination=8)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id == 2  # closest to floor 4

    def test_round_robin_sub_algo_returns_valid_elevator(self):
        algo = make_zone_algo(sub_algorithm="round_robin")
        elevators = make_zone_elevators()
        p = make_passenger(origin=4, destination=8)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id in {1, 2}

    def test_random_sub_algo_returns_valid_elevator(self):
        algo = make_zone_algo(sub_algorithm="random")
        elevators = make_zone_elevators()
        p = make_passenger(origin=15, destination=18)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result is not None
        assert result.id in {3, 4}


# ---------------------------------------------------------------------------
# ZonedDispatchAlgorithm – overlapping zones
# Zones: 0=[1-15] elevators {1,2}, 1=[10-20] elevators {3,4}
# Overlap region: floors 10-15
# ---------------------------------------------------------------------------

OVERLAP_ZONE_CONFIG = {
    "sub_algorithm": "nearest_car",
    "zones": [
        {"floors": [1, 15], "elevator_ids": [1, 2]},
        {"floors": [10, 20], "elevator_ids": [3, 4]},
    ],
}


def make_overlap_algo() -> ZonedDispatchAlgorithm:
    cfg = SimConfig(num_floors=20, num_elevators=4, elevator_capacity=4, stop_ticks=0)
    return ZonedDispatchAlgorithm(cfg, algo_config=OVERLAP_ZONE_CONFIG)


def make_overlap_elevators() -> list[Elevator]:
    return [
        make_elevator(1, floor=1, capacity=4),
        make_elevator(2, floor=8, capacity=4),
        make_elevator(3, floor=10, capacity=4),
        make_elevator(4, floor=18, capacity=4),
    ]


class TestZonedDispatchOverlappingZones:
    def test_destination_only_in_zone0_uses_zone0(self):
        """Destination in non-overlapping part of zone 0 -> zone 0 elevators."""
        algo = make_overlap_algo()
        elevators = make_overlap_elevators()
        p = make_passenger(origin=3, destination=5)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result.id in {1, 2}

    def test_destination_only_in_zone1_uses_zone1(self):
        """Destination in non-overlapping part of zone 1 -> zone 1 elevators."""
        algo = make_overlap_algo()
        elevators = make_overlap_elevators()
        p = make_passenger(origin=18, destination=17)
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result.id in {3, 4}

    def test_destination_in_overlap_origin_in_zone0_only_uses_zone0(self):
        """Destination in overlap, origin only in zone 0 -> zone 0 covers both."""
        algo = make_overlap_algo()
        elevators = make_overlap_elevators()
        p = make_passenger(origin=5, destination=12)  # origin 5 only in zone 0
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result.id in {1, 2}

    def test_destination_in_overlap_origin_in_zone1_only_uses_zone1(self):
        """Destination in overlap, origin only in zone 1 -> zone 1 covers both."""
        algo = make_overlap_algo()
        elevators = make_overlap_elevators()
        p = make_passenger(origin=18, destination=12)  # origin 18 only in zone 1
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result.id in {3, 4}

    def test_destination_in_overlap_origin_also_in_overlap_uses_first_match(self):
        """Both origin and destination in overlap -> both zones qualify; first zone wins."""
        algo = make_overlap_algo()
        elevators = make_overlap_elevators()
        p = make_passenger(origin=11, destination=13)  # both in overlap
        result = algo.pick_elevator_for_passenger(p, elevators)
        assert result.id in {1, 2}  # zone 0 is first

    def test_find_zone_destination_in_overlap_origin_zone0(self):
        """Direct _find_zone check: origin in zone 0 only -> returns zone 0 index."""
        cfg = SimConfig(num_floors=20, num_elevators=4, elevator_capacity=4, stop_ticks=0)
        algo = ZonedDispatchAlgorithm(cfg, algo_config=OVERLAP_ZONE_CONFIG)
        idx, zone = algo._find_zone(origin=5, destination=12)
        assert idx == 0

    def test_find_zone_destination_in_overlap_origin_zone1(self):
        """Direct _find_zone check: origin in zone 1 only -> returns zone 1 index."""
        cfg = SimConfig(num_floors=20, num_elevators=4, elevator_capacity=4, stop_ticks=0)
        algo = ZonedDispatchAlgorithm(cfg, algo_config=OVERLAP_ZONE_CONFIG)
        idx, zone = algo._find_zone(origin=18, destination=12)
        assert idx == 1

    def test_find_zone_no_match_returns_none(self):
        """Destination outside all zones -> returns (−1, None)."""
        cfg = SimConfig(num_floors=20, num_elevators=4, elevator_capacity=4, stop_ticks=0)
        algo = ZonedDispatchAlgorithm(cfg, algo_config=OVERLAP_ZONE_CONFIG)
        idx, zone = algo._find_zone(origin=5, destination=25)
        assert idx == -1
        assert zone is None
