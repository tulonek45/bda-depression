"""Collect the evaluation tables into summary.md."""
import pandas as pd
from pathlib import Path

from src.evaluation_io import TABLE_DIR, SUMMARY_PATH


def section(title: str, table: pd.DataFrame, note: str = "") -> str:
    return f"## {title}\n\n{note}\n\n```\n{table.to_string(index=False)}\n```\n"


def report_evaluation(include_sensitivity: bool = True) -> None:
    read = lambda name: pd.read_csv(TABLE_DIR / f"{name}.csv")
    rates = read("ppc_rates")

    pairwise = read("loo_pairwise")
    pairwise["clear"] = (pairwise["elpd_diff"].abs() > 4) & (pairwise["elpd_diff"].abs() > 2 * pairwise["se"])

    parts = [
        "# Model evaluation\n",
        section("1. Convergence", read("convergence"),
                "Targets: R-hat <= 1.01, ESS >= 400, no divergences or max tree depth hits."),
        section("2. Posterior predictive checks: subgroups outside the 90% interval",
                rates[rates["outside_90"] & (rates["variable"] != "cluster")],
                "About 1 in 10 groups falls outside by chance."),
        section("2. Posterior predictive checks: survey clusters", read("ppc_clusters"),
                "About 3 of 30 clusters fall outside by chance. ppp_sd near 0 means the model "
                "under-predicts how much the rate varies between clusters."),
        section("3. PSIS-LOO", read("loo"), "Pareto k > 0.7 would make LOO unreliable."),
        section("3. LOO predictive metrics", read("loo_metrics").round(3),
                "Out-of-sample AUC, Brier score vs. null rate, and logistic calibration intercept (target 0) and slope (target 1)."),
        section("3. Pairwise elpd differences", pairwise,
                "Clear when |elpd_diff| > 4 and > 2 SE. M1 - M0: do habits help? M2 - M1: do clusters help?"),
        section("3. az.compare", read("model_comparison").rename(columns={"Unnamed: 0": "model"})),
    ]
    if include_sensitivity:
        sens = read("prior_sensitivity")
        base = sens[sens["prior_scale"] == 1].set_index(["model", "term"])
        sens["shift_in_sd"] = [(r["mean"] - base.loc[(r["model"], r["term"]), "mean"])
                               / base.loc[(r["model"], r["term"]), "sd"] for _, r in sens.iterrows()]
        table = sens.pivot_table(index=["model", "term"], columns="prior_scale", values="mean")
        table["max_abs_shift_in_sd"] = sens.groupby(["model", "term"])["shift_in_sd"].apply(lambda s: s.abs().max())
        parts.append(section("4. Prior sensitivity: posterior means by prior scale", table.round(3).reset_index(),
                             "Shifts above about 0.5 posterior SD are worth discussing."))

    nadir_path = TABLE_DIR / "sleep_nadir.csv"
    if nadir_path.exists():
        nadir = pd.read_csv(nadir_path)
        if not nadir.empty:
            parts.append(section("5. Sleep nadir (hours, 89% credible interval)", nadir.round(2),
                                 "Estimated minimum-risk sleep duration 7.5 - b1 / (2 * b2) for models with linear and quadratic sleep terms."))

    text = "\n".join(parts)
    SUMMARY_PATH.write_text(text)
    print(text)
