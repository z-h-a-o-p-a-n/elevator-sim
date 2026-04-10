# elevator-sim

A simplified simulation of an intelligent elevator system using destination dispatch scheduling.

## Setup

```bash
uv sync --extra dev
```

## Run

```bash
# Basic usage (CSV file required)
uv run elevator-sim sample_requests.csv --floors 60

# Full options
uv run elevator-sim requests.csv \
  --floors 60 \
  --elevators 4 \
  --capacity 8 \
  --stop-ticks 0 \
  --algorithm nearest_car \
  --output-dir output/ \
  --run-id my_run
```

### Input CSV format

```csv
time,id,source,dest
0,passenger1,1,51
0,passenger2,1,37
10,passenger3,28,1
```

| Column | Description |
|---|---|
| `time` | Tick when the request is submitted |
| `id` | Unique passenger identifier |
| `source` | Origin floor |
| `dest` | Destination floor |

### Programmatic usage

```python
from elevator_sim.config import SimConfig
from elevator_sim.io.reader import parse_csv, parse_records
from elevator_sim.main import run

# From CSV
requests = parse_csv("requests.csv")
run(requests, config=SimConfig(num_floors=60, num_elevators=4))

# From list of dicts
requests = parse_records([
    {"time": 0, "id": "p1", "source": 1, "dest": 10},
])
run(requests)
```

## Output

Two CSV files are written to `output/` (or `--output-dir`) per run:

**`<run_id>_positions.csv`** — elevator positions at every tick:
```
time,E1,E2
0,1,1
1,2,1
...
```

**`<run_id>_passengers.csv`** — per-passenger timing:
```
passengerId,source,dest,start_time,board_elevator_time,exit_time
passenger1,1,51,0,0,50
...
```

Statistics (min/max/avg/p95 for wait time and total time) are printed to stdout.

## Generating Mock Data

Use the mock data generator to create synthetic request CSVs for testing.

```bash
# Basic usage (uniform distribution, 100 records, 10 floors, 1000 ticks)
uv run python -m elevator_sim.mock_data.generate

# Full options
uv run python -m elevator_sim.mock_data.generate \
  --num-records 500 \
  --num-floors 60 \
  --num-ticks 2000 \
  --distribution workday \
  --output input/my_requests.csv \
  --seed 42
```

### Options

| Flag | Short | Description | Default |
|---|---|---|---|
| `--num-records` | `-n` | Number of passenger requests to generate | `100` |
| `--num-floors` | `-f` | Number of floors in the building | `10` |
| `--num-ticks` | `-t` | Total simulation ticks (time horizon) | `1000` |
| `--distribution` | `-d` | Time distribution (see below) | `uniform` |
| `--output` | `-o` | Output CSV file path | `output/mock_requests.csv` |
| `--seed` | | Random seed for reproducibility | none |

### Distributions

| Distribution | Behavior |
|---|---|
| `uniform` | Requests spread evenly across all ticks |
| `gaussian` | Requests clustered around the midpoint (σ = num_ticks / 6) |
| `exponential` | Front-loaded — most requests early, decaying over time |
| `workday` | Realistic office building pattern (see below) |

The `workday` distribution simulates a typical office building with three traffic peaks:

- **AM rush** (~10% into the day, 30% of requests) — passengers travel from floor 1 to upper floors
- **Lunch (down)** (~40%, 15%) — passengers travel from upper floors to floor 1
- **Lunch (up)** (~47%, 10%) — passengers return from floor 1 to upper floors
- **PM rush** (~80%, 30%) — passengers travel from upper floors to floor 1
- **Background** (throughout the day, 15%) — random requests between any floors

## Test

```bash
make test
```

## Algorithms

| Name | Description |
|---|---|
| `nearest_car` | Assigns passenger to the elevator with the lowest travel cost to their origin, factoring in current direction |
| `round_robin` | Assigns the nth passenger to elevator n mod m (cycling through all elevators in order); skips assignment if the selected elevator is at capacity |

New algorithms can be added by subclassing `BaseAlgorithm` in `src/elevator_sim/algorithms/` and registering in `REGISTRY`.

## Assumptions & Trade-offs

- **Time model**: 1 tick = 1 floor of travel. Boarding/exiting is instantaneous by default (`--stop-ticks 0`).
- **Destination dispatch**: Passengers declare origin and destination upfront; assignment is immediate and final.
- **No peeking**: The simulation only sees requests at or before the current tick.
- **All elevators start at floor 1**.
- **Boarding/exiting on same tick**: An elevator can drop off and pick up passengers at the same floor in one tick.
- **Capacity**: If an elevator is full, assigned passengers at that floor wait until the next visit.

## What I'd Improve With More Time

- Zone-based and round-robin dispatch algorithms
- Express elevator support (skip floors)
- Visualization (floor-by-floor animation or Gantt chart)
- Benchmark suite to compare algorithms across traffic patterns
