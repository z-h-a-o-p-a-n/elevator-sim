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

## Test

```bash
make test
```

## Algorithms

| Name | Description |
|---|---|
| `nearest_car` | Assigns passenger to the elevator with the lowest travel cost to their origin, factoring in current direction |

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
