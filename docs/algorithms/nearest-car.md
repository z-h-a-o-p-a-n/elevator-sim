# Nearest-Car Algorithm

## Summary

Each new passenger is assigned to the elevator with the **lowest cost score**. The score estimates how many floors the elevator must travel before it can pick up the passenger, with adjustments for direction alignment and committed overshoot. Lower score is better. Ties are broken by current load. If the current loads are equal, 
the elevator with lower number wins.

---

## Score formula

```
score = (distance + direction_bonus + 2 × overshoot, load)
```

The result is a two-element tuple. Python's `min` compares tuples lexicographically, so `load` only acts as a tie-breaker when two elevators produce the same primary score.

---

## Components

### 1. Distance

```
distance = |effective_position − passenger.origin|
```

`effective_position` is normally the elevator's `current_floor`, but is adjusted when the elevator is **moving away** from the passenger's origin. In that case the elevator cannot turn around until it reaches its furthest committed destination in the current direction:

| Elevator direction | Origin relative to elevator | Effective position |
|--------------------|----------------------------|--------------------|
| UP | above (toward origin) | `current_floor` |
| UP | below (away from origin) | `max(destinations above current_floor)` |
| DOWN | below (toward origin) | `current_floor` |
| DOWN | above (away from origin) | `min(destinations below current_floor)` |
| IDLE | any | `current_floor` |

This ensures the distance reflects the floors the elevator *actually needs to travel* before it can begin heading toward the pickup.

### 2. Direction bonus (optional)

```
direction_bonus = −direction_bonus_config   (when heading toward origin)
                  0                          (otherwise)
```

When enabled (`direction_bonus > 0` in config), a bonus is subtracted from the score for elevators already travelling toward the passenger's origin floor. This favors elevators that can pick up the passenger en route without reversing.

The bonus is disabled by default (`direction_bonus = 0`).

### 3. Overshoot penalty

```
overshoot penalty = 2 × overshoot_floors
```

Overshoot is the number of extra floors the elevator will travel *past* the origin before it can stop, due to already-committed destinations beyond the pickup:

| Elevator direction | Origin relative to elevator | Overshoot |
|--------------------|-----------------------------|-----------|
| UP | above current floor | floors committed beyond origin: `max(destinations > origin) − origin` |
| DOWN | below current floor | floors committed beyond origin: `origin − min(destinations < origin)` |
| any | moving away from origin | 0 (already accounted for in effective position) |
| IDLE | any | 0 |

The `2×` multiplier reflects that overshoot costs two trips per extra floor — the elevator travels there and then back.

When two equidistant elevators are compared, the one with fewer committed stops beyond the origin will pick up the passenger sooner and cause less unnecessary riding for current passengers.

### 4. Tie-break: load

```
load = len(passengers) + len(assigned)
```

When two elevators produce the same primary score, the one with fewer committed passengers (riding + assigned but not yet boarded) is preferred. This spreads load across the fleet.

---

## Worked example

Building: 10 floors, 2 elevators, `direction_bonus = 0`.

```
Elevator 1: floor 3, direction UP, destinations = {5, 8}
Elevator 2: floor 7, direction DOWN, destinations = {4}

New passenger: origin = 6, destination = 9
```

**Elevator 1:**
- Heading UP, origin (6) is above current floor (3) → effective position = 3
- Distance = |3 − 6| = 3
- Overshoot: destinations above origin (6) → {8}, overshoot = 8 − 6 = 2
- Score = (3 + 0 + 2×2, load) = **(7, 1)**

**Elevator 2:**
- Heading DOWN, origin (6) is above current floor (7)? No — 6 < 7, origin is *below*.
- Elevator is moving away from origin → effective position = min(destinations below 7) = 4
- Distance = |4 − 6| = 2
- Overshoot: elevator is moving away, not toward origin → 0
- Score = (2 + 0 + 0, load) = **(2, 1)**

Elevator 2 wins despite being further away, because Elevator 1 must first travel to floor 8 before it can come back down to 6.

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
