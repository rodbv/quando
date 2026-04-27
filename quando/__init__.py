from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple, Sequence

import numpy as np
import pandas as pd


class SLE(NamedTuple):
    p50: int
    p85: int
    p95: int


class Quando:
    def __init__(
        self,
        items: Sequence[tuple[date | datetime, date | datetime]],
    ) -> None:
        if not items:
            raise ValueError("items is empty")
        lead_times: list[int] = []
        for start, end in items:
            s = start.date() if isinstance(start, datetime) else start
            e = end.date() if isinstance(end, datetime) else end
            if e < s:
                raise ValueError(f"end {e} is before start {s}")
            lead_times.append((e - s).days + 1)
        self.lead_times = lead_times

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
        df[started_col] = pd.to_datetime(df[started_col], errors="coerce", format="mixed")
        df[finished_col] = pd.to_datetime(df[finished_col], errors="coerce", format="mixed")
        df = df.dropna(subset=[started_col, finished_col])
        df[started_col] = df[started_col].dt.normalize()
        df[finished_col] = df[finished_col].dt.normalize()
        items = list(zip(df[started_col].dt.date, df[finished_col].dt.date))
        return cls(items)

    def percentile(self, p: float) -> int:
        return int(math.ceil(float(np.percentile(self.lead_times, p))))

    def sle(self) -> SLE:
        return SLE(
            p50=self.percentile(50),
            p85=self.percentile(85),
            p95=self.percentile(95),
        )
