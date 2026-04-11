# Round-Robin Algorithm

## Summary

Passengers are assigned to elevators in strict rotation. The nth passenger is sent to elevator at position `n mod m` in the eligible elevator list, where `m` is the number of elevators. The counter increments with every assignment attempt.

---

## Behavior

A single global counter starts at 0 and never resets. On each call to `get_elevator`:

1. Compute `index = counter mod m` where `m = len(elevators)`.
2. Select `elevators[index]`.
3. Increment the counter.
4. Retuurn the selected elevator.

---

## Limitations

- **No travel-cost awareness.** The algorithm ignores elevator positions, directions, and load. A passenger may be assigned to an elevator at the opposite end of the building when an idle elevator is one floor away.
- **Counter never resets.** The rotation is global across the entire simulation run. There is no per-tick or per-group reset.

Round-robin is best used as a baseline or as a sub-algorithm inside `ZonedDispatchAlgorithm`, where the elevator pool is already constrained to a relevant subset.

---

## Usage as a sub-algorithm

When used inside `ZonedDispatchAlgorithm` with `"sub_algorithm": "round_robin"`, each zone gets its **own independent** `RoundRobinAlgorithm` instance with its own counter. Rotation within one zone does not affect the counter of any other zone.

---

## Configuration

The round-robin algorithm has no configuration keys. When used standalone:

```json
{}
```

When used as a sub-algorithm inside zoned dispatch:

```json
{
  "sub_algorithm": "round_robin",
  "zones": [...]
}
```
