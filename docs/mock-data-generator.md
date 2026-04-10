# Mock Data Generator

## Summary

The mock data generator produces synthetic passenger request CSVs for testing and benchmarking. Each record contains a tick timestamp, a passenger ID, a source floor, and a destination floor. Records are sorted ascending by tick before being written.

---

## Output format

```csv
time,id,source,dest
0,passenger1,1,14
3,passenger2,7,1
...
```

| Column | Description |
|--------|-------------|
| `time` | Tick when the request is submitted |
| `id` | Passenger ID — `passenger1`, `passenger2`, ... assigned after sorting by time |
| `source` | Origin floor |
| `dest` | Destination floor (always different from `source`) |

Passenger IDs are assigned **after** sorting. `passenger1` is always the earliest request in time, regardless of generation order.

---

## Generation pipeline

```
for each record:
    1. Sample a tick from the chosen time distribution
    2. Sample a (source, dest) floor pair (with optional bias)

sort all records by tick

assign passenger IDs in sorted order

write to CSV
```

---

## Time distributions

The distribution controls when requests arrive across the simulation's time horizon `[0, num_ticks)`.

### `uniform`
Each request is placed at a tick drawn uniformly at random from `[0, num_ticks)`. Produces a flat, evenly spread traffic pattern.

### `gaussian`
Ticks are drawn from a normal distribution centred at the midpoint of the time horizon:

```
mean = num_ticks / 2
std  = num_ticks / 6
```

Values are clamped to `[0, num_ticks)`. Produces a single traffic peak at the middle of the day.

### `exponential`
Ticks are drawn from an exponential distribution with scale `num_ticks / 5`, then clamped:

```
scale = num_ticks / 5
tick  = Exponential(1 / scale)  clamped to [0, num_ticks)
```

Produces a front-loaded pattern where most requests arrive early and traffic decays over time.

### `workday`
Simulates a realistic office building day with five overlapping traffic components. Each record first selects a component by weighted random choice, then samples a tick and floor pair from that component:

| Component | Center | Std | Weight | Floor bias |
|-----------|--------|-----|--------|------------|
| AM rush | 10% of day | 4% | 30% | `up_from_1` — floor 1 → upper floor |
| Lunch (down) | 40% | 3% | 15% | `down_to_1` — upper floor → floor 1 |
| Lunch (up) | 47% | 3% | 10% | `up_from_1` |
| PM rush | 80% | 4% | 30% | `down_to_1` |
| Background | 50% | 30% | 15% | `none` — fully random |

Center and std are expressed as fractions of `num_ticks`, so the pattern scales to any time horizon. The background component has a wide standard deviation (30%) to spread low-level traffic across the whole day.

---

## Floor pair sampling

Each distribution (except `workday`) samples floor pairs independently of the tick using `_sample_floor_pair`. The `workday` distribution couples tick and floor sampling — the floor bias is determined by whichever traffic component was selected.

| Bias | Source | Destination |
|------|--------|-------------|
| `up_from_1` | Always floor 1 | Random from `[2, num_floors]` |
| `down_to_1` | Random from `[2, num_floors]` | Always floor 1 |
| `inter_floor` | Random from `[2, num_floors]` | Random, ≠ source and ≠ floor 1 |
| `none` | Random from `[1, num_floors]` | Random, ≠ source |

The destination is always guaranteed to differ from the source.

---

## Reproducibility

Passing `--seed` sets `random.seed()` before any sampling occurs. The same seed, distribution, and parameter combination always produces identical output.

---

## Programmatic usage

```python
from elevator_sim.mock_data.generate import generate_records, write_csv

records = generate_records(
    num_records=500,
    num_floors=60,
    num_ticks=2000,
    distribution="workday",
)
write_csv(records, "input/requests.csv")
```

`generate_records` returns a list of `(time, id, source, dest)` tuples sorted by time. `write_csv` creates any missing parent directories before writing.
