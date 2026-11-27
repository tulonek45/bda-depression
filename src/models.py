import numpy as np
import pandas as pd
import bambi as bmb

MODELS = {
    # baseline model: control
    "M0": "y ~ age_z + gender_female + income_z",
    "M1a": (
        "y ~ age_z + gender_female + income_z "
        "+ vigorous_act + sedentary_z + alcohol_z "
        "+ sleep_c + smoking_former + smoking_current"
    ),
    "M1b": (
        "y ~ age_z + gender_female + income_z "
        "+ vigorous_act + sedentary_z + alcohol_z "
        "+ I(sleep_c ** 2) + smoking_former + smoking_current"
    ),
    "M1c": (
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


MODEL_COLUMNS = {
    "M0": (
        "y",
        "age_z",
        "gender_female",
        "income_z",
    ),
    "M1a": (
        "y",
        "age_z",
        "gender_female",
        "income_z",
        "vigorous_act",
        "sedentary_z",
        "alcohol_z",
        "sleep_c",
        "smoking_former",
        "smoking_current",
    ),
    "M1b": (
        "y",
        "age_z",
        "gender_female",
        "income_z",
        "vigorous_act",
        "sedentary_z",
        "alcohol_z",
        "sleep_c",
        "smoking_former",
        "smoking_current",
    ),
    "M1c": (
        "y",
        "age_z",
        "gender_female",
        "income_z",
        "vigorous_act",
        "sedentary_z",
        "alcohol_z",
        "sleep_c",
        "smoking_former",
        "smoking_current",
    ),
    "M2": (
        "y",
        "age_z",
        "gender_female",
        "income_z",
        "vigorous_act",
        "sedentary_z",
        "alcohol_z",
        "sleep_c",
        "smoking_former",
        "smoking_current",
        "stratum_psu",
    ),
}


def prepare_bambi_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "y" not in out.columns:
        for outcome_column in ("depression_status_int", "depression_binary"):
            if outcome_column in out.columns:
                out["y"] = out[outcome_column]
                break
        else:
            raise ValueError(
                "Model data must include 'y', 'depression_status_int', "
                "or 'depression_binary'."
            )
    out["y"] = pd.to_numeric(out["y"], errors="raise")
    if out["y"].isna().any() or not out["y"].isin([0, 1]).all():
        raise ValueError("The model outcome 'y' must contain only non-missing 0/1 values.")
    out["y"] = out["y"].astype(int)
    if "stratum_psu" in out.columns:
        if out["stratum_psu"].isna().any():
            raise ValueError(
                "The M2 grouping column 'stratum_psu' must not contain missing values."
            )
        out["stratum_psu"] = out["stratum_psu"].astype(str)
    return out


# generate priors
def get_priors(model_name: str):
    if model_name not in MODELS:
        raise ValueError(f"Unknown model {model_name!r}; expected one of {tuple(MODELS)}.")

    priors = {
        "common": bmb.Prior("Normal", mu=0.0, sigma=0.5),
        "Intercept": bmb.Prior("Normal", mu=-2.2, sigma=0.75),
    }

    if model_name in ("M1", "M2"):
        priors["I(sleep_c ** 2)"] = bmb.Prior("Normal", mu=0, sigma=0.1)
    if model_name == "M2":
        priors["1|stratum_psu"] = bmb.Prior(
            "Normal", mu=0, sigma=bmb.Prior("Exponential", lam=1)
        )

    return priors

# blueprint function for building the different models
def build_model(model_name: str, df: pd.DataFrame):
    if model_name not in MODELS:
        raise ValueError(f"Unknown model {model_name!r}; expected one of {tuple(MODELS)}.")

    priors = get_priors(model_name)
    data = prepare_bambi_df(df)
    required = MODEL_COLUMNS[model_name]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"{model_name} data is missing required columns: {missing}")
    incomplete = [column for column in required if data[column].isna().any()]
    if incomplete:
        raise ValueError(f"{model_name} data contains missing values in: {incomplete}")
    if model_name == "M2" and data["stratum_psu"].nunique() < 2:
        raise ValueError("M2 requires at least two distinct stratum/PSU groups.")

    model = bmb.Model(
        MODELS[model_name],
        data=data,
        family="bernoulli",
        priors=priors
    )
    model.build()

    return model