"""Configuration settings for the paint-by-language-model application."""
from pathlib import Path

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

# Canvas settings
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
CANVAS_BACKGROUND_COLOR = "#FFFFFF"

# Stroke constraints
MAX_STROKE_THICKNESS = 10
MIN_STROKE_THICKNESS = 1
MAX_STROKE_OPACITY = 1.0
MIN_STROKE_OPACITY = 0.1

# VLM (Vision Language Model) settings
VLM_MODEL = "lmistralai/ministral-3-3b"  # Or other multimodal model loaded in LMStudio
VLM_TIMEOUT = 180  # VLM queries are slower than text-only (3 minutes)
