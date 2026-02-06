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

from pathlib import Path

# ============================================================================
# PHASE 1: Artist Analysis (Existing)
# ============================================================================

# LMStudio API settings
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
LMSTUDIO_MODEL = "local-model"  # LMStudio uses this as default

# Request settings
REQUEST_TIMEOUT = 120  # seconds - LLM responses can be slow
MAX_TOKENS = 1024

# File paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
ARTISTS_FILE = PROJECT_ROOT / "datafiles" / "artists.json"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Prompt template
PROMPT_TEMPLATE = """What are the notable features of {artist_name}'s artwork?
Please provide a structured response covering:
1. Artistic style and techniques
2. Common themes and subjects
3. Use of color and composition
4. Historical significance and influence
5. Most famous works

Respond in a clear, informative manner."""


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
MAX_STROKE_THICKNESS = 10
MIN_STROKE_THICKNESS = 1

# Opacity limits (0.0 = fully transparent, 1.0 = fully opaque)
MAX_STROKE_OPACITY = 1.0
MIN_STROKE_OPACITY = 0.1

# Supported stroke types (Phase 1 implementation)
SUPPORTED_STROKE_TYPES = ["line"]  # Future: ["line", "curve", "fill"]

# Arc constraints
MAX_ARC_ANGLE = 360
MIN_ARC_ANGLE = 1

# Polyline constraints
MAX_POLYLINE_POINTS = 50
MIN_POLYLINE_POINTS = 2

# Circle constraints
MAX_CIRCLE_RADIUS = 400
MIN_CIRCLE_RADIUS = 1


# ----------------------------------------------------------------------------
# VLM (Vision Language Model) Settings
# ----------------------------------------------------------------------------

# VLM model identifier
VLM_MODEL = "lmistralai/ministral-3-3b"  # Or other multimodal model loaded in LMStudio

# VLM request timeout (VLMs are significantly slower than text-only LLMs)
VLM_TIMEOUT = 180  # 3 minutes

# Evaluation VLM (can be same as or different from stroke VLM)
EVALUATION_VLM_MODEL = "lmistralai/ministral-3-3b"

# VLM prompt temperature settings
STROKE_PROMPT_TEMPERATURE = 0.7  # Higher for creativity in stroke generation
EVALUATION_PROMPT_TEMPERATURE = 0.3  # Lower for consistency in scoring


# ----------------------------------------------------------------------------
# Generation Loop Settings
# ----------------------------------------------------------------------------

# Maximum iterations before stopping (safety limit)
MAX_ITERATIONS = 10000

# Minimum iterations before considering early stopping
MIN_ITERATIONS = 20

# Target style score to stop generation (0-100 scale)
TARGET_STYLE_SCORE = 75.0

# Minimum expected score improvement per iteration
MIN_STYLE_SCORE_IMPROVEMENT = 2.0


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
}

# Supported image export formats
IMAGE_EXPORT_FORMATS = ["PNG", "JPEG"]

# Default image export format for snapshots
SNAPSHOT_FORMAT = "PNG"


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
