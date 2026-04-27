6# quando

[![CI](https://github.com/rodbv/quando/actions/workflows/ci.yml/badge.svg)](https://github.com/rodbv/quando/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Kanban flow metrics for Python. Answers the eternal question: **"quando vai ficar pronto?"** — *when will it be done?*

`quando` computes [Service Level Expectations (SLE)](https://kanbanguides.org/) from your team's historical delivery data: given a list of work item start/end dates, it tells you at what percentile a single item will be finished.

> This library was built to support the talk [**"Quando vai ficar pronto?"**](https://github.com/rodbv/quando-vai-ficar-pronto), which walks through SLE and Monte Carlo forecasting for software teams using kanban.

---

## Installation

```bash
pip install quando-forecast
```

## Quick start

```python
from datetime import date
from quando import Quando

items = [
    (date(2024, 1,  1), date(2024, 1,  3)),  # 3 days
    (date(2024, 1,  5), date(2024, 1,  5)),  # 1 day  (same-day delivery)
    (date(2024, 1,  8), date(2024, 1, 14)),  # 7 days
    # ... more historical items
]

w = Quando(items)

w.percentile(85)   # → int: 85% of items finish within this many days
w.percentile(50)   # → int: median lead time

sle = w.sle()      # → SLE(p50=..., p85=..., p95=...)
sle.p85            # → int: named access
p50, p85, p95 = sle  # or unpack as a tuple
```

### Loading from a CSV

```python
w = Quando.from_csv("delivery_data.csv")
```

The CSV is expected to have `started_at` and `finished_at` columns (header is optional). Both date (`2024-01-15`) and datetime (`2024-01-15 09:00:00`) formats are accepted.

```csv
started_at,finished_at
2024-01-01,2024-01-03
2024-01-05,2024-01-05
2024-01-08,2024-01-14
```

Custom column names are supported:

```python
w = Quando.from_csv("export.csv", started_col="start_date", finished_col="end_date")
```

---

## API

### `Quando(items)`

Constructs a flow dataset from a sequence of `(start, end)` tuples.

- `start` and `end` can be `datetime.date` or `datetime.datetime` (time component is ignored)
- Raises `ValueError` if `items` is empty or any tuple has `end < start`

### `Quando.from_csv(path, *, started_col="started_at", finished_col="finished_at")`

Constructs from a CSV file. Handles mixed date/datetime formats and drops unparseable rows.

### `.lead_times -> list[int]`

The computed lead time in calendar days for each item (`end - start + 1`, so a same-day item = 1).

### `.percentile(p: float) -> int`

Returns the `p`-th percentile of the lead time distribution, ceiling-rounded. `p` is 0–100 (e.g. `85`, not `0.85`).

### `.sle() -> SLE`

Returns an `SLE(p50, p85, p95)` named tuple — the three standard confidence thresholds for a kanban SLE commitment. Can be unpacked or accessed by name.

---

## What is SLE?

A **Service Level Expectation** is a probabilistic commitment: *"X% of our work items finish within N days."*

```
"Our SLE is 7 days @ 85% confidence"
→ 85% of items in our history finished in 7 days or fewer.
```

P85 is the recommended default for external commitments: it gives a 15% error rate by design, which is honest and achievable. P50 (median) is useful internally; P95 is for high-stakes items.

---

## Related

- [**quando-vai-ficar-pronto**](https://github.com/rodbv/quando-vai-ficar-pronto) — the companion talk and Jupyter notebook that demonstrates SLE and Monte Carlo forecasting end-to-end

---

## License

[MIT](LICENSE)
