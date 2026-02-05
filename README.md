# paint-by-language-model

A Python application that uses Vision Language Models (VLMs) to iteratively create original artwork in the style of famous artists. The system starts with a blank canvas and progressively adds strokes suggested by VLMs, building unique images that embody specific artistic styles.

**Current Status**: Phase 2 in development - Core VLM client and canvas management implemented.

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

## Running the App

### Phase 1: Artist Analysis (Text-based LLM)

Query an LLM about artists and save responses as JSON:

```sh
conda activate paint-by-language-model
uv run src/paint_by_language_model/main.py
```

### Phase 2: Iterative Image Generation (VLM)

Test the Stroke VLM Client:

```sh
conda activate paint-by-language-model
python tests/manual_test_stroke_vlm.py
```

This will:
1. Initialize a blank canvas
2. Query the VLM for stroke suggestions based on Van Gogh's style
3. Apply suggested strokes to the canvas
4. Save snapshots and interaction history to `test_output/`

**Output Structure**:
- `test_output/iteration-002.png` - Latest snapshot
- `test_output/by_date/{run_datetime}/` - Date-organized outputs
  - `iteration-{timestamp}.png` - Canvas snapshot
  - `interaction-{timestamp}.json` - Full VLM interaction history

## Output

### Phase 1: Artist Analysis

Results are saved as JSON files in `src/output/` with the format:

```json
{
  "artist_name": "Vincent van Gogh",
  "query_timestamp": "2026-01-03T10:30:45.123456",
  "response": "LLM response text...",
  "model_used": "local-model"
}
```

### Phase 2: Image Generation

Outputs are organized in `test_output/by_date/{run_datetime}/`:

**Interaction History** (`interaction-{timestamp}.json`):
```json
[
  {
    "timestamp": "2026-02-05T09:29:33.379896",
    "iteration": 2,
    "artist_name": "Vincent van Gogh",
    "subject": "Starry Night Landscape",
    "prompt": "Full prompt sent to VLM...",
    "raw_response": "Raw VLM response before parsing...",
    "parsed_response": {
      "stroke": {
        "type": "line",
        "start_x": 40,
        "start_y": 25,
        "end_x": 75,
        "end_y": 80,
        "color_hex": "#0069AB",
        "thickness": 8,
        "opacity": 0.7,
        "reasoning": "VLM's explanation..."
      },
      "updated_strategy": "Strategy for next iterations..."
    },
    "model": "lmistralai/ministral-3-3b"
  }
]
```

**Canvas Snapshots**: PNG images showing progressive stroke application

## Configuration

Edit [src/paint_by_language_model/config.py](src/paint_by_language_model/config.py) to customize:

**Phase 1 (Text LLM)**:
- LMStudio server URL (default: `http://localhost:1234/v1`)
- Request timeout (default: 120 seconds)
- Maximum tokens (default: 1024)
- Prompt template

**Phase 2 (VLM Image Generation)**:
- Canvas dimensions (default: 800x600)
- Background color (default: white `#FFFFFF`)
- Stroke constraints (thickness, opacity ranges)
- VLM model (default: `lmistralai/ministral-3-3b`)
- VLM timeout (default: 180 seconds)

## Architecture

### Current Components

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

- **LMStudio Client** ([lmstudio_client.py](src/paint_by_language_model/lmstudio_client.py))
  - Wraps OpenAI-compatible API
  - Supports multimodal queries (text + image)
  - Handles base64 image encoding

### Data Models

- **Stroke** ([models/stroke.py](src/paint_by_language_model/models/stroke.py)) - Drawing operation parameters
- **StrokeVLMResponse** ([models/stroke_vlm_response.py](src/paint_by_language_model/models/stroke_vlm_response.py)) - VLM response structure
- **CanvasState** ([models/canvas_state.py](src/paint_by_language_model/models/canvas_state.py)) - Canvas state snapshot

## Development Roadmap

- [x] Phase 1: Text-based artist analysis
- [x] Phase 2.1: Canvas management system
- [x] Phase 2.2: Stroke data models
- [x] Phase 2.3: Multimodal LMStudio client
- [x] Phase 2.4: Canvas manager implementation
- [x] Phase 2.5: Stroke VLM client with history tracking
- [ ] Phase 2.6: Evaluation VLM client
- [ ] Phase 2.7: Strategy manager
- [ ] Phase 2.8: Generation orchestrator
- [ ] Phase 3: Multi-iteration generation loop