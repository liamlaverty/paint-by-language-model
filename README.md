# paint-by-language-model

A Python application that uses Vision Language Models (VLMs) to iteratively create original artwork in the style of famous artists. The system starts with a blank canvas and progressively adds strokes suggested by VLMs, building unique images that embody specific artistic styles.

The project includes a Next.js viewer application for interactively exploring generated artworks, viewing stroke-by-stroke creation timelines, and examining metadata and evaluation scores.

**Current Status**: Phase 11 complete - Stroke sample images attached to VLM prompt for visual context, multi-image VLMClient support, and StrokeSampleGenerator service.

## Prerequisites

### Python Backend
- **Python**: 3.12.2 or higher
- **Conda**: Anaconda or Miniconda for environment management
- A VLM provider (one of):
  - **Mistral API**: Get an API key at https://console.mistral.ai/
  - **LMStudio** (local): Download from https://lmstudio.ai/ and run with server enabled on port 1234
  - **Anthropic API**: Get an API key at https://console.anthropic.com/

### Next.js Viewer (Optional)
- **Node.js**: 18.0.0 or higher
- **pnpm**: 9.15.0 or higher (install with `npm install -g pnpm`)

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

### 3. Configure Environment

Copy `.env.example` to `.env` and set your API key:

```sh
cp .env.example .env
```

Edit `.env`:

```env
# VLM Provider ("mistral", "lmstudio", or "anthropic")
PROVIDER=mistral

# Mistral API key (required when PROVIDER=mistral)
MISTRAL_API_KEY=your_api_key_here

# Anthropic API key (required when PROVIDER=anthropic)
# ANTHROPIC_API_KEY=your_api_key_here
```

| Provider | Use Case | Auth Required |
|----------|----------|---------|
| `mistral` | Remote API, production use | Yes (`MISTRAL_API_KEY`) |
| `lmstudio` | Local development, no API costs | No |
| `anthropic` | Remote API, Claude models | Yes (`ANTHROPIC_API_KEY`) |

The provider can also be overridden via the `--provider` CLI flag.

### 4. Install Development Tools (Optional)

For linting, type checking, and testing:

```sh
cd src/paint_by_language_model
uv pip install -e ".[dev]"
```

### 5. Install Viewer Dependencies (Optional)

To run the interactive web viewer:

```sh
pnpm -C src/viewer install
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
| `--subject` | Short one-sentence subject description |
| `--output-id` | Unique identifier for this artwork (used for output directory) |

#### Optional Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--expanded-subject` | | None | Detailed multi-sentence description for richer planning |
| `--planner-model` | | from config | Override planner model (e.g., `mistral-large-latest`) |
| `--max-iterations` | `-i` | 10000 | Maximum iterations before stopping |
| `--target-score` | `-t` | 75.0 | Target style score (0-100) to stop generation early |
| `--strokes-per-query` | `-n` | 5 | Number of strokes per VLM query (1-20) |
| `--stroke-types` | | all | Comma-separated stroke types to use |
| `--provider` | | from `.env` | VLM provider: `mistral`, `lmstudio`, or `anthropic` |
| `--api-key` | | from `.env` | API key (overrides `MISTRAL_API_KEY` env var) |
| `--gif-frame-duration` | | 150 | GIF frame duration in milliseconds |
| `--log-level` | | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

#### Examples

Basic generation:
```sh
python main.py \
  --artist "Claude Monet" \
  --subject "Water Lilies" \
  --output-id monet-001
```

With detailed planning (recommended):
```sh
python main.py \
  --artist "Vincent van Gogh" \
  --subject "Starry night over a quiet village" \
  --expanded-subject "A swirling night sky filled with dynamic spiral patterns and bright stars dominates the upper canvas. Below, a peaceful village with a prominent church steeple nestles in rolling hills. The sky should feature Van Gogh's characteristic thick, energetic brushwork with deep blues transitioning to lighter tones near the horizon." \
  --output-id vangogh-starry-001 \
  --planner-model "mistral-large-latest"
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

Generate with LMStudio (local):
```sh
python main.py \
  --artist "Claude Monet" \
  --subject "Water Lilies" \
  --output-id monet-001 \
  --provider lmstudio
```

Override API key at runtime:
```sh
python main.py \
  --artist "Pablo Picasso" \
  --subject "Abstract Portrait" \
  --output-id picasso-001 \
  --api-key sk-your-key-here
