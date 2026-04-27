from datetime import date, datetime, timedelta

import numpy as np
import pytest

from quando import Quando, SLE, SimulationResult


def test_same_day_is_one():
    w = Quando([(date(2024, 1, 5), date(2024, 1, 5))])
    assert w.lead_times == [1]


def test_multi_day():
    w = Quando([(date(2024, 1, 1), date(2024, 1, 5))])
    assert w.lead_times == [5]


def test_multiple_items():
    w = Quando([
        (date(2024, 1, 1), date(2024, 1, 3)),
        (date(2024, 1, 5), date(2024, 1, 5)),
        (date(2024, 1, 7), date(2024, 1, 10)),
    ])
    assert w.lead_times == [3, 1, 4]


def test_datetime_strips_time():
    w = Quando([(datetime(2024, 1, 1, 9, 0), datetime(2024, 1, 3, 17, 0))])
    assert w.lead_times == [3]


def test_percentile_known_values():
    # lead times 1..10
    items = [(date(2024, 1, 1), date(2024, 1, i)) for i in range(1, 11)]
    w = Quando(items)
    assert w.percentile(50) == 6   # ceil(5.5) = 6
    assert w.percentile(85) == 9   # ceil(8.65) = 9
    assert w.percentile(95) == 10  # ceil(9.55) = 10


def test_percentile_custom():
    items = [(date(2024, 1, 1), date(2024, 1, i)) for i in range(1, 11)]
    w = Quando(items)
    assert w.percentile(70) == 8   # ceil(7.3) = 8


def test_sle_is_named_tuple():
    items = [(date(2024, 1, 1), date(2024, 1, i)) for i in range(1, 11)]
    w = Quando(items)
    result = w.sle()
    assert isinstance(result, SLE)
    assert isinstance(result, tuple)


def test_sle_unpacks():
    items = [(date(2024, 1, 1), date(2024, 1, i)) for i in range(1, 11)]
    p50, p85, p95 = Quando(items).sle()
    assert p50 == 6
    assert p85 == 9
    assert p95 == 10


def test_sle_named_access():
    items = [(date(2024, 1, 1), date(2024, 1, i)) for i in range(1, 11)]
    result = Quando(items).sle()
    assert result.p50 == 6
    assert result.p85 == 9
    assert result.p95 == 10


def test_from_csv(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("started_at,finished_at\n2024-01-01,2024-01-05\n2024-01-03,2024-01-03\n")
    w = Quando.from_csv(csv)
    assert w.lead_times == [5, 1]


def test_from_csv_custom_columns(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("start,end\n2024-01-01,2024-01-03\n")
    w = Quando.from_csv(csv, started_col="start", finished_col="end")
    assert w.lead_times == [3]


def test_from_csv_with_datetime(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("started_at,finished_at\n2024-01-01 09:00:00,2024-01-03 17:00:00\n")
    w = Quando.from_csv(csv)
    assert w.lead_times == [3]


def test_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        Quando([])


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        Quando([(date(2024, 1, 5), date(2024, 1, 1))])


# --- throughput ---

def _items_with_throughput(daily_counts: list[int]) -> list[tuple[date, date]]:
    """Build items finishing on consecutive days with the given daily counts."""
    items = []
    base = date(2024, 1, 1)
    for offset, count in enumerate(daily_counts):
        d = base + timedelta(days=offset)
        for _ in range(count):
            items.append((d, d))
    return items


def test_throughput_shape():
    w = Quando(_items_with_throughput([3, 1, 2]))
    assert list(w.throughput) == [3, 1, 2]


def test_throughput_includes_zero_days():
    w = Quando(_items_with_throughput([2, 0, 3]))
    assert list(w.throughput) == [2, 0, 3]


# --- shared fixture ---

def _steady_quando() -> Quando:
    """Quando with consistent 2-items/day throughput for predictable simulations."""
    return Quando(_items_with_throughput([2] * 20))


# --- forecast_days ---

def test_forecast_days_returns_simulation_result():
    assert isinstance(_steady_quando().forecast_days(n_items=4), SimulationResult)


def test_forecast_days_distribution_length():
    result = _steady_quando().forecast_days(n_items=4, num_simulations=500)
    assert len(result.distribution) == 500


def test_forecast_days_values_are_positive():
    result = _steady_quando().forecast_days(n_items=4, num_simulations=200)
    assert (result.distribution >= 1).all()


def test_forecast_days_sle_ordering():
    result = _steady_quando().forecast_days(n_items=4, num_simulations=200)
    p50, p85, p95 = result.sle()
    assert p50 <= p85 <= p95


def test_forecast_days_seed_reproducible():
    w = _steady_quando()
    r1 = w.forecast_days(n_items=4, num_simulations=200, seed=42)
    r2 = w.forecast_days(n_items=4, num_simulations=200, seed=42)
    assert np.array_equal(r1.distribution, r2.distribution)


def test_forecast_days_invalid_n_items():
    with pytest.raises(ValueError):
        _steady_quando().forecast_days(n_items=0)


# --- forecast_items ---

def test_forecast_items_returns_simulation_result():
    assert isinstance(_steady_quando().forecast_items(n_days=5), SimulationResult)


def test_forecast_items_distribution_length():
    result = _steady_quando().forecast_items(n_days=5, num_simulations=500)
    assert len(result.distribution) == 500


def test_forecast_items_values_are_non_negative():
    result = _steady_quando().forecast_items(n_days=5, num_simulations=200)
    assert (result.distribution >= 0).all()


def test_forecast_items_sle_ordering():
    result = _steady_quando().forecast_items(n_days=10, num_simulations=200)
    p50, p85, p95 = result.sle()
    assert p50 <= p85 <= p95


def test_forecast_items_seed_reproducible():
    w = _steady_quando()
    r1 = w.forecast_items(n_days=5, num_simulations=200, seed=7)
    r2 = w.forecast_items(n_days=5, num_simulations=200, seed=7)
    assert np.array_equal(r1.distribution, r2.distribution)


def test_forecast_items_invalid_n_days():
    with pytest.raises(ValueError):
        _steady_quando().forecast_items(n_days=0)


# --- SimulationResult ---

def test_simulation_result_repr():
    result = _steady_quando().forecast_days(n_items=4, num_simulations=200, seed=1)
    r = repr(result)
    assert r.startswith("SimulationResult(")
    assert "p50=" in r
    assert "p85=" in r
    assert "p95=" in r
    assert "n=200" in r


def test_simulation_result_percentile_returns_int():
    result = _steady_quando().forecast_days(n_items=4, num_simulations=200)
    assert isinstance(result.percentile(85), int)


def test_simulation_result_distribution_is_ndarray():
    result = _steady_quando().forecast_items(n_days=5)
    assert isinstance(result.distribution, np.ndarray)
