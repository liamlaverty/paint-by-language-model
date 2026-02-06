# paint-by-language-model

A Python application that uses Vision Language Models (VLMs) to iteratively create original artwork in the style of famous artists. The system starts with a blank canvas and progressively adds strokes suggested by VLMs, building unique images that embody specific artistic styles.

**Current Status**: Phase 2 complete - Full iterative generation pipeline with VLM-driven stroke generation, evaluation, and strategy management.

## Prerequisites

- **LMStudio**: Install and run [LMStudio](https://lmstudio.ai/) with the local server enabled on port 1234
- **VLM Model**: Load a Vision Language Model (e.g., LLaVA, MiniStral) in LMStudio for image-based queries
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

### 3. Install Development Tools (Optional)

For linting, type checking, and testing:

```sh
cd src/paint_by_language_model
uv pip install -e ".[dev]"
```

## Running the App

### Image Generation (Main Usage)

Generate artwork using the command-line interface:

```sh
conda activate paint-by-language-model
cd src/paint_by_language_model
python main.py \
  --artist "Vincent van Gogh" \
  --subject "Starry Night Landscape" \
  --output-id vangogh-001
```

#### Required Arguments

| Argument | Description |
|----------|-------------|
| `--artist` | Target artist name (e.g., "Claude Monet", "Vincent van Gogh") |
| `--subject` | Subject to paint (e.g., "Water Lilies", "Starry Night Landscape") |
| `--output-id` | Unique identifier for this artwork (used for output directory) |

#### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--max-iterations` | 10000 | Maximum iterations before stopping |
| `--target-score` | 75.0 | Target style score (0-100) to stop generation early |
| `--log-level` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

#### Examples

Basic generation:
```sh
python main.py \
  --artist "Claude Monet" \
  --subject "Water Lilies" \
  --output-id monet-001
```

Custom iteration limits and target score:
```sh
python main.py \
  --artist "Wassily Kandinsky" \
  --subject "Abstract Composition" \
  --output-id kandinsky-001 \
  --max-iterations 50 \
  --target-score 80
```

Debug mode with verbose logging:
```sh
python main.py \
  --artist "Frida Kahlo" \
  --subject "Self Portrait with Flowers" \
  --output-id frida-001 \
  --log-level DEBUG
```

### Generation Process

The application will:
1. Initialize a blank canvas (800×600 pixels)
2. Query the VLM for stroke suggestions based on the artist's style
3. Apply suggested strokes to the canvas
4. Evaluate the current canvas against the artist's style
5. Update strategy based on evaluation feedback
6. Repeat until target score is reached or max iterations exceeded
7. Generate a final report with metrics

**Resumable**: If interrupted, re-running with the same `--output-id` will resume from the last completed iteration.

### Output Structure

All outputs are saved to `src/output/{output-id}/`:

```
src/output/vangogh-001/
├── metadata.json           # Generation metadata
├── generation_report.md    # Human-readable summary
├── snapshots/              # Canvas images per iteration
│   ├── iteration-001.png
│   ├── iteration-002.png
│   └── ...
├── strokes/                # Stroke data per iteration
│   ├── iteration-001.json
│   └── ...
├── evaluations/            # VLM evaluation results
│   ├── iteration-001.json
│   └── ...
└── strategies/             # Strategy updates
    ├── strategy-001.md
    └── ...
```

## Output Examples

### Generation Summary (console output)

```
================================================================================
GENERATION COMPLETE
================================================================================
Artwork ID: vangogh-001
Total Iterations: 45
Final Score: 78.5/100
Total Strokes: 45
Output Directory: src/output/vangogh-001
================================================================================
```

### Metadata (`metadata.json`)

```json
{
  "artwork_id": "vangogh-001",
  "artist_name": "Vincent van Gogh",
  "subject": "Starry Night Landscape",
  "canvas_width": 800,
  "canvas_height": 600,
  "started_at": "2026-02-05T10:30:45.123456",
  "vlm_model": "lmistralai/ministral-3-3b"
}
```

### Stroke Data (`strokes/iteration-001.json`)

```json
{
  "type": "line",
  "start_x": 40,
  "start_y": 25,
  "end_x": 75,
  "end_y": 80,
  "color_hex": "#0069AB",
  "thickness": 8,
  "opacity": 0.7,
  "reasoning": "VLM's explanation of why this stroke was chosen..."
}
```

### Evaluation Result (`evaluations/iteration-001.json`)

```json
{
  "style_score": 45.5,
  "strengths": ["Bold brushwork", "Good color palette"],
  "weaknesses": ["Lacks texture variation"],
  "suggestions": "Add more swirling patterns typical of Van Gogh"
}
```

## Development Tools

### Linting & Formatting (Ruff)

```sh
conda activate paint-by-language-model
cd src/paint_by_language_model

# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

**Configuration**: Line length 100, includes pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear checks.

### Type Checking (Mypy)

```sh
conda activate paint-by-language-model
cd src/paint_by_language_model

# Check types
mypy .
```

**Configuration**: Strict mode with required type annotations on all function definitions.

### Testing (Pytest)

```sh
conda activate paint-by-language-model
cd src/paint_by_language_model

# Run all tests
pytest

# Run with coverage report
pytest --cov-report=term-missing

# Skip slow tests
pytest -m "not slow"

# Generate HTML coverage report
pytest --cov-report=html
```

**Test locations**: `tests/` directory at project root.

## Configuration

Edit [src/paint_by_language_model/config.py](src/paint_by_language_model/config.py) to customize:

**Canvas Settings**:
- `CANVAS_WIDTH` / `CANVAS_HEIGHT` - Canvas dimensions (default: 800×600)
- `CANVAS_BACKGROUND_COLOR` - Background color (default: `#FFFFFF`)

**Stroke Constraints**:
- `MAX_STROKE_THICKNESS` / `MIN_STROKE_THICKNESS` - Thickness range (default: 1-10 pixels)
- `MAX_STROKE_OPACITY` / `MIN_STROKE_OPACITY` - Opacity range (default: 0.1-1.0)
- `SUPPORTED_STROKE_TYPES` - Currently `["line"]`, future: curves, fills

**VLM Settings**:
- `VLM_MODEL` - Stroke generation model (default: `lmistralai/ministral-3-3b`)
- `EVALUATION_VLM_MODEL` - Style evaluation model
- `VLM_TIMEOUT` - Request timeout (default: 180 seconds)
- `STROKE_PROMPT_TEMPERATURE` - Creativity setting (default: 0.7)
- `EVALUATION_PROMPT_TEMPERATURE` - Consistency setting (default: 0.3)

**Generation Loop**:
- `MAX_ITERATIONS` - Safety limit (default: 10000)
- `MIN_ITERATIONS` - Minimum before early stop (default: 20)
- `TARGET_STYLE_SCORE` - Target score 0-100 (default: 75.0)

**Strategy Management**:
- `STRATEGY_CONTEXT_WINDOW` - Recent strategies to include (default: 5)
- `STROKE_PROMPT_INCLUDE_STRATEGY` - Include strategy context (default: True)

## Architecture

### Current Components

- **Generation Orchestrator** ([generation_orchestrator.py](src/paint_by_language_model/generation_orchestrator.py))
  - Main entry point for generation workflow
  - Coordinates all components (canvas, VLMs, strategy)
  - Handles iteration loop and stopping conditions
  - Supports resumable generation

- **Canvas Manager** ([services/canvas_manager.py](src/paint_by_language_model/services/canvas_manager.py))
  - Manages image canvas with PIL
  - Applies strokes (lines, curves, fills)
  - Validates stroke parameters
  - Saves snapshots

- **Stroke VLM Client** ([services/stroke_vlm_client.py](src/paint_by_language_model/services/stroke_vlm_client.py))
  - Queries VLMs with canvas images
  - Builds prompts with artist context
  - Parses JSON responses robustly
  - Tracks interaction history for debugging

- **Evaluation VLM Client** ([services/evaluation_vlm_client.py](src/paint_by_language_model/services/evaluation_vlm_client.py))
  - Evaluates canvas against target artist style
  - Returns style scores (0-100)
  - Provides strengths, weaknesses, and suggestions

- **Strategy Manager** ([strategy_manager.py](src/paint_by_language_model/strategy_manager.py))
  - Manages multi-iteration context
  - Saves and loads strategy files
  - Provides recent strategy window for prompts

- **LMStudio Client** ([lmstudio_client.py](src/paint_by_language_model/lmstudio_client.py))
  - Wraps OpenAI-compatible API
  - Supports multimodal queries (text + image)
  - Handles base64 image encoding

### Data Models

- **Stroke** ([models/stroke.py](src/paint_by_language_model/models/stroke.py)) - Drawing operation parameters
- **StrokeVLMResponse** ([models/stroke_vlm_response.py](src/paint_by_language_model/models/stroke_vlm_response.py)) - VLM response structure
- **EvaluationResult** ([models/evaluation_result.py](src/paint_by_language_model/models/evaluation_result.py)) - Style evaluation data
- **CanvasState** ([models/canvas_state.py](src/paint_by_language_model/models/canvas_state.py)) - Canvas state snapshot

## Development Roadmap

- [x] Phase 1: Text-based artist analysis
- [x] Phase 2: Generation orchestrator & CLI
- [ ] Phase 3: Additional stroke types (curves, fills), multiple strokes per iteration
- [ ] Phase 4: Connect to remote VLMs
