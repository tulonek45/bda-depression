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


def prepare_df(dataframe: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    df = dataframe.copy()
    df = _clean_uninformative_answers(df, config)
    df = _prepare_phq_attributes(df, config)
    df = _prepare_phq_score(df, config)
    df = _prepare_depression_status(df, config)
    return df
