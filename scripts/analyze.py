"""Run turning-point detection on BBRI daily closes and print a phase summary."""

import pandas as pd

from turning_point_analysis.detector import detect_turning_points, summarize_phases
from turning_point_analysis.plotting import plot_phases

DATA_PATH = "bbri_stock_data.csv"


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["Date"]).set_index("Date")
    prices = df["Close"]

    phases = detect_turning_points(prices, window=20, min_phase_days=20, min_amplitude_pct=15.0)
    summary = summarize_phases(phases)

    print(summary.to_string(index=False))
    print()
    bull = summary[summary["regime"] == "bull"]
    bear = summary[summary["regime"] == "bear"]
    print(f"Bull phases: {len(bull)}, avg duration {bull['duration_days'].mean():.0f}d, "
          f"avg return {bull['return_pct'].mean():.1f}%")
    print(f"Bear phases: {len(bear)}, avg duration {bear['duration_days'].mean():.0f}d, "
          f"avg return {bear['return_pct'].mean():.1f}%")
    print(f"Current regime: {phases[-1].regime.value}")

    plot_phases(prices, phases, "phases.png")
    print("\nSaved plot to phases.png")


if __name__ == "__main__":
    main()
