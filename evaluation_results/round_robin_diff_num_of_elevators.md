# Evaluation: Round Robin Algorithm — Effect of Number of Elevators

**Input file:** `mock_work_day.csv`
**Config:** floors=50 | capacity=8 | stop_ticks=0
**Variable:** number of elevators swept as odd values from 1 to 11 (increment of 2)
**Passengers:** 1,000

---

## Results

### Overview

| Metric                        | rr_1  | rr_3  | rr_5  | rr_7  | rr_9  | rr_11 |
|-------------------------------|-------|-------|-------|-------|-------|-------|
| Passengers served             | 1000  | 1000  | 1000  | 1000  | 1000  | 1000  |
| Simulation duration (ticks)   | 4669  | 2525  | 2199  | 2075  | 2056  | 2056  |
| Total floors traveled         | 4668  | 7418  | 10168 | 12674 | 14629 | 16612 |

### Wait Time

| Metric | rr_1   | rr_3   | rr_5   | rr_7  | rr_9  | rr_11 |
|--------|--------|--------|--------|-------|-------|-------|
| avg    | 703.7  | 152.2  | 80.5   | 51.7  | 40.3  | 35.9  |
| std    | 951.9  | 202.8  | 101.1  | 52.5  | 32.0  | 26.0  |
| p95    | 2721.9 | 653.1  | 321.5  | 176.0 | 86.0  | 82.0  |
| max    | 3327   | 993    | 571    | 372   | 269   | 179   |

### Total Time (wait + ride)

| Metric | rr_1   | rr_3   | rr_5   | rr_7  | rr_9  | rr_11 |
|--------|--------|--------|--------|-------|-------|-------|
| avg    | 749.1  | 194.5  | 120.8  | 89.2  | 74.1  | 67.4  |
| std    | 961.9  | 213.0  | 111.3  | 63.2  | 41.5  | 34.9  |
| p95    | 2775.4 | 711.2  | 382.2  | 236.0 | 147.0 | 123.0 |
| max    | 3357   | 1044   | 623    | 421   | 321   | 228   |

### Elevator Utilization

| Elevator | rr_1   | rr_3   | rr_5   | rr_7   | rr_9   | rr_11  |
|----------|--------|--------|--------|--------|--------|--------|
| avg      | 100.0% | 98.0%  | 92.8%  | 87.7%  | 79.6%  | 74.0%  |
| min      | 100.0% | 96.4%  | 89.4%  | 82.0%  | 75.3%  | 67.7%  |
| max      | 100.0% | 99.6%  | 97.5%  | 94.1%  | 84.3%  | 79.4%  |
| E1       | 100.0% | 96.4%  | 97.5%  | 86.2%  | 84.2%  | 79.4%  |
| E2       | —      | 99.6%  | 89.8%  | 83.3%  | 80.2%  | 73.3%  |
| E3       | —      | 97.9%  | 96.0%  | 94.1%  | 75.3%  | 71.8%  |
| E4       | —      | —      | 89.4%  | 87.6%  | 77.8%  | 76.5%  |
| E5       | —      | —      | 91.4%  | 89.7%  | 80.8%  | 75.0%  |
| E6       | —      | —      | —      | 91.3%  | 79.5%  | 73.8%  |
| E7       | —      | —      | —      | 82.0%  | 84.3%  | 77.3%  |
| E8       | —      | —      | —      | —      | 76.1%  | 72.0%  |
| E9       | —      | —      | —      | —      | 78.4%  | 67.7%  |
| E10      | —      | —      | —      | —      | —      | 74.8%  |
| E11      | —      | —      | —      | —      | —      | 72.5%  |

---

## Analysis

### Summary

This experiment isolates the effect of fleet size on the **Round Robin** dispatch algorithm. Round Robin assigns incoming passengers to elevators in a fixed cyclic order (E1 -> E2 -> ... -> En -> E1 -> ...), completely ignoring elevator position and current load. The fleet is swept from 1 to 11 elevators (odd values only), while capacity, floors, and input workload are held constant.

---

### Simulation Duration: Plateau at 9 elevators

Simulation duration falls as more elevators are added, then stabilises:

| Elevators | Duration (ticks) | Change from previous |
|-----------|-----------------|----------------------|
| 1         | 4669            | —                    |
| 3         | 2525            | −46%                 |
| 5         | 2199            | −13%                 |
| 7         | 2075            | −6%                  |
| 9         | 2056            | −1%                  |
| 11        | 2056            | 0%                   |

The hard plateau at 2056 ticks for rr_9 and rr_11 indicates a **throughput ceiling**: the bottleneck has shifted from fleet capacity to the arrival pattern of passengers. Beyond 9 elevators, further additions cannot accelerate the simulation because passengers are simply not arriving fast enough to keep additional elevators productive.

With a single elevator the situation is extreme — it is continuously occupied for the entire 4,669-tick simulation at 100% utilisation, making one trip after another. The simulation is more than twice as long as the plateau value.

---

### Total Floors Traveled: Increases with more elevators (Round Robin's key inefficiency)

This is the most counterintuitive result in the dataset. Unlike proximity-based algorithms, adding more elevators under Round Robin *increases* total floors traveled:

| Elevators | Total floors traveled | Per-elevator avg |
|-----------|----------------------|-----------------|
| 1         | 4,668                | 4,668           |
| 3         | 7,418                | 2,473           |
| 5         | 10,168               | 2,034           |
| 7         | 12,674               | 1,811           |
| 9         | 14,629               | 1,626           |
| 11        | 16,612               | 1,510           |

The collective fleet travels 3.6× more floor-distance with 11 elevators than with 1. The root cause is Round Robin's position-blind dispatch: each elevator is assigned passengers regardless of where it currently sits. With more elevators in the pool, a newly assigned elevator is statistically farther from the passenger than the nearest available car would be. Every added elevator introduces more deadhead travel (empty or repositioning movement to reach an assigned pick-up).

