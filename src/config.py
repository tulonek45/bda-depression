from __future__ import annotations
from pathlib import Path
import yaml
from dataclasses import dataclass

@dataclass
class DatasetConfig():
    data_base_url: str
    data_path: Path
    phq_dataset: str
    phq_attributes: list[str]
    datafiles: list[str]
    selected_attributes: dict[str, list[str]]
    missing_codes: dict[str, list[int]]
    depression_cutoffs: list[dict]

    def __post_init__(self):
        self.data_path = Path(self.data_path)

    @classmethod
    def from_file(cls, path: str | Path) -> DatasetConfig:
        path = Path(path)
        with open(path, "r") as f:
              data = yaml.safe_load(f)
        return cls(**data)
