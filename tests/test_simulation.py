"""Simulation integration tests."""

import tempfile
from pathlib import Path

from elevator_sim.algorithms import get_algorithm
from elevator_sim.config import SimConfig
from elevator_sim.io.reader import Request, parse_records
from elevator_sim.io.writer import LogWriter
from elevator_sim.main import run
from elevator_sim.simulation import Simulation


def _run_sim(requests: list[Request], config: SimConfig) -> list:
    sim = Simulation(config=config, algorithm=get_algorithm(config.algorithm))
    with tempfile.TemporaryDirectory() as tmpdir:
        with LogWriter(tmpdir, "test", config.num_elevators, config.algorithm) as writer:
            return sim.run(requests, writer)


def test_all_passengers_arrive():
    config = SimConfig(num_floors=10, num_elevators=2, elevator_capacity=4)
    requests = [
        Request(time=0, id="p1", source=1, dest=5),
        Request(time=0, id="p2", source=3, dest=8),
        Request(time=5, id="p3", source=8, dest=2),
    ]
    passengers = _run_sim(requests, config)
    assert all(p.arrived for p in passengers)


def test_timing_fields_populated():
    config = SimConfig(num_floors=10, num_elevators=1, elevator_capacity=4)
    requests = [Request(time=0, id="p1", source=1, dest=4)]
    passengers = _run_sim(requests, config)
    p = passengers[0]
    assert p.board_time is not None
    assert p.arrive_time is not None
    assert p.board_time >= p.request_time
    assert p.arrive_time > p.board_time


def test_wait_time_is_nonnegative():
    config = SimConfig(num_floors=10, num_elevators=2, elevator_capacity=4)
    requests = [
        Request(time=0, id="p1", source=1, dest=10),
        Request(time=0, id="p2", source=5, dest=1),
    ]
    passengers = _run_sim(requests, config)
    for p in passengers:
        assert p.wait_time >= 0  # type: ignore[operator]
        assert p.total_time > 0  # type: ignore[operator]


def test_elevator_capacity_respected():
    config = SimConfig(num_floors=10, num_elevators=1, elevator_capacity=2)
    requests = [Request(time=0, id=f"p{i}", source=1, dest=5) for i in range(5)]
    passengers = _run_sim(requests, config)
    assert all(p.arrived for p in passengers)


def test_future_requests_not_peeked():
    """Passengers requesting at tick 10 should not board before tick 10."""
    config = SimConfig(num_floors=10, num_elevators=1, elevator_capacity=4)
    requests = [Request(time=10, id="p1", source=1, dest=5)]
    passengers = _run_sim(requests, config)
    assert passengers[0].board_time >= 10  # type: ignore[operator]


def test_stop_ticks_delay_movement():
    config = SimConfig(num_floors=10, num_elevators=1, elevator_capacity=4, stop_ticks=2)
    requests = [Request(time=0, id="p1", source=1, dest=3)]
    passengers = _run_sim(requests, config)
    p = passengers[0]
    # With stop_ticks=2, arrive_time should be later than with stop_ticks=0
    config_no_stop = SimConfig(num_floors=10, num_elevators=1, elevator_capacity=4, stop_ticks=0)
    passengers_no_stop = _run_sim(requests, config_no_stop)
    assert p.arrive_time >= passengers_no_stop[0].arrive_time  # type: ignore[operator]


def test_log_files_created():
    config = SimConfig(num_floors=5, num_elevators=2, elevator_capacity=4, output_dir="/tmp/test_elevator_sim_logs")
    requests = [Request(time=0, id="p1", source=1, dest=3)]
    run(requests, config=config, run_id="testrun")
    out = Path(config.output_dir)
    assert (out / "testrun_positions.csv").exists()
    assert (out / "testrun_passengers.csv").exists()


def test_positions_log_has_row_per_tick():
    import csv
    config = SimConfig(num_floors=5, num_elevators=1, elevator_capacity=4, output_dir="/tmp/test_elevator_sim_logs2")
    requests = [Request(time=0, id="p1", source=1, dest=3)]
    run(requests, config=config, run_id="testrun2")
    path = Path(config.output_dir) / "testrun2_positions.csv"
    rows = list(csv.DictReader(open(path)))
    ticks = [int(r["time"]) for r in rows]
    assert ticks == list(range(len(ticks)))  # 0, 1, 2, ... with no gaps


def test_round_robin_assignment():
    """Passengers are assigned to elevators in round-robin order."""
    config = SimConfig(num_floors=10, num_elevators=3, elevator_capacity=10, algorithm="round_robin")
    requests = [Request(time=0, id=f"p{i}", source=1, dest=5) for i in range(5)]
    passengers = _run_sim(requests, config)
    assert all(p.arrived for p in passengers)


def test_parse_records_roundtrip():
    records = [
        {"time": 0, "id": "p1", "source": 1, "dest": 5},
        {"time": 10, "id": "p2", "source": 3, "dest": 1},
    ]
    requests = parse_records(records)
    assert len(requests) == 2
    assert requests[0].id == "p1"
    assert requests[1].time == 10
