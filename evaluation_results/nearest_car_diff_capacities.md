# Evaluation: Nearest Car Algorithm — Effect of Elevator Capacity

**Input file:** `mock_work_day.csv`
**Config:** floors=50 | elevators=12 | stop_ticks=0
**Variable:** elevator capacity increased from 1 to 19 (incremented by 2)
**Passengers:** 1,000

---

## Results

### Overview

| Metric                        | cap=1  | cap=3  | cap=5  | cap=7  | cap=9  | cap=11 | cap=13 | cap=15 | cap=17 | cap=19 |
|-------------------------------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| Passengers served             | 1000   | 1000   | 1000   | 1000   | 1000   | 1000   | 1000   | 1000   | 1000   | 1000   |
| Simulation duration (ticks)   | 4348   | 2404   | 2269   | 2049   | 2049   | 2049   | 2049   | 2049   | 2049   | 2049   |
| Total floors traveled         | 31441  | 14645  | 11975  | 11168  | 10762  | 10394  | 10234  | 10256  | 10190  | 10036  |

### Wait Time

| Metric | cap=1   | cap=3  | cap=5  | cap=7 | cap=9 | cap=11 | cap=13 | cap=15 | cap=17 | cap=19 |
|--------|---------|--------|--------|-------|-------|--------|--------|--------|--------|--------|
| avg    | 331.2   | 56.9   | 30.1   | 20.1  | 13.3  | 12.8   | 12.4   | 12.1   | 11.7   | 11.6   |
| std    | 544.1   | 107.1  | 60.1   | 32.5  | 15.5  | 15.6   | 14.7   | 13.2   | 12.0   | 11.6   |
| p95    | 1608.3  | 289.2  | 114.0  | 91.0  | 40.0  | 40.0   | 38.0   | 34.0   | 33.0   | 33.0   |
| max    | 2563    | 657    | 504    | 217   | 97    | 114    | 114    | 93     | 93     | 93     |

### Total Time (wait + ride)

| Metric | cap=1  | cap=3  | cap=5  | cap=7  | cap=9 | cap=11 | cap=13 | cap=15 | cap=17 | cap=19 |
|--------|--------|--------|--------|--------|-------|--------|--------|--------|--------|--------|
| avg    | 369.9  | 90.8   | 62.3   | 51.6   | 43.4  | 43.6   | 43.0   | 42.5   | 41.7   | 41.7   |
| std    | 553.8  | 116.9  | 69.1   | 43.4   | 27.3  | 27.7   | 26.8   | 25.2   | 24.2   | 24.0   |
| p95    | 1656.0 | 347.1  | 169.0  | 145.0  | 91.0  | 91.0   | 89.0   | 88.0   | 86.0   | 86.0   |
| max    | 2612   | 705    | 553    | 267    | 179   | 179    | 168    | 148    | 158    | 144    |

### Elevator Utilization

| Elevator | cap=1 | cap=3 | cap=5 | cap=7 | cap=9 | cap=11 | cap=13 | cap=15 | cap=17 | cap=19 |
|----------|-------|-------|-------|-------|-------|--------|--------|--------|--------|--------|
| avg      | 60.4% | 51.3% | 44.6% | 46.1% | 44.5% | 43.0%  | 42.4%  | 42.5%  | 42.2%  | 41.6%  |
| min      | 46.2% | 40.2% | 36.0% | 33.3% | 28.5% | 28.0%  | 27.1%  | 27.1%  | 27.1%  | 23.8%  |
| max      | 86.6% | 67.7% | 60.3% | 58.5% | 65.5% | 63.9%  | 62.6%  | 63.1%  | 61.7%  | 60.9%  |
| E1       | 49.3% | 58.7% | 54.6% | 58.5% | 65.5% | 63.9%  | 62.6%  | 60.9%  | 61.7%  | 60.9%  |
| E2       | 57.3% | 41.5% | 38.5% | 43.0% | 46.9% | 40.7%  | 40.7%  | 40.7%  | 51.8%  | 46.9%  |
| E3       | 63.8% | 61.9% | 37.7% | 44.3% | 45.0% | 44.1%  | 46.8%  | 46.8%  | 45.4%  | 48.2%  |
| E4       | 64.9% | 51.0% | 36.0% | 51.0% | 41.7% | 43.4%  | 34.0%  | 34.7%  | 36.4%  | 42.1%  |
| E5       | 71.6% | 67.7% | 60.3% | 54.8% | 59.1% | 60.2%  | 60.2%  | 63.1%  | 60.7%  | 59.4%  |
| E6       | 46.2% | 50.0% | 38.6% | 45.1% | 35.2% | 39.4%  | 39.5%  | 41.0%  | 42.2%  | 36.4%  |
| E7       | 47.1% | 52.1% | 51.1% | 48.8% | 55.6% | 46.1%  | 54.3%  | 44.3%  | 46.8%  | 46.9%  |
| E8       | 47.0% | 42.1% | 41.8% | 42.5% | 36.8% | 39.4%  | 34.6%  | 36.7%  | 34.6%  | 34.6%  |
| E9       | 55.8% | 40.2% | 41.4% | 41.0% | 28.5% | 28.3%  | 36.2%  | 41.6%  | 27.9%  | 24.9%  |
| E10      | 86.6% | 50.5% | 53.9% | 33.3% | 41.1% | 38.0%  | 35.4%  | 35.4%  | 34.5%  | 37.6%  |
| E11      | 52.1% | 48.7% | 41.3% | 54.9% | 34.7% | 28.0%  | 27.1%  | 27.1%  | 27.1%  | 23.8%  |
| E12      | 83.1% | 52.1% | 39.8% | 35.8% | 43.8% | 45.2%  | 37.9%  | 37.9%  | 37.9%  | 37.9%  |

---

## Analysis

### Summary

This experiment isolates the effect of elevator capacity on the **Nearest Car** algorithm. All other parameters are held constant (50 floors, 12 elevators, 1,000 passengers, zero stop-tick penalty). Capacity is swept in steps of 2 from 1 to 19.

---

### Simulation Duration: Throughput ceiling at capacity 7

The most striking structural observation is that simulation duration drops sharply with capacity and then hits a hard floor:

- **cap=1:** 4348 ticks — more than 2× longer than any other configuration
- **cap=3:** 2404 ticks
- **cap=5:** 2269 ticks
- **cap=7+:** 2049 ticks (plateau)

From capacity 7 onwards, the simulation finishes in exactly the same number of ticks regardless of further capacity increases. This plateau is the **input starvation**: with 12 elevators and the Nearest Car dispatch policy, the bottleneck shifts from elevator capacity to the arrival pattern of passengers. Raising capacity beyond 7 does not reduce the time to serve all 1,000 passengers from the input file.

At cap=1, each elevator can only carry one person per trip, forcing many more trips and creating severe queuing. The 2× longer duration reflects the fundamental throughput limitation of single-occupancy operation.

---

### Total Floors Traveled: Large early gains, diminishing returns

Total floors traveled by all elevators drops from 31,441 (cap=1) to 10,036 (cap=19), a 68% reduction. However, most of the gain is front-loaded:

| Capacity range | Reduction in floors traveled |
|----------------|------------------------------|
| 1 -> 3          | −53% (31441 -> 14645)         |
| 3 -> 5          | −18% (14645 -> 11975)         |
| 5 -> 7          | −7%  (11975 -> 11168)         |
| 7 -> 19         | −10% across 6 further steps  |

With cap=1, elevators must make far more trips to serve the same passengers, traveling far more floor-distance in total. By cap=3, batching just 2–3 passengers per trip cuts the total distance roughly in half. After cap=7, each incremental capacity increase yields only marginal floor savings because most trips are no longer capacity-constrained.

---

### Wait Time: The most capacity-sensitive metric

Average wait time improves dramatically with capacity and is the most sensitive metric to this variable:

- cap=1 -> avg **331.2** ticks, p95 **1608**, max **2563** — extreme queuing, long tail
- cap=3 -> avg **56.9** (−83%), p95 **289**
- cap=7 -> avg **20.1**, p95 **91**, max **217**
- cap=9 -> avg **13.3**, p95 **40**, max **97** — tail largely tamed
- cap=19 -> avg **11.6**, p95 **33**, max **93**

The p95 and max values illustrate tail behavior. At cap=1, the 95th-percentile wait is over 1,600 ticks — passengers near the end of the queue wait an extraordinarily long time. By cap=9, p95 drops to 40 ticks, a 40× improvement. Gains beyond cap=9 are modest: the std of wait time halves from cap=1 to cap=9 (544 -> 15.5) and barely changes further, confirming that capacity is no longer the source of variance.

The high std relative to the mean at low capacities (std/mean ≈ 1.6 at cap=1) signals heavy-tailed queuing behaviour typical of an overloaded system. By cap=9 the ratio drops below 1.2 and stabilises, indicating the system is no longer overloaded.

---

### Total Time: Ride-time dominates above capacity 9

Total time (wait + ride) closely mirrors wait time but converges more slowly because ride time (floor distance to destination) cannot be eliminated by raising capacity:

- cap=1 -> avg **369.9** ticks
- cap=9 -> avg **43.4** ticks
- cap=19 -> avg **41.7** ticks

The gap between avg wait and avg total time shrinks as capacity rises:

| Capacity | avg wait | avg total | implied avg ride |
|----------|----------|-----------|-----------------|
| 1        | 331.2    | 369.9     | 38.7            |
| 9        | 13.3     | 43.4      | 30.1            |
| 19       | 11.6     | 41.7      | 30.1            |

At low capacity, wait time dominates total time (90% of total at cap=1). At high capacity, ride time dominates (~72% of total at cap=9+). The average ride time (~30 ticks at cap≥9) represents the irreducible floor-travel component for this workload and cannot be improved by capacity alone.

---

### Elevator Utilization: Fewer, more efficient trips

Average utilization decreases steadily from 60.4% (cap=1) to 41.6% (cap=19). This is expected: higher capacity means each elevator serves more passengers per trip and therefore spends a smaller fraction of the simulation in motion.

At cap=1, E10 and E12 hit 86.6% and 83.1% utilisation respectively — these elevators were running nearly continuously, a sign the system was under heavy stress. By cap=3, no elevator exceeds 67.7%, and from cap=7 onward the maximum stays around 60–65%.

Utilization spread between elevators (min/max gap) narrows as capacity increases:

| Capacity | min util | max util | spread |
|----------|----------|----------|--------|
| 1        | 46.2%    | 86.6%    | 40.4 pp |
| 9        | 28.5%    | 65.5%    | 37.0 pp |
| 19       | 23.8%    | 60.9%    | 37.1 pp |

The persistent spread of ~37 percentage points at higher capacities reflects the **Nearest Car** algorithm's inherent load imbalance: elevators closest to request origins are always preferred, causing some elevators (E1, E5, E7) to consistently handle more requests than others (E9, E11). This is a structural limitation of the nearest-car dispatch policy and is independent of capacity.

---

### Key Takeaways

| Finding | Detail |
|---------|--------|
| **Capacity 7 is the throughput threshold** | Simulation duration plateaus at 2049 ticks for cap≥7; raising capacity further does not improve overall completion time |
| **Capacity 9 is the service-quality sweet spot** | The largest per-unit improvements in avg wait, p95 wait, and max wait all occur at or before cap=9; gains above 9 are marginal |
| **Cap=1 is qualitatively worse** | Average wait 25× higher than cap=9; simulation 2× longer; system operates in a heavily overloaded regime |
| **Ride time sets a hard floor** | ~30 ticks average ride time is irreducible regardless of capacity; total time cannot fall below ~41 ticks with this algorithm and layout |
| **Nearest Car produces persistent load imbalance** | ~37 pp spread between least- and most-used elevators persists at all capacities, a consequence of proximity-only dispatch rather than a capacity effect |
