# Nearest-Car Algorithm

## Summary

Each new passenger is assigned to the elevator with the **lowest cost score**. The score estimates the passenger's total journey time: time spent waiting for the elevator to arrive plus time spent travelling to the destination. Lower score is better. Ties are broken by current load.

---

## Score formula

The algorithm uses one of two scoring paths depending on whether the elevator can pick up the passenger on its current run.

**Normal path** — elevator has capacity at the origin floor:
```
score = (wait + direct_travel + direction_bonus + 2 × detour, load)
```

**Post-trip path** — elevator is full at the origin floor, must finish its current run first:
```
score = (wait + direct_travel, load)
```

The result is a two-element tuple. Python's `min` compares tuples lexicographically, so `load` only acts as a tie-breaker when two elevators produce the same primary score.

---

## Components

### 1. Projected load at origin

Before scoring, the algorithm estimates how many passengers will be aboard when the elevator reaches the origin floor. For an elevator already heading toward the origin, passengers who exit at or above (for a DOWN elevator) or at or below (for an UP elevator) the origin floor will have already disembarked, freeing seats.

If the projected load is below capacity, the **normal path** is used. If the elevator will be full when it arrives, the **post-trip path** is used.

### 2. Wait

How long until the elevator can accept the new passenger.

**Normal path** — elevator is already heading toward the origin:
```
wait = |effective_position − origin|
```

`effective_position` is the elevator's current floor when heading toward the origin, or its furthest committed destination in the current direction when heading away:

| Elevator direction | Origin relative to elevator | Effective position |
|--------------------|----------------------------|--------------------|
| UP | above or at current floor | `current_floor` |
| UP | below current floor | `max(destinations ≥ current_floor)` |
| DOWN | below or at current floor | `current_floor` |
| DOWN | above current floor | `min(destinations ≤ current_floor)` |
| IDLE | any | `current_floor` |

**Post-trip path** — elevator is full and must complete its current run:
```
post_trip_position = furthest committed destination in current direction
wait = |current_floor − post_trip_position| + |post_trip_position − origin|
```

After the run the elevator is idle, so it travels directly from the post-trip position to the origin.

### 3. Direct travel

```
direct_travel = |origin − destination|
```

The minimum floors the passenger must travel regardless of which elevator is assigned. Constant across all elevators for a given passenger, but included so the score represents the true estimated total time.

### 4. Detour penalty (normal path only)

```
detour penalty = 2 × detour_floors
```

When the elevator picks up the passenger but still has committed stops beyond the origin that are **opposite** to the passenger's destination, the passenger must ride those extra floors before the elevator can reverse. Each detour floor costs 2 ticks — one going the wrong way, one to recover that distance heading toward the destination.

| Elevator direction | Passenger direction | Detour |
|--------------------|---------------------|--------|
| UP | UP | 0 — same direction, no reversal needed |
| UP | DOWN | `max(destinations > origin) − origin` |
| DOWN | DOWN | 0 — same direction, no reversal needed |
| DOWN | UP | `origin − min(destinations < origin)` |
| any | any (post-trip or moving away) | 0 — already captured in wait |

### 5. Direction bonus (optional)

```
direction_bonus = −direction_bonus_config   (when heading toward origin)
                  0                          (otherwise)
```

When enabled, a bonus is subtracted from the score for elevators already travelling toward the passenger's origin. Disabled by default (`direction_bonus = 0`).

### 6. Tie-break: load

```
load = len(passengers) + len(assigned)
```

When two elevators produce the same primary score, the one with fewer committed passengers is preferred to spread load across the fleet.

---

## Examples

Building: 10 floors, 2 elevators, `direction_bonus = 0`.

### Example 1 — Ideal en-route pickup (same direction)

```
Elevator 1: floor 3, UP, destinations = {8}, load = 1, capacity = 2
Elevator 2: floor 7, DOWN, destinations = {6, 4}, load = 2, capacity = 2
  passengers: one going to floor 6, one going to floor 4

New passenger: origin = 6, destination = 1 (going DOWN)
```

