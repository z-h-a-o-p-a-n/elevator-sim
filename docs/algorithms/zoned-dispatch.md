# Zoned Dispatch Algorithm

## Summary

The building's floors are divided into **named zones**, each served by a dedicated subset of elevators. When a passenger requests a ride, their **origin floor** determines which zone — and therefore which subset of elevators — is eligible to serve them. Within that eligible subset, a configurable **sub-algorithm** picks the specific elevator. 

A zone is contiguous set of floors. A zone has 1 or more floors. Zones can serve overlapping floors (i.e. zone 1 serves floors 1-10, zone 2 serves floors 5-15, ...).

Cross-zone requests (origin in one zone, destination in another) are handled entirely by the origin zone's elevators; no transfer or handoff occurs.

---

## Zone assignment

A zone is defined by an inclusive floor range `[floor_min, floor_max]` and a set of elevator IDs:

```json
"zones": [
  {"floors": [1,  50], "elevator_ids": [1, 2]},
  {"floors": [51, 100], "elevator_ids": [3, 4]}
]
```

At assignment time, the algorithm finds the zone whose range contains `passenger.destination`. If no zone contains the destination floor, it's an unexpected error and the simulation will end.

When zones overlap and multiple zones contain the destination floor, the algorithm picks the zone that **also contains the origin floor**. If no overlapping zone contains the origin, the first matching zone is used.

---

## Within-zone selection (sub-algorithm)

Once the eligible elevator pool is determined, one of three sub-algorithms selects the specific elevator:

| `sub_algorithm` value | Behaviour |
|----------------------|-----------|
| `"nearest_car"` (default) | Delegates to `NearestCarAlgorithm.get_elevator` — picks the elevator with the lowest travel-cost score. See [nearest-car.md](nearest-car.md) for scoring details. |
| `"round_robin"` | Cycles through the zone's elevators in order using a per-zone counter. Each zone maintains its own independent counter. |
| `"random"` | Picks uniformly at random from the eligible elevators. |

---

## Capacity filtering

Before the sub-algorithm runs, elevators whose `len(assigned) + len(passengers) >= capacity` are removed from the candidate pool. If the filtered pool is empty, `None` is returned and the simulation retries the assignment on the next tick.

---

## Cross-zone trips

A passenger whose origin and destination span two different non-overlapping zones is assigned to the **origin zone's** elevators. The elevator carries the passenger directly from their origin to their destination — crossing zone boundaries mid-ride is allowed. No transfer at a boundary floor takes place.

When origin and destination fall in an **overlapping** region shared by multiple zones, the algorithm prefers the zone that covers both floors, keeping the trip within a single zone's elevator pool.

This is a deliberate simplification. For a model that enforces zone boundaries and handles transfers, see the Sky Lobby algorithm.

---

## Configuration

```json
{
  "sub_algorithm": "nearest_car",
  "zones": [
    {"floors": [1,  50], "elevator_ids": [1, 2]},
    {"floors": [51, 100], "elevator_ids": [3, 4]}
  ]
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `sub_algorithm` | `string` | `"nearest_car"` | Selection strategy within a zone: `"nearest_car"`, `"round_robin"`, or `"random"` |
| `zones` | `array` | `[]` | Ordered list of zone definitions. Each entry requires `"floors": [min, max]` and `"elevator_ids": [id, ...]` |

---

## Limitations

- **Destination-primary routing.** Zone membership is determined by the destination floor. In overlapping regions, the zone covering both origin and destination is preferred; otherwise the first destination-matching zone wins.
- **No transfer logic.** Passengers ride a single elevator end-to-end regardless of zone boundaries.
