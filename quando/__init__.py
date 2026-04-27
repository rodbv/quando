from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple, Sequence

import numpy as np
import pandas as pd

__version__ = "0.1.0"
__all__ = ["Quando", "SLE", "SimulationResult"]


class SLE(NamedTuple):
    p50: int
    p85: int
    p95: int


class SimulationResult:
    """Result of a Monte Carlo simulation. Holds the raw distribution and
    exposes percentile queries consistent with Quando.percentile()."""

    def __init__(self, distribution: np.ndarray) -> None:
        self.distribution = distribution

    def percentile(self, p: float) -> int:
        return int(math.ceil(float(np.percentile(self.distribution, p))))

    def sle(self) -> SLE:
        return SLE(
            p50=self.percentile(50),
            p85=self.percentile(85),
            p95=self.percentile(95),
        )

    def __repr__(self) -> str:
        s = self.sle()
        return (
            f"SimulationResult(p50={s.p50}, p85={s.p85}, p95={s.p95},"
            f" n={len(self.distribution)})"
        )


class Quando:
    def __init__(
        self,
        items: Sequence[tuple[date | datetime | str, date | datetime | str]],
    ) -> None:
        if not items:
            raise ValueError("items is empty")
        lead_times: list[int] = []
        end_dates: list[date] = []
        for start, end in items:
            # Accept string, date, or datetime
            s = self._parse_date(start)
            e = self._parse_date(end)
            if e < s:
                raise ValueError(f"end {e} is before start {s}")
            lead_times.append((e - s).days + 1)
            end_dates.append(e)
        self.lead_times = lead_times
        self._end_dates = end_dates

    @staticmethod
    def _parse_date(val: date | datetime | str) -> date:
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            # Try parsing as date or datetime string
            try:
                return datetime.fromisoformat(val).date()
            except ValueError:
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError(f"Could not parse date string: {val}")
        raise TypeError(f"Unsupported type for date: {type(val)}")

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        *,
        started_col: str = "started_at",
        finished_col: str = "finished_at",
    ) -> "Quando":
        df = pd.read_csv(
            path,
            header=None,
            names=[started_col, finished_col],
            usecols=[0, 1],
        )
        df[started_col] = pd.to_datetime(
            df[started_col], errors="coerce", format="mixed"
        )
        df[finished_col] = pd.to_datetime(
            df[finished_col], errors="coerce", format="mixed"
        )
        df = df.dropna(subset=[started_col, finished_col])
        df[started_col] = df[started_col].dt.normalize()
        df[finished_col] = df[finished_col].dt.normalize()
        items = list(zip(df[started_col].dt.date, df[finished_col].dt.date))
        return cls(items)

    @property
    def throughput(self) -> np.ndarray:
        """Items finished per calendar day, including zero-throughput days."""
        finished = pd.Series(pd.to_datetime(self._end_dates))
        days = pd.date_range(finished.min(), finished.max(), freq="D")
        return (
            finished.value_counts()
            .sort_index()
            .reindex(days, fill_value=0)
            .to_numpy(dtype=int)
        )

    def percentile(self, p: float) -> int:
        return int(math.ceil(float(np.percentile(self.lead_times, p))))

    def sle(self) -> SLE:
        return SLE(
            p50=self.percentile(50),
            p85=self.percentile(85),
            p95=self.percentile(95),
        )

    def forecast_days(
        self,
        n_items: int,
        *,
        num_simulations: int = 10_000,
        seed: int | None = None,
    ) -> SimulationResult:
        """Simulate how many days to deliver n_items, based on historical throughput."""
        if n_items < 1:
            raise ValueError("n_items must be >= 1")
        tp = self.throughput
        rng = np.random.default_rng(seed)
        results = np.empty(num_simulations, dtype=int)
        for i in range(num_simulations):
            done = 0
            days = 0
            while done < n_items:
                done += int(rng.choice(tp))
                days += 1
            results[i] = days
        return SimulationResult(results)

    def forecast_items(
        self,
        n_days: int,
        *,
        num_simulations: int = 10_000,
        seed: int | None = None,
    ) -> SimulationResult:
        """Simulate how many items can be delivered within n_days."""
        if n_days < 1:
            raise ValueError("n_days must be >= 1")
        tp = self.throughput
        rng = np.random.default_rng(seed)
        results = (
            rng.choice(tp, size=(num_simulations, n_days), replace=True)
            .sum(axis=1)
            .astype(int)
        )
        return SimulationResult(results)
