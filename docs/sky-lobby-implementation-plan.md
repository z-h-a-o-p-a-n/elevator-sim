# Sky Lobby Algorithm — Implementation Plan

## Overview

A sky-lobby dispatch algorithm where:
- A set of **local elevators** serve floors 1–N and carry passengers to/from the sky lobby
- **Upper zone elevators** serve the sky lobby floor and above, partitioned into zones
- Passengers whose trip crosses zone boundaries are automatically **split into two legs** with a transfer at the sky lobby
- Some shafts are **shared** by a lower car and an upper car that cannot occupy the same floor simultaneously

The input CSV continues to specify each passenger's **true final destination**; the algorithm handles all routing and transfer logic internally.

---

## Files to Create

### `src/elevator_sim/algorithms/sky_lobby.py`

The main new algorithm. Inherits from `BaseAlgorithm` and overrides `assign`, `handle_arrivals`, and `configure_elevators`.

#### `assign(passenger, elevators)`

Classifies each trip by origin and destination zone, sets transfer fields when needed, and delegates to the appropriate elevator pool using the configured sub-algorithm.

| Origin | Destination | Transfer? | Assigned elevator pool |
|--------|-------------|-----------|------------------------|
| Local floor | Local floor | No | Local elevators |
| Local floor | Sky lobby | No | Local elevators |
| Local floor | Upper zone | Yes — leg 1 to sky lobby | Local elevators |
| Sky lobby | Upper zone | No | Matching zone elevators |
| Sky lobby | Local floor | No | Local elevators |
| Upper zone | Same zone | No | Same zone elevators |
| Upper zone | Different zone | Yes — leg 1 to sky lobby | Origin zone elevators |
| Upper zone | Sky lobby | No | Origin zone elevators |
| Upper zone | Local floor | Yes — leg 1 to sky lobby | Origin zone elevators |

When a transfer is required:
```
passenger.transfer_floor    = sky_lobby_floor
passenger.final_destination = passenger.destination   # true destination saved
passenger.destination       = sky_lobby_floor         # leg 1 destination
```

#### `handle_arrivals(arrived, tick) -> list[Passenger]`

Called by the simulation after each elevator's `exit()`. Detects passengers whose `transfer_floor` is set (i.e., they just reached the sky lobby and need a second leg):

```
p.transfer_time     = tick
p.arrive_time       = None          # not truly arrived yet
p.origin            = p.transfer_floor
p.destination       = p.final_destination
p.transfer_floor    = None
p.final_destination = None
```

Returns the list of transferring passengers. The simulation re-queues them in `pending_transfers`.

#### `configure_elevators(elevators, config)`

Reads the `shafts` config entry. For each shared shaft pair:
- **Lower car**: `floor_min = 1`, `floor_max = sky_lobby_floor`, `current_floor = 1`
- **Upper car**: `floor_min = sky_lobby_floor`, `floor_max = zone_max`, `current_floor = sky_lobby_floor`

Single-car elevators are left at defaults (`floor_min = 1`, `floor_max = num_floors`, `current_floor = 1`).

Also exposes `shaft_pairs: dict[int, int]` (lower_id → upper_id) for the simulation to use during conflict resolution.

---

## Files to Modify

### `src/elevator_sim/models/passenger.py`

Add four new fields:

| Field | Type | Purpose |
|-------|------|---------|
| `transfer_floor` | `int \| None` | Sky lobby floor; signals leg 1 is in progress |
| `final_destination` | `int \| None` | True destination, stored while `destination` is redirected to sky lobby |
| `transfer_time` | `int \| None` | Tick when passenger arrived at sky lobby |
| `transfer_board_time` | `int \| None` | Tick when passenger boarded the leg-2 elevator |

Add property:
```python
@property
def sky_lobby_wait_time(self) -> int | None:
    if self.transfer_board_time is None or self.transfer_time is None:
        return None
    return self.transfer_board_time - self.transfer_time
```

---

### `src/elevator_sim/models/elevator.py`

**Add floor boundary fields:**
```python
floor_min: int = 1
floor_max: int = 100   # overridden by configure_elevators for shared-shaft cars
```

**Modify `board()`** — preserve leg-1 `board_time` for transfer passengers:
```python
if p.board_time is None:
    p.board_time = tick
else:
    p.transfer_board_time = tick
```

---

### `src/elevator_sim/algorithms/base.py`

Add two new optional methods with no-op defaults:

```python
def handle_arrivals(self, arrived: list[Passenger], tick: int) -> list[Passenger]:
    """Detect and reset transfer passengers. Returns passengers that need re-queuing."""
    return []

def configure_elevators(self, elevators: list[Elevator], config: SimConfig) -> None:
    """Set per-elevator floor bounds and starting positions."""
```

---

### `src/elevator_sim/simulation.py`

#### 1. Elevator creation and configuration
After creating elevators, call the algorithm's configure hook and store shaft pairs:
```python
self.elevators = [Elevator(id=i+1, capacity=config.elevator_capacity) for i in range(config.num_elevators)]
self.algorithm.configure_elevators(self.elevators, config)
self._elevator_map = {e.id: e for e in self.elevators}
self._shaft_pairs = getattr(self.algorithm, 'shaft_pairs', {})  # lower_id -> upper_id
```

#### 2. Pending transfer queue
```python
self.pending_transfers: list[Passenger] = []
```

#### 3. Restructured per-tick loop

The existing single-pass loop (exit → board → set_direction → move per elevator) is split into **three passes** so shaft conflicts can be resolved after all directions are known but before any car moves.

