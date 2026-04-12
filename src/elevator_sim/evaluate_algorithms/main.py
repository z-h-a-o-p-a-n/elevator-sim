"""CLI entry point for evaluate-algorithms."""

import argparse
import json
import logging
import sys
from pathlib import Path

from .. import configure_logging
from ..algorithms import REGISTRY
from ..config import SimConfig
from ..io.reader import parse_csv
from .display import print_results
from .runner import AlgoSpec, algo_spec_from_dict, run_algo

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
        "--config-file",
        metavar="PATH",
        help=(
            "Path to a JSON file containing an array of algorithm run objects. "
            "Each object must have 'name' (label), 'algorithm' (algorithm name), "
            "and optionally 'config' (algorithm parameters) and sim overrides "
            "('floors', 'elevators', 'capacity', 'stop_ticks'). "
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

    if not args.config_file:
        logger.error("Error: --config-file is required.")
        sys.exit(1)

    config_path = Path(args.config_file)
    if not config_path.exists():
        logger.error("Error: config file '%s' not found.", config_path)
        sys.exit(1)

    try:
        raw_entries = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        logger.error("Error: failed to parse config file: %s", e)
        sys.exit(1)

    specs: list[AlgoSpec] = []
    for entry in raw_entries:
        spec = algo_spec_from_dict(entry)
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
