from .base import BaseAlgorithm
from .nearest_car import NearestCarAlgorithm
from .round_robin import RoundRobinAlgorithm

REGISTRY: dict[str, type[BaseAlgorithm]] = {
    "nearest_car": NearestCarAlgorithm,
    "round_robin": RoundRobinAlgorithm,
}


def get_algorithm(name: str, algo_configs: dict = {}) -> BaseAlgorithm:
    if name not in REGISTRY:
        raise ValueError(f"Unknown algorithm '{name}'. Available: {list(REGISTRY)}")
    if name == "nearest_car":
        return NearestCarAlgorithm(algo_configs)
    if name == "round_robin":
        return RoundRobinAlgorithm(algo_configs)
    return REGISTRY[name]()


__all__ = ["BaseAlgorithm", "NearestCarAlgorithm", "RoundRobinAlgorithm", "REGISTRY", "get_algorithm"]
