"""Artwork persistence service for file-write operations."""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from config import OUTPUT_STRUCTURE
from models import EvaluationResult, PlanLayer, Stroke

logger = logging.getLogger(__name__)


class ArtworkPersistence:
    """Handles all file-write operations for a single artwork run.

    This service centralises every write-to-disk operation so that
    ``GenerationOrchestrator`` does not contain direct ``json.dump`` /
    ``open`` calls for the extracted responsibilities.
    """

    def __init__(self, artwork_dir: Path, artwork_id: str, output_dir: Path) -> None:
        """Initialise the persistence service.

        Args:
            artwork_dir (Path): Root directory for this artwork run
                (e.g. ``output_dir / artwork_id``).
            artwork_id (str): Unique identifier for this artwork run.
            output_dir (Path): Base output directory that contains all
                artwork runs.
        """
        self.artwork_dir = artwork_dir
        self.artwork_id = artwork_id
        self.output_dir = output_dir

    # ------------------------------------------------------------------
    # Evaluation persistence
    # ------------------------------------------------------------------

    def save_evaluation(self, evaluation: EvaluationResult) -> None:
        """Save an evaluation result to a per-iteration JSON file.

        Args:
            evaluation (EvaluationResult): The evaluation result to save.
        """
        eval_dir = self.artwork_dir / OUTPUT_STRUCTURE["evaluations"]
        eval_dir.mkdir(parents=True, exist_ok=True)
        filename = f"iteration-{evaluation['iteration']:03d}.json"
        filepath = eval_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(evaluation, f, indent=2)

        logger.debug(f"Saved evaluation: {filename}")

    def save_evaluations_summary(self, evaluations: list[EvaluationResult]) -> None:
        """Save all evaluations to a single summary JSON file.

        Args:
            evaluations (list[EvaluationResult]): All evaluation results
                accumulated during the generation run.
        """
        eval_dir = self.artwork_dir / OUTPUT_STRUCTURE["evaluations"]
        eval_dir.mkdir(parents=True, exist_ok=True)
        filepath = eval_dir / "all_evaluations.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(evaluations, f, indent=2)

        logger.info(f"Saved {len(evaluations)} evaluations")

    # ------------------------------------------------------------------
    # Stroke persistence
    # ------------------------------------------------------------------

    def save_stroke_batch(
        self,
        strokes: list[Stroke],
        iteration: int,
        batch_reasoning: str,
        results: list[dict[str, Any]],
        current_layer: PlanLayer | None = None,
        layer_complete: bool | None = None,
    ) -> None:
        """Save a batch of strokes with per-stroke metadata to a JSON file.

        Args:
            strokes (list[Stroke]): The strokes that were requested in this
                batch.
            iteration (int): The iteration number used to name the file.
            batch_reasoning (str): The VLM's reasoning for the whole batch.
            results (list[dict[str, Any]]): Per-stroke application result
                dicts containing at least ``index``, ``success``, and
                ``error`` keys.
            current_layer (PlanLayer | None): The current painting layer,
                or ``None`` when no plan is active.
            layer_complete (bool | None): Whether the stroke VLM signalled
                that the current layer is complete.
        """
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        strokes_dir.mkdir(parents=True, exist_ok=True)
        filename = f"iteration-{iteration:03d}_batch.json"
        filepath = strokes_dir / filename

        applied_count = sum(1 for r in results if r["success"])
        skipped_count = sum(1 for r in results if not r["success"])

        batch_data = {
            "iteration": iteration,
            "strokes": strokes,
            "batch_reasoning": batch_reasoning,
            "applied_count": applied_count,
            "skipped_count": skipped_count,
            "total_requested": len(strokes),
            "timestamp": datetime.now().isoformat(),
            "layer_number": current_layer["layer_number"] if current_layer else None,
            "layer_name": current_layer["name"] if current_layer else None,
            "layer_complete": layer_complete,
            "results": [
                {
                    "stroke_index": i,
                    "stroke_type": strokes[r["index"]]["type"],
                    "success": r["success"],
                    "error": r["error"] if not r["success"] else None,
                }
                for i, r in enumerate(results)
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, indent=2)

        logger.debug(f"Saved batch: {filename}")

    def save_all_strokes(self, strokes: list[Stroke]) -> None:
        """Save the complete list of strokes to a single JSON file.

        Args:
            strokes (list[Stroke]): All strokes accumulated during the
                generation run.
        """
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        strokes_dir.mkdir(parents=True, exist_ok=True)
        filepath = strokes_dir / "all_strokes.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(strokes, f, indent=2)

        logger.info(f"Saved {len(strokes)} strokes")

    # ------------------------------------------------------------------
    # Metadata persistence
    # ------------------------------------------------------------------

    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save generation metadata to the metadata JSON file.

        Args:
            metadata (dict[str, Any]): The metadata dictionary assembled
                by the orchestrator.
        """
        filepath = self.artwork_dir / OUTPUT_STRUCTURE["metadata"]
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info("Saved metadata")

    # ------------------------------------------------------------------
    # Exception logging
    # ------------------------------------------------------------------

    def log_exception(
        self,
        iteration: int,
        exception: Exception,
        error_type: str,
        raw_response: str | None = None,
    ) -> None:
        """Write exception details to a timestamped log file for debugging.

        The log file is written to
        ``output_dir/exception_logs/<artwork_id>/``.

        Args:
            iteration (int): The iteration number at which the error
                occurred.
            exception (Exception): The exception that was raised.
            error_type (str): A short label for the error category, e.g.
                ``"evaluation"`` or ``"stroke_generation"``.
            raw_response (str | None): The raw text returned by the VLM
                before parsing, if available.
        """
        exception_log_dir = self.output_dir / "exception_logs" / self.artwork_id
        exception_log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"iteration-{iteration:03d}_{error_type}_{timestamp}.log"
        log_filepath = exception_log_dir / log_filename

        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(f"Exception Log - {self.artwork_id}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Iteration: {iteration}\n")
            f.write(f"Error Type: {error_type}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Exception: {type(exception).__name__}\n")
            f.write(f"Message: {str(exception)}\n\n")
            f.write("Traceback:\n")
            f.write("-" * 80 + "\n")
            f.write(traceback.format_exc())
            f.write("-" * 80 + "\n")

            if raw_response is not None:
                f.write("\nRaw VLM Response:\n")
                f.write("-" * 80 + "\n")
                f.write(raw_response)
                f.write("\n" + "-" * 80 + "\n")

        logger.info(f"Exception logged to: {log_filepath}")
