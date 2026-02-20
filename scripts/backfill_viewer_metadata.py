"""Backfill metadata fields into existing viewer_data.json files.

Reads every artwork directory under ``src/viewer/public/data/``, checks for a
corresponding ``src/output/<artwork_id>/metadata.json``, and — if found — copies
``generation_date``, ``vlm_models``, ``final_score``, ``planner_model``,
``batch_statistics``, and ``layer_progression`` into the ``viewer_data.json``
metadata block.  Also copies ``generation_report.md`` to the viewer data directory.

The updated JSON is written back minified (no indentation) to keep file sizes small.

Usage (from project root):
    conda activate paint-by-language-model
    python scripts/backfill_viewer_metadata.py
    python scripts/backfill_viewer_metadata.py --dry-run
"""

import argparse
import json
import logging
import shutil
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
REPORT_FILENAME = "generation_report.md"


def backfill_artwork(artwork_id: str, dry_run: bool = False) -> bool:
    """Backfill a single artwork's viewer_data.json with metadata fields.

    Reads ``viewer_data.json`` for the given artwork, attempts to locate a
    corresponding ``metadata.json`` in the output directory, and copies
    ``generation_date``, ``vlm_models``, ``final_score``, ``planner_model``,
    ``batch_statistics``, and ``layer_progression`` into the viewer data metadata
    block.  Also copies ``generation_report.md`` to the viewer data directory.

    Args:
        artwork_id (str): The artwork identifier (subdirectory name under public/data/).
        dry_run (bool): If True, log intended changes without writing any files.

    Returns:
        bool: True if the file was (or would be) updated, False if skipped.
    """
    viewer_data_path = VIEWER_DATA_DIR / artwork_id / VIEWER_DATA_FILENAME
    metadata_path = OUTPUT_DIR / artwork_id / METADATA_FILENAME

    if not viewer_data_path.exists():
        logger.warning(f"[{artwork_id}] viewer_data.json not found — skipping")
        return False

    if not metadata_path.exists():
        logger.warning(
            f"[{artwork_id}] metadata.json not found in src/output/ — skipping"
        )
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

    # Collect all fields to patch from metadata.json
    generation_date = metadata.get("generation_date")
    vlm_models = metadata.get("vlm_models")
    final_score = metadata.get("final_score")
    # Fallback: use stroke_generator model if planner_model is absent
    planner_model = metadata.get("planner_model") or (
        (metadata.get("vlm_models") or {}).get("stroke_generator")
    )
    batch_statistics = metadata.get("batch_statistics")
    layer_progression = metadata.get("layer_progression")

    if not any(
        [
            generation_date,
            vlm_models,
            final_score,
            planner_model,
            batch_statistics,
            layer_progression,
        ]
    ):
        logger.info(
            f"[{artwork_id}] No backfill fields available in metadata.json — skipping"
        )
        return False

    # Patch the metadata block
    meta_block: dict = viewer_data.setdefault("metadata", {})
    updates: dict = {}
    if generation_date is not None:
        updates["generation_date"] = generation_date
    if vlm_models is not None:
        updates["vlm_models"] = vlm_models
    if final_score is not None:
        updates["final_score"] = final_score
    if planner_model is not None:
        updates["planner_model"] = planner_model
    if batch_statistics is not None:
        updates["batch_statistics"] = batch_statistics
    if layer_progression is not None:
        updates["layer_progression"] = layer_progression

    if dry_run:
        logger.info(
            f"[{artwork_id}] DRY RUN — would update fields: {list(updates.keys())}"
        )
    else:
        meta_block.update(updates)
        with open(viewer_data_path, "w", encoding="utf-8") as f:
            json.dump(viewer_data, f, separators=(",", ":"))
        logger.info(f"[{artwork_id}] Updated fields: {list(updates.keys())}")

    # Copy generation_report.md if available
    _copy_report(artwork_id, dry_run=dry_run)

    return True


def _copy_report(artwork_id: str, dry_run: bool = False) -> None:
    """Copy generation_report.md from the output directory to the viewer data directory.

    Args:
        artwork_id (str): The artwork identifier.
        dry_run (bool): If True, log the copy without performing it.
    """
    report_src = OUTPUT_DIR / artwork_id / REPORT_FILENAME
    report_dest = VIEWER_DATA_DIR / artwork_id / REPORT_FILENAME

    if not report_src.exists():
        logger.info(
            f"[{artwork_id}] generation_report.md not found in output — skipping report copy"
        )
        return

    if dry_run:
        logger.info(f"[{artwork_id}] DRY RUN — would copy report to {report_dest}")
    else:
        shutil.copy2(report_src, report_dest)
        logger.info(f"[{artwork_id}] Copied generation_report.md to {report_dest}")


def main() -> None:
    """Scan all artwork directories and backfill viewer_data.json files.

    Parses CLI arguments, then iterates over every subdirectory in
    ``src/viewer/public/data/``, calling :func:`backfill_artwork` for each one.
    Prints a summary of updated vs skipped artworks on completion.
    """
    parser = argparse.ArgumentParser(
        description="Backfill viewer_data.json with metadata from metadata.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes without writing files",
    )
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN mode — no files will be written")

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
        if backfill_artwork(artwork_id, dry_run=args.dry_run):
            updated += 1
        else:
            skipped += 1

    logger.info(
        f"Backfill complete: {updated} updated, {skipped} skipped (total {len(artwork_dirs)})"
    )


if __name__ == "__main__":
    main()
