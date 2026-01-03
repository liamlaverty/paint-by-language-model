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
