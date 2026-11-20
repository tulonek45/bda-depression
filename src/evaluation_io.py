"""Paths shared by the evaluation scripts.

    src/evaluation.py         fit models, compute results -> tables/*.csv
    src/plot_evaluation.py    cached fits + tables -> figures/*.png
    src/report_evaluation.py  tables -> summary.md
"""
from pathlib import Path

OUT_DIR = Path("outputs/evaluation")
TABLE_DIR = OUT_DIR / "tables"
FIGURE_DIR = OUT_DIR / "figures"
IDATA_DIR = OUT_DIR / "idata"
