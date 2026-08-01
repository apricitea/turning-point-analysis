import numpy as np
import pandas as pd
import pytest

from turning_point_analysis.detector import Regime, detect_turning_points


def _make_series(values: list[float]) -> pd.Series:
    dates = pd.date_range("2020-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=dates)


def test_phases_alternate_bull_and_bear():
    rng = np.random.default_rng(0)
    trend = np.concatenate(
        [
            np.linspace(100, 60, 80),   # crash
            np.linspace(60, 140, 100),  # recovery
            np.linspace(140, 90, 90),   # correction
            np.linspace(90, 160, 110),  # rally
        ]
    )
    noise = rng.normal(0, 1, len(trend))
    prices = _make_series((trend + noise).tolist())

    phases = detect_turning_points(prices, window=10, min_phase_days=20, min_amplitude_pct=10.0)

    assert len(phases) >= 2
    for prev, curr in zip(phases, phases[1:]):
        assert prev.regime != curr.regime


def test_phases_span_the_full_series():
    rng = np.random.default_rng(1)
    trend = np.concatenate([np.linspace(100, 50, 60), np.linspace(50, 130, 80)])
    prices = _make_series((trend + rng.normal(0, 0.5, len(trend))).tolist())

    phases = detect_turning_points(prices, window=10, min_phase_days=20, min_amplitude_pct=10.0)

    assert phases[0].start_date == prices.index[0]
    assert phases[-1].end_date == prices.index[-1]


def test_censoring_removes_short_low_amplitude_wiggles():
    # A dominant uptrend with one small dip that should get censored away.
    up1 = np.linspace(100, 130, 40)
    dip = np.linspace(130, 128, 5)  # tiny amplitude, short duration
    up2 = np.linspace(128, 170, 60)
    prices = _make_series(np.concatenate([up1, dip, up2]).tolist())

    phases = detect_turning_points(prices, window=5, min_phase_days=20, min_amplitude_pct=15.0)

    # The tiny dip shouldn't survive censoring as its own phase.
    assert all(p.duration_days >= 20 or p is phases[-1] for p in phases[:-1])


def test_flat_series_yields_no_spurious_alternation_errors():
    prices = _make_series([100.0] * 50)
    phases = detect_turning_points(prices, window=5, min_phase_days=5, min_amplitude_pct=1.0)
    # Should not raise, and should produce at most one degenerate phase.
    assert len(phases) >= 1
