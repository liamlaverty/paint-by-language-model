# paint-by-language-model

## Conda Environment

This app uses a conda environment for dependency management.

- **Environment name:** `paint-by-language-model`
- **Python version:** 3.12.2

To create the environment, run:

```sh
conda create -n paint-by-language-model python=3.12.2
conda activate paint-by-language-model
pip install uv
```

## Running the App

To run the application from the root directory using `uv`:

```sh
uv run src/paint_by_language_model/main.py
```