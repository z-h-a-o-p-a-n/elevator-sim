"""Tests for stats computation."""

import pytest

from elevator_sim.models.passenger import Passenger
from elevator_sim.stats import compute_stats


def _make_passenger(wait: int, total: int) -> Passenger:
    p = Passenger(id="x", origin=1, destination=5, request_time=0)
    p.board_time = wait
    p.arrive_time = total
    return p


def test_basic_stats():
    passengers = [_make_passenger(2, 5), _make_passenger(4, 9), _make_passenger(6, 11)]
    stats = compute_stats(passengers)
    assert stats.min_wait == 2
    assert stats.max_wait == 6
    assert stats.avg_wait == pytest.approx(4.0)
    assert stats.min_total == 5
    assert stats.max_total == 11


def test_single_passenger():
    passengers = [_make_passenger(3, 7)]
    stats = compute_stats(passengers)
    assert stats.min_wait == stats.max_wait == 3
    assert stats.p95_wait == pytest.approx(3.0)


def test_no_completed_passengers_raises():
    p = Passenger(id="x", origin=1, destination=5, request_time=0)
    with pytest.raises(ValueError):
        compute_stats([p])
