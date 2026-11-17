import numpy as np
import numpy.random as rng
import pandas as pd
import pymc as pm
import bambi as bmb

# from src.load import prepare_df, load_df

"""
The blueprint file for running the models.
Fetch the pandas Dataframe from src.load.

"""
# TODO verify the preprocessed df, Bambi creates the z-standardized columns ???
# - BMI ???
# - how is smoking handled ???
# - sedentary ???

# Baseline attributes (control variables)
# assumes new, preprocessed z-standardized columns (data contract) 
CONTROL_COLS = ["age_z", "gender_female", "income_z"]
# Habit attributes (predictors)
HABIT_COLS = [
    "vigorous_act",
    "sedentary_z",
    "alcohol_z",
    "sleep_c",
    "smoking_former",
    "smoking_current",
]


MODELS = {
    # baseline model: control
    "M0": "y ~ age_z + gender_female + income_z",
    # linear + non-linear model: habits + non-linear sleep
    "M1": (
            "y ~ age_z + gender_female + income_z "
            "+ vigorous_act + sedentary_z + alcohol_z "
            "+ sleep_c + I(sleep_c ** 2) + smoking_former + smoking_current"
        ),
    # hierarchical model: (1 | stratum_psu) and varying intercepts
    "M2": (
            "y ~ age_z + gender_female + income_z "
            "+ vigorous_act + sedentary_z + alcohol_z "
            "+ sleep_c + I(sleep_c ** 2) + smoking_former + smoking_current "
            "+ (1 | stratum_psu)"
        ),
}

# 
def prepare_bambi_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "y" not in out.columns and "depression_binary" in out.columns:
        out["y"] = out["depression_binary"]
    out["y"] = out["y"].astype(int)
    if "stratum_psu" in out.columns:
        out["stratum_psu"] = out["stratum_psu"].astype(str)
    return out

# helper function to generate synthetic data before the preprocessed data is ready
def generate_synthetic_covariates(n, seed):
    rnd = np.random.default_rng(seed)

    smoking = rnd.choice(["never", "former", "current"], size=n, p=[0.6, 0.2, 0.2])
    # Simulate ~30 unique stratum_psu clusters (15 strata x 2 PSUs)
    clusters = [f"{s}_{p}" for s in range(173, 188) for p in (1, 2)]

    synthetic_df = pd.DataFrame({
        "age_z": rnd.normal(0.0, 1.0, size=n),
        "gender_female": rnd.binomial(1, 0.5, size=n),
        "income_z": rnd.normal(0.0, 1.0, size=n),
        "vigorous_act": rnd.binomial(1, 0.45, size=n),
        "sedentary_z": rnd.normal(0.0, 1.0, size=n),
        "alcohol_z": np.clip(rnd.normal(0.0, 1.0, size=n), -0.8, 4.0),
        "sleep_c": np.clip(rnd.normal(0.0, 1.4, size=n), -4.5, 5.5),
        "smoking_former": (smoking == "former").astype(int),
        "smoking_current": (smoking == "current").astype(int),
        "stratum_psu": rnd.choice(clusters, size=n),
        "y": rnd.integers(0, 2, size=n),
    })
    
    return prepare_bambi_df(synthetic_df)

# generate priors
def get_priors(model_name: str):
    priors = {
        # common Normal distribution prior
        "common": bmb.Prior("Normal", mu=0.0, sigma=0.5),
        "Intercept": bmb.Prior("Normal", mu=-2.2, sigma=0.75),
    }

    # add the following priors regarding the model
    if model_name in ("M1", "M2"):
        priors["I(sleep_c ** 2)"] = bmb.Prior("Normal", mu=0, sigma=0.1)
    if model_name == "M2":
        priors["1|stratum_psu"] = bmb.Prior(
            "Normal", mu=0, sigma=bmb.Prior("Exponential", lam=1)
        )

    return priors

# blueprint function for building the different models
def build_model(model_name: str, df: pd.DataFrame):
    # get priors via the model name
    priors = get_priors(model_name)
    data = prepare_bambi_df(df)

    # build model with bambi with "bernoulli "
    model = bmb.Model(
        MODELS[model_name],
        data=data,
        family="bernoulli",
        priors=priors
    )
    model.build()

    return model