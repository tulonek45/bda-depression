# bda-depression

## Quick start

### Requirements

- Python 3.10 or later
- Node.js and npm

From the repository root, there's options to download the configured NHANES datasets and to run the analysis:

```sh
npm run download
npm run analyze
```

The commands creates a local `.venv` and installs the packages in
`requirements.txt` if needed. Downloads are saved to the directory specified in dataset_config.yml; files
that already exist are not downloaded again.

### Configuration and development

Edit `dataset_config.yml` to change the data URL, dataset files, selected
attributes, missing-value codes, or depression cutoffs. The download and analysis
commands are defined in `package.json` and dispatched by `run.cjs`.

After changing Python dependencies in `requirements.txt`, just run either npm command
normally to automatically update the virtual environment. To start fresh, remove `.venv` and rerun
the command.
