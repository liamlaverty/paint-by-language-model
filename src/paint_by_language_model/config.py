"""
Configuration settings for the paint-by-language-model application.

This module contains all configurable parameters for both Phase 1 (artist
analysis) and Phase 2 (image generation). Settings are organized by function
and include inline comments explaining their purpose.

To customize the system behavior, modify values in this file rather than
hardcoding values in other modules.

Organization:
    - Phase 1: Artist Analysis (text-based LLM queries)
    - Phase 2: Image Generation System
        - Canvas Settings: Dimensions, appearance
        - Stroke Constraints: Validation limits
        - VLM Settings: Model configuration
        - Generation Loop: Iteration controls
        - Strategy Management: Multi-iteration context
        - Output Structure: File organization
        - Logging: Debug output configuration
        - Performance: Optimization settings (future)
        - Validation: Input checking rules
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PHASE 1: Artist Analysis (Existing)
# ============================================================================

# File paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
ARTISTS_FILE = PROJECT_ROOT / "datafiles" / "artists.json"
OUTPUT_DIR = PROJECT_ROOT / "output"
GLOBAL_PROMPT_LOG_DIR = PROJECT_ROOT / "prompt_logs"


# ============================================================================
# PROVIDER CONFIGURATION
# ============================================================================

# Provider selection ("mistral" or "lmstudio")
PROVIDER = os.getenv("PROVIDER", "mistral")

# Mistral API settings
MISTRAL_BASE_URL = "https://api.mistral.ai/v1"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_DEFAULT_MODEL = "mistral-large-latest"
MISTRAL_VLM_MODEL = "mistral-large-latest"
MISTRAL_EVALUATION_VLM_MODEL = "mistral-large-latest"

# LMStudio API settings (for local development)
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
LMSTUDIO_MODEL = "local-model"
LMSTUDIO_VLM_MODEL = "lmistralai/ministral-3-3b"
LMSTUDIO_EVALUATION_VLM_MODEL = "lmistralai/ministral-3-3b"

# Anthropic API settings
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"
# ANTHROPIC_VLM_MODEL = "claude-sonnet-4-6"
# ANTHROPIC_EVALUATION_VLM_MODEL = "claude-sonnet-4-6"
# ANTHROPIC_PLANNER_MODEL = "claude-sonnet-4-6"
ANTHROPIC_DEFAULT_MODEL = "claude-opus-4-7"
ANTHROPIC_VLM_MODEL = "claude-opus-4-7"
ANTHROPIC_EVALUATION_VLM_MODEL = "claude-sonnet-4-6"
ANTHROPIC_PLANNER_MODEL = "claude-opus-4-7"
ANTHROPIC_VERSION = "2023-06-01"

# Planner LLM Settings
MISTRAL_PLANNER_MODEL = "mistral-large-latest"
LMSTUDIO_PLANNER_MODEL = "local-model"

# Resolved settings based on active provider
if PROVIDER == "mistral":
    API_BASE_URL = MISTRAL_BASE_URL
    API_KEY = MISTRAL_API_KEY
    DEFAULT_MODEL = MISTRAL_DEFAULT_MODEL
    VLM_MODEL = MISTRAL_VLM_MODEL
    EVALUATION_VLM_MODEL = MISTRAL_EVALUATION_VLM_MODEL
    PLANNER_MODEL = MISTRAL_PLANNER_MODEL
elif PROVIDER == "anthropic":
    API_BASE_URL = ANTHROPIC_BASE_URL
    API_KEY = ANTHROPIC_API_KEY
    DEFAULT_MODEL = ANTHROPIC_DEFAULT_MODEL
    VLM_MODEL = ANTHROPIC_VLM_MODEL
    EVALUATION_VLM_MODEL = ANTHROPIC_EVALUATION_VLM_MODEL
    PLANNER_MODEL = ANTHROPIC_PLANNER_MODEL
else:  # lmstudio
    API_BASE_URL = LMSTUDIO_BASE_URL
    API_KEY = ""  # No auth for LMStudio
    DEFAULT_MODEL = LMSTUDIO_MODEL
    VLM_MODEL = LMSTUDIO_VLM_MODEL
    EVALUATION_VLM_MODEL = LMSTUDIO_EVALUATION_VLM_MODEL
    PLANNER_MODEL = LMSTUDIO_PLANNER_MODEL

# Planner prompt settings
PLANNER_PROMPT_TEMPERATURE = 0.4
PLANNER_TIMEOUT = 180
PLANNER_MAX_TOKENS = 16384  # Planner needs much more tokens for detailed multi-layer plans

# Request settings
REQUEST_TIMEOUT = 120  # seconds - LLM responses can be slow
MAX_TOKENS = 8192


# ============================================================================
# PHASE 2: Image Generation System
# ============================================================================

# ----------------------------------------------------------------------------
# Canvas Settings
# ----------------------------------------------------------------------------

# Canvas dimensions (in pixels)
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# Canvas appearance
CANVAS_BACKGROUND_COLOR = "#FFFFFF"  # White background


# ----------------------------------------------------------------------------
# Stroke Constraints
# ----------------------------------------------------------------------------

# Thickness limits (in pixels)
MAX_STROKE_THICKNESS = 300
MIN_STROKE_THICKNESS = 1

# Opacity limits (0.0 = fully transparent, 1.0 = fully opaque)
MAX_STROKE_OPACITY = 1.0
MIN_STROKE_OPACITY = 0.1

# Supported stroke types (Phase 18 - expressive strokes added)
SUPPORTED_STROKE_TYPES = [
    "line",
    "arc",
    "polyline",
    "circle",
    "splatter",
    "dry-brush",
    "chalk",
    "wet-brush",
    "burn",
    "dodge",
]

# Arc constraints
MAX_ARC_ANGLE = 360
MIN_ARC_ANGLE = 1

# Polyline constraints
MAX_POLYLINE_POINTS = 50
MIN_POLYLINE_POINTS = 2

# Circle constraints
MAX_CIRCLE_RADIUS = 400
MIN_CIRCLE_RADIUS = 1

# Splatter constraints
MAX_SPLATTER_COUNT = 100
MIN_SPLATTER_COUNT = 1
MAX_SPLATTER_RADIUS = 200
MIN_SPLATTER_RADIUS = 5
MAX_DOT_SIZE = 20
MIN_DOT_SIZE = 1

# Dry-brush constraints
MIN_BRUSH_WIDTH = 4
MAX_BRUSH_WIDTH = 20
MIN_BRISTLE_COUNT = 3
MAX_BRISTLE_COUNT = 20
MIN_GAP_PROBABILITY = 0.0
MAX_GAP_PROBABILITY = 0.7

# Chalk constraints
MIN_CHALK_WIDTH = 2
MAX_CHALK_WIDTH = 20
MIN_GRAIN_DENSITY = 1
MAX_GRAIN_DENSITY = 8

# Wet-brush constraints
MIN_SOFTNESS = 1
MAX_SOFTNESS = 30
MIN_FLOW = 0.1
MAX_FLOW = 1.0

# Burn/Dodge constraints
MIN_BURN_DODGE_RADIUS = 5
MAX_BURN_DODGE_RADIUS = 300
MIN_BURN_DODGE_INTENSITY = 0.05
MAX_BURN_DODGE_INTENSITY = 0.8


# ----------------------------------------------------------------------------
# Stroke Sample Image Settings
# ----------------------------------------------------------------------------

# Dimensions for stroke sample images sent alongside canvas in VLM prompts
STROKE_SAMPLE_WIDTH = 200
STROKE_SAMPLE_HEIGHT = 100

# Background colour for stroke sample images
STROKE_SAMPLE_BACKGROUND = "#F5F5F5"

# Number of strokes to render per sample image
STROKES_PER_SAMPLE = 5

# Directory where generated stroke sample PNGs are persisted
STROKE_SAMPLE_DIR = PROJECT_ROOT / "datafiles" / "stroke_samples"

# ----------------------------------------------------------------------------
# VLM (Vision Language Model) Settings
# ----------------------------------------------------------------------------

# VLM request timeout (VLMs are significantly slower than text-only LLMs)
VLM_TIMEOUT = 180  # 3 minutes

# VLM prompt temperature settings
STROKE_PROMPT_TEMPERATURE = 0.7  # Higher for creativity in stroke generation
EVALUATION_PROMPT_TEMPERATURE = 0.3  # Lower for consistency in scoring

# Multi-stroke query settings (Phase 3)
DEFAULT_STROKES_PER_QUERY = 5  # Default number of strokes to request per VLM query
MAX_STROKES_PER_QUERY = 20  # Maximum strokes allowed in a single query
MIN_STROKES_PER_QUERY = 1  # Minimum strokes (1 for backward compatibility)


# ----------------------------------------------------------------------------
# Generation Loop Settings
# ----------------------------------------------------------------------------

# Maximum iterations before stopping (safety limit)
MAX_ITERATIONS = 150

# Minimum iterations before considering early stopping
MIN_ITERATIONS = 10

# Target style score to stop generation (0-100 scale)
TARGET_STYLE_SCORE = 70.0

# Minimum expected score improvement per iteration
MIN_STYLE_SCORE_IMPROVEMENT = 2.0

# Minimum iterations per layer before allowing layer advancement.
# Each iteration applies one batch of strokes (strokes_per_query, default 5).
# The stroke VLM may continue a layer beyond this minimum, but cannot signal
# layer_complete: true until this threshold has been reached.
MIN_STROKES_PER_LAYER = 15


# ----------------------------------------------------------------------------
# Strategy Management Settings
# ----------------------------------------------------------------------------

# Number of recent strategies to include in VLM prompts
STRATEGY_CONTEXT_WINDOW = 5

# Strategy directory name (subdirectory under each artwork)
STRATEGY_DIR_NAME = "strategies"

# Whether to include strategy context in stroke prompts
STROKE_PROMPT_INCLUDE_STRATEGY = True


# ----------------------------------------------------------------------------
# Output Structure Settings
# ----------------------------------------------------------------------------

# Output subdirectory names
OUTPUT_STRUCTURE = {
    "snapshots": "snapshots",  # Intermediate canvas images
    "strategies": "strategies",  # Strategy markdown files
    "evaluations": "evaluations",  # Evaluation JSON files
    "strokes": "strokes",  # Stroke data JSON
    "metadata": "metadata.json",  # Generation metadata
    "final_artwork": "final_artwork",  # Final image (no extension)
    "report": "generation_report.md",  # Human-readable report
    "viewer": "viewer",  # HTML Canvas viewer
    "painting_plan": "painting_plan.json",  # Painting plan from planner VLM
    "prompt_log": "prompt-log",  # Full LLM prompt/response pairs
}

# Supported image export formats
IMAGE_EXPORT_FORMATS = ["PNG", "JPEG"]

# Default image export format for snapshots
SNAPSHOT_FORMAT = "PNG"


# ----------------------------------------------------------------------------
# GIF Generation Settings
# ----------------------------------------------------------------------------

# Frame duration in milliseconds (controls playback speed)
GIF_FRAME_DURATION_MS = 150  # ~6.7 fps

# Hold duration on the final frame (lets viewers appreciate finished artwork)
GIF_FINAL_FRAME_HOLD_MS = 1500

# Max width or height in pixels (frames resized to keep GIF file size manageable)
GIF_MAX_DIMENSION = 400

# Output filename for the timelapse GIF
GIF_FILENAME = "timelapse.gif"

# Loop count (0 = infinite loop)
GIF_LOOP_COUNT = 0


# ----------------------------------------------------------------------------
# Viewer Settings
# ----------------------------------------------------------------------------

# Viewer output directory name (subdirectory under each artwork)
VIEWER_DIR_NAME = "viewer"

# Viewer data filename
VIEWER_DATA_FILENAME = "viewer_data.json"

# Path to the Next.js viewer's public data directory
NEXTJS_VIEWER_DIR = PROJECT_ROOT / "viewer"
NEXTJS_VIEWER_DATA_DIR = NEXTJS_VIEWER_DIR / "public" / "data"


# ----------------------------------------------------------------------------
# Logging Settings
# ----------------------------------------------------------------------------

# Log level for generation process
GENERATION_LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR

# Whether to log VLM raw responses (useful for debugging)
LOG_VLM_RAW_RESPONSES = False


# ----------------------------------------------------------------------------
# Performance Settings
# ----------------------------------------------------------------------------

# Whether to resize canvas images before sending to VLM (reduces tokens)
RESIZE_FOR_VLM = False  # Future optimization

# Target size for VLM queries if resizing is enabled
VLM_IMAGE_MAX_DIMENSION = 512  # pixels


# ----------------------------------------------------------------------------
# Validation Settings
# ----------------------------------------------------------------------------

# Whether to validate stroke coordinates strictly
STRICT_STROKE_VALIDATION = True

# Whether to allow strokes with zero length
ALLOW_ZERO_LENGTH_STROKES = False

# Color hex pattern for validation
COLOR_HEX_PATTERN = r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$"  # Accepts 6 or 8 chars (with alpha)
