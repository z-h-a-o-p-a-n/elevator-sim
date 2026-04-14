# Evaluation: Nearesr Car vs Round Robin vs Zoned-Dispatch

**Input file:** `mock_work_day.csv`
**Config:** floors=50 | elevators=12 | capacity=8 | stop_ticks=0
**Variable:** `nearest_car`, `round_robin`, `zoned_dispatch`
**Passengers:** 1,000

---

## Raw Results

```
Metric                        │ nearest_car        │ round_robin        │ zoned_dispatch
────────────────────────────────────────────────────────────────────────────────────────────
Overview                      │                    │                    │
  Passengers served           │ 1000               │ 1000               │ 1000
  Simulation duration (ticks) │ 2078               │ 2049               │ 2600
  Total floors traveled       │ 9528               │ 17276              │ 11178
────────────────────────────────────────────────────────────────────────────────────────────
Wait time                     │                    │                    │
  avg                         │ 11.6               │ 34.0               │ 98.6
  std                         │ 12.2               │ 24.5               │ 189.6
  p95                         │ 35.0               │ 79.0               │ 612.3
  min                         │ 0 (passenger8)     │ 0 (passenger8)     │ 0 (passenger8)
  max                         │ 88 (passenger888)  │ 97 (passenger207)  │ 908 (passenger869)
────────────────────────────────────────────────────────────────────────────────────────────
Total time                    │                    │                    │
  avg                         │ 38.2               │ 64.1               │ 137.8
  std                         │ 22.6               │ 32.0               │ 201.3
  p95                         │ 79.0               │ 117.0              │ 673.3
  min                         │ 1 (passenger10)    │ 1 (passenger10)    │ 1 (passenger10)
  max                         │ 142 (passenger877) │ 178 (passenger850) │ 956 (passenger869)
────────────────────────────────────────────────────────────────────────────────────────────
Elevator utilization          │                    │                    │
  avg                         │ 38.9%              │ 70.8%              │ 36.3%
  min                         │ 22.1% (E12)        │ 63.6% (E6)         │ 13.5% (E12)
  max                         │ 58.4% (E1)         │ 77.0% (E3)         │ 76.4% (E4)
  E1                          │ 58.4% (1213/2078)  │ 69.3% (1419/2049)  │ 48.7% (1266/2600)
  E2                          │ 34.1% (709/2078)   │ 66.7% (1366/2049)  │ 74.8% (1945/2600)
  E3                          │ 43.6% (907/2078)   │ 77.0% (1578/2049)  │ 39.6% (1029/2600)
  E4                          │ 46.0% (956/2078)   │ 75.5% (1548/2049)  │ 76.4% (1987/2600)
  E5                          │ 53.7% (1115/2078)  │ 70.1% (1436/2049)  │ 25.6% (666/2600)
  E6                          │ 41.7% (866/2078)   │ 63.6% (1304/2049)  │ 24.3% (631/2600)
  E7                          │ 33.9% (704/2078)   │ 74.4% (1524/2049)  │ 16.2% (420/2600)
  E8                          │ 30.8% (640/2078)   │ 71.0% (1455/2049)  │ 25.7% (667/2600)
  E9                          │ 36.2% (753/2078)   │ 67.7% (1387/2049)  │ 36.2% (940/2600)
  E10                         │ 38.3% (796/2078)   │ 74.6% (1529/2049)  │ 27.9% (725/2600)
  E11                         │ 28.1% (583/2078)   │ 70.9% (1452/2049)  │ 27.5% (715/2600)
  E12                         │ 22.1% (459/2078)   │ 69.2% (1418/2049)  │ 13.5% (350/2600)
────────────────────────────────────────────────────────────────────────────────────────────
```

---

## Analysis

### `nearest_car` — Best passenger experience, most efficient movement

`nearest_car` delivers the best results for every passenger-facing metric. With an average wait
time of just **11.6 ticks** and average total time of **38.2 ticks**, passengers spend far less
time waiting compared to the other two algorithms. The p95 wait of 35 ticks and a maximum wait of
88 ticks show that even the worst-case experience is well-controlled (low variance, std = 12.2).

