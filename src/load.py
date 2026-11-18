from pathlib import Path
from src.config import DatasetConfig
import pandas as pd


SAS_ZERO_ARTIFACT = 5.397605346934028e-79


def load(data_path: Path, name: str) -> pd.DataFrame:
    path = data_path / f"{name}.xpt"
    dataframe = pd.read_sas(path, format="xport", encoding="utf-8")
    numeric_columns = dataframe.select_dtypes(include="number").columns
    dataframe[numeric_columns] = dataframe[numeric_columns].replace(SAS_ZERO_ARTIFACT, 0)
    return dataframe


def _load_columns(data_path: Path, dataset: str, columns: tuple[str, ...]) -> pd.DataFrame:
    dataframe = load(data_path, dataset)
    required = ("SEQN", *columns)
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise ValueError(f"{dataset}: missing required columns: {missing}")
    return dataframe.loc[:, list(required)].copy()


def load_df(config: DatasetConfig) -> pd.DataFrame:
    df = _load_columns(config.data_path, config.phq_dataset, config.phq_attributes)
    for dataset, columns in config.selected_attributes.items():
        predictors = _load_columns(config.data_path, dataset, columns)
        df = df.merge(predictors, how="left", on="SEQN", sort=False, validate="one_to_one")
    return df


def _clean_uninformative_answers(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    for column, codes in config.missing_codes.items():
        df[column] = df[column].mask(df[column].isin(codes))
    return df


def _prepare_phq_attributes(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    items = df.loc[:, list(config.phq_attributes)]
    items = items.where(items.isin([0, 1, 2, 3]))
    df[list(config.phq_attributes)] = items
    return df


def _prepare_phq_score(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    items = df.loc[:, list(config.phq_attributes)]
    score = items.sum(axis=1, min_count=len(config.phq_attributes)).astype("Int64")
    df["phq_score"] = score
    return df


def _prepare_depression_status(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    score = df["phq_score"]
    
    depression_status = pd.Series([None] * len(df), index=df.index, dtype=object)
    depression_status_int = pd.Series(pd.NA, index=df.index, dtype="Int64")
    
    for c in config.depression_cutoffs:
        mask = ((score >= c["min"]) & (score <= c["max"])).fillna(False)
        depression_status[mask] = c["label"]
        depression_status_int[mask] = c["label_int"]
        
    df["depression_status"] = depression_status
    df["depression_status_int"] = depression_status_int
    return df


def _prepare_lifestyle_attributes(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    frequency = pd.to_numeric(df["ALQ121"], errors="coerce")
    drinks_per_drinking_day = pd.to_numeric(df["ALQ130"], errors="coerce")
    days_per_year = frequency.map(config.alcohol_days_per_year)
    drinks_per_week = days_per_year * drinks_per_drinking_day / 52
    abstinent = df["ALQ111"].eq(2) | frequency.eq(0)
    df["alcohol_drinks_week"] = drinks_per_week.mask(abstinent, 0)

    activity_frequency = pd.to_numeric(df["PAD810Q"], errors="coerce")
    activity_unit = df["PAD810U"].astype("string").str.strip()
    valid_activity_unit = activity_unit.isin(["D", "W", "M", "Y"])
    activity_known = activity_frequency.eq(0) | (
        activity_frequency.gt(0) & valid_activity_unit
    )
    df["vigorous_act"] = activity_frequency.gt(0).where(activity_known)

    weekdays_sleep = pd.to_numeric(df["SLD012"], errors="coerce")
    weekend_sleep = pd.to_numeric(df["SLD013"], errors="coerce")
    df["sleep_hours"] = (5 * weekdays_sleep + 2 * weekend_sleep) / 7
    df["sedentary_minutes"] = pd.to_numeric(df["PAD680"], errors="coerce")

    smoked_100 = pd.to_numeric(df["SMQ020"], errors="coerce")
    smoking_now = pd.to_numeric(df["SMQ040"], errors="coerce")
    never_smoked = smoked_100.eq(2)
    answered_current = smoked_100.eq(1) & smoking_now.isin([1, 2, 3])
    current = smoked_100.eq(1) & smoking_now.isin([1, 2])
    former = smoked_100.eq(1) & smoking_now.eq(3)

    known_smoking_status = never_smoked | answered_current
    df["smoking_current"] = current.astype(float).where(known_smoking_status)
    df["smoking_former"] = former.astype(float).where(known_smoking_status)
    df.loc[never_smoked, ["smoking_current", "smoking_former"]] = 0.0
    return df


def _standardize(series: pd.Series, name: str) -> pd.Series:
    mean = series.mean()
    std = series.std(ddof=0)
    if pd.isna(std) or std == 0:
        raise ValueError(f"Cannot standardize {name}: it has no variation.")
    return (series - mean) / std


def prepare_df(dataframe: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    df = dataframe.copy()
    df = _clean_uninformative_answers(df, config)
    df = _prepare_phq_attributes(df, config)
    df = _prepare_phq_score(df, config)
    df = _prepare_depression_status(df, config)
    df = _prepare_lifestyle_attributes(df, config)
    return df


def prepare_model_df(dataframe: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    numeric_columns = config.numeric_columns
    df = dataframe.copy()
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    df = df.loc[df["RIDAGEYR"] >= 18].copy()
    df = df.dropna(subset=numeric_columns).copy()
    if df.empty:
        raise ValueError("No adult complete cases remain for the model predictors.")

    invalid_gender = ~df["RIAGENDR"].isin([1, 2])
    if invalid_gender.any():
        raise ValueError("RIAGENDR contains values outside the NHANES codes 1 and 2.")
    invalid_outcome = ~df["depression_status_int"].isin([0, 1])
    if invalid_outcome.any():
        raise ValueError("The depression outcome must contain only 0 and 1.")

    df["y"] = df["depression_status_int"].astype(int)
    df["age_z"] = _standardize(df["RIDAGEYR"], "age")
    df["gender_female"] = df["RIAGENDR"].eq(2).astype(int)
    df["income_z"] = _standardize(df["INDFMPIR"], "income")
    df["sleep_c"] = df["sleep_hours"] - 7.5
    df["sedentary_z"] = _standardize(df["sedentary_minutes"], "sedentary time")
    df["alcohol_z"] = _standardize(df["alcohol_drinks_week"], "alcohol drinks/week")
    df["stratum_psu"] = (
        df["SDMVSTRA"].astype("Int64").astype("string")
        + "_"
        + df["SDMVPSU"].astype("Int64").astype("string")
    )
    return df
