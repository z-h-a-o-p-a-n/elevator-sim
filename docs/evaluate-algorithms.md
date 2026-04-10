# Algorithm Evaluator

## Summary

`evaluate-algorithms` runs multiple dispatch algorithms (or multiple configurations of the same algorithm) against an identical input file and prints a side-by-side comparison table. Each algorithm gets its own full simulation run; results are collected and rendered together at the end.

---

## Architecture

The tool is split into three modules:

| Module | Responsibility |
|--------|---------------|
| `evaluate_algorithms/main.py` | CLI parsing, spec validation, orchestration |
| `evaluate_algorithms/runner.py` | Per-algorithm simulation execution, result collection |
| `evaluate_algorithms/display.py` | Terminal table rendering |

---

## Execution flow

```
parse CLI args
    │
    ├─ build base SimConfig from shared flags (--floors, --elevators, etc.)
    ├─ parse each --algo spec into an AlgoSpec
    └─ load requests from CSV (once, shared across all runs)

for each AlgoSpec:
    merge base SimConfig with per-spec sim overrides → run SimConfig
    instantiate algorithm
    run Simulation with NullWriter        ← no log files written
    collect SimStats + ElevatorUtilization + total_floors_traveled → EvalResult

print_results(all EvalResults)
```

The input CSV is parsed **once** and the same `list[Request]` is passed to every run. Each run creates a fresh `Simulation` and fresh `Elevator` objects, so runs are fully independent.

---

## `AlgoSpec` — the spec format

Each `--algo` argument is parsed into an `AlgoSpec`:

```
name
name:key=val,key=val,...
```

Key–value pairs are split into two buckets:

**Sim-config overrides** — keys that map to `SimConfig` fields replace the corresponding base-config value for that run only:

| CLI key | `SimConfig` field |
|---------|------------------|
| `floors` / `num_floors` | `num_floors` |
| `elevators` / `num_elevators` | `num_elevators` |
| `capacity` / `elevator_capacity` | `elevator_capacity` |
| `stop_ticks` | `stop_ticks` |

**Algorithm parameters** — all other keys are passed directly to the algorithm as `algo_params`.

Values are coerced in order: `int` → `float` → `str`.

The human-readable `label` is built from the algorithm name plus all parameters (sim overrides and algo params combined):

```
nearest_car (direction_bonus=5.0, num_floors=60)
```

If no `--algo` flags are given, the tool defaults to running every algorithm in `REGISTRY` once with no extra parameters.

---

## `NullWriter` — suppressing log output

Each run uses a `NullWriter` in place of the normal `LogWriter`. It implements the same interface but discards all calls. This prevents the evaluator from writing position and passenger CSV files to disk for every algorithm run.

---

## `EvalResult` — collected metrics

| Field | Source |
|-------|--------|
| `label` | From `AlgoSpec.label` |
| `stats` | `compute_stats(passengers)` — wait and total time distributions |
| `utilization` | `compute_elevator_utilization(elevators, total_ticks)` — per-elevator active fraction |
| `simulation_duration` | `sim.total_ticks` |
| `total_floors_traveled` | Sum of `elevator.floors_traveled` across all elevators |

---

## Output table

The table is rendered side-by-side with one column per algorithm run. Column widths are sized to content and then clamped to the terminal width (detected via `shutil.get_terminal_size`, fallback 120). If the table is too wide, value columns are shrunk evenly; the metric label column is never truncated.

Metrics are grouped into four sections separated by horizontal dividers:

### Overview
| Metric | Description |
|--------|-------------|
| Passengers served | Total passengers who completed their journey |
| Simulation duration (ticks) | Tick at which the last passenger arrived |
| Total floors traveled | Sum of all floors moved across all elevators — a proxy for energy use |

### Wait time
Time from request submission to boarding. Reports avg, std, p95, min (with passenger ID), max (with passenger ID).

### Total time
Time from request submission to arrival at destination. Same statistics as wait time.

### Elevator utilization
Fraction of ticks each elevator spent in a non-idle state. Reports avg, min (with elevator ID), max (with elevator ID), and a per-elevator breakdown. If runs have different elevator counts, missing elevators display `—`.

---

## Example output

```
=== Algorithm Evaluation: mock_requests.csv ===
Config: floors=60 | elevators=4 | capacity=8 | stop_ticks=0

Metric                          │ nearest_car    │ round_robin
────────────────────────────────────────────────────────────────
Overview                        │                │
  Passengers served             │ 500            │ 500
  Simulation duration (ticks)   │ 312            │ 401
  Total floors traveled         │ 18432          │ 21905
────────────────────────────────────────────────────────────────
Wait time                       │                │
  avg                           │ 4.2            │ 11.7
  ...
```
