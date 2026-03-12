"""Artwork state loader service for resuming interrupted generation runs."""

import json
import logging
from pathlib import Path
from typing import TypedDict

from config import OUTPUT_STRUCTURE
from models import EvaluationResult, PaintingPlan, Stroke
from services.canvas_manager import CanvasManager

logger = logging.getLogger(__name__)


class ArtworkState(TypedDict):
    """Snapshot of all resumable state for a generation run.

    Fields:
        strokes: All strokes that were successfully applied in the
            previous run(s), in order.
        evaluations: All evaluation results from the previous run(s).
        starting_iteration: The iteration number to start (or resume)
            from.  ``1`` when starting fresh, ``N+1`` when resuming
            after ``N`` completed iterations.
        total_strokes_applied: Cumulative count of strokes that were
            successfully applied to the canvas.
        total_strokes_requested: Cumulative count of strokes that were
            requested from the VLM (applied + skipped).
        total_strokes_skipped: Cumulative count of strokes that were
            requested but could not be applied.
        stroke_type_counts: Mapping of stroke-type name to the number
            of times it was successfully applied.
        current_layer_index: Zero-based index into the painting plan's
            layer list indicating the current layer.
        layer_iterations: Mapping of layer number to the count of
            iterations that were spent on that layer.
        painting_plan: The painting plan loaded from disk, or ``None``
            if no plan file exists yet.
    """

    strokes: list[Stroke]
    evaluations: list[EvaluationResult]
    starting_iteration: int
    total_strokes_applied: int
    total_strokes_requested: int
    total_strokes_skipped: int
    stroke_type_counts: dict[str, int]
    current_layer_index: int
    layer_iterations: dict[int, int]
    painting_plan: PaintingPlan | None


def _fresh_state() -> ArtworkState:
    """Return an ``ArtworkState`` representing a brand-new run with no history.

    Returns:
        ArtworkState: A state with ``starting_iteration=1``, empty
            collections, all counters set to zero, and
            ``painting_plan=None``.
    """
    return ArtworkState(
        strokes=[],
        evaluations=[],
        starting_iteration=1,
        total_strokes_applied=0,
        total_strokes_requested=0,
        total_strokes_skipped=0,
        stroke_type_counts={},
        current_layer_index=0,
        layer_iterations={},
        painting_plan=None,
    )


