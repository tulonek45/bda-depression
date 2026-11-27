"""Model evaluation: fits M0-M2 (or loads cached fits) and writes result tables.

1. Convergence: R-hat, bulk/tail ESS, divergences, max tree depth hits.
2. Posterior predictive checks: depression rate overall, by habit subgroup and
   by survey cluster, compared with data replicated from the posterior.
3. PSIS-LOO for each model and a rate-only baseline, pairwise differences and
   az.compare.
4. Prior sensitivity: M1 and M2 refit with every prior scale x0.5 and x2.
"""

import arviz as az
import bambi as bmb
import numpy as np
import pandas as pd

from src.config import DatasetConfig, CONFIG_PATH
from src.evaluation_io import IDATA_DIR, TABLE_DIR
from src.load import load_df, prepare_df, prepare_model_df
from src.models import MODELS, get_priors, prepare_bambi_df

SEED = 42
PPC_DRAWS = 1000
PRIOR_SCALES = (0.5, 2.0)
SENSITIVITY_MODELS = ("M1", "M2")


def load_data() -> pd.DataFrame:
    config = DatasetConfig.from_file(CONFIG_PATH)
    return prepare_model_df(prepare_df(load_df(config), config), config).reset_index(drop=True)


def scale_prior(prior: bmb.Prior, factor: float) -> bmb.Prior:
    """Multiply a prior's scale by `factor` (sigma times, Exponential rate divided)."""
    args = {}
    for key, value in prior.args.items():
        if isinstance(value, bmb.Prior):
            value = scale_prior(value, factor)
        elif key == "sigma":
            value = value * factor
        elif key == "lam":
            value = value / factor
        args[key] = value
    return bmb.Prior(prior.name, **args)


def fit(name: str, df: pd.DataFrame, args, prior_scale: float = 1.0):
    suffix = "" if prior_scale == 1.0 else f"_prior{prior_scale:g}"
    path = IDATA_DIR / f"{name}{suffix}.nc"
    if path.exists() and not args.refit:
        print(f"Loading cached fit {path}")
        return az.from_netcdf(path)

    print(f"Fitting {name} (prior scale x{prior_scale:g})")
    priors = {term: scale_prior(p, prior_scale) for term, p in get_priors(name).items()}
    model = bmb.Model(MODELS[name], prepare_bambi_df(df), family="bernoulli", priors=priors)
    idata = model.fit(draws=args.draws, tune=args.tune, chains=args.chains, cores=args.cores,
                      random_seed=SEED, target_accept=0.9, idata_kwargs={"log_likelihood": True})
    IDATA_DIR.mkdir(parents=True, exist_ok=True)
    idata.to_netcdf(path)
    return idata


def parameters(idata) -> list[str]:
    """Posterior variables, excluding per-observation quantities."""
    post = idata["posterior"]
    return [v for v in post.data_vars if "__obs__" not in post[v].dims]


def scalar_parameters(idata) -> list[str]:
    """Parameters with one value per draw (no per-cluster effects)."""
    return [v for v in parameters(idata) if idata["posterior"][v].ndim == 2]


def summary(idata, var_names=None) -> pd.DataFrame:
    return az.summary(idata, var_names=var_names or parameters(idata)).apply(pd.to_numeric)


# 1. Convergence -------------------------------------------------------------

def convergence(name: str, idata) -> dict:
    table = summary(idata)
    table.to_csv(TABLE_DIR / f"summary_{name}.csv")
    stats = idata["sample_stats"]
    return {
        "model": name,
        "max_r_hat": table["r_hat"].max(),
        "min_ess_bulk": table["ess_bulk"].min(),
        "min_ess_tail": table["ess_tail"].min(),
        "divergences": int(stats["diverging"].values.sum()),
        "max_treedepth_hits": int(stats["reached_max_treedepth"].values.sum()),
    }


# 2. Posterior predictive checks ---------------------------------------------

def pointwise_loglik(idata) -> np.ndarray:
    """Log-likelihood as (samples, observations)."""
    ll_group = idata["log_likelihood"]
    ll = ll_group[list(ll_group.data_vars)[0]].values
    return ll.reshape(-1, ll.shape[-1])


def replicate(idata, y: np.ndarray, rng) -> np.ndarray:
    """Replicated outcomes (draws, observations) from the posterior.

    P(y_i = 1) per draw follows from the Bernoulli log-likelihood:
    it is exp(ll) where y_i = 1 and 1 - exp(ll) where y_i = 0.
    """
    ll = pointwise_loglik(idata)
    ll = ll[rng.choice(len(ll), PPC_DRAWS, replace=False)]
    p = np.where(y == 1, np.exp(ll), -np.expm1(ll))
    return (rng.random(p.shape) < p).astype(np.int8)


def subgroups(df: pd.DataFrame) -> dict[str, pd.Series]:
    smoking = np.select([df["smoking_current"] == 1, df["smoking_former"] == 1], ["current", "former"], "never")
    return {
        "overall": pd.Series("all", index=df.index),
        "smoking": pd.Series(smoking, index=df.index),
        "vigorous_activity": df["vigorous_act"].map({0: "no", 1: "yes"}),
        "sleep": pd.cut(df["sleep_hours"], [0, 6, 7, 8, 9, 24], right=False,
                        labels=["<6h", "6-7h", "7-8h", "8-9h", ">=9h"]),
        "alcohol": pd.cut(df["alcohol_drinks_week"], [-1, 0, 7, 14, np.inf],
                          labels=["none", "0-7/wk", "7-14/wk", ">14/wk"]),
        "cluster": df["stratum_psu"],
    }


