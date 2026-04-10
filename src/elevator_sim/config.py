"""Simulation configuration."""

from dataclasses import dataclass


@dataclass
class SimConfig:
    num_floors: int = 100
    num_elevators: int = 2
    elevator_capacity: int = 8
    stop_ticks: int = 0  # ticks an elevator remains stopped after boarding/exiting
    output_dir: str = "output"
    algorithm: str = "nearest_car"

    # work around for "object is not subscriptable"
    def __getitem__(self, index):
        match index:
            case "nearest_car":
                return {
                    "direction_bonus": 0.0  # subtracted from score when elevator heads toward origin; 0 = disabled
                }
            case "zoned_dispatch":
                return {
                    "sub_algorithm": "nearest_car",  # "nearest_car" | "round_robin" | "random"
                    "zones": [
                        {"floors": [1, 50],  "elevator_ids": [1, 2]},
                        {"floors": [51, 100], "elevator_ids": [3, 4]},
                    ]
                }
            case _:
                return {}
    