# Evaluation: Overlapping vs Non-Overlapping Zones

**Input file:** `mock_work_day.csv`
**Config:** floors=50 | elevators=12 | capacity=8 | stop_ticks=0
**Variable:** overlap vs non-overlap zones
**Passengers:** 1,000

## Results

### Overview

| Metric | 2-non-overlap-zones | 2-overlap-zones | 3-non-overlap-zones | 3-overlap-zones | 4-non-overlap-zones | 4-overlap-zones |
|---|---|---|---|---|---|---|
| Passengers served | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 |
| Simulation duration (ticks) | 2174 | 2384 | 2480 | 2335 | 2669 | 2953 |
| Total floors traveled | 10643 | 10399 | 11197 | 10933 | 12386 | 12057 |

### Wait Time

| Metric | 2-non-overlap-zones | 2-overlap-zones | 3-non-overlap-zones | 3-overlap-zones | 4-non-overlap-zones | 4-overlap-zones |
|---|---|---|---|---|---|---|
| avg | 44.4 | 52.1 | 81.8 | 87.0 | 142.9 | 141.9 |
| std | 74.1 | 107.6 | 145.2 | 146.3 | 237.7 | 250.0 |
| p95 | 224.1 | 283.1 | 468.1 | 490.0 | 697.1 | 705.6 |
| min | 0 (passenger8) | 0 (passenger8) | 0 (passenger8) | 0 (passenger8) | 0 (passenger8) | 0 (passenger8) |
| max | 497 (passenger869) | 707 (passenger869) | 803 (passenger869) | 636 (passenger869) | 1096 (passenger740) | 1354 (passenger761) |

### Total Time

| Metric | 2-non-overlap-zones | 2-overlap-zones | 3-non-overlap-zones | 3-overlap-zones | 4-non-overlap-zones | 4-overlap-zones |
|---|---|---|---|---|---|---|
| avg | 82.0 | 89.6 | 121.7 | 127.8 | 186.1 | 183.9 |
| std | 85.4 | 117.2 | 156.4 | 157.3 | 248.9 | 261.6 |
| p95 | 279.5 | 349.0 | 529.1 | 543.0 | 757.0 | 763.3 |
| min | 1 (passenger10) | 1 (passenger10) | 1 (passenger10) | 1 (passenger10) | 1 (passenger10) | 1 (passenger10) |
| max | 547 (passenger869) | 757 (passenger869) | 853 (passenger869) | 686 (passenger869) | 1148 (passenger740) | 1404 (passenger761) |

### Elevator Utilization

| Elevator | 2-non-overlap-zones | 2-overlap-zones | 3-non-overlap-zones | 3-overlap-zones | 4-non-overlap-zones | 4-overlap-zones |
|---|---|---|---|---|---|---|
| avg | 41.3% | 36.9% | 38.1% | 39.5% | 39.2% | 34.4% |
| min | 10.8% (E12) | 2.1% (E12) | 19.2% (E7) | 13.5% (E8) | 13.9% (E12) | 10.3% (E6) |
| max | 75.2% (E2) | 67.1% (E5) | 72.9% (E2) | 79.0% (E1) | 80.3% (E2) | 87.2% (E3) |
| E1 | 56.8% (1235/2174) | 45.1% (1075/2384) | 66.4% (1647/2480) | 79.0% (1845/2335) | 80.0% (2136/2669) | 63.6% (1878/2953) |
| E2 | 75.2% (1635/2174) | 49.6% (1183/2384) | 72.9% (1809/2480) | 70.1% (1637/2335) | 80.3% (2142/2669) | 59.6% (1759/2953) |
| E3 | 45.8% (996/2174) | 47.4% (1129/2384) | 54.6% (1355/2480) | 73.8% (1724/2335) | 65.9% (1759/2669) | 87.2% (2576/2953) |
| E4 | 59.3% (1290/2174) | 49.2% (1173/2384) | 53.5% (1327/2480) | 69.4% (1621/2335) | 27.1% (724/2669) | 26.8% (791/2953) |
| E5 | 52.9% (1151/2174) | 67.1% (1599/2384) | 25.8% (641/2480) | 22.3% (521/2335) | 24.5% (655/2669) | 23.4% (692/2953) |
| E6 | 50.7% (1103/2174) | 49.4% (1177/2384) | 28.4% (704/2480) | 16.4% (383/2335) | 22.0% (586/2669) | 10.3% (305/2953) |
| E7 | 42.6% (926/2174) | 25.1% (598/2384) | 19.2% (475/2480) | 14.3% (333/2335) | 30.3% (810/2669) | 16.2% (479/2953) |
| E8 | 27.7% (603/2174) | 32.5% (774/2384) | 22.2% (550/2480) | 13.5% (315/2335) | 31.8% (850/2669) | 24.2% (714/2953) |
| E9 | 16.5% (358/2174) | 28.6% (681/2384) | 38.7% (960/2480) | 39.5% (922/2335) | 17.8% (476/2669) | 12.8% (379/2953) |
| E10 | 42.3% (919/2174) | 32.5% (774/2384) | 23.5% (584/2480) | 36.9% (862/2335) | 43.3% (1155/2669) | 37.1% (1095/2953) |
| E11 | 15.2% (330/2174) | 14.1% (335/2384) | 30.5% (756/2480) | 23.9% (559/2335) | 33.2% (885/2669) | 24.5% (724/2953) |
| E12 | 10.8% (235/2174) | 2.1% (50/2384) | 21.9% (543/2480) | 15.0% (350/2335) | 13.9% (371/2669) | 27.3% (807/2953) |

