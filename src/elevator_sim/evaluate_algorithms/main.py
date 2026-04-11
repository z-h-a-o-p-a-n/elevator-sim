"""CLI entry point for evaluate-algorithms."""

import argparse
import logging
import sys
from pathlib import Path

from .. import configure_logging
from ..algorithms import REGISTRY
from ..config import SimConfig
from ..io.reader import parse_csv
from .display import print_results
from .runner import AlgoSpec, parse_algo_spec, run_algo

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="evaluate-algorithms",
        description="Run multiple elevator dispatch algorithms against the same input and compare results.",
    )
    parser.add_argument("input", help="Path to the CSV request file")
    parser.add_argument("--floors", "-f", type=int, default=10, metavar="N", help="Number of floors (default: 10)")
    parser.add_argument("--elevators", "-e", type=int, default=3, metavar="N", help="Number of elevators (default: 3)")
    parser.add_argument("--capacity", "-c", type=int, default=8, metavar="N", help="Elevator capacity (default: 8)")
    parser.add_argument("--stop-ticks", type=int, default=0, metavar="N", help="Stop-tick penalty (default: 0)")
    parser.add_argument(
        "--algo",
        action="append",
        dest="algos",
        metavar="SPEC",
        help=(
            "Algorithm spec: name or name:key=val,... "
            "Sim-config keys: floors, elevators, capacity, stop_ticks. "
            "All other keys are passed as algorithm parameters (e.g. direction_bonus=5.0). "
            "Repeat --algo to compare multiple configurations. "
            f"Available algorithms: {', '.join(REGISTRY)}."
        ),
    )
    parser.add_argument(
        "--log-level",
        default=None,
        metavar="LEVEL",
        help="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO, overrides LOG_LEVEL env var)",
    )

    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Error: input file '%s' not found.", input_path)
        sys.exit(1)

    base_config = SimConfig(
        num_floors=args.floors,
        num_elevators=args.elevators,
        elevator_capacity=args.capacity,
        stop_ticks=args.stop_ticks,
    )

    # Default: run all registered algorithms once if no --algo flags given.
    raw_specs: list[str] = args.algos if args.algos else list(REGISTRY.keys())

    specs: list[AlgoSpec] = []
    for raw in raw_specs:
        try:
            spec = parse_algo_spec(raw)
        except ValueError as e:
            logger.error("Error: %s", e)
            sys.exit(1)
        if spec.name not in REGISTRY:
            logger.error("Error: unknown algorithm '%s'. Available: %s.", spec.name, ", ".join(REGISTRY))
            sys.exit(1)
        specs.append(spec)

    requests = parse_csv(input_path)

    results = []
    for spec in specs:
        logger.info("Running %s...", spec.label)
        result = run_algo(requests, base_config, spec)
        results.append(result)
        logger.info("done")

    base_config_desc = (
        f"floors={args.floors} | elevators={args.elevators} | "
        f"capacity={args.capacity} | stop_ticks={args.stop_ticks}"
    )
    print_results(results, input_path.name, base_config_desc)