By contrast, a single elevator with capacity 8 reuses its momentum — it loads multiple passengers from nearby floors in one pass and drops them off sequentially, accumulating surprisingly low total distance. The efficiency here is not a virtue of having fewer elevators; it is a coincidental effect of serial batching.

This metric starkly illustrates that **Round Robin trades dispatch efficiency for simplicity and fairness** — the algorithm guarantees equal workload distribution but at a systematic floor-distance penalty.

---

### Wait Time: Large gains up to rr_5, diminishing returns beyond

Each elevator added reduces average wait time, but returns diminish sharply:

| Transition | avg wait reduction | reduction per elevator added |
|------------|--------------------|------------------------------|
| rr_1 -> rr_3 | −551.5 ticks      | −275.7 per elevator          |
| rr_3 -> rr_5 | −71.7 ticks       | −35.9 per elevator           |
| rr_5 -> rr_7 | −28.8 ticks       | −14.4 per elevator           |
| rr_7 -> rr_9 | −11.4 ticks       | −5.7 per elevator            |
| rr_9 -> rr_11 | −4.4 ticks       | −2.2 per elevator            |

The tail metrics (p95 and max) tell a sharper story. At rr_1, the 95th-percentile wait is **2722 ticks** — a passenger near the back of the queue waits nearly the entire simulation. By rr_9, p95 has dropped to **86 ticks**, an over 30× improvement. The maximum wait falls from 3327 (rr_1) to 179 (rr_11), showing that the worst-case experience improves continuously even as avg gains shrink.

The high std/mean ratio at rr_1 (951.9 / 703.7 ≈ 1.35) confirms heavy-tailed, overloaded queuing. By rr_9 the ratio has dropped to 0.79, indicating a system no longer in distress.

---

### Total Time: Ride time decreases alongside wait time

Unlike the Nearest Car experiment where ride time was approximately constant (~30 ticks), here ride time shrinks as more elevators are added:

| Elevators | avg wait | avg total | implied avg ride |
|-----------|----------|-----------|-----------------|
| 1         | 703.7    | 749.1     | 45.4            |
| 3         | 152.2    | 194.5     | 42.3            |
| 5         | 80.5     | 120.8     | 40.3            |
| 7         | 51.7     | 89.2      | 37.5            |
| 9         | 40.3     | 74.1      | 33.8            |
| 11        | 35.9     | 67.4      | 31.5            |

With a single overloaded elevator, passengers are batched together more densely and the elevator makes more intermediate stops, lengthening individual rides. As the fleet grows, each elevator handles fewer simultaneous passengers, resulting in more direct routes and shorter rides. This ride-time improvement is modest (45 -> 32 ticks) but real and consistent.

At rr_11 the implied average ride of ~31.5 ticks approaches the theoretical minimum for the 50-floor layout, suggesting the system is close to dispatching-optimally in terms of ride distance.

---

### Elevator Utilization: Near-perfect balance, persistently high

Round Robin's defining characteristic is its uniformly high utilisation:

| Elevators | avg util | min util | max util | spread |
|-----------|----------|----------|----------|--------|
| 1         | 100.0%   | 100.0%   | 100.0%   | 0 pp   |
| 3         | 98.0%    | 96.4%    | 99.6%    | 3.2 pp |
| 5         | 92.8%    | 89.4%    | 97.5%    | 8.1 pp |
| 7         | 87.7%    | 82.0%    | 94.1%    | 12.1 pp|
| 9         | 79.6%    | 75.3%    | 84.3%    | 9.0 pp |
| 11        | 74.0%    | 67.7%    | 79.4%    | 11.7 pp|

Compared to Nearest Car (which showed ~37–40 pp spread and average utilisation of 41–60%), Round Robin achieves far more balanced load distribution — the spread between least- and most-used elevators is at most ~12 pp here. This is the algorithm's main structural advantage: cyclic assignment distributes work evenly by construction.

However, the absolute utilisation values are notably high. At rr_9, all elevators still run at 75–84% — the system is working hard across the entire fleet, not just a subset. This is consistent with the earlier observation that Round Robin generates more total travel distance: the elevators are busy, but a significant portion of that busyness is deadhead travel rather than productive passenger transport.

At rr_1 the single elevator runs at 100% throughout, meaning it never idles — the queue always has waiting passengers. This is a saturated single-server queuing system.

---

### Key Takeaways

| Finding | Detail |
|---------|--------|
| **9 elevators is the throughput ceiling** | Simulation duration plateaus at 2056 ticks for rr_9 and rr_11; adding the 10th and 11th elevators reduces wait time but does not finish the simulation sooner |
| **Total floor travel increases with fleet size** | Round Robin's position-blind dispatch generates increasing deadhead travel as more elevators compete for randomly assigned passengers; 11 elevators travel 3.6× the total distance of 1 |
| **Single elevator is catastrophically overloaded** | 100% utilisation, avg wait 703 ticks, p95 wait 2722 ticks — the system is a saturated queue; rr_1 is an informative lower bound, not a viable configuration |
| **Diminishing returns set in quickly** | Half the total wait-time improvement comes from rr_1->rr_3; beyond rr_5, each additional elevator saves fewer than 30 avg ticks |
| **Ride time decreases with fleet size** | More elevators -> fewer simultaneous passengers per elevator -> more direct routes; avg ride shrinks from 45 ticks (rr_1) to ~32 ticks (rr_11) |
| **Near-perfect load balance at a cost** | Round Robin keeps all elevators busy (67–100% util) with minimal spread between elevators, but this "efficiency" is partly wasted on suboptimal position-blind dispatch |