class ArtworkStateLoader:
    """Loads persisted artwork state to resume an interrupted generation run.

    The loader reads from the batch-file format produced by
    :class:`~services.artwork_persistence.ArtworkPersistence` and falls
    back to the legacy single-stroke format for backward compatibility.
    It also loads historical evaluations and an existing
    ``painting_plan.json`` when present.
    """

    def __init__(self, artwork_dir: Path) -> None:
        """Initialise the state loader.

        Args:
            artwork_dir (Path): Root directory for the artwork run, i.e.
                the directory that contains the ``strokes/``,
                ``evaluations/``, and ``painting_plan.json`` artefacts.
        """
        self.artwork_dir = artwork_dir

    def load(self, canvas_manager: CanvasManager) -> ArtworkState:
        """Load persisted state and replay strokes onto the canvas.

        The method checks for the presence of batch files
        (``iteration-*_batch.json``) first.  If none are found it falls
        back to legacy single-stroke files (``iteration-*.json``).
        Evaluations are always loaded from ``evaluations/iteration-*.json``
        regardless of which stroke format is used.

        When no existing files are found at all a fresh
        :class:`ArtworkState` is returned with ``starting_iteration=1``
        and all counters/collections initialised to their zero values.

        Args:
            canvas_manager (CanvasManager): The canvas manager instance
                onto which successfully-applied strokes will be replayed
                via :meth:`~services.canvas_manager.CanvasManager.apply_stroke`.

        Returns:
            ArtworkState: Fully populated state ready for the orchestrator
                to assign to its instance variables.
        """
        state = _fresh_state()

        # ------------------------------------------------------------------
        # 1. Load painting plan if present
        # ------------------------------------------------------------------
        plan_path = self.artwork_dir / "painting_plan.json"
        if plan_path.exists():
            with open(plan_path, encoding="utf-8") as f:
                plan: PaintingPlan = json.load(f)
            state["painting_plan"] = plan
            logger.info(f"Loaded existing painting plan with {len(plan['layers'])} layers")

        # ------------------------------------------------------------------
        # 2. Load stroke state
        # ------------------------------------------------------------------
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        if not strokes_dir.exists():
            logger.debug("No existing state found, starting fresh")
            return state

        batch_files = sorted(strokes_dir.glob("iteration-*_batch.json"))

        if batch_files:
            state = self._load_from_batch_files(batch_files, canvas_manager, state)
        else:
            stroke_files = sorted(strokes_dir.glob("iteration-*.json"))
            if not stroke_files:
                logger.debug("No existing strokes found, starting fresh")
            else:
                state = self._load_from_legacy_files(stroke_files, canvas_manager, state)

        # ------------------------------------------------------------------
        # 3. Load historical evaluations
        # ------------------------------------------------------------------
        eval_dir = self.artwork_dir / OUTPUT_STRUCTURE["evaluations"]
        if eval_dir.exists():
            eval_files = sorted(eval_dir.glob("iteration-*.json"))
            for eval_file in eval_files:
                try:
                    with open(eval_file, encoding="utf-8") as f:
                        state["evaluations"].append(json.load(f))
                except Exception as e:
                    logger.error(f"Failed to load evaluation from {eval_file}: {e}")
                    raise

            logger.info(f"Loaded {len(state['evaluations'])} evaluations")

        logger.info(f"Will resume from iteration {state['starting_iteration']}")
        return state

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_from_batch_files(
        self,
        batch_files: list[Path],
        canvas_manager: CanvasManager,
        state: ArtworkState,
    ) -> ArtworkState:
        """Load state from the batch-file format.

        Args:
            batch_files (list[Path]): Sorted list of batch JSON files.
            canvas_manager (CanvasManager): Canvas manager to replay
                strokes onto.
            state (ArtworkState): The state dict to populate and return.

        Returns:
            ArtworkState: Updated state with all batch data applied.
        """
        logger.info(f"Found {len(batch_files)} batch files, loading state...")

        for batch_file in batch_files:
            try:
                with open(batch_file, encoding="utf-8") as f:
                    batch_data = json.load(f)

                state["total_strokes_requested"] += batch_data["total_requested"]
                state["total_strokes_applied"] += batch_data["applied_count"]
                state["total_strokes_skipped"] += batch_data["skipped_count"]

                for result in batch_data["results"]:
                    if result["success"]:
                        stroke_idx = result["stroke_index"]
                        stroke: Stroke = batch_data["strokes"][stroke_idx]
                        state["strokes"].append(stroke)
                        canvas_manager.apply_stroke(stroke)

                        stroke_type: str = stroke["type"]
                        state["stroke_type_counts"][stroke_type] = (
                            state["stroke_type_counts"].get(stroke_type, 0) + 1
                        )

            except Exception as e:
                logger.error(f"Failed to load batch from {batch_file}: {e}")
                raise

        logger.info(
            f"Replayed {len(state['strokes'])} strokes on canvas from {len(batch_files)} batches"
        )

        state["starting_iteration"] = len(batch_files) + 1

        # Rebuild layer tracking from batch metadata
        painting_plan = state["painting_plan"]
        if painting_plan and batch_files:
            for batch_file in batch_files:
                with open(batch_file, encoding="utf-8") as f:
                    batch_data = json.load(f)
                layer_num = batch_data.get("layer_number")
                if layer_num:
                    state["layer_iterations"][layer_num] = (
                        state["layer_iterations"].get(layer_num, 0) + 1
                    )

            # Determine current layer index from most recent batch
            with open(batch_files[-1], encoding="utf-8") as f:
                last_batch = json.load(f)
            last_layer_num = last_batch.get("layer_number")
            if last_layer_num:
                for idx, layer in enumerate(painting_plan["layers"]):
                    if layer["layer_number"] == last_layer_num:
                        state["current_layer_index"] = idx
                        break
                logger.info(f"Resuming on Layer {last_layer_num}")

        return state

    def _load_from_legacy_files(
        self,
        stroke_files: list[Path],
        canvas_manager: CanvasManager,
        state: ArtworkState,
    ) -> ArtworkState:
        """Load state from the legacy single-stroke-per-file format.

        Args:
            stroke_files (list[Path]): Sorted list of legacy stroke JSON
                files (``iteration-NNN.json``).
            canvas_manager (CanvasManager): Canvas manager to replay
                strokes onto.
            state (ArtworkState): The state dict to populate and return.

        Returns:
            ArtworkState: Updated state with all legacy strokes applied.
        """
        logger.info(
            f"Found {len(stroke_files)} existing stroke files (legacy format), loading state..."
        )

        for stroke_file in stroke_files:
            try:
                with open(stroke_file, encoding="utf-8") as f:
                    stroke: Stroke = json.load(f)
                    state["strokes"].append(stroke)
                    canvas_manager.apply_stroke(stroke)

                    stroke_type: str = stroke["type"]
                    state["stroke_type_counts"][stroke_type] = (
                        state["stroke_type_counts"].get(stroke_type, 0) + 1
                    )
            except Exception as e:
                logger.error(f"Failed to load stroke from {stroke_file}: {e}")
                raise

        logger.info(f"Replayed {len(state['strokes'])} strokes on canvas")

        state["total_strokes_applied"] = len(state["strokes"])
        state["total_strokes_requested"] = len(state["strokes"])
        state["starting_iteration"] = len(state["strokes"]) + 1

        return state
