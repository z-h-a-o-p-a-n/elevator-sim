"""Zoned destination dispatch algorithm."""

import random
import logging
from dataclasses import dataclass

from ..models.elevator import Elevator
from ..models.passenger import Passenger
from ..config import SimConfig
from .base import BaseAlgorithm
from .nearest_car import NearestCarAlgorithm
from .round_robin import RoundRobinAlgorithm


logger = logging.getLogger(__name__)

@dataclass
class Zone:
    floor_min: int
    floor_max: int
    elevator_ids: set[int]


class ZonedDispatchAlgorithm(BaseAlgorithm):
    """Assigns passengers to elevators based on configured floor zones.

    A passenger's origin floor determines their zone. Within the zone, the
    sub_algorithm selects which elevator to assign. Cross-zone requests
    (origin in one zone, destination in another) are handled by the origin zone.
    Returns None if all elevators in the zone are at capacity.

    Config keys:
        sub_algorithm: "nearest_car" | "round_robin" | "random" (default: "nearest_car")
        zones: list of dicts, each with:
            "floors": [min_floor, max_floor]  (inclusive, 1-indexed)
            "elevator_ids": [id, ...]
    """

    def __init__(self, config: SimConfig, algo_config: dict = {}) -> None:
        self._config = config
        self._zones: list[Zone] = [
            Zone(
                floor_min=z["floors"][0],
                floor_max=z["floors"][1],
                elevator_ids=set(z["elevator_ids"]),
            )
            for z in algo_config.get("zones", [])
        ]
        self._sub_algorithm = algo_config.get("sub_algorithm", "nearest_car")
        # use a separate round_robin algo instance for each zone
        self._rr_algos: dict[int, RoundRobinAlgorithm] = {_: RoundRobinAlgorithm(config) for _ in range(len(self._zones))}
        # use a single nearest_car algo instance for all zones
        self._nearest_car = NearestCarAlgorithm(config)

    def assign(self, passenger: Passenger, elevators: list[Elevator]) -> Elevator:
        zone_idx, zone = self._find_zone(passenger.origin, passenger.destination)
        if zone is None:
            logger.error("Unable to determine the zone for floor %s", passenger.destination)
            exit(-1)

        zone_elevators = [e for e in elevators if e.id in zone.elevator_ids]

        return self._pick(zone_elevators, passenger, zone_idx)

    def _find_zone(self, origin: int, destination: int) -> tuple[int, Zone | None]:
        matches = [
            (i, zone) for i, zone in enumerate(self._zones)
            if zone.floor_min <= destination <= zone.floor_max
        ]
        if not matches:
            return -1, None
        if len(matches) == 1:
            return matches[0]
        for i, zone in matches:
            if zone.floor_min <= origin <= zone.floor_max:
                return i, zone
        return matches[0]

    def _pick(self, elevators: list[Elevator], passenger: Passenger, zone_idx: int) -> Elevator:
        if self._sub_algorithm == "nearest_car":
            return self._nearest_car.assign(passenger, elevators)
        if self._sub_algorithm == "round_robin":
            rr_algo = self._rr_algos.get(zone_idx)
            return rr_algo.assign(passenger, elevators)
        # random
        return random.choice(elevators)