```

### Generation Process

The application will:
1. **Planning Phase**: Generate a structured multi-layer painting plan using a planner LLM
2. Initialize a blank canvas (800×600 pixels)
3. Query the VLM for stroke suggestions guided by the current layer's plan
4. Apply suggested strokes to the canvas
5. Evaluate the current canvas against the artist's style and layer objectives
6. Advance to the next layer when evaluator indicates layer completion
7. Update strategy based on evaluation feedback
8. Repeat until target score is reached or max iterations exceeded
9. Generate a final report with metrics and layer breakdown
10. Create an animated GIF timelapse of the creation process

**Resumable**: If interrupted, re-running with the same `--output-id` will resume from the last completed iteration. The painting plan is saved and reused on resume.

### Output Structure

All outputs are saved to `src/output/{output-id}/`:

```
src/output/vangogh-001/
├── painting_plan.json      # Multi-layer painting plan (NEW in Phase 8)
├── timelapse.gif           # Animated creation timelapse
├── final_artwork.png       # Final completed artwork
├── final_artwork.jpeg      # Final artwork (JPEG format)
├── metadata.json           # Generation metadata
├── generation_report.md    # Human-readable summary
├── viewer_data.json        # Aggregated data for web viewer (auto-generated)
├── snapshots/              # Canvas images per iteration
│   ├── iteration-001.png
│   ├── iteration-002.png
│   └── ...
├── strokes/                # Stroke data per iteration (includes layer info)
│   ├── iteration-001.json
│   └── ...
├── evaluations/            # VLM evaluation results (includes layer completion)
│   ├── iteration-001.json
│   └── ...
└── strategies/             # Strategy updates
    ├── strategy-001.md
    └── ...
```

**Note**: `viewer_data.json` is automatically generated after each successful generation. This aggregated file contains all iteration data needed by the web viewer.

## Interactive Viewer

### Running the Viewer

The Next.js viewer provides an interactive web interface for exploring generated artworks:

```sh
pnpm -C src/viewer dev
```

View the gallery at: http://localhost:3000

### Features

- **Gallery View**: Browse all generated artworks with preview cards
- **Inspector**: Step through artwork creation stroke-by-stroke
- **Timeline Playback**: Animate the creation process with play/pause controls
- **Metadata Display**: View artist name, subject, scores, and generation statistics
- **Evaluation Insights**: See VLM feedback for each iteration (strengths, weaknesses, suggestions)
- **Stroke Details**: Examine individual stroke parameters, colors, and reasoning

### Preparing Data for the Viewer

**Automatic Export**: `viewer_data.json` is automatically generated after each successful artwork generation.

**Manual Export**: To re-export data for existing artworks:

```sh
conda activate paint-by-language-model
python -c "from src.paint_by_language_model.services.viewer_data_export import export_viewer_data; export_viewer_data('vangogh-001')"
```

**Copy to Viewer**: Copy artwork directories to the viewer's public data folder:

```sh
# Copy (for production builds)
cp -r src/output/vangogh-001 src/viewer/public/data/vangogh-001
```

**Minify for Production**: Reduce file sizes before deployment:

```sh
conda activate paint-by-language-model
python scripts/minify_viewer_data.py
```

### Building for Production

```sh
pnpm -C src/viewer build
pnpm -C src/viewer start  # Serves optimized production build
```

Or export static HTML:

```sh
pnpm -C src/viewer build
# Static files are in src/viewer/out/
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
  "subject": "Starry night over a quiet village",
  "expanded_subject": "A swirling night sky filled with dynamic spiral patterns...",
  "canvas_width": 800,
  "canvas_height": 600,
  "started_at": "2026-02-05T10:30:45.123456",
  "vlm_model": "pixtral-large-latest",
  "planner_model": "mistral-large-latest",
  "provider": "mistral",
  "painting_plan": {
    "total_layers": 4,
    "layers": [
      {"layer_number": 1, "name": "Sky background", "..." : "..."}
    ]
  },
  "layer_progression": {
    "1": 12,
    "2": 15,
    "3": 10,
    "4": 8
  }
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
  "suggestions": "Add more swirling patterns typical of Van Gogh",
  "layer_complete": false,
  "layer_number": 1
}
```

### Result

**"Millet style drawing of a person at a computer desk"**

<img width="515" height="383" alt="image" src="https://github.com/user-attachments/assets/03923116-8e5e-4851-9cd9-cb9997b61a8f" />


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

**Stroke Sample Images**:
- `STROKE_SAMPLE_WIDTH` / `STROKE_SAMPLE_HEIGHT` - Sample canvas dimensions (default: 200×100)
- `STROKE_SAMPLE_BACKGROUND` - Sample background colour (default: `#F5F5F5`)
- `STROKES_PER_SAMPLE` - Number of example strokes per sample image (default: 5)

**Stroke Constraints**:
- `MAX_STROKE_THICKNESS` / `MIN_STROKE_THICKNESS` - Thickness range (default: 1-10 pixels)
- `MAX_STROKE_OPACITY` / `MIN_STROKE_OPACITY` - Opacity range (default: 0.1-1.0)
- `SUPPORTED_STROKE_TYPES` - `["line", "arc", "polyline", "circle", "splatter"]`

