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
    # 3 items on day 0, 1 item on day 1, 2 items on day 2
    w = Quando(_items_with_throughput([3, 1, 2]))
    tp = w.throughput
    assert list(tp) == [3, 1, 2]


def test_throughput_includes_zero_days():
    # items on day 0 and day 2 only — day 1 should be 0
    w = Quando(_items_with_throughput([2, 0, 3]))
    assert list(w.throughput) == [2, 0, 3]


# --- monte_carlo ---

def _steady_quando() -> Quando:
    """Quando with consistent 2-items/day throughput for predictable MCS."""
    return Quando(_items_with_throughput([2] * 20))


def test_monte_carlo_returns_simulation_result():
    result = _steady_quando().monte_carlo(n_items=4)
    assert isinstance(result, SimulationResult)


def test_monte_carlo_distribution_length():
    result = _steady_quando().monte_carlo(n_items=4, num_simulations=500)
    assert len(result.distribution) == 500


def test_monte_carlo_distribution_type():
    result = _steady_quando().monte_carlo(n_items=4)
    assert isinstance(result.distribution, np.ndarray)


def test_monte_carlo_values_are_positive():
    result = _steady_quando().monte_carlo(n_items=4, num_simulations=200)
    assert (result.distribution >= 1).all()


def test_monte_carlo_percentile_returns_int():
    result = _steady_quando().monte_carlo(n_items=4, num_simulations=200)
    assert isinstance(result.percentile(85), int)


def test_monte_carlo_sle_is_named_tuple():
    result = _steady_quando().monte_carlo(n_items=4, num_simulations=200)
    sle = result.sle()
    assert isinstance(sle, SLE)
    p50, p85, p95 = sle
    assert p50 <= p85 <= p95


def test_monte_carlo_seed_reproducible():
    w = _steady_quando()
    r1 = w.monte_carlo(n_items=4, num_simulations=200, seed=42)
    r2 = w.monte_carlo(n_items=4, num_simulations=200, seed=42)
    assert np.array_equal(r1.distribution, r2.distribution)


def test_monte_carlo_invalid_n_items():
    with pytest.raises(ValueError):
        _steady_quando().monte_carlo(n_items=0)