**Top of tick — retry pending transfers:**
```python
still_pending = []
for p in self.pending_transfers:
    elevator = self.algorithm.assign(p, self.elevators)
    if elevator is not None:
        elevator.assign(p)
    else:
        still_pending.append(p)
self.pending_transfers = still_pending
```

**Pass 1 — exit, board, stop penalty:**
```python
skip_move: set[int] = set()

for elevator in self.elevators:
    if elevator.state != ElevatorState.IDLE or elevator.destinations:
        elevator.active_ticks += 1

    if elevator.stop_ticks_remaining > 0:
        elevator.stop_ticks_remaining -= 1
        skip_move.add(elevator.id)
        continue

    arrived = elevator.exit(tick)
    boarded = elevator.board(tick)

    transferring = self.algorithm.handle_arrivals(arrived, tick)
    for p in transferring:
        self.pending_transfers.append(p)
    for p in arrived:
        if p not in transferring:
            writer.log_passenger(p)

    if (arrived or boarded) and self.config.stop_ticks > 0:
        elevator.stop_ticks_remaining = self.config.stop_ticks
        elevator.state = ElevatorState.STOPPED
        skip_move.add(elevator.id)
```

**Pass 2 — set direction:**
```python
for elevator in self.elevators:
    if elevator.id not in skip_move:
        self._set_direction(elevator)
```

**Pass 3 — resolve shaft conflicts, then move:**
```python
self._resolve_shaft_conflicts(skip_move)

for elevator in self.elevators:
    if elevator.id not in skip_move:
        elevator.move()
```

#### 4. `_set_direction` — use per-elevator floor bounds
Replace hardcoded `1` and `num_floors` boundary guards with `elevator.floor_min` and `elevator.floor_max`.

#### 5. `_resolve_shaft_conflicts(skip_move)`

For each `(lower_id, upper_id)` pair, compute each car's intended next floor based on its current direction, then check for collision:

```
lower_next = lower.current_floor + direction_delta(lower)
upper_next = upper.current_floor + direction_delta(upper)
```

If `lower_next == upper_next`:

| Situation | Resolution |
|-----------|-----------|
| Lower going UP, upper is free to move | Force-move upper UP by 1 (direct `current_floor += 1`, `floors_traveled += 1`, `state = MOVING`); add upper to `skip_move` to prevent a second move |
| Lower going UP, upper is stopped (can't move) | Halt lower: `direction = IDLE`, add lower to `skip_move` |
| Upper going DOWN, lower is free to move | Force-move lower DOWN by 1; add lower to `skip_move` |
| Upper going DOWN, lower is stopped | Halt upper: `direction = IDLE`, add upper to `skip_move` |
| Both approaching (lower UP + upper DOWN) | Treat as "lower going UP" case — nudge upper UP |

---

### `src/elevator_sim/stats.py`

Add `TransferStats` dataclass and corresponding compute/print functions:

```python
@dataclass
class TransferStats:
    transfer_count: int         # passengers who transferred
    avg_sky_lobby_wait: float   # avg transfer_board_time - transfer_time
    p95_sky_lobby_wait: float
    max_sky_lobby_wait: int
```

`compute_transfer_stats(passengers)` filters for passengers where `transfer_time is not None`.
`print_transfer_stats(stats)` appends a new section to the existing output.

---

### `src/elevator_sim/config.py`

Add `sky_lobby` to `SimConfig.__getitem__`:

```python
case "sky_lobby":
    return {
        "sky_lobby_floor": 6,
        "local_floors": [1, 5],
        "sub_algorithm": "nearest_car",
        "shafts": [
            {"lower_elevator_id": 1, "upper_elevator_id": 3},
            {"lower_elevator_id": 2, "upper_elevator_id": 4},
        ],
        "zones": [
            {"floors": [7, 50],   "elevator_ids": [3, 4]},
            {"floors": [51, 100], "elevator_ids": [5, 6]},
        ],
    }
```

---

### `src/elevator_sim/algorithms/__init__.py`

Register the new algorithm:
```python
from .sky_lobby import SkyLobbyAlgorithm

REGISTRY["sky_lobby"] = SkyLobbyAlgorithm

# add to get_algorithm dispatch
if name == "sky_lobby":
    return SkyLobbyAlgorithm(config, algo_config)
```

---

## Key Design Decisions

### Why split the loop into three passes?
Shaft conflict resolution requires knowing *all* elevators' intended directions before any car moves. The original single-pass loop (direction → move per elevator) would process some cars before others, making conflict detection order-dependent and unpredictable.

### Why `pending_transfers` in the simulation?
Transfer passengers arrive at the sky lobby without a guaranteed upper-zone elevator available (all may be at capacity). This mirrors how initial requests are retried — the simulation already has a retry loop structure for this case. The end condition (`all(p.arrived for p in passengers)`) naturally covers pending transfers because transfer passengers have `arrive_time = None` until their final destination.

### Why `configure_elevators` on the algorithm?
Floor boundaries and starting positions are determined by the algorithm config (shaft pairs, zone ranges), not by `SimConfig`. Keeping this on the algorithm avoids coupling `SimConfig` to algorithm-specific concepts while still letting the simulation set up elevators correctly before the first tick.

### Why `board_time` / `transfer_board_time` split in `Elevator.board()`?
`board_time` must reflect the *first* boarding (leg 1) to preserve correct `wait_time = board_time - request_time`. A new `transfer_board_time` field captures when the passenger boarded for leg 2, enabling `sky_lobby_wait_time = transfer_board_time - transfer_time` without any ambiguity.
