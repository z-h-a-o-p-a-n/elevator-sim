"""CLI entry point for elevator-sim."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from . import configure_logging
from .algorithms import REGISTRY, get_algorithm
from .config import SimConfig
from .io.reader import Request, parse_csv, parse_records
from .io.writer import LogWriter
from .simulation import Simulation
from .stats import (
    compute_elevator_utilization,
    compute_stats,
    print_elevator_utilization,
    print_stats,
)

logger = logging.getLogger(__name__)


def run(
    requests: list[Request],
    config: SimConfig | None = None,
    algo_config: dict | None = None,
    run_id: str | None = None,
) -> None:
    """Run the simulation programmatically.

    Args:
        requests: Parsed elevator requests (use parse_csv or parse_records).
        config:   Simulation configuration. Defaults to SimConfig().
        algo_config: Algorithm configuration. Defaults to the value defined in SimConfig().
        run_id:   Log file prefix. Defaults to a timestamp string.
    """
    if config is None:
        config = SimConfig()
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # if the algo configuration is not specified, use the default
    if algo_config is None:
        algo_config = config.algo_config[config.algorithm]

    algorithm = get_algorithm(config, algo_config)
    logger.info("Simulation configuration: %s", config)
    logger.info("Algorithm config: %s", algo_config)

    sim = Simulation(config=config, algorithm=algorithm)

    with LogWriter(
        output_dir=config.output_dir,
        run_id=run_id,
        num_elevators=config.num_elevators,
        algorithm=config.algorithm
    ) as writer:
        passengers = sim.run(requests, writer)

    stats = compute_stats(passengers)
    print_stats(stats)

    utilizations = compute_elevator_utilization(sim.elevators, sim.total_ticks)
    print_elevator_utilization(utilizations)

    out = Path(config.output_dir)
    logger.info("\nLogs written to:")
    logger.info("  %s", out / f"{run_id}_positions.csv")
    logger.info("  %s", out / f"{run_id}_passengers.csv")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="elevator-sim",
        description="Intelligent elevator system simulation.",
    )
    parser.add_argument("input", help="Path to CSV request file (time,id,source,dest)")
    parser.add_argument(
        "--elevators", type=int, default=3, metavar="N", help="Number of elevators (default: 2)"
    )
    parser.add_argument(
        "--floors", type=int, default=10, metavar="N", help="Number of floors (default: 10)"
    )
    parser.add_argument(
        "--capacity", type=int, default=8, metavar="N", help="Elevator capacity (default: 8)"
    )
    parser.add_argument(
        "--stop-ticks",
        type=int,
        default=0,
        metavar="N",
        help="Ticks spent stopped after boarding/exiting (default: 0)",
    )
    parser.add_argument(
        "--algorithm",
        choices=list(REGISTRY),
        default="nearest_car",
        help="Dispatch algorithm (default: nearest_car)",
    )
    parser.add_argument(
        "--algo-config",
        type=json.loads,
        metavar="N",
        help="A JSON of the algorithm configuration (i.e, {\"direction_bonus\": 0.0})",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        metavar="DIR",
        help="Directory for log files (default: output/)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        metavar="ID",
        help="Log file prefix (default: timestamp)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        metavar="LEVEL",
        help="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO, overrides LOG_LEVEL env var)",
    )

    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    config = SimConfig(
        num_floors=args.floors,
        num_elevators=args.elevators,
        elevator_capacity=args.capacity,
        stop_ticks=args.stop_ticks,
        output_dir=args.output_dir,
        algorithm=args.algorithm
    )
    if args.algo_config is not None:
        algo_config = dict(args.algo_config)
    else:
        algo_config = None

    try:
        requests = parse_csv(args.input)
    except FileNotFoundError:
        logger.error("Error: input file not found: %s", args.input)
        sys.exit(1)

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    run(requests, config=config, algo_config=algo_config, run_id=run_id)


if __name__ == "__main__":
    main()
