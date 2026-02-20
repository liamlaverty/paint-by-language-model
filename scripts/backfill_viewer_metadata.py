"""Backfill `generation_date` and `vlm_models` fields into existing viewer_data.json files.

Reads every artwork directory under ``src/viewer/public/data/``, checks for a
corresponding ``src/output/<artwork_id>/metadata.json``, and — if found — copies
``generation_date`` and ``vlm_models`` into the ``viewer_data.json`` metadata block.

The updated JSON is written back minified (no indentation) to keep file sizes small.

Usage (from project root):
    conda activate paint-by-language-model
    python scripts/backfill_viewer_metadata.py
"""

import json
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path constants (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIEWER_DATA_DIR = PROJECT_ROOT / "src" / "viewer" / "public" / "data"
OUTPUT_DIR = PROJECT_ROOT / "src" / "output"
VIEWER_DATA_FILENAME = "viewer_data.json"
METADATA_FILENAME = "metadata.json"


def backfill_artwork(artwork_id: str) -> bool:
    """Backfill a single artwork's viewer_data.json with metadata fields.

    Reads ``viewer_data.json`` for the given artwork, attempts to locate a
    corresponding ``metadata.json`` in the output directory, and copies
    ``generation_date`` and ``vlm_models`` into the viewer data metadata block.

    Args:
        artwork_id (str): The artwork identifier (subdirectory name under public/data/).

    Returns:
        bool: True if the file was updated, False if skipped or no changes needed.
    """
    viewer_data_path = VIEWER_DATA_DIR / artwork_id / VIEWER_DATA_FILENAME
    metadata_path = OUTPUT_DIR / artwork_id / METADATA_FILENAME

    if not viewer_data_path.exists():
        logger.warning(f"[{artwork_id}] viewer_data.json not found — skipping")
        return False

    if not metadata_path.exists():
        logger.warning(f"[{artwork_id}] metadata.json not found in src/output/ — skipping")
        return False

    # Read files
    try:
        with open(viewer_data_path, encoding="utf-8") as f:
            viewer_data: dict = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error(f"[{artwork_id}] Failed to parse viewer_data.json: {exc}")
        return False

    try:
        with open(metadata_path, encoding="utf-8") as f:
            metadata: dict = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error(f"[{artwork_id}] Failed to parse metadata.json: {exc}")
        return False

    # Determine whether there is anything to copy
    generation_date = metadata.get("generation_date")
    vlm_models = metadata.get("vlm_models")

    if generation_date is None and vlm_models is None:
        logger.info(f"[{artwork_id}] No backfill fields available in metadata.json — skipping")
        return False

    # Check whether viewer_data already has both fields (idempotent)
    existing_meta: dict = viewer_data.get("metadata", {})
    already_has_date = existing_meta.get("generation_date") is not None
    already_has_models = existing_meta.get("vlm_models") is not None

    if already_has_date and already_has_models:
        logger.info(f"[{artwork_id}] Already has both fields — skipping (no change)")
        return False

    # Patch the metadata block
    if generation_date is not None:
        viewer_data["metadata"]["generation_date"] = generation_date
    if vlm_models is not None:
        viewer_data["metadata"]["vlm_models"] = vlm_models

    # Write back minified (separators removes whitespace)
    with open(viewer_data_path, "w", encoding="utf-8") as f:
        json.dump(viewer_data, f, separators=(",", ":"))

    logger.info(
        f"[{artwork_id}] Updated — generation_date={generation_date!r}, "
        f"vlm_models={vlm_models!r}"
    )
    return True


def main() -> None:
    """Scan all artwork directories and backfill viewer_data.json files.

    Iterates over every subdirectory in ``src/viewer/public/data/``, calling
    :func:`backfill_artwork` for each one. Prints a summary of updated vs skipped
    artworks on completion.
    """
    if not VIEWER_DATA_DIR.exists():
        logger.error(f"Viewer data directory not found: {VIEWER_DATA_DIR}")
        sys.exit(1)

    artwork_dirs = [d for d in VIEWER_DATA_DIR.iterdir() if d.is_dir()]

    if not artwork_dirs:
        logger.warning("No artwork directories found — nothing to backfill")
        return

    updated = 0
    skipped = 0

    for artwork_dir in sorted(artwork_dirs):
        artwork_id = artwork_dir.name
        if backfill_artwork(artwork_id):
            updated += 1
        else:
            skipped += 1

    logger.info(
        f"Backfill complete: {updated} updated, {skipped} skipped (total {len(artwork_dirs)})"
    )


if __name__ == "__main__":
    main()
