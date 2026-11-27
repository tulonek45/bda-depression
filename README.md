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
`npm run analyze` runs `scripts/analyze.py`, which preprocesses the configured
NHANES files and fits M0–M2 on adult complete cases. It prints posterior
summaries, divergence counts, and a PSIS-LOO model comparison.

### Configuration and development

Edit `dataset_config.yml` to change the data URL, dataset files, selected
attributes, missing-value codes, or depression cutoffs. The npm commands are
defined in `package.json` and dispatched by `run.cjs`; analysis entry-point
logic lives in `scripts/`.

After changing Python dependencies in `requirements.txt`, just run either npm
command normally to automatically update the virtual environment. To start
fresh, remove `.venv` and rerun the command.

### Running Prior Predictive Checks

From the repository root:

```bash
npm run prior-checks
```

This compiles `M0`–`M2`, saves prior density plots to
`figures/preliz_prior_predictive.png`, and prints the implied prior prevalence
`P(y = 1)`. It uses the configured NHANES data and the same preprocessed adult
complete-case model frame as the analysis. Run `npm run download` first if the
configured data files are not already present.

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

### Running model evaluation

From the repository root:

```bash
npm run evaluate
```

The command evaluates the models, generates plots in `figures/evaluation/`,
and writes tables and `summary.md` under `outputs/evaluation/`. Figures are
not gitignored; tables, the report, and cached model fits are.

Fits are reused from `outputs/evaluation/idata/` unless `--refit` is specified.
Use `--refit` after changing the data or models. Sampling options and the
optional sensitivity analysis can be controlled, for example:

```bash
npm run evaluate -- --refit
npm run evaluate -- --skip-sensitivity
npm run evaluate -- --draws 300 --tune 300 --chains 4 --cores 1
```

`--skip-sensitivity` excludes sensitivity results from the new report and
does not regenerate sensitivity plots. Older sensitivity tables and figures
remain on disk and may no longer correspond to the current run.

#### What is evaluated

1. **Convergence:** R-hat, bulk and tail ESS, divergent transitions and
   maximum tree depth hits for every parameter. Targets: R-hat ≤ 1.01,
   ESS ≥ 400, no divergences.
2. **Posterior predictive checks:** the observed depression rate is compared
   with rates in data replicated from the posterior, overall, by habit subgroup
   (smoking, vigorous activity, sleep, alcohol) and by survey cluster
   (`stratum_psu`). The between-cluster spread of the rate shows whether the
   cluster effects in M2 are needed.
3. **Predictive performance:** PSIS-LOO (`az.loo`, `az.compare`) for each model
   and for a rate-only baseline. Pairwise differences answer: M0 vs baseline
   (do the controls predict?), M1 vs M0 (do living habits add predictive
   value?) and M2 vs M1 (do survey clusters add predictive value?).
4. **Prior sensitivity:** M1 and M2 are refit with every prior scale multiplied
   by 0.5 and 2, and the posterior means are compared.
