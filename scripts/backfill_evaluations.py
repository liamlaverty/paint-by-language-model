"""Backfill evaluation data into existing viewer_data.json files.

This one-off script adds the ``evaluations`` array to pre-Phase-17
``viewer_data.json`` files that were generated before evaluation data was
included in the viewer export.

For each artwork directory found under ``src/output/``:

1. Reads ``evaluations.json`` (saved by the orchestrator during generation).
2. Reads the existing ``viewer_data.json``.
3. Adds (or replaces) the ``evaluations`` key.
4. Writes the updated ``viewer_data.json`` back to both:
   - The artwork's local viewer directory (``<artwork>/viewer/viewer_data.json``)
   - The Next.js public data directory
     (``src/viewer/public/data/<artwork_id>/viewer_data.json``), if it exists.

Usage::

    conda activate paint-by-language-model
    python scripts/backfill_evaluations.py

The script is idempotent — running it multiple times is safe.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent
_OUTPUT_DIR = _PROJECT_ROOT / "src" / "output"
_NEXTJS_DATA_DIR = _PROJECT_ROOT / "src" / "viewer" / "public" / "data"

_EVALUATIONS_SUBDIR = "evaluations"
_EVALUATIONS_FILENAME = "all_evaluations.json"
_VIEWER_DATA_FILENAME = "viewer_data.json"
_LOCAL_VIEWER_SUBDIR = "viewer"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    """Load and return a JSON file.

    Args:
        path (Path): Path to the JSON file to load.

    Returns:
        Any: Parsed JSON content.

    Raises:
        FileNotFoundError: If *path* does not exist.
        json.JSONDecodeError: If *path* is not valid JSON.
    """
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: Path, data: Any) -> None:
    """Write *data* to *path* as JSON (overwrites).

    Args:
        path (Path): Destination file path.
        data (Any): JSON-serialisable data to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def _build_evaluations_list(
    raw_evaluations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract the fields required by the viewer from raw evaluation records.

    Args:
        raw_evaluations (list[dict[str, Any]]): Full evaluation records as saved
            by ``GenerationOrchestrator._save_evaluations()``.

    Returns:
        list[dict[str, Any]]: Filtered list containing only ``iteration``,
            ``score``, ``feedback``, ``strengths``, and ``suggestions``.
    """
    return [
        {
            "iteration": ev.get("iteration", i + 1),
            "score": ev.get("score", 0),
            "feedback": ev.get("feedback", ""),
            "strengths": ev.get("strengths", ""),
            "suggestions": ev.get("suggestions", ""),
        }
        for i, ev in enumerate(raw_evaluations)
    ]


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def backfill_artwork(artwork_dir: Path) -> None:
    """Backfill evaluation data for a single artwork directory.

    Args:
        artwork_dir (Path): Path to the artwork output directory
            (e.g. ``src/output/horse-battle-sketch-001/``).
    """
    artwork_id = artwork_dir.name
    evaluations_path = artwork_dir / _EVALUATIONS_SUBDIR / _EVALUATIONS_FILENAME
    local_viewer_data_path = artwork_dir / _LOCAL_VIEWER_SUBDIR / _VIEWER_DATA_FILENAME
    nextjs_data_path = _NEXTJS_DATA_DIR / artwork_id / _VIEWER_DATA_FILENAME

    # ------------------------------------------------------------------ #
    # 1.  Check that an evaluations.json exists                           #
    # ------------------------------------------------------------------ #
    if not evaluations_path.exists():
        logger.warning(
            f"[{artwork_id}] No evaluations/all_evaluations.json found — skipping."
        )
        return

    raw_evaluations: list[dict[str, Any]] = _load_json(evaluations_path)
    if not raw_evaluations:
        logger.info(f"[{artwork_id}] evaluations.json is empty — skipping.")
        return

    evaluations_list = _build_evaluations_list(raw_evaluations)
    logger.info(f"[{artwork_id}] Loaded {len(evaluations_list)} evaluations.")

    # ------------------------------------------------------------------ #
    # 2.  Update local viewer_data.json                                   #
    # ------------------------------------------------------------------ #
    if local_viewer_data_path.exists():
        viewer_data: dict[str, Any] = _load_json(local_viewer_data_path)
        viewer_data["evaluations"] = evaluations_list
        _save_json(local_viewer_data_path, viewer_data)
        logger.info(f"[{artwork_id}] Updated local viewer_data.json.")
    else:
        logger.warning(
            f"[{artwork_id}] Local viewer_data.json not found at {local_viewer_data_path} — skipping local write."
        )

    # ------------------------------------------------------------------ #
    # 3.  Update Next.js viewer_data.json (if present)                    #
    # ------------------------------------------------------------------ #
    if nextjs_data_path.exists():
        nextjs_viewer_data: dict[str, Any] = _load_json(nextjs_data_path)
        nextjs_viewer_data["evaluations"] = evaluations_list
        _save_json(nextjs_data_path, nextjs_viewer_data)
        logger.info(f"[{artwork_id}] Updated Next.js viewer_data.json.")
    else:
        logger.info(
            f"[{artwork_id}] No Next.js viewer_data.json found — skipping Next.js write."
        )


def main() -> None:
    """Entry point: iterate over all artwork directories and backfill evaluations."""
    if not _OUTPUT_DIR.exists():
        logger.error(f"Output directory not found: {_OUTPUT_DIR}")
        sys.exit(1)

    artwork_dirs = sorted(d for d in _OUTPUT_DIR.iterdir() if d.is_dir())

    if not artwork_dirs:
        logger.warning(f"No artwork directories found under {_OUTPUT_DIR}.")
        return

    logger.info(f"Found {len(artwork_dirs)} artwork director(y/ies) to process.")

    processed = 0
    skipped = 0

    for artwork_dir in artwork_dirs:
        try:
            backfill_artwork(artwork_dir)
            processed += 1
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[{artwork_dir.name}] Error during backfill: {exc}")
            skipped += 1

    logger.info(
        f"Backfill complete. Processed: {processed}, Skipped/Errored: {skipped}."
    )


if __name__ == "__main__":
    main()
