import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
# pymc and bambi compile error fix
import pymc as pm
if not hasattr(pm, "compile_pymc"):
    pm.compile_pymc = None
import preliz as pz

from src.models import MODELS, build_model, generate_synthetic_covariates

"""
Running prior checks.

"""
CATEGORIES = [
    "0: Minimal (0-4)",
    "1: Mild (5-9)",
    "2: Moderate (10-14)",
    "3: Mod. Severe (15-19)",
    "4: Severe (20-27)",
]

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
    axes[2].set_title("Age-Group SD (1|age_group)\nExponential(1)")

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

    # create the synthetic data
    df_syn = generate_synthetic_covariates(n=1000, seed=42)

    # sample from priors of each model
    for model_name in MODELS:
        model = build_model(model_name, df_syn)
        model.build()
        # print model to check "threshold" priors created by Bambi
        print(f"\n BUILT MODEL: {model_name}")
        print(model)

        # sample from priors
        prior_idata = model.prior_predictive(draws=500, random_seed=42)
        y_prior = prior_idata.prior_predictive["y"].values[0]

        print(f"\nSIMULATED PHQ-9 ({model_name}):")
        for k, label in enumerate(CATEGORIES):
            shares = (y_prior == k).mean(axis=1)
            low, high = np.percentile(shares, [5, 95])
            print(f"  {label:<24} mean={shares.mean():.3f}  [90% CI: {low:.3f}, {high:.3f}]")

if __name__ == "__main__":
    run_prior_checks()