**Provider Settings**:
- `PROVIDER` - VLM provider: `mistral` (default), `lmstudio`, or `anthropic`
- `MISTRAL_API_KEY` - API key for Mistral (loaded from `.env`)
- `ANTHROPIC_API_KEY` - API key for Anthropic (loaded from `.env`)
- `VLM_MODEL` - Stroke generation model (Mistral: `pixtral-large-latest`, LMStudio: `lmistralai/ministral-3-3b`)
- `EVALUATION_VLM_MODEL` - Style evaluation model
- `PLANNER_MODEL` - Planning LLM model (Mistral: `mistral-large-latest`, LMStudio: `local-model`)
- `VLM_TIMEOUT` - Request timeout (default: 180 seconds)
- `PLANNER_TIMEOUT` - Planning request timeout (default: 180 seconds)
- `STROKE_PROMPT_TEMPERATURE` - Creativity setting (default: 0.7)
- `EVALUATION_PROMPT_TEMPERATURE` - Consistency setting (default: 0.3)
- `PLANNER_PROMPT_TEMPERATURE` - Planning creativity (default: 0.4)

**Generation Loop**:
- `MAX_ITERATIONS` - Safety limit (default: 10000)
- `MIN_ITERATIONS` - Minimum before early stop (default: 20)

**GIF Generation**:
- `GIF_FRAME_DURATION_MS` - Frame duration in milliseconds (default: 150)
- `GIF_FINAL_FRAME_HOLD_MS` - Final frame hold duration (default: 1500)
- `GIF_MAX_DIMENSION` - Max frame width/height for file size optimization (default: 400px)
- `GIF_LOOP_COUNT` - Animation loop count, 0 = infinite (default: 0)
- `TARGET_STYLE_SCORE` - Target score 0-100 (default: 75.0)

**Strategy Management**:
- `STRATEGY_CONTEXT_WINDOW` - Recent strategies to include (default: 5)
- `STROKE_PROMPT_INCLUDE_STRATEGY` - Include strategy context (default: True)

## Architecture

### Python Backend Components

- **Generation Orchestrator** ([generation_orchestrator.py](src/paint_by_language_model/generation_orchestrator.py))
  - Main entry point for generation workflow
  - Runs planning phase before generation begins
  - Coordinates all components (canvas, VLMs, strategy)
  - Handles layer-aware iteration loop and stopping conditions
  - Tracks layer progression and advancement
  - Supports resumable generation with plan persistence
  - Auto-exports viewer data on completion

- **Canvas Manager** ([services/canvas_manager.py](src/paint_by_language_model/services/canvas_manager.py))
  - Manages image canvas with PIL
  - Applies strokes (lines, arcs, polylines, circles, splatters)
  - Validates stroke parameters
  - Saves snapshots
  - Delegates rendering to `StrokeRendererFactory`

- **Planner LLM Client** ([services/planner_llm_client.py](src/paint_by_language_model/services/planner_llm_client.py))
  - Generates structured multi-layer painting plans before generation
  - Uses separate (potentially more capable) text-only model
  - Produces layer-by-layer guidance with palettes, techniques, and objectives
  - Validates and parses plan responses into structured data
  - Plans are cached to disk for resume support

- **Stroke VLM Client** ([services/stroke_vlm_client.py](src/paint_by_language_model/services/stroke_vlm_client.py))
  - Queries VLMs with canvas image plus 5 stroke sample images (one per stroke type)
  - Builds layer-aware prompts with artist context, plan, and strategy
  - Prompt descriptions reference the attached visual sample for each stroke type
  - References current layer's palette, techniques, and objectives
  - Parses JSON responses robustly (handles malformed VLM output)
  - Supports batch stroke generation
  - Tracks interaction history for debugging

- **Stroke Sample Generator** ([services/stroke_sample_generator.py](src/paint_by_language_model/services/stroke_sample_generator.py))
  - Generates a 200×100 PNG sample image for each of the 5 stroke types
  - Each sample contains 5 varied example strokes (differing thickness, opacity, colour, position)
  - Uses the existing `CanvasManager` and renderer pipeline for pixel-accurate samples
  - In-memory cache prevents redundant regeneration across iterations
  - Initialised eagerly at `StrokeVLMClient` startup

- **Evaluation VLM Client** ([services/evaluation_vlm_client.py](src/paint_by_language_model/services/evaluation_vlm_client.py))
  - Evaluates canvas against target artist style and layer objectives
  - Returns style scores (0-100) and layer completion status
  - Provides strengths, weaknesses, and suggestions
  - Triggers layer advancement when objectives are met
  - Guides strategy updates