---

## Analysis: Why More Zones Produces Worse Performance

### 1. Load Imbalance is the Primary Driver

The utilization breakdown reveals the root cause. The `mock_work_day.csv` pattern concentrates demand on low floors (heavy lobby traffic), but with more zones the low-floor elevators are locked into a small pool that cannot be supplemented.

**4-non-overlap-zones:**
- E1–E3 (floors 1–12): **80.0%, 80.3%, 65.9%** — nearly saturated
- E4–E6 (floors 13–25): 27.1%, 24.5%, 22.0% — mostly idle
- E7–E12 (floors 26–50): 13.9%–43.3% — mostly idle

With 4 zones, 3 low-floor elevators are maxed out while 9 elevators sit underutilized in adjacent zones — unable to help because of zone rigidity. Passengers pile up waiting for E1–E3.

**2-non-overlap-zones:**
- E1–E6 (floors 1–25): ~57% average utilization — demand is absorbed across 6 elevators, none saturated
- E7–E12 (floors 26–50): ~26% average — slack capacity

### 2. Progressive Degradation in the Numbers

| Config | Avg wait | p95 wait | Avg total | p95 total | Sim duration |
|---|---|---|---|---|---|
| 2-non-overlap | 44.4 | 224.1 | 82.0 | 279.5 | 2174 |
| 3-non-overlap | 81.8 | 468.1 | 121.7 | 529.1 | 2480 |
| 4-non-overlap | 142.9 | 697.1 | 186.1 | 757.0 | 2669 |

Average wait time nearly **triples** (44 -> 143 ticks) and p95 wait **triples** (224 -> 697 ticks) from 2 to 4 zones. Total floors traveled also increases (10,643 -> 12,386), meaning elevators work harder yet deliver worse service — a sign of inefficient positioning caused by over-assignment to already-loaded elevators.

### 3. Overlapping Zones Don't Help

Counterintuitively, overlap consistently makes things *worse or equal* at the same zone count:

| Config | Avg wait | p95 wait |
|---|---|---|
| 2-non-overlap | **44.4** | **224.1** |
| 2-overlap | 52.1 | 283.1 |
| 3-non-overlap | **81.8** | **468.1** |
| 3-overlap | 87.0 | 490.0 |
| 4-non-overlap | **142.9** | **697.1** |
| 4-overlap | 141.9 | 705.6 |

The overlap zone selection logic prefers zones containing both origin and destination, but this can assign passengers to a zone whose elevators are farther away or more loaded than the alternative. Overlap adds scheduling complexity without giving elevators any extra capacity.

### Summary

The data shows the core problem is **demand concentration vs. zone granularity**. A workday pattern front-loads traffic to low floors. With 2 zones, 6 elevators absorb that demand across a wider pool. Splitting into 4 zones locks 3 elevators into serving the hotspot, saturates them at 80%+, and strands 9 other elevators in idle zones — causing wait times and total times to nearly triple.
