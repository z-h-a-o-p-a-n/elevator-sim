"""Shared pytest fixtures."""

import pytest

from elevator_sim.algorithms import get_algorithm
from elevator_sim.config import SimConfig
from elevator_sim.io.reader import Request
from elevator_sim.models import Elevator
from elevator_sim.simulation import Simulation


@pytest.fixture
def default_config() -> SimConfig:
    return SimConfig(num_floors=10, num_elevators=2, elevator_capacity=4, stop_ticks=0)


@pytest.fixture
def simple_requests() -> list[Request]:
    return [
        Request(time=0, id="p1", source=1, dest=5),
        Request(time=0, id="p2", source=3, dest=8),
        Request(time=10, id="p3", source=8, dest=1),
    ]


@pytest.fixture
def sim(default_config: SimConfig) -> Simulation:
    return Simulation(config=default_config, algorithm=get_algorithm("nearest_car"))
