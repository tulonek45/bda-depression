from pathlib import Path

import pandas as pd
import requests

BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/{}.xpt"
FILES = ["DPQ_J", "DEMO_J", "BMX_J", "SLQ_J", "SMQ_J", "MCQ_J"]
DATA = Path("data")
DATA.mkdir(exist_ok=True)


def download(name: str) -> Path:
    path = DATA / f"{name}.xpt"
    if path.exists():
        return path
    r = requests.get(BASE.format(name), headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path


def load(name: str) -> pd.DataFrame:
    return pd.read_sas(download(name), format="xport", encoding="utf-8")

if __name__ == "__main__":
    dpq, demo, bmx, slq, smq, mcq = (load(f) for f in FILES)