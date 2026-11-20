from pathlib import Path
import multiprocessing
import arviz as az

from src.config import DatasetConfig
from src.load import load_df, prepare_df, prepare_model_df
from src.models import MODELS, build_model


CONFIG_PATH = Path("dataset_config.yml")


def analyze(draws: int = 1000, tune: int = 1000, chains: int = 4) -> None:
    available_cores = multiprocessing.cpu_count()
    cores = min(chains, available_cores)
    
    print(f"System CPU cores available: {available_cores} | Using cores for sampling: {cores}")

    config = DatasetConfig.from_file(CONFIG_PATH)
    df = load_df(config)
    df = prepare_df(df, config)
    model_df = prepare_model_df(df, config)

    print(f"Adult complete-case participants: {len(model_df)}")
    print("Depression outcome counts:")
    outcome_counts = model_df["y"].value_counts().sort_index().rename(
        index={0: "not_depressed", 1: "depressed"}
    )
    print(outcome_counts.to_string())
    print(
        "Note: these models are unweighted and are not population-representative "
        "NHANES estimates."
    )

    idatas = {}
    for model_name in MODELS:
        print(f"\nFitting {model_name}: {MODELS[model_name]}")
        model = build_model(model_name, model_df)
        idata = model.fit(
            draws=draws,
            tune=tune,
            chains=chains,
            cores=cores,
            random_seed=42,
            target_accept=0.9,
            idata_kwargs={"log_likelihood": True},
        )
        idatas[model_name] = idata
        print(f"{model_name} posterior summary:")
        print(az.summary(idata, round_to=3).to_string())
        divergences = int(idata.sample_stats["diverging"].sum().item())
        print(f"{model_name} divergent transitions: {divergences}")

    print("\nModel comparison (PSIS-LOO; all models use the same participants):")
    print(az.compare(idatas).to_string())


if __name__ == "__main__":
    analyze()
