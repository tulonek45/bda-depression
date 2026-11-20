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

The commands create a local `.venv` and install the packages in
`requirements.txt` if needed. Downloads are saved to the directory specified in
dataset_config.yml; files that already exist are not downloaded again.
`npm run analyze` preprocesses the configured NHANES files and fits M0–M2 on
adult complete cases. It prints posterior summaries, divergence counts, and a
PSIS-LOO model comparison.

### Configuration and development

Edit `dataset_config.yml` to change the data URL, dataset files, selected
attributes, missing-value codes, or depression cutoffs. The download and
analysis commands are defined in `package.json` and dispatched by `run.cjs`.

After changing Python dependencies in `requirements.txt`, just run either npm
command normally to automatically update the virtual environment. To start
fresh, remove `.venv` and rerun the command.

### Running Prior Predictive Checks

From the repository root:

```bash
npm run prior-checks
```

This compiles `M0`–`M2`, saves prior density plots to
`outputs/preliz_prior_predictive.png`, and prints the implied prior prevalence
`P(y = 1)`. It uses synthetic covariates for prior checks; `npm run analyze`
fits the models to the preprocessed NHANES data.

### Modeling Interface & Data Contract (`src/models.py`)

`build_model(model_name, df)` compiles a Bayesian Bernoulli logistic regression
model (`"M0"`, `"M1"`, or `"M2"`). `src.load.prepare_model_df` creates the
preprocessed modeling frame from the configured NHANES files:

- **Population:** adults aged 18+ with complete data for the predictors and
  PHQ-9 outcome, shared by all three models.
- **Outcome:** complete-case PHQ-9 score categorized with the configured cutoff:
  `y = 0` (`not_depressed`) or `1` (`depressed`).
- **Controls (`M0`):** `age_z`, `gender_female`, `income_z`.
- **Habit Predictors (`M1`):** `vigorous_act`, `sedentary_z`, `alcohol_z`,
  `sleep_c` (weekday/weekend weighted sleep centered at 7.5h; quadratic
  `I(sleep_c ** 2)` is built automatically), `smoking_former`,
  `smoking_current`.
- **Grouping (`M2`):** `stratum_psu` (unique survey cluster ID combining
  `SDMVSTRA` and `SDMVPSU` from `DEMO_L`).
- **Alcohol (`ALQ_L`):** drinks/week is derived from `ALQ121` drinking
  frequency and `ALQ130` drinks per drinking day (`15+` is treated as 15).
  Refused/don't-know codes in `ALQ111`, `ALQ121`, and `ALQ130` are treated as
  missing; confirmed abstainers are assigned 0. The frequency-to-days/year
  mapping is documented in `src/load.py`.
- **Activity (`PAQ_L`):** any reported vigorous leisure-time activity is coded
  as `vigorous_act`; `PAD680` supplies daily sedentary minutes.

The models currently do not apply NHANES sample weights; their posterior
summaries and model comparisons should not be interpreted as population-
representative estimates.
