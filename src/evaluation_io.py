"""Paths shared by the evaluation scripts.

    src/evaluation.py         fit models, compute results -> outputs/evaluation/tables/*.csv
    src/plot_evaluation.py    cached fits + tables -> figures/evaluation/*.png
    src/report_evaluation.py  tables -> outputs/evaluation/summary.md
"""
from pathlib import Path

OUT_DIR = Path("evaluation")
TABLE_DIR = OUT_DIR / "tables"
FIGURE_DIR = OUT_DIR / "figures"
IDATA_DIR = OUT_DIR / ".cache" /"idata"
SUMMARY_PATH = OUT_DIR / "summary.md"
