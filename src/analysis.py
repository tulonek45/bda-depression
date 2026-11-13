from src.config import DatasetConfig
from src.load import prepare_df, load_df


CONFIG_PATH = "dataset_config.yml"


def analyze():
  config = DatasetConfig.from_file(CONFIG_PATH)
  df = load_df(config)
  df = prepare_df(df, config)

  print(df[config.phq_attributes + ["phq_score", "depression_status", "depression_status_int"]].head())

  print(df["depression_status"].value_counts(dropna=False))

if __name__ == "__main__":
  analyze()
