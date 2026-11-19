import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
# pymc and bambi compile error fix
import pymc as pm
if not hasattr(pm, "compile_pymc"):
    pm.compile_pymc = None
import preliz as pz

from src.models import MODELS, build_model, generate_synthetic_covariates

"""Run prior predictive checks for the configured models."""

# Plot probability density curves for the priors, image to PDF format
def plot_prior_densities(out_dir: Path) -> None:
    # the same priors but using preliz variable for plotting
    prior_common = pz.Normal(mu=0.0, sigma=0.5)
    prior_sleep_sq = pz.Normal(mu=0.0, sigma=0.1)
    prior_hier_sd = pz.Exponential(lam=1.0)

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))

    prior_common.plot_pdf(ax=axes[0])
    axes[0].set_title("Linear Slopes (common)\nNormal(0, 0.5)")

    prior_sleep_sq.plot_pdf(ax=axes[1])
    axes[1].set_title("Quadratic Sleep I (sleep_c**2)\nNormal(0, 0.1)")

    prior_hier_sd.plot_pdf(ax=axes[2])
    axes[2].set_title("Cluster SD (1 | stratum_psu)\nExponential(1)")

    # save and plot
    plt.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_path = out_dir / "preliz_prior_predictive.png"
    plt.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"Preliz plots created: {plot_path}")



def run_prior_checks() -> None:
    # first plot the priors
    out_dir = Path("outputs")
    plot_prior_densities(out_dir)

    # Prior predictive checks use synthetic covariates, not observed outcomes.
    df_base = generate_synthetic_covariates(n=1000, seed=42)

    df_x = df_base.drop(
        columns=["y", "depression_binary", "depression_status_int", "phq_score"],
        errors="ignore",
    ).copy()
    # dummy "y" binary values to satisfy Bambi builder
    df_x["y"] = np.arange(len(df_x)) % 2

    # sample from priors of each model
    for name in MODELS:
        model = build_model(name, df_x)
        idata = model.prior_predictive(draws=500, random_seed=42)
        sim_prev = idata.prior_predictive["y"].values.mean(axis=-1).ravel()
        lo, hi = np.quantile(sim_prev, [0.05, 0.95])
        print(f"{name}: mean prior P(y=1) = {sim_prev.mean():.3f} (90% CI: [{lo:.3f}, {hi:.3f}])")

if __name__ == "__main__":
    run_prior_checks()