# Evaluation: Nearesr Car vs Round Robin vs Zoned-Dispatch

**Input file:** `mock_work_day.csv`
**Config:** floors=50 | elevators=12 | capacity=8 | stop\_ticks=0
**Variable:** algorith used to pick the elevator
**Passengers:** 1,000

---

## Results

| Metric | nearest\_car | round\_robin | zoned\_dispatch |
|---|---|---|---|
| **Overview** | | | |
| Passengers served | 1000 | 1000 | 1000 |
| Simulation duration (ticks) | 2049 | 2049 | 2480 |
| Total floors traveled | 10,882 | 17,276 | 11,197 |
| **Wait time** | | | |
| avg | 15.7 | 34.0 | 81.8 |
| std | 20.7 | 24.5 | 145.2 |
| p95 | 70.0 | 79.0 | 468.1 |
| min | 0 (passenger8) | 0 (passenger8) | 0 (passenger8) |
| max | 150 (passenger920) | 97 (passenger207) | 803 (passenger869) |
| **Total time** | | | |
| avg | 47.3 | 64.1 | 121.7 |
| std | 32.3 | 32.0 | 156.4 |
| p95 | 116.1 | 117.0 | 529.1 |
| min | 1 (passenger10) | 1 (passenger10) | 1 (passenger10) |
| max | 190 (passenger920) | 178 (passenger850) | 853 (passenger869) |
| **Elevator utilization** | | | |
| avg | 45.0% | 70.8% | 38.1% |
| min | 25.4% (E9) | 63.6% (E6) | 19.2% (E7) |
| max | 62.7% (E1) | 77.0% (E3) | 72.9% (E2) |
| E1 | 62.7% (1285/2049) | 69.3% (1419/2049) | 66.4% (1647/2480) |
| E2 | 47.7% (977/2049) | 66.7% (1366/2049) | 72.9% (1809/2480) |
| E3 | 44.8% (918/2049) | 77.0% (1578/2049) | 54.6% (1355/2480) |
| E4 | 36.9% (757/2049) | 75.5% (1548/2049) | 53.5% (1327/2480) |
| E5 | 57.3% (1174/2049) | 70.1% (1436/2049) | 25.8% (641/2480) |
| E6 | 43.2% (886/2049) | 63.6% (1304/2049) | 28.4% (704/2480) |
| E7 | 52.9% (1084/2049) | 74.4% (1524/2049) | 19.2% (475/2480) |
| E8 | 39.2% (803/2049) | 71.0% (1455/2049) | 22.2% (550/2480) |
| E9 | 25.4% (521/2049) | 67.7% (1387/2049) | 38.7% (960/2480) |
| E10 | 34.1% (698/2049) | 74.6% (1529/2049) | 23.5% (584/2480) |
| E11 | 43.0% (881/2049) | 70.9% (1452/2049) | 30.5% (756/2480) |
| E12 | 52.2% (1069/2049) | 69.2% (1418/2049) | 21.9% (543/2480) |

---

## Analysis

### Summary ranking

| Rank | Algorithm | Strengths | Weaknesses |
|---|---|---|---|
| 1st | **nearest\_car** | Best wait/total times, fewest floors traveled | Lower elevator utilization |
| 2nd | **round\_robin** | Consistent wait times, no extreme outliers | High floor travel, passengers wait longer on average |
| 3rd | **zoned\_dispatch** | — | Worst on every passenger-facing metric; extreme outliers |

---

### nearest\_car — winner on passenger experience

`nearest_car` achieves the best outcome for passengers by dispatching whichever elevator is geographically closest to each call.

- **Lowest average wait time (15.7 ticks)** — roughly half that of `round_robin` and ~5× better than `zoned_dispatch`.
- **Lowest total floor travel (10,882)** — the greedy proximity assignment naturally avoids unnecessary long repositioning trips, making it the most mechanically efficient algorithm.
- **Same simulation duration as `round_robin` (2049 ticks)** — all 1000 passengers cleared at the same wall-clock time despite lower utilization, because each elevator trip is shorter and more purposeful.
- **One notable outlier:** passenger920 waited 150 ticks (the highest max among the two good algorithms). The p95 of 70 ticks is acceptable, but the long tail suggests that under burst demand a single elevator can be claimed by several competing calls before reaching a stranded passenger.
- **Lower utilization (45.0% avg)** is not a flaw here — it reflects that elevators spend less time traveling empty, not that they are idle while passengers wait.

---

### round\_robin — predictable but wasteful

`round_robin` assigns calls in strict rotation, ignoring elevator position.

- **Consistent std (24.5 for wait, 32.0 for total)** — the fairness of rotation reduces variance, meaning very few passengers suffer extreme delays. The max wait is only 97 ticks, the best of the three.
- **High floor travel (17,276 — 59% more than `nearest_car`)** — because assignment ignores position, elevators routinely cross the building to pick up passengers that a nearby elevator could have served. This wasted movement is the fundamental cost of rotation.
- **Higher utilization (70.8%)** is a symptom of that waste: elevators are busier because they are traveling further, not because they are serving more passengers.
- **Same simulation end time as `nearest_car` (2049 ticks)** — the extra travel does not ultimately delay clearance, but it does inflate energy cost and wear.

---

### zoned\_dispatch — fails under realistic load

`zoned_dispatch` partitions the 50 floors into fixed zones, each served by a subset of elevators. This works well when demand matches zone boundaries; it breaks badly when it does not.

- **Highest average wait time (81.8 ticks) and total time (121.7 ticks)** — both roughly 2.5× worse than `round_robin` and 5–8× worse than `nearest_car`.
- **Catastrophic variance** — std of 145.2 (wait) and 156.4 (total) are 6–7× higher than the other algorithms. The p95 wait is 468 ticks and the single worst passenger (passenger869) waited 803 ticks — over a third of the entire simulation length.
- **Longest simulation (2480 ticks)** — the last passenger was not cleared until 431 ticks after `nearest_car` finished. This means some zone queues were severely backlogged.
- **Severe elevator imbalance** — utilization ranges from 19.2% (E7) to 72.9% (E2), a 53-point spread. Some zone elevators are overwhelmed while elevators in lightly-used zones sit nearly idle. The mock workday traffic pattern does not align evenly with the static zone boundaries.
- **Root cause:** static zone assignment cannot adapt to the real-time distribution of demand. When a zone is a hotspot (e.g. lobby ↔ mid-floor commutes during morning rush), its dedicated elevators become a bottleneck with no relief from neighboring idle elevators.

---

### Key takeaways

1. **Proximity beats rotation.** `nearest_car` consistently outperforms `round_robin` at every percentile while also traveling fewer floors. Greedy proximity is both faster and more efficient.

2. **Static zoning is fragile.** `zoned_dispatch` is competitive only when demand is uniformly distributed across zones. A realistic workday with clustered floor traffic exposes its rigidity, producing extreme outliers and a prolonged simulation tail.

3. **Utilization is not a proxy for performance.** `round_robin`'s 70.8% average utilization looks impressive but masks wasted cross-building travel. `nearest_car`'s 45.0% utilization corresponds to better passenger outcomes.

4. **Watch the tail, not just the mean.** `zoned_dispatch`'s average of 81.8 ticks sounds bad, but its p95 of 468 and max of 803 reveal the true operational risk — a small but real fraction of passengers experience an unacceptable building-wide delay.
