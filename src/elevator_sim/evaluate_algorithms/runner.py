"""Run a single algorithm configuration and return structured results."""

from dataclasses import dataclass
from typing import Any

from ..algorithms import get_algorithm
from ..config import SimConfig
from ..io.reader import Request
from ..io.writer import LogWriter
from ..models.elevator import Elevator
from ..models.passenger import Passenger
from ..simulation import Simulation
from ..stats import ElevatorUtilization, SimStats, compute_elevator_utilization, compute_stats


@dataclass
class AlgoSpec:
    """Specification for one algorithm run."""

    name: str
    label: str
    algo_params: dict[str, Any]
    sim_overrides: dict[str, Any]


@dataclass
class EvalResult:
    """Results from a single algorithm run."""

    label: str
    stats: SimStats
    utilization: list[ElevatorUtilization]
    simulation_duration: int
    total_floors_traveled: int


class NullWriter(LogWriter):
    """No-op writer — discards all log output."""

    def __init__(self) -> None:
        pass

    def log_tick(self, _tick: int, _elevators: list[Elevator]) -> None:
        pass

    def log_passenger(self, _passenger: Passenger) -> None:
        pass

    def close(self) -> None:
        pass

    def __exit__(self, *_: object) -> None:
        pass


# SimConfig field names that can be overridden per algo spec.
# Maps CLI shorthand → SimConfig field name.
_SIM_PARAM_ALIASES: dict[str, str] = {
    "floors": "num_floors",
    "elevators": "num_elevators",
    "capacity": "elevator_capacity",
    "stop_ticks": "stop_ticks",
    # Also accept the full names directly.
    "num_floors": "num_floors",
    "num_elevators": "num_elevators",
    "elevator_capacity": "elevator_capacity",
}


def parse_algo_spec(raw: str) -> AlgoSpec:
    """Parse an --algo argument into an AlgoSpec.

    Format: ``name`` or ``name:key=val,key=val,...``

    Keys matching SimConfig fields (floors, elevators, capacity, stop_ticks) are
    treated as sim-config overrides; all other keys are algorithm parameters.
    """
    if ":" in raw:
        name, params_str = raw.split(":", 1)
    else:
        name, params_str = raw, ""

    name = name.strip()
    algo_params: dict[str, Any] = {}
    sim_overrides: dict[str, Any] = {}

    if params_str:
        for part in params_str.split(","):
            part = part.strip()
            if "=" not in part:
                raise ValueError(f"Invalid parameter '{part}' in algo spec '{raw}'. Expected key=value.")
            key, val_str = part.split("=", 1)
            key = key.strip()
            val_str = val_str.strip()

            # Try to coerce to int, then float, then leave as str.
            val: int | float | str
            try:
                val = int(val_str)
            except ValueError:
                try:
                    val = float(val_str)
                except ValueError:
                    val = val_str

            if key in _SIM_PARAM_ALIASES:
                sim_overrides[_SIM_PARAM_ALIASES[key]] = val
            else:
                algo_params[key] = val

    # Build a human-readable label.
    all_params = {**{k: v for k, v in sim_overrides.items()}, **algo_params}
    if all_params:
        param_str = ", ".join(f"{k}={v}" for k, v in all_params.items())
        label = f"{name} ({param_str})"
    else:
        label = name

    return AlgoSpec(name=name, label=label, algo_params=algo_params, sim_overrides=sim_overrides)


def run_algo(requests: list[Request], base_config: SimConfig, spec: AlgoSpec) -> EvalResult:
    """Run the simulation for one AlgoSpec and return an EvalResult."""
    # Merge base config with per-spec sim overrides.
    config = SimConfig(
        num_floors=spec.sim_overrides.get("num_floors", base_config.num_floors),
        num_elevators=spec.sim_overrides.get("num_elevators", base_config.num_elevators),
        elevator_capacity=spec.sim_overrides.get("elevator_capacity", base_config.elevator_capacity),
        stop_ticks=spec.sim_overrides.get("stop_ticks", base_config.stop_ticks),
        algorithm=spec.name,
    )

    algorithm = get_algorithm(spec.name, spec.algo_params)

    sim = Simulation(config, algorithm)
    with NullWriter() as writer:
        sim.run(requests, writer)

    stats = compute_stats(sim.passengers)
    utilization = compute_elevator_utilization(sim.elevators, sim.total_ticks)
    total_floors = sum(e.floors_traveled for e in sim.elevators)

    return EvalResult(
        label=spec.label,
        stats=stats,
        utilization=utilization,
        simulation_duration=sim.total_ticks,
        total_floors_traveled=total_floors,
    )
