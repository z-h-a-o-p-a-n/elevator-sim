"""CLI entry point for evaluate-algorithms."""

import argparse
import sys
from pathlib import Path

from ..algorithms import REGISTRY
from ..config import SimConfig
from ..io.reader import parse_csv
from .display import print_results
from .runner import AlgoSpec, parse_algo_spec, run_algo


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

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file '{input_path}' not found.", file=sys.stderr)
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
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if spec.name not in REGISTRY:
            print(
                f"Error: unknown algorithm '{spec.name}'. Available: {', '.join(REGISTRY)}.",
                file=sys.stderr,
            )
            sys.exit(1)
        specs.append(spec)

    requests = parse_csv(input_path)

    results = []
    for spec in specs:
        print(f"Running {spec.label}...", end=" ", flush=True)
        result = run_algo(requests, base_config, spec)
        results.append(result)
        print("done")

    base_config_desc = (
        f"floors={args.floors} | elevators={args.elevators} | "
        f"capacity={args.capacity} | stop_ticks={args.stop_ticks}"
    )
    print_results(results, input_path.name, base_config_desc)
