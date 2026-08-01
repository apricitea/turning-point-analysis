import matplotlib.pyplot as plt
import pandas as pd

from turning_point_analysis.detector import Phase, Regime


def plot_phases(prices: pd.Series, phases: list[Phase], out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(prices.index, prices.values, color="black", linewidth=0.8)

    for phase in phases:
        color = "#2ca02c" if phase.regime == Regime.BULL else "#d62728"
        ax.axvspan(phase.start_date, phase.end_date, color=color, alpha=0.15)

    ax.set_title("BBRI — Detected Bull/Bear Phases")
    ax.set_ylabel("Close price (IDR)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
