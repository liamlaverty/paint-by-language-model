# paint-by-language-model

A Python application that queries an LLM about notable features of famous artists' work and saves the responses as individual JSON files.

## Prerequisites

- **LMStudio**: Install and run [LMStudio](https://lmstudio.ai/) with the local server enabled on port 1234
- **Conda**: Anaconda or Miniconda for environment management
- **Python**: 3.12.2 or higher

## Setup

### 1. Create Conda Environment

```sh
conda create -n paint-by-language-model python=3.12.2
conda activate paint-by-language-model
pip install uv
```

### 2. Install Dependencies

From the project root, navigate to the package directory and install in editable mode:

```sh
cd src/paint_by_language_model
uv pip install -e .
```

This will install the required dependencies.

## Running the App

### 1. Start LMStudio

Before running the app, ensure:
1. LMStudio is running
2. A model is loaded
3. The local server is enabled (default port: 1234)

### 2. Run the Application

From the project root directory:

```sh
conda activate paint-by-language-model
uv run src/paint_by_language_model/main.py
```

The application will:
1. Connect to LMStudio
2. Load artist names from `src/datafiles/artists.json`
3. Query the LLM about each artist's notable features
4. Save individual JSON files to `src/output/`

## Output

Results are saved as JSON files in `src/output/` with the format:

```json
{
  "artist_name": "Vincent van Gogh",
  "query_timestamp": "2026-01-03T10:30:45.123456",
  "response": "LLM response text...",
  "model_used": "local-model"
}
```

## Configuration

Edit `src/paint_by_language_model/config.py` to customize:
- LMStudio server URL (default: `http://localhost:1234/v1`)
- Request timeout (default: 120 seconds)
- Maximum tokens (default: 1024)
- Prompt template