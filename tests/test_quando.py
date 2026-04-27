from datetime import date, datetime

import pytest

from quando import Quando, SLE


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
