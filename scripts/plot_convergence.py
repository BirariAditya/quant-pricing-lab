"""Plot the committed convergence experiment; requires the plots extra."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/convergence.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/convergence.png"))
    args = parser.parse_args()
    result = json.loads(args.input.read_text(encoding="utf-8"))
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    ):
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8), layout="constrained")
        for antithetic, label, color in (
            (False, "Plain sampling", "#2563eb"),
            (True, "Antithetic pairs", "#c2410c"),
        ):
            rows = [row for row in result["summaries"] if row["antithetic"] == antithetic]
            paths = [row["paths"] for row in rows]
            axes[0].loglog(paths, [row["rmse"] for row in rows], "o-", label=label, color=color)
            axes[1].loglog(
                paths,
                [row["mean_standard_error"] for row in rows],
                "o-",
                label=label,
                color=color,
            )
        axes[0].set_title("Observed error across 40 replications", loc="left", fontsize=11)
        axes[0].set_ylabel("Empirical RMSE (price units)")
        axes[1].set_title("Mean estimated sampling uncertainty", loc="left", fontsize=11)
        axes[1].set_ylabel("Estimated standard error (price units)")
        for ax in axes:
            ax.set_xlabel("Total payoff evaluations (paths)")
            ax.grid(True, which="major", alpha=0.2)
            ax.legend(frameon=False, fontsize=9)
        fig.suptitle("Monte Carlo precision at equal path budgets", fontsize=16, fontweight="bold")
        fig.supxlabel(
            "One ATM European call; S=K=100, T=1, r=5%, q=2%, volatility=20%. Seeds 0-39.\n"
            "Pair averages are the independent antithetic observations. Results are case-specific.",
            fontsize=9,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=180, facecolor="white")
        plt.close(fig)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