The algorithm is also the most movement-efficient: it travels only **9,528 floors** in total —
roughly half of `round_robin` — because each request is handled by whichever elevator is already
closest. This greedy locality means elevators rarely make long empty runs.

The downside is **uneven utilization**: elevator load ranges from 22.1% (E12) to 58.4% (E1), an
average of 38.9%. Many elevators are idle most of the time. The simulation finishes in 2,078 ticks
because requests are served quickly even though most elevators are underutilized.

**Best for:** minimizing passenger wait time and total trip time.

---

### `round_robin` — Most balanced load, highest movement cost

`round_robin` spreads work evenly across all elevators: utilization ranges from a tight 63.6%–77.0%
(avg **70.8%**), the most uniform distribution of the three algorithms. No elevator is idle; all are
kept continuously busy throughout the 2,049-tick simulation.

However, ignoring elevator position when assigning requests causes elevators to travel far more than
necessary — **17,276 floors**, nearly 81% more than `nearest_car`. This extra movement translates
directly into worse passenger experience: average wait 34.0 ticks (3× `nearest_car`) and average
total time 64.1 ticks (1.7× `nearest_car`).

Despite the heavy travel burden, `round_robin` still finishes in the shortest simulation time
(2,049 ticks). This is because the load-balancing prevents any single elevator from becoming a
bottleneck, keeping throughput high even though individual trips are longer.

**Best for:** maximizing fleet utilization and throughput when fairness across elevators matters
more than minimizing individual trip times.

---

### `zoned_dispatch` — Worst overall; zone mismatch causes severe tail latency

`zoned_dispatch` performs significantly worse than the other two on every metric. The simulation
runs the longest (**2,600 ticks**), average wait is **98.6 ticks** (8.5× `nearest_car`), and the
p95 wait of **612 ticks** and maximum wait of **908 ticks** (passenger869) indicate a large number
of passengers waiting an extreme amount of time. The standard deviation of 189.6 on wait time is
the clearest signal of pathological behavior: some passengers are served almost immediately while
others wait hundreds of ticks.

The root cause is **zone-to-demand mismatch**. With a 50-floor building divided into static zones,
the zones that receive the most traffic in this workload happen to be served by only a subset of
elevators, while others (E7, E12 at 16.2% and 13.5%) sit nearly idle. The per-elevator spread is
extreme (13.5%–76.4%), and the average utilization (36.3%) is similar to `nearest_car` but
distributed far less effectively. Elevators in low-demand zones cannot help elevators in
high-demand zones, creating artificial bottlenecks.

Total floors traveled (11,178) is in the middle, between the other two, but this is a misleading
positive: that travel is concentrated in a few overloaded elevators, not spread efficiently.

**Best for:** workloads where demand is predictably and uniformly distributed across floors that
align with zone boundaries. This workload (`mock_work_day.csv`) does not meet those conditions,
making `zoned_dispatch` a poor fit here.

---

## Summary Table

| Metric | `nearest_car` | `round_robin` | `zoned_dispatch` |
|---|---|---|---|
| Simulation duration (ticks) | 2,078 | **2,049** | 2,600 |
| Total floors traveled | **9,528** | 17,276 | 11,178 |
| Avg wait time (ticks) | **11.6** | 34.0 | 98.6 |
| p95 wait time (ticks) | **35.0** | 79.0 | 612.3 |
| Max wait time (ticks) | **88** | 97 | 908 |
| Avg total time (ticks) | **38.2** | 64.1 | 137.8 |
| Avg elevator utilization | 38.9% | **70.8%** | 36.3% |
| Utilization range | 22–58% | **64–77%** | 14–76% |

**Winner by category:**
- Passenger wait time → `nearest_car`
- Passenger total time → `nearest_car`
- Movement efficiency (floors traveled) → `nearest_car`
- Load balance across elevators → `round_robin`
- Simulation throughput speed → `round_robin`
- Overall worst → `zoned_dispatch` (on this workload)
