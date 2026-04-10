from .base import BaseAlgorithm
from .nearest_car import NearestCarAlgorithm

REGISTRY: dict[str, type[BaseAlgorithm]] = {
    "nearest_car": NearestCarAlgorithm,
}


def get_algorithm(name: str, algo_configs: dict = {}) -> BaseAlgorithm:
    if name not in REGISTRY:
        raise ValueError(f"Unknown algorithm '{name}'. Available: {list(REGISTRY)}")
    if name == "nearest_car":
        return NearestCarAlgorithm(algo_configs)
    return REGISTRY[name]()


__all__ = ["BaseAlgorithm", "NearestCarAlgorithm", "REGISTRY", "get_algorithm"]
