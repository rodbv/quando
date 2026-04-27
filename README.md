# quando

See the `justfile` for common development commands (setup, testing, linting, etc.) using uv. Install just with `uv pip install just` if needed.
# quando

[![CI](https://github.com/rodbv/quando/actions/workflows/ci.yml/badge.svg)](https://github.com/rodbv/quando/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/quando-forecast.svg)](https://pypi.org/project/quando-forecast/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Kanban flow metrics for Python. Answers the eternal question: **"quando vai ficar pronto?"** — *when will it be done?*

`quando` computes [Service Level Expectations (SLE)](https://kanbanguides.org/) and Monte Carlo forecasts from your team's historical delivery data.

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

# Historical delivery data: list of (start_date, end_date) tuples
items = [
    (date(2024, 1,  1), date(2024, 1,  3)),  # 3 days
    (date(2024, 1,  5), date(2024, 1,  5)),  # 1 day (same-day delivery)
    (date(2024, 1,  8), date(2024, 1, 14)),  # 7 days
    # ... more historical items
]

w = Quando(items)
```

### SLE — how long does one item take?

```python
w.percentile(85)   # → int: 85% of items finish within this many days
w.percentile(50)   # → int: median lead time

sle = w.sle()      # → SLE(p50=3, p85=7, p95=9)
sle.p85            # → int: named access
p50, p85, p95 = sle  # or unpack as a tuple
```

### Monte Carlo — forecasting multiple items

```python
# How many days to deliver 10 items?
result = w.forecast_days(n_items=10)
result.percentile(85)  # → int: days needed with 85% confidence
result.sle()           # → SLE(p50=..., p85=..., p95=...)
result.distribution    # → np.ndarray of raw simulation results (for plotting)

# How many items fit in a 2-week sprint?
result = w.forecast_items(n_days=10)
result.percentile(50)  # → int: median items delivered in 10 days
```

Both methods accept `num_simulations` (default `10_000`) and `seed` for reproducibility:

```python
result = w.forecast_days(n_items=10, num_simulations=50_000, seed=42)
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
- Lead time is counted in **calendar days** inclusive: same-day = 1, Mon→Fri = 5
- Raises `ValueError` if `items` is empty or any tuple has `end < start`

### `Quando.from_csv(path, *, started_col="started_at", finished_col="finished_at")`

Constructs from a CSV file. Handles mixed date/datetime formats and drops unparseable rows.

### `.lead_times -> list[int]`

The computed lead time in calendar days for each item.

### `.throughput -> np.ndarray`

Items delivered per calendar day across the full date range, including zero-throughput days. Used internally by the Monte Carlo methods.

### `.percentile(p: float) -> int`

Returns the `p`-th percentile of the lead time distribution, ceiling-rounded. `p` is 0–100 (e.g. `85`, not `0.85`).

### `.sle() -> SLE`

Returns `SLE(p50, p85, p95)` — the three standard confidence thresholds. Can be unpacked or accessed by name (`.p50`, `.p85`, `.p95`).

### `.forecast_days(n_items, *, num_simulations=10_000, seed=None) -> SimulationResult`

Monte Carlo simulation: given `n_items` to deliver, returns the distribution of how many days it will take. Samples from the historical daily throughput distribution, accumulating until `n_items` are done.

### `.forecast_items(n_days, *, num_simulations=10_000, seed=None) -> SimulationResult`

Monte Carlo simulation: given a fixed `n_days` window, returns the distribution of how many items can be delivered. Useful for sprint planning.

### `SimulationResult`

Returned by both forecast methods.

| Attribute / Method | Description |
|--------------------|-------------|
| `.distribution` | `np.ndarray` of raw simulation results — use for histograms or custom analysis |
| `.percentile(p)` | `p`-th percentile of the simulation, ceiling-rounded |
| `.sle()` | Convenience `SLE(p50, p85, p95)` from the simulation |

```python
repr(result)
# SimulationResult(p50=8, p85=12, p95=15, n=10000)
```

---

## What is SLE?

A **Service Level Expectation** is a probabilistic commitment based on past performance: *"X% of our work items finish within N days."*

```
"Our SLE is 7 days @ 85% confidence"
→ 85% of items in our history finished in 7 days or fewer.
```

P85 is the recommended default for external commitments — it gives a 15% error rate by design, which is honest and achievable. P50 is useful internally; P95 for high-stakes items.

## What is Monte Carlo forecasting?

Monte Carlo simulation answers questions about groups of items by repeatedly sampling from your historical throughput distribution. Each run simulates a possible future; after thousands of runs, the distribution of outcomes tells you the probability of hitting a deadline.

- **`forecast_days(n_items=10)`** → "With 85% confidence, 10 items will take N days"
- **`forecast_items(n_days=10)`** → "With 85% confidence, we'll deliver N items in a 2-week sprint"

Zero-throughput days (weekends, interruptions) are included in the sampling pool, which produces honest, conservative estimates.

---

## Related

- [**quando-vai-ficar-pronto**](https://github.com/rodbv/quando-vai-ficar-pronto) — the companion talk and Jupyter notebook that demonstrates SLE and Monte Carlo forecasting end-to-end

---

## License

[MIT](LICENSE)
