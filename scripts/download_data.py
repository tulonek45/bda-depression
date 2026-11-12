from pathlib import Path
from src.config import DatasetConfig

import requests

CONFIG = DatasetConfig.from_file("dataset_config.yml") 

BASE = CONFIG.data_base_url
FILES = CONFIG.datafiles
DATA = CONFIG.data_path
DATA.mkdir(exist_ok=True)


def download(name: str) -> Path:
    path = DATA / f"{name}.xpt"
    if path.exists():
        return path
    r = requests.get(BASE.format(name), headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path


if __name__ == "__main__":
    for f in FILES: download(f)