from elevator_sim.config import SimConfig

from .base import BaseAlgorithm
from .nearest_car import NearestCarAlgorithm
from .round_robin import RoundRobinAlgorithm
from .zoned_dispatch import ZonedDispatchAlgorithm

REGISTRY: dict[str, type[BaseAlgorithm]] = {
    "nearest_car": NearestCarAlgorithm,
    "round_robin": RoundRobinAlgorithm,
    "zoned_dispatch": ZonedDispatchAlgorithm,
}


def get_algorithm(config: SimConfig, algo_config: dict = {}) -> BaseAlgorithm:
    name = config.algorithm
    if name not in REGISTRY:
        raise ValueError(f"Unknown algorithm '{name}'. Available: {list(REGISTRY)}")
    if name == "nearest_car":
        return NearestCarAlgorithm(config, algo_config)
    if name == "round_robin":
        return RoundRobinAlgorithm(config, algo_config)
    if name == "zoned_dispatch":
        return ZonedDispatchAlgorithm(config, algo_config)
    return REGISTRY[name]()


__all__ = ["BaseAlgorithm", "NearestCarAlgorithm", "RoundRobinAlgorithm", "ZonedDispatchAlgorithm", "REGISTRY", "get_algorithm"]
