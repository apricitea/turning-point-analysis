"""Bull/bear turning-point detection via a Bry-Boschan-style censored local-extrema algorithm.

Reference: Pagan & Sossounov (2003), "A Simple Framework for Analysing Bull and Bear
Markets", Journal of Applied Econometrics — the standard approach for dating market
cycles: find local extrema over a window, then censor phases that are too short or
whose amplitude is too small, merging them into the neighboring phase.
"""

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


class Regime(Enum):
    BULL = "bull"
    BEAR = "bear"


@dataclass
class Phase:
    regime: Regime
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    start_price: float
    end_price: float

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days

    @property
    def return_pct(self) -> float:
        return (self.end_price / self.start_price - 1) * 100


def find_raw_turning_points(prices: pd.Series, window: int = 20) -> pd.Series:
    """Local maxima/minima over a trailing+leading window, as candidate turning points.

    Returns a Series indexed like `prices`, with +1 at local peaks, -1 at local
    troughs, and 0 elsewhere.
    """
    values = prices.to_numpy()
    peaks = argrelextrema(values, np.greater_equal, order=window)[0]
    troughs = argrelextrema(values, np.less_equal, order=window)[0]

    labels = pd.Series(0, index=prices.index)
    labels.iloc[peaks] = 1
    labels.iloc[troughs] = -1
    return labels


def _alternate(candidates: list[tuple[pd.Timestamp, float, int]]) -> list[tuple[pd.Timestamp, float, int]]:
    """Enforce strict peak/trough alternation, keeping the more extreme point
    whenever two same-type candidates appear consecutively."""
    if not candidates:
        return []

    result = [candidates[0]]
    for date, price, sign in candidates[1:]:
        last_date, last_price, last_sign = result[-1]
        if sign == last_sign:
            # Same type twice in a row: keep whichever is more extreme.
            if (sign == 1 and price >= last_price) or (sign == -1 and price <= last_price):
                result[-1] = (date, price, sign)
            # else: drop the new, weaker candidate.
        else:
            result.append((date, price, sign))
    return result


def detect_turning_points(
    prices: pd.Series,
    window: int = 20,
    min_phase_days: int = 20,
    min_amplitude_pct: float = 15.0,
) -> list[Phase]:
    """Detect bull/bear phases, censoring phases that are too short or too small.

    Parameters mirror the classic Bry-Boschan / Pagan-Sossounov censoring rules:
    a genuine market phase must last at least `min_phase_days` and move at least
    `min_amplitude_pct`, otherwise it's merged into its neighbors.
    """
    raw = find_raw_turning_points(prices, window=window)
    candidates = [
        (date, prices.loc[date], sign) for date, sign in raw.items() if sign != 0
    ]
    candidates = _alternate(candidates)

    # Always start from the series' actual first point so no data is discarded.
    if not candidates or candidates[0][0] != prices.index[0]:
        first_sign = -candidates[0][2] if candidates else 1
        candidates.insert(0, (prices.index[0], prices.iloc[0], first_sign))
    if candidates[-1][0] != prices.index[-1]:
        last_sign = -candidates[-1][2]
        candidates.append((prices.index[-1], prices.iloc[-1], last_sign))

    changed = True
    while changed and len(candidates) > 2:
        changed = False
        for i in range(1, len(candidates) - 1):
            date, price, sign = candidates[i]
            prev_date, prev_price, _ = candidates[i - 1]
            duration = (date - prev_date).days
            amplitude = abs(price / prev_price - 1) * 100
            if duration < min_phase_days or amplitude < min_amplitude_pct:
                del candidates[i]
                candidates = _alternate(candidates)
                changed = True
                break

    phases = []
    for i in range(len(candidates) - 1):
        start_date, start_price, start_sign = candidates[i]
        end_date, end_price, _ = candidates[i + 1]
        regime = Regime.BULL if start_sign == -1 else Regime.BEAR
        phases.append(Phase(regime, start_date, end_date, start_price, end_price))

    return phases


def summarize_phases(phases: list[Phase]) -> pd.DataFrame:
    rows = [
        {
            "regime": p.regime.value,
            "start": p.start_date.date(),
            "end": p.end_date.date(),
            "duration_days": p.duration_days,
            "return_pct": round(p.return_pct, 2),
        }
        for p in phases
    ]
    return pd.DataFrame(rows)
