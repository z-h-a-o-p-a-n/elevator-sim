# elevator-sim

A simplified simulation of an intelligent elevator system using destination dispatch scheduling.

## How to Run

```bash
# Install dependencies
uv sync --extra dev

# Basic usage (CSV file required)
uv run elevator-sim sample_requests.csv --floors 60

# Full options
uv run elevator-sim requests.csv \
  --floors 60 \
  --elevators 4 \
  --capacity 8 \
  --stop-ticks 0 \
  --algorithm nearest_car \
  --algo-config '{"direction_bonus": 5.0}' \
  --output-dir output/ \
  --run-id my_run \
  --log-level INFO

# Zone-based dispatch with custom zones
uv run elevator-sim requests.csv \
  --floors 100 \
  --elevators 6 \
  --algorithm zoned_dispatch \
  --algo-config '{
    "sub_algorithm": "nearest_car",
    "zones": [
      {"floors": [1, 33],   "elevator_ids": [1, 2]},
      {"floors": [34, 66],  "elevator_ids": [3, 4]},
      {"floors": [67, 100], "elevator_ids": [5, 6]}
    ]
  }'
```

## Time Spent

| Task | Hours |
|---|---|
| Requirement analysis | 1.0 |
| Simulation loop proof-of-concept | 3.0 |
| Nearest-car algorithm | 2.0 |
| Round-robin algorithm | 0.5 |
| Zone-dispatch algorithm | 2.0 |
| Mock data generator | 1.5 |
| Algorithm Evaluator | 1.5 |
| Documentation (with Claude) | 0.5 |
| **Total** | **12.0** |

## Assumptions & Trade-offs

- **Time model**: 1 tick = 1 floor of travel. Boarding/exiting is instantaneous by default (`--stop-ticks 0`).
- **Destination dispatch**: Passengers declare origin and destination upfront; assignment is immediate and final.
- **No peeking**: The simulation only sees requests at or before the current tick.
- **All elevators start at floor 1**.
- **Boarding/exiting on same tick**: An elevator can drop off and pick up passengers at the same floor in one tick.
- **Capacity**: If an elevator is full, assigned passengers at that floor wait until the next visit.
- **Sky-lobby**: Two elevator cars can share the SAME elevator shaft. The upper one serves one of the top zones, the lower one serves the lower local floors.


## What I'd Improve With More Time

- Complete Sky-lobby implementation
- Express elevator support (skip floors)
- Produce the necessary artifacts (full time-series records, decision logs, etc) for Supervised and Reinforcement trainings
- Visualization (floor-by-floor animation or Gantt chart)
- Benchmark suite to compare algorithms across traffic patterns

## Documentation

- [Usage guide](USAGE.md) — input format, output format, mock data generator, algorithm evaluator, programmatic API
- [Requirements](requirements.md) — Original requirements
- [Simulation loop design](docs/simulation-loop.md)
- [Mock data generator](docs/mock-data-generator.md)
- [Algorithm evaluator](docs/evaluate-algorithms.md)
- [Nearest-car algorithm](docs/algorithms/nearest-car.md)
- [Round-robin algorithm](docs/algorithms/round-robin.md)
- [Zoned dispatch algorithm](docs/algorithms/zone-dispatch.md)