- **Strategy Manager** ([strategy_manager.py](src/paint_by_language_model/strategy_manager.py))
  - Manages multi-iteration context
  - Saves and loads strategy files
  - Prepends current layer context to strategy guidance
  - Provides recent strategy window for prompts
  - Tracks strategic evolution over iterations and layers

- **VLM Client** ([vlm_client.py](src/paint_by_language_model/vlm_client.py))
  - Provider-aware client supporting Mistral, LMStudio, and Anthropic APIs
  - Mistral and LMStudio use OpenAI-compatible format; Anthropic uses a non-OpenAI-compatible Messages API
  - Supports single-image multimodal queries (`query_multimodal()`) and multi-image queries (`query_multimodal_multi_image()`)
  - Multi-image method accepts a list of `(image_bytes, label)` tuples; each image is preceded by its label text block
  - Bearer token authentication (Mistral), `x-api-key` header (Anthropic), or no auth (LMStudio)
  - Rate-limit retry with exponential backoff (HTTP 429)
  - Configurable temperature per request

- **Viewer Data Export** ([services/viewer_data_export.py](src/paint_by_language_model/services/viewer_data_export.py))
  - Aggregates iteration data into `viewer_data.json`
  - Embeds base64-encoded snapshot images
  - Auto-exports after successful generation
  - Optimized format for web viewer performance

- **GIF Generator** ([services/gif_generator.py](src/paint_by_language_model/services/gif_generator.py))
  - Creates animated timelapses from iteration snapshots
  - Resizes frames for manageable file sizes
  - Configurable frame duration and looping
  - Auto-generates `timelapse.gif` on completion

- **Stroke Renderers** ([services/renderers/](src/paint_by_language_model/services/renderers/))
  - Modular rendering system for different stroke types
  - Implementations: line, arc, polyline, circle, splatter
  - Factory pattern for extensibility
  - Consistent parameter validation

### Next.js Viewer (Frontend)

- **Gallery** ([src/viewer/src/app/page.tsx](src/viewer/src/app/page.tsx))
  - Homepage displaying all generated artworks
  - Responsive grid of artwork cards
  - Static generation at build time

- **Inspector** ([src/viewer/src/app/inspect/[artworkId]/page.tsx](src/viewer/src/app/inspect/[artworkId]/page.tsx))
  - Interactive artwork viewer with timeline
  - Stroke-by-stroke playback controls
  - Side panel with metadata, evaluation scores, and stroke details
  - Canvas overlay rendering

- **Components**:
  - `StrokeCanvas`: HTML5 canvas for rendering strokes
  - `Timeline`: Interactive timeline with play/pause controls
  - `SidePanel`: Metadata, evaluations, and stroke information
  - `Toolbar`: Playback controls and display options
  - `ArtworkCard`: Preview cards in gallery view
  - `Gallery`: Responsive grid layout

### Data Flow

1. **Generation**: Python backend creates artwork → saves iteration files
2. **Export**: `viewer_data.json` generated with aggregated data + base64 images
3. **Deployment**: Link/copy artwork folders to `src/viewer/public/data/`
4. **Build**: Next.js discovers artworks → generates static pages
5. **Runtime**: Client-side React components render interactive UI

### Data Models

- **PaintingPlan** ([models/painting_plan.py](src/paint_by_language_model/models/painting_plan.py)) - Multi-layer plan structure with layers, palettes, and techniques
- **PlanLayer** ([models/painting_plan.py](src/paint_by_language_model/models/painting_plan.py)) - Individual layer specification within a plan
- **Stroke** ([models/stroke.py](src/paint_by_language_model/models/stroke.py)) - Drawing operation parameters
- **StrokeVLMResponse** ([models/stroke_vlm_response.py](src/paint_by_language_model/models/stroke_vlm_response.py)) - VLM response structure
- **EvaluationResult** ([models/evaluation_result.py](src/paint_by_language_model/models/evaluation_result.py)) - Style evaluation data with layer completion status
- **CanvasState** ([models/canvas_state.py](src/paint_by_language_model/models/canvas_state.py)) - Canvas state snapshot

## Development Roadmap

- [x] Phase 1: Text-based artist analysis
- [x] Phase 2: Generation orchestrator & CLI
- [x] Phase 3: Additional stroke types (arc, polyline, circle, splatter), multiple strokes per iteration
- [x] Phase 4: Provider-agnostic VLM client (Mistral API + LMStudio)
- [x] Phase 5: Interactive Next.js viewer with timeline playback
- [x] Phase 6: Advanced stroke types and rendering techniques
- [x] Phase 7: Multi-layer strategy management
- [x] Phase 8: Multi-layer planning phase with structured painting plans
- [ ] Phase 9: Public deployment and gallery hosting
- [x] Phase 10: Anthropic API provider support
- [x] Phase 11: Stroke sample images in VLM prompt for visual context
