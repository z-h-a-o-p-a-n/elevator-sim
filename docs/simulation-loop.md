# Simulation Loop Design

## Unit of time

One **tick** equals one floor of travel. An elevator that is moving advances exactly one floor per tick. All timing — wait times, total journey times, stop penalties — is expressed in ticks.

---

## Inputs

| Input | Description |
|-------|-------------|
| `requests: list[Request]` | Passenger requests, each with a timestamp, ID, source floor, and destination floor |
| `algorithm: BaseAlgorithm` | Dispatch algorithm that assigns passengers to elevators |
| `config: SimConfig` | Number of floors, number of elevators, elevator capacity, stop-tick penalty |

Requests are sorted ascending by timestamp at the start of the run. The simulation _does not_ peek ahead — a request is only visible to the algorithm on or after its timestamp tick.

---

## Pseudo Code

```
tick 0, 1, 2, ...
│
├─ 1. Fetch the requests for the current tick
├─ 2. Log elevator positions
├─ 3. For each elevator:
│   ├─ a. Tracking the total time this elevator had traveled
│   ├─ b. (Optional) Wait for passengers to exit and board at the current floor
│   ├─ c. Exit passengers at current floor
│   ├─ d. Board assigned passengers at current floor
│   ├─ e. Log arrived passengers
│   ├─ f. (Optional) Apply stop penalty (if boarding or exiting occurred)
│   ├─ g. Set elevator car direction
│   └─ h. Move the elevator up or down if not idle
│
└─ 4. End condition check (all passengers have arrived)
```

---

## Step 1 — Release requests

At the start of each tick, all requests whose timestamp = current tick are submitted to the algorithm. The loop processes them in timestamp order.

Each request is converted to a `Passenger` object and passed to `algorithm.assign(passenger, elevators)`. If the algorithm returns an elevator, the passenger is added to that elevator's `assigned` queue and the request is consumed.

---

## Step 2 — Log elevator positions

Each elevator's current floor is written to the position log before any movement occurs. This captures the state at the *start* of the tick.

---

## Step 3 — For each elevator

Elevators are processed sequentially in ID order.

### a. Tracking the total time this elevator had traveled
If the elevator is not idle (state ≠ `IDLE` or it has pending destinations), `active_ticks` is incremented. This counter is used for utilization statistics.

### b. (Optional) Process stop penalty
Stop penalty is enabled if the `stop-tick` is set to a positive integer to model door open/close time. When `stop_ticks_remaining > 0`, the elevator is serving a stop penalty . The counter is decremented and the rest of the elevator's processing for this tick is skipped — the elevator neither boards/exits passengers nor moves.

### c. Exit passengers
`elevator.exit(tick)` removes all passengers whose `destination == current_floor`, sets their `arrive_time = tick`, and discards that floor from the elevator's destination set.

### d. Board assigned passengers
`elevator.board(tick)` boards any passengers in the elevator's `assigned` queue whose `origin == current_floor`, up to the elevator's remaining capacity. Each boarded passenger has `board_time = tick` set and their destination floor is added to the elevator's destination set. Their origin floor is removed from destinations once no other assigned passengers remain waiting there.

### e. Log arrived passengers
Passengers returned by `exit()` are written to the passenger log.

### f. (Optional) Start stop penalty
If any passengers exited or boarded this tick and `config.stop_ticks > 0`, the elevator enters `STOPPED` state with `stop_ticks_remaining = config.stop_ticks`. Processing for this elevator ends here; it will not move until the countdown expires.

### g. Set elevator direction

Direction follows a **SCAN-like** (look-both-ways) policy:

1. If no destinations remain, the elevator becomes `IDLE`.
2. If already moving in a direction and destinations remain in that direction, continue.
3. Otherwise, reverse to whichever side has destinations (prefer the side with destinations; if both, prefer the direction away from idle).

Hard boundary guards prevent the elevator from moving below floor 1 or above `num_floors`.

### h. Move
`elevator.move()` advances `current_floor` by one in the current direction and increments `floors_traveled`. An `IDLE` elevator does not move.

---

## Step 4 — End condition

The simulation terminates when both conditions hold:

- All requests have been consumed (`next_request_idx >= len(pending)`)
- All passengers have arrived (`all(p.arrived for p in passengers)`)

These are checked at the *end* of each tick, after all elevator movements. The tick counter at termination becomes `total_ticks`, used for utilization calculations.

---

## Elevator state machine

```
          ┌──────────────────────────────────┐
          │                                  │
       IDLE ──── assigned passenger ───► MOVING
          ▲                                  │
          │                          arrives at floor
          │                                  │
          │    stop_ticks == 0          STOPPED
          └──────────────────────── (stop countdown)
```

| State | Meaning |
|-------|---------|
| `IDLE` | No destinations; elevator is stationary |
| `MOVING` | Advancing one floor per tick toward a destination |
| `STOPPED` | At a floor after a boarding/exiting event; stop-tick countdown active |

---

## Assignment contract

`algorithm.assign(passenger, elevators)` is called **once per passenger**, at the tick their request is released.

A passnger is guaranteed an elevator assignment. However, the passenger is not allowed to board if the elevator is at capacity when it reaches the source floor. In that case the passenger will continue to wait, and the elevator will return to pick up the passenger after the current passengers had exited.

---

## Capacity and ordering guarantees

- An elevator will not board more passengers than its capacity at any one stop; partial boarding is possible if multiple passengers share an origin floor and the elevator fills mid-stop.
- Requests with the same timestamp are processed in their original file order.
- There is no guarantee that requests issued in the same tick will be assigned before the elevators move; assignment happens before movement within a tick.
