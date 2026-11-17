# bda-depression

## Quick start

### Requirements

- Python 3.10 or later
- Node.js and npm

From the repository root, there's options to download the configured NHANES
datasets and to run the analysis:

```sh
npm run download
npm run analyze
```

The commands creates a local `.venv` and installs the packages in
`requirements.txt` if needed. Downloads are saved to the directory specified in
dataset_config.yml; files that already exist are not downloaded again.

### Configuration and development

Edit `dataset_config.yml` to change the data URL, dataset files, selected
attributes, missing-value codes, or depression cutoffs. The download and
analysis commands are defined in `package.json` and dispatched by `run.cjs`.

After changing Python dependencies in `requirements.txt`, just run either npm
command normally to automatically update the virtual environment. To start
fresh, remove `.venv` and rerun the command.

### Running Prior Predictive Checks

From the repository root with the virtual environment active:

```bash
python -m src.prior_checks
```

This compiles `M0`–`M2`, saves prior density plots to
`outputs/preliz_prior_predictive.png`, and prints the implied prior prevalence
`P(y = 1)`.

### Modeling Interface & Data Contract (`src/models.py`)

`build_model(model_name, df)` compiles a Bayesian Bernoulli logistic regression
model (`"M0"`, `"M1"`, or `"M2"`) and expects a preprocessed `pandas.DataFrame`
containing:

- **Outcome:** `y` (or `depression_status_int` / `depression_binary`) coded as
  binary integers `0` (`not_depressed`) or `1` (`depressed`, PHQ-9 clinical
  cutoff).
- **Controls (`M0`):** `age_z`, `gender_female`, `income_z`.
- **Habit Predictors (`M1`):** `vigorous_act`, `sedentary_z`, `alcohol_z`,
  `sleep_c` (centered at 7.5h; quadratic `I(sleep_c ** 2)` is built
  automatically), `smoking_former`, `smoking_current`.
- **Grouping (`M2`):** `stratum_psu` (unique survey cluster ID combining
  `SDMVSTRA` and `SDMVPSU` from `DEMO_L`).
