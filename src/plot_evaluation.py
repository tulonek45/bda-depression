"""Evaluation figures from the cached fits and evaluation tables."""
import arviz as az
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.evaluation_io import FIGURE_DIR, IDATA_DIR, TABLE_DIR
from src.models import MODELS


def plot_traces(name: str) -> None:
    idata = az.from_netcdf(IDATA_DIR / f"{name}.nc")
    post = idata["posterior"]
    scalars = [v for v in post.data_vars if post[v].ndim == 2]
    az.plot_trace_dist(idata, var_names=scalars).savefig(FIGURE_DIR / f"trace_{name}.png")


def plot_ppc(name: str, rates: pd.DataFrame) -> None:
    rates = rates[rates["model"] == name]
    subgroups = rates[rates["variable"] != "cluster"].reset_index(drop=True)
    clusters = rates[rates["variable"] == "cluster"].sort_values("observed").reset_index(drop=True)

    fig, (left, right) = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)
    pos = np.arange(len(subgroups))[::-1]
    left.hlines(pos, subgroups["rep_q05"], subgroups["rep_q95"], color="0.6", lw=3, label="replicated 90%")
    left.plot(subgroups["observed"], pos, "o", color="black", label="observed")
    left.set_yticks(pos, subgroups["variable"] + ": " + subgroups["group"])
    left.set_xlabel("depression rate")
    left.legend(loc="lower right")

    x = np.arange(len(clusters))
    right.vlines(x, clusters["rep_q05"], clusters["rep_q95"], color="0.6", lw=3)
    right.plot(x, clusters["observed"], "o", color="black")
    right.set_xticks(x, clusters["group"], rotation=90, fontsize=7)
    right.set_ylabel("depression rate")
    right.set_title(f"Survey clusters ({clusters['outside_90'].sum()}/{len(clusters)} outside 90%)")

    fig.suptitle(f"{name}: posterior predictive checks")
    fig.savefig(FIGURE_DIR / f"ppc_{name}.png", dpi=120)
    plt.close(fig)


def plot_sensitivity(sens: pd.DataFrame) -> None:
    for name, table in sens.groupby("model"):
        terms = table.loc[table["prior_scale"] == 1, "term"].tolist()
        fig, ax = plt.subplots(figsize=(7, 0.45 * len(terms) + 1.5), constrained_layout=True)
        for offset, (scale, group) in zip([-0.2, 0, 0.2], table.groupby("prior_scale")):
            group = group.set_index("term").loc[terms]
            pos = np.arange(len(terms))[::-1] + offset
            ax.errorbar(group["mean"], pos, xerr=group["sd"], fmt="o", label=f"prior scale x{scale:g}")
        ax.axvline(0, color="0.5", lw=1)
        ax.set_yticks(np.arange(len(terms))[::-1], terms)
        ax.set_xlabel("posterior mean ± sd (log-odds)")
        ax.set_title(f"{name}: prior sensitivity")
        ax.legend()
        fig.savefig(FIGURE_DIR / f"prior_sensitivity_{name}.png", dpi=120)
        plt.close(fig)


def plot_loo_metrics(metrics: pd.DataFrame) -> None:
    models = metrics[metrics["model"] != "baseline"].reset_index(drop=True)
    null_brier = metrics.loc[metrics["model"] == "baseline", "brier_null"].iloc[0]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    y_pos = np.arange(len(models))[::-1]

    axes[0].plot(models["auc"], y_pos, "o", color="black")
    axes[0].axvline(0.5, color="0.6", ls="--", lw=1)
    axes[0].set_yticks(y_pos, models["model"])
    axes[0].set_xlabel("LOO AUC")
    axes[0].set_title("Discrimination")

    axes[1].plot(models["brier"], y_pos, "o", color="black")
    axes[1].axvline(null_brier, color="0.6", ls="--", lw=1, label="null Brier")
    axes[1].set_yticks(y_pos, models["model"])
    axes[1].set_xlabel("LOO Brier score")
    axes[1].set_title("Overall accuracy")
    axes[1].legend(loc="best")

    axes[2].plot(models["cal_slope"], y_pos, "o", color="black", label="slope")
    axes[2].plot(models["cal_intercept"], y_pos, "s", color="0.5", label="intercept")
    axes[2].axvline(1.0, color="0.6", ls="--", lw=1)
    axes[2].axvline(0.0, color="0.6", ls=":", lw=1)
    axes[2].set_yticks(y_pos, models["model"])
    axes[2].set_xlabel("Calibration parameter")
    axes[2].set_title("Calibration (target: 0 & 1)")
    axes[2].legend(loc="best")

    fig.savefig(FIGURE_DIR / "loo_metrics.png", dpi=120)
    plt.close(fig)


def plot_evaluation(include_sensitivity: bool = True) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    rates = pd.read_csv(TABLE_DIR / "ppc_rates.csv")
    for name in MODELS:
        plot_traces(name)
        plot_ppc(name, rates)

    comparison = pd.read_csv(TABLE_DIR / "model_comparison.csv", index_col=0)
    pc = az.plot_compare(comparison)
    pc.savefig(FIGURE_DIR / "model_comparison.png", dpi=120, bbox_inches="tight")
    plt.close("all")

    sensitivity_path = TABLE_DIR / "prior_sensitivity.csv"
    if include_sensitivity:
        plot_sensitivity(pd.read_csv(sensitivity_path))

    loo_metrics_path = TABLE_DIR / "loo_metrics.csv"
    if loo_metrics_path.exists():
        plot_loo_metrics(pd.read_csv(loo_metrics_path))
        
    print(f"Figures written to {FIGURE_DIR}/")
