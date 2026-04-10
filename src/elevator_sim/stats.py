"""Compute and display passenger statistics."""

import math
from dataclasses import dataclass

from .models.elevator import Elevator
from .models.passenger import Passenger


@dataclass
class SimStats:
    count: int
    min_wait: int
    min_wait_id: str
    max_wait: int
    max_wait_id: str
    avg_wait: float
    std_wait: float
    p95_wait: float
    min_total: int
    min_total_id: str
    max_total: int
    max_total_id: str
    avg_total: float
    std_total: float
    p95_total: float


@dataclass
class ElevatorUtilization:
    elevator_id: int
    active_ticks: int
    total_ticks: int
    utilization: float  # percentage


def compute_stats(passengers: list[Passenger]) -> SimStats:
    completed = [p for p in passengers if p.arrived]
    if not completed:
        raise ValueError("No completed passengers to compute stats from.")

    wait_times = sorted(p.wait_time for p in completed)  # type: ignore[misc]
    total_times = sorted(p.total_time for p in completed)  # type: ignore[misc]

    def percentile(data: list[int], pct: float) -> float:
        if len(data) == 1:
            return float(data[0])
        idx = (len(data) - 1) * pct / 100
        lo, hi = int(idx), min(int(idx) + 1, len(data) - 1)
        return data[lo] + (data[hi] - data[lo]) * (idx - lo)

    def stdev(data: list[int], mean: float) -> float:
        if len(data) < 2:
            return 0.0
        return math.sqrt(sum((x - mean) ** 2 for x in data) / (len(data) - 1))

    avg_wait = sum(wait_times) / len(wait_times)
    avg_total = sum(total_times) / len(total_times)

    min_wait_p = min(completed, key=lambda p: p.wait_time)  # type: ignore[arg-type]
    max_wait_p = max(completed, key=lambda p: p.wait_time)  # type: ignore[arg-type]
    min_total_p = min(completed, key=lambda p: p.total_time)  # type: ignore[arg-type]
    max_total_p = max(completed, key=lambda p: p.total_time)  # type: ignore[arg-type]

    return SimStats(
        count=len(completed),
        min_wait=wait_times[0],
        min_wait_id=min_wait_p.id,
        max_wait=wait_times[-1],
        max_wait_id=max_wait_p.id,
        avg_wait=avg_wait,
        std_wait=stdev(wait_times, avg_wait),
        p95_wait=percentile(wait_times, 95),
        min_total=total_times[0],
        min_total_id=min_total_p.id,
        max_total=total_times[-1],
        max_total_id=max_total_p.id,
        avg_total=avg_total,
        std_total=stdev(total_times, avg_total),
        p95_total=percentile(total_times, 95),
    )


def compute_elevator_utilization(
    elevators: list[Elevator], total_ticks: int
) -> list[ElevatorUtilization]:
    result = []
    for e in elevators:
        util = (e.active_ticks / total_ticks * 100) if total_ticks > 0 else 0.0
        result.append(
            ElevatorUtilization(
                elevator_id=e.id,
                active_ticks=e.active_ticks,
                total_ticks=total_ticks,
                utilization=util,
            )
        )
    return result


def print_stats(stats: SimStats) -> None:
    print("\n=== Passenger Statistics ===")
    print(f"  Passengers served : {stats.count}")
    print(f"  Wait time  — min: {stats.min_wait} (id={stats.min_wait_id}), "
          f"max: {stats.max_wait} (id={stats.max_wait_id}), "
          f"avg: {stats.avg_wait:.1f}, std: {stats.std_wait:.1f}, p95: {stats.p95_wait:.1f}")
    print(f"  Total time — min: {stats.min_total} (id={stats.min_total_id}), "
          f"max: {stats.max_total} (id={stats.max_total_id}), "
          f"avg: {stats.avg_total:.1f}, std: {stats.std_total:.1f}, p95: {stats.p95_total:.1f}")


def print_elevator_utilization(utilizations: list[ElevatorUtilization]) -> None:
    print("\n=== Elevator Utilization ===")
    for u in utilizations:
        print(f"  Elevator {u.elevator_id}: {u.utilization:.1f}%  "
              f"({u.active_ticks}/{u.total_ticks} ticks active)")

    rates = [u.utilization for u in utilizations]
    avg = sum(rates) / len(rates)
    std = math.sqrt(sum((r - avg) ** 2 for r in rates) / len(rates)) if len(rates) > 1 else 0.0
    sorted_rates = sorted(rates)
    if len(sorted_rates) == 1:
        p95 = sorted_rates[0]
    else:
        idx = (len(sorted_rates) - 1) * 95 / 100
        lo, hi = int(idx), min(int(idx) + 1, len(sorted_rates) - 1)
        p95 = sorted_rates[lo] + (sorted_rates[hi] - sorted_rates[lo]) * (idx - lo)
    print(f"  ---")
    print(f"  Utilization — min: {min(rates):.1f}%, max: {max(rates):.1f}%, "
          f"avg: {avg:.1f}%, std: {std:.1f}%, p95: {p95:.1f}%")
