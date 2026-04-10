"""
Mock elevator request data generator.

Generates CSV files in the format: time,id,source,dest

Usage:
    python -m elevator_sim.mock_data.generate [options]
    python generate.py [options]
"""

import argparse
import csv
import random
from pathlib import Path


# ---------------------------------------------------------------------------
# Floor-pair sampling helpers
# ---------------------------------------------------------------------------

def _other_floor(floor: int, num_floors: int) -> int:
    """Return a random floor that is not `floor`."""
    choices = [f for f in range(1, num_floors + 1) if f != floor]
    return random.choice(choices)


def _sample_floor_pair(num_floors: int, bias: str = "none") -> tuple[int, int]:
    """
    Sample (source, dest) pair.

    bias:
        "up_from_1"   – source is floor 1, dest is upper floor
        "down_to_1"   – source is upper floor, dest is floor 1
        "inter_floor"  – neither source nor dest is floor 1
        "none"         – fully random
    """
    if bias == "up_from_1":
        src = 1
        dst = random.randint(2, num_floors)
    elif bias == "down_to_1":
        src = random.randint(2, num_floors)
        dst = 1
    elif bias == "inter_floor":
        src = random.randint(2, num_floors)
        dst = _other_floor(src, num_floors)
        while dst == 1:
            dst = _other_floor(src, num_floors)
    else:  # "none"
        src = random.randint(1, num_floors)
        dst = _other_floor(src, num_floors)
    return src, dst


# ---------------------------------------------------------------------------
# Time-distribution samplers  (each returns a tick in [0, num_ticks))
# ---------------------------------------------------------------------------

def _uniform_tick(num_ticks: int) -> int:
    return random.randint(0, num_ticks - 1)


def _gaussian_tick(num_ticks: int) -> int:
    mean = num_ticks / 2
    std = num_ticks / 6
    tick = int(random.gauss(mean, std))
    return max(0, min(num_ticks - 1, tick))


def _exponential_tick(num_ticks: int) -> int:
    scale = num_ticks / 5
    tick = int(random.expovariate(1.0 / scale))
    return max(0, min(num_ticks - 1, tick))


# Workday tick constants (as fractions of num_ticks, assuming a ~10-hour day)
_WORKDAY_PEAKS = {
    # (center_fraction, std_fraction, weight, bias)
    "am_rush":    (0.10, 0.04, 0.30, "up_from_1"),
    "lunch_down": (0.40, 0.03, 0.15, "down_to_1"),
    "lunch_up":   (0.47, 0.03, 0.10, "up_from_1"),
    "pm_rush":    (0.80, 0.04, 0.30, "down_to_1"),
    "background": (0.50, 0.30, 0.15, "none"),
}


def _workday_sample(num_ticks: int, num_floors: int) -> tuple[int, int, int]:
    """Return (tick, source, dest) drawn from the workday distribution."""
    peaks = list(_WORKDAY_PEAKS.values())
    weights = [p[2] for p in peaks]
    (center_frac, std_frac, _, bias) = random.choices(peaks, weights=weights, k=1)[0]

    center = center_frac * num_ticks
    std = std_frac * num_ticks
    tick = int(random.gauss(center, std))
    tick = max(0, min(num_ticks - 1, tick))

    src, dst = _sample_floor_pair(num_floors, bias=bias)
    return tick, src, dst


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def generate_records(
    num_records: int,
    num_floors: int,
    num_ticks: int,
    distribution: str,
) -> list[tuple[int, str, int, int]]:
    """
    Generate a list of (time, id, source, dest) tuples sorted by time.

    distribution: "uniform" | "gaussian" | "exponential" | "workday"
    """
    if num_floors < 2:
        raise ValueError("num_floors must be at least 2")
    if num_ticks < 1:
        raise ValueError("num_ticks must be at least 1")
    if num_records < 1:
        raise ValueError("num_records must be at least 1")

    records: list[tuple[int, str, int, int]] = []

    for i in range(num_records):
        passenger_id = "passenger_x"    #temp placeholder

        if distribution == "uniform":
            tick = _uniform_tick(num_ticks)
            src, dst = _sample_floor_pair(num_floors)
        elif distribution == "gaussian":
            tick = _gaussian_tick(num_ticks)
            src, dst = _sample_floor_pair(num_floors)
        elif distribution == "exponential":
            tick = _exponential_tick(num_ticks)
            src, dst = _sample_floor_pair(num_floors)
        elif distribution == "workday":
            tick, src, dst = _workday_sample(num_ticks, num_floors)
        else:
            raise ValueError(f"Unknown distribution: {distribution!r}")

        records.append((tick, passenger_id, src, dst))

    records.sort(key=lambda r: r[0])

    # assign passenger ids incrementally
    for i in range(num_records):
        passenger_id = f"passenger{i + 1}"
        tick = records[i][0]
        src = records[i][2]
        dst = records[i][3]
        records[i] = (tick, passenger_id, src, dst)

    return records


def write_csv(records: list[tuple[int, str, int, int]], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "id", "source", "dest"])
        writer.writerows(records)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate mock elevator request CSV data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-n", "--num-records",
        type=int,
        default=100,
        help="Number of passenger request records to generate",
    )
    parser.add_argument(
        "-f", "--num-floors",
        type=int,
        default=10,
        help="Number of floors in the building",
    )
    parser.add_argument(
        "-t", "--num-ticks",
        type=int,
        default=1000,
        help="Total simulation ticks (time horizon)",
    )
    parser.add_argument(
        "-d", "--distribution",
        choices=["uniform", "gaussian", "exponential", "workday"],
        default="uniform",
        help=(
            "Time distribution for requests: "
            "uniform (evenly spread), "
            "gaussian (clustered at midpoint), "
            "exponential (front-loaded), "
            "workday (AM rush / lunch / PM rush peaks)"
        ),
    )
    parser.add_argument(
        "-o", "--output",
        default="output/mock_requests.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)

    print(f"Generating {args.num_records} records "
          f"({args.num_floors} floors, {args.num_ticks} ticks, "
          f"distribution={args.distribution!r}) ...")

    records = generate_records(
        num_records=args.num_records,
        num_floors=args.num_floors,
        num_ticks=args.num_ticks,
        distribution=args.distribution,
    )

    write_csv(records, args.output)
    print(f"Written to {args.output}")


if __name__ == "__main__":
    main()