**Projected load at origin 6:**
- Elevator 1 (UP, origin 6 ≥ floor 3): exits = 0 (passenger going to 8, above 6) → projected load = 1 → normal path
- Elevator 2 (DOWN, origin 6 ≤ floor 7): exits = 1 (passenger going to 6) → projected load = 1 → normal path

**Scores** (`direct_travel = |6−1| = 5`):

| | Elevator 1 | Elevator 2 |
|---|---|---|
| effective position | 3 | 7 |
| wait | \|3−6\| = 3 | \|7−6\| = 1 |
| detour | UP elevator, DOWN passenger: `max({8}) − 6 = 2` | DOWN elevator, DOWN passenger: **0** (same direction) |
| score | 3 + 5 + 2×2 = **12** | 1 + 5 + 0 = **6** |

**Elevator 2 is assigned.** It is one floor away, travelling the same direction as the new passenger, and the floor-6 passenger exits right as the new passenger boards. The elevator continues directly to floor 1 with no detour.

---

### Example 2 — En-route pickup with direction mismatch (detour)

```
Elevator 1: floor 3, UP, destinations = {8}, load = 1, capacity = 2
Elevator 2: floor 9, IDLE, destinations = {}, load = 0, capacity = 2

New passenger: origin = 6, destination = 1 (going DOWN)
```

**Projected load at origin 6:**
- Elevator 1 (UP): projected load = 1 → normal path
- Elevator 2 (IDLE): projected load = 0 → normal path

**Scores** (`direct_travel = 5`):

| | Elevator 1 | Elevator 2 |
|---|---|---|
| wait | \|3−6\| = 3 | \|9−6\| = 3 |
| detour | UP elevator, DOWN passenger: `max({8}) − 6 = 2` | IDLE, no committed stops: **0** |
| score | 3 + 5 + 2×2 = **12** | 3 + 5 + 0 = **8** |

**Elevator 2 is assigned.** Although both elevators are equidistant from floor 6, elevator 1 carries the passenger one floor up to floor 8 before reversing down to floor 1 — a 4-tick penalty. The idle elevator 2 picks up at floor 6 and travels directly to floor 1.

---

### Example 3 — Full elevator triggers post-trip scoring

```
Elevator 1: floor 3, UP, destinations = {8}, load = 2, capacity = 2
  (both passengers going to floor 8)
Elevator 2: floor 7, DOWN, destinations = {6, 4}, load = 2, capacity = 2
  (one going to floor 6, one going to floor 4)

New passenger: origin = 6, destination = 1 (going DOWN)
```

**Projected load at origin 6:**
- Elevator 1 (UP): exits = 0 (both going to 8, above 6) → projected load = 2 → **post-trip path**
- Elevator 2 (DOWN): exits = 1 (passenger going to 6) → projected load = 1 → normal path

**Scores** (`direct_travel = 5`):

| | Elevator 1 (post-trip) | Elevator 2 (normal) |
|---|---|---|
| post-trip position | `max({8})` = 8 | — |
| wait | \|3−8\| + \|8−6\| = 5 + 2 = **7** | \|7−6\| = **1** |
| detour | 0 (idle after run) | DOWN + DOWN: **0** |
| score | 7 + 5 = **12** | 1 + 5 + 0 = **6** |

**Elevator 2 is assigned.** Elevator 1 is full with no exits before floor 6 — it must travel 5 floors up to floor 8, drop off both passengers, then come back 2 floors to floor 6 before it can pick up. Elevator 2 arrives in 1 tick with a free seat.

---

## Configuration

```json
{
  "direction_bonus": 0.0
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `direction_bonus` | `float` | `0.0` | Subtracted from score when elevator is heading toward the origin. `0` disables the bonus. |

---

## Usage as a sub-algorithm

`NearestCarAlgorithm` can be re-used by other algorithms (e.g. `ZonedDispatchAlgorithm`) without duplicating the selection logic.