def ppc(name: str, df: pd.DataFrame, y: np.ndarray, y_rep: np.ndarray) -> tuple[pd.DataFrame, dict]:
    rows = []
    for variable, groups in subgroups(df).items():
        levels = groups.cat.categories if hasattr(groups, "cat") else sorted(groups.unique())
        for level in levels:
            mask = (groups == level).to_numpy()
            observed, replicated = y[mask].mean(), y_rep[:, mask].mean(axis=1)
            low, high = np.quantile(replicated, [0.05, 0.95])
            rows.append({"model": name, "variable": variable, "group": level, "n": mask.sum(),
                         "observed": observed, "rep_q05": low, "rep_q95": high,
                         "outside_90": not low <= observed <= high})
    rates = pd.DataFrame(rows)

    # Between-cluster SD of the rate: does the model reproduce how much the
    # rate varies between survey clusters? (ppp near 0 = spread under-predicted)
    codes = pd.factorize(df["stratum_psu"])[0]
    def cluster_sd(values):
        return pd.DataFrame(np.atleast_2d(values)).T.groupby(codes).mean().std(ddof=0).to_numpy()
    observed_sd, replicated_sd = cluster_sd(y)[0], cluster_sd(y_rep)
    clusters = rates[rates["variable"] == "cluster"]
    cluster_stat = {"model": name, "clusters_outside_90": int(clusters["outside_90"].sum()),
                    "n_clusters": len(clusters), "observed_sd": observed_sd,
                    "replicated_sd_mean": replicated_sd.mean(),
                    "ppp_sd": np.mean(replicated_sd >= observed_sd)}
    return rates, cluster_stat


# 3. LOO -----------------------------------------------------------------------

def loo(name: str, idata) -> tuple[dict, np.ndarray]:
    result = az.loo(idata, pointwise=True)
    k = np.asarray(result.pareto_k).ravel()
    row = {"model": name, "elpd_loo": result.elpd, "se": result.se, "p_loo": result.p,
           "max_pareto_k": k.max(), "n_pareto_k_gt_0.7": int((k > 0.7).sum())}
    return row, np.asarray(result.elpd_i).ravel()


def baseline_elpd(y: np.ndarray) -> np.ndarray:
    """Exact leave-one-out log score of predicting everyone with the overall rate."""
    rate = (y.sum() - y) / (len(y) - 1)
    return np.where(y == 1, np.log(rate), np.log1p(-rate))


def pairwise(elpd: dict, a: str, b: str) -> dict:
    diff = elpd[a] - elpd[b]
    return {"comparison": f"{a} - {b}", "elpd_diff": diff.sum(), "se": np.sqrt(len(diff) * diff.var())}


# 4. Prior sensitivity -------------------------------------------------------

def sensitivity(name: str, df: pd.DataFrame, base, args) -> pd.DataFrame:
    tables = []
    for scale, idata in [(1.0, base)] + [(s, fit(name, df, args, s)) for s in PRIOR_SCALES]:
        table = summary(idata, scalar_parameters(idata))[["mean", "sd"]]
        tables.append(table.assign(model=name, prior_scale=scale).rename_axis("term").reset_index())
    return pd.concat(tables)


def evaluate(args) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    df = load_data()
    y = df["y"].to_numpy()
    print(f"Participants: {len(df)}, depressed: {y.sum()} ({y.mean():.1%})")

    idatas = {name: fit(name, df, args) for name in MODELS}
    conv, rates, clusters, loo_rows, elpd = [], [], [], [], {}
    for name, idata in idatas.items():
        conv.append(convergence(name, idata))
        rate_table, cluster_stat = ppc(name, df, y, replicate(idata, y, rng))
        rates.append(rate_table)
        clusters.append(cluster_stat)
        row, elpd[name] = loo(name, idata)
        loo_rows.append(row)

    elpd["baseline"] = baseline_elpd(y)
    loo_rows.append({"model": "baseline", "elpd_loo": elpd["baseline"].sum()})

    pd.DataFrame(conv).to_csv(TABLE_DIR / "convergence.csv", index=False)
    pd.concat(rates).to_csv(TABLE_DIR / "ppc_rates.csv", index=False)
    pd.DataFrame(clusters).to_csv(TABLE_DIR / "ppc_clusters.csv", index=False)
    pd.DataFrame(loo_rows).to_csv(TABLE_DIR / "loo.csv", index=False)
    pd.DataFrame([pairwise(elpd, "M0", "baseline"), pairwise(elpd, "M1", "M0"),
                  pairwise(elpd, "M2", "M1")]).to_csv(TABLE_DIR / "loo_pairwise.csv", index=False)
    az.compare(idatas).to_csv(TABLE_DIR / "model_comparison.csv")

    if not args.skip_sensitivity:
        sens = [sensitivity(name, df, idatas[name], args) for name in SENSITIVITY_MODELS]
        pd.concat(sens).to_csv(TABLE_DIR / "prior_sensitivity.csv", index=False)

    print(f"Tables written to {TABLE_DIR}/")
