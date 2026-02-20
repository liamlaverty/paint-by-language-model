"""Generation Orchestrator for iterative image generation."""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from config import (
    CANVAS_BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_STROKES_PER_QUERY,
    EVALUATION_VLM_MODEL,
    GIF_FILENAME,
    GIF_FRAME_DURATION_MS,
    IMAGE_EXPORT_FORMATS,
    MAX_ITERATIONS,
    MIN_ITERATIONS,
    NEXTJS_VIEWER_DATA_DIR,
    OUTPUT_DIR,
    OUTPUT_STRUCTURE,
    PLANNER_MODEL,
    SUPPORTED_STROKE_TYPES,
    TARGET_STYLE_SCORE,
    VIEWER_DATA_FILENAME,
    VLM_MODEL,
)
from models import EvaluationResult, PaintingPlan, PlanLayer, Stroke
from services import CanvasManager, EvaluationVLMClient, PlannerLLMClient, StrokeVLMClient
from services.gif_generator import GifGenerator
from strategy_manager import StrategyManager
from utils.json_utils import minify_json_file

logger = logging.getLogger(__name__)


class GenerationOrchestrator:
    """Orchestrates the iterative image generation process."""

    def __init__(
        self,
        artist_name: str,
        subject: str,
        artwork_id: str,
        output_dir: Path = OUTPUT_DIR,
        strokes_per_query: int = DEFAULT_STROKES_PER_QUERY,
        gif_frame_duration: int = GIF_FRAME_DURATION_MS,
        expanded_subject: str | None = None,
    ) -> None:
        """
        Initialize Generation Orchestrator.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject to paint
            artwork_id (str): Unique artwork identifier
            output_dir (Path): Base output directory
            strokes_per_query (int): Number of strokes to request per VLM query
            gif_frame_duration (int): GIF frame duration in milliseconds
            expanded_subject (str | None): Detailed description of the final image
        """
        self.artist_name = artist_name
        self.subject = subject
        self.expanded_subject = expanded_subject
        self.artwork_id = artwork_id
        self.output_dir = output_dir
        self.artwork_dir = output_dir / artwork_id
        self.strokes_per_query = strokes_per_query
        self.gif_frame_duration = gif_frame_duration

        # Initialize components
        logger.info(f"Initializing generation for '{subject}' in style of {artist_name}")

        self.canvas_manager = CanvasManager()
        self.stroke_vlm = StrokeVLMClient()
        self.eval_vlm = EvaluationVLMClient()
        self.strategy_manager = StrategyManager(artwork_id=artwork_id, output_dir=output_dir)

        # Log provider information
        import config

        logger.info(f"Using provider: {config.PROVIDER} ({config.API_BASE_URL})")

        # Tracking
        self.evaluations: list[EvaluationResult] = []
        self.strokes: list[Stroke] = []
        self.generation_start_time = datetime.now()
        self.starting_iteration = 1

        # Batch statistics tracking
        self.total_strokes_requested = 0
        self.total_strokes_applied = 0
        self.total_strokes_skipped = 0
        self.stroke_type_counts: dict[str, int] = {}

        # Painting plan tracking
        self.painting_plan: PaintingPlan | None = None
        self.current_layer_index: int = 0
        self.layer_iterations: dict[int, int] = {}

        # Create output directories
        self._create_output_directories()

        # Check for existing work and resume if present
        self._load_existing_state()

        logger.info(f"Orchestrator initialized for artwork: {artwork_id}")
        if self.starting_iteration > 1:
            logger.info(
                f"Resuming from iteration {self.starting_iteration} "
                f"({len(self.strokes)} strokes, {len(self.evaluations)} evaluations)"
            )

    def generate(self) -> dict[str, Any]:
        """
        Execute the complete generation loop.

        Returns:
            dict[str, Any]: Generation summary with metrics

        Raises:
            RuntimeError: If generation fails critically
            ConnectionError: If VLM servers are unreachable
        """
        logger.info("=" * 80)
        logger.info(f"Starting generation: {self.artwork_id}")
        logger.info(f"Artist: {self.artist_name}")
        logger.info(f"Subject: {self.subject}")
        if self.starting_iteration > 1:
            logger.info(f"Resuming from iteration {self.starting_iteration}")
        logger.info("=" * 80)

        # NEW: Run planning phase
        self.painting_plan = self._run_planning_phase()
        self._save_painting_plan(self.painting_plan)

        try:
            # Main iteration loop
            iteration = 1
            for iteration in range(self.starting_iteration, MAX_ITERATIONS + 1):
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Iteration {iteration}/{MAX_ITERATIONS}")
                logger.info(f"{'=' * 80}")

                # Determine current layer
                current_layer = (
                    self.painting_plan["layers"][self.current_layer_index]
                    if self.painting_plan
                    else None
                )

                # Execute single iteration
                should_stop = self._execute_iteration(iteration, current_layer)

                # Check stopping conditions
                if should_stop:
                    logger.info(f"Stopping condition met at iteration {iteration}")
                    break

            # Generation complete
            final_iteration = min(iteration, MAX_ITERATIONS)
            logger.info(f"\nGeneration complete after {final_iteration} iterations")

            # Save final artifacts
            summary = self._finalize_generation(final_iteration)

            return summary

        except KeyboardInterrupt:
            logger.warning("\nGeneration interrupted by user")
            final_iteration = len(self.evaluations)
            return self._finalize_generation(final_iteration, interrupted=True)

        except Exception as e:
            logger.error(f"Generation failed with error: {e}")
            raise RuntimeError(f"Generation failed: {e}") from e

    def _execute_iteration(self, iteration: int, current_layer: PlanLayer | None = None) -> bool:
        """
        Execute a single iteration of generation.

        Args:
            iteration (int): Current iteration number
            current_layer (PlanLayer | None): Current painting layer information

        Returns:
            bool: True if should stop, False to continue
        """
        try:
            # Step 1: Get strategy context
            strategy_context = self.strategy_manager.get_recent_strategies(
                current_iteration=iteration, current_layer=current_layer
            )
            logger.debug(f"Strategy context: {strategy_context[:100]}...")

            # Step 2: Get canvas image bytes
            canvas_bytes = self.canvas_manager.get_image_bytes()
            logger.debug(f"Canvas image: {len(canvas_bytes)} bytes")

            # Step 3: Query Stroke VLM for batch of strokes
            logger.info(f"Requesting {self.strokes_per_query} strokes from VLM...")
            try:
                stroke_response = self.stroke_vlm.suggest_strokes(
                    canvas_image=canvas_bytes,
                    artist_name=self.artist_name,
                    subject=self.subject,
                    iteration=iteration,
                    strategy_context=strategy_context,
                    num_strokes=self.strokes_per_query,
                    painting_plan=self.painting_plan,
                    current_layer=current_layer,
                    expanded_subject=self.expanded_subject,
                )
                strokes_batch = stroke_response["strokes"]
                batch_reasoning = stroke_response.get("batch_reasoning", "")
            except (ValueError, RuntimeError) as e:
                # Stroke VLM failed - log and skip this iteration
                logger.error(f"Stroke generation failed in iteration {iteration}: {e}")
                self._log_exception(iteration, e, "stroke_generation")
                logger.warning("Skipping this iteration and continuing...")
                return False  # Continue to next iteration

            logger.info(f"Received {len(strokes_batch)} strokes from VLM")
            if batch_reasoning:
                logger.info(f"Batch reasoning: {batch_reasoning[:100]}...")

            # Update statistics
            self.total_strokes_requested += self.strokes_per_query

            # Step 4: Apply strokes individually using batch method
            snapshot_dir = self.artwork_dir / OUTPUT_STRUCTURE["snapshots"]
            logger.info(f"Applying {len(strokes_batch)} strokes...")

            try:
                results = self.canvas_manager.apply_strokes(
                    strokes=strokes_batch,
                    save_snapshots=True,
                    snapshot_dir=snapshot_dir,
                    base_iteration=iteration,
                )
            except Exception as e:
                logger.error(f"Failed to apply stroke batch: {e}")
                self._log_exception(iteration, e, "stroke_batch_application")
                logger.warning("Skipping this iteration and continuing...")
                return False

            # Process results
            successful_strokes = [r for r in results if r["success"]]
            failed_strokes = [r for r in results if not r["success"]]

            # Log each stroke result
            for i, result in enumerate(results, 1):
                stroke = strokes_batch[
                    result["index"]
                ]  # Get stroke from original batch using index
                if result["success"]:
                    logger.info(f"  [{i}/{len(results)}] {stroke['type']}: ✓ applied")
                    self.strokes.append(stroke)
                    self.total_strokes_applied += 1

                    # Track stroke type counts
                    stroke_type = stroke["type"]
                    self.stroke_type_counts[stroke_type] = (
                        self.stroke_type_counts.get(stroke_type, 0) + 1
                    )
                else:
                    logger.warning(
                        f"  [{i}/{len(results)}] {stroke['type']}: ✗ skipped ({result['error']})"
                    )
                    self.total_strokes_skipped += 1

            logger.info(
                f"Batch complete: {len(successful_strokes)}/{len(strokes_batch)} applied, "
                f"{len(failed_strokes)} skipped (total strokes: {self.total_strokes_applied})"
            )

            # Step 4b: Save batch metadata
            self._save_stroke_batch(
                strokes_batch, iteration, batch_reasoning, results, current_layer
            )

            # Update current stroke file with last successful stroke
            if successful_strokes:
                strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
                current_stroke_path = strokes_dir / "current-stroke.json"
                # Get the last successful stroke from the original batch
                last_successful_index = successful_strokes[-1]["index"]
                last_stroke = strokes_batch[last_successful_index]
                with open(current_stroke_path, "w", encoding="utf-8") as f:
                    json.dump(last_stroke, f, indent=2)
                logger.debug("Updated current-stroke.json")

            # Step 5: Save current iteration snapshot
            snapshot_dir = self.artwork_dir / OUTPUT_STRUCTURE["snapshots"]
            current_snapshot_path = snapshot_dir / "current-iteration.png"
            self.canvas_manager.image.save(current_snapshot_path, "PNG")
            logger.debug("Updated current-iteration.png")

            # Step 6: Update strategy if provided
            updated_strategy = stroke_response.get("updated_strategy")
            if updated_strategy:
                # Handle both string and dict types
                if isinstance(updated_strategy, dict):
                    # Convert dict to formatted string
                    strategy_text = json.dumps(updated_strategy, indent=2)
                else:
                    strategy_text = str(updated_strategy)

                self.strategy_manager.save_strategy(iteration=iteration, strategy=strategy_text)
                self.strategy_manager.save_current_strategy_link()
                logger.info("Updated strategy")

            # Step 7: Get updated canvas bytes for evaluation
            canvas_bytes = self.canvas_manager.get_image_bytes()

            # Step 8: Query Evaluation VLM
            logger.info("Requesting style evaluation from VLM...")
            try:
                evaluation = self.eval_vlm.evaluate_style(
                    canvas_image=canvas_bytes,
                    artist_name=self.artist_name,
                    subject=self.subject,
                    iteration=iteration,
                    painting_plan=self.painting_plan,
                    current_layer=current_layer,
                )

                self.evaluations.append(evaluation)
                logger.info(f"Evaluation score: {evaluation['score']:.1f}/100")
                logger.info(f"Feedback: {evaluation['feedback'][:100]}...")

                # Step 9: Save evaluation
                self._save_evaluation(evaluation)

                # Also save as current evaluation for easy viewing
                eval_dir = self.artwork_dir / OUTPUT_STRUCTURE["evaluations"]
                current_eval_path = eval_dir / "current-evaluation.json"
                with open(current_eval_path, "w", encoding="utf-8") as f:
                    json.dump(evaluation, f, indent=2)
                logger.debug("Updated current-evaluation.json")

                # Track layer iterations
                if current_layer:
                    layer_num = current_layer["layer_number"]
                    self.layer_iterations[layer_num] = self.layer_iterations.get(layer_num, 0) + 1

                # Check for layer advancement
                if (
                    evaluation.get("layer_complete", False)
                    and self.painting_plan is not None
                    and self.current_layer_index < len(self.painting_plan["layers"]) - 1
                ):
                    self.current_layer_index += 1
                    next_layer = self.painting_plan["layers"][self.current_layer_index]
                    logger.info(
                        f"Advancing to Layer {next_layer['layer_number']}: {next_layer['name']}"
                    )

                # Step 10: Check stopping conditions
                should_stop = self._check_stopping_conditions(iteration, evaluation)

            except (ValueError, RuntimeError) as e:
                # VLM evaluation failed - log and continue
                logger.error(f"Evaluation failed in iteration {iteration}: {e}")
                self._log_exception(iteration, e, "evaluation")
                logger.warning("Skipping evaluation for this iteration and continuing...")
                should_stop = False  # Continue despite evaluation failure

            return should_stop

        except ValueError as e:
            logger.error(f"Validation error in iteration {iteration}: {e}")
            logger.warning("Skipping this iteration and continuing...")
            return False  # Continue despite error

        except ConnectionError as e:
            logger.error(f"Connection error in iteration {iteration}: {e}")
            raise  # Stop generation on connection errors

        except Exception as e:
            logger.error(f"Unexpected error in iteration {iteration}: {e}")
            raise

    def _check_stopping_conditions(self, iteration: int, evaluation: EvaluationResult) -> bool:
        """
        Check if generation should stop.

        Args:
            iteration (int): Current iteration number
            evaluation (EvaluationResult): Latest evaluation

        Returns:
            bool: True if should stop, False to continue
        """
        # Condition 1: Max iterations reached
        if iteration >= MAX_ITERATIONS:
            logger.info(f"Max iterations ({MAX_ITERATIONS}) reached")
            return True

        # Condition 2: Target score achieved (after minimum iterations)
        if iteration >= MIN_ITERATIONS and evaluation["score"] >= TARGET_STYLE_SCORE:
            logger.info(
                f"Target score ({TARGET_STYLE_SCORE}) reached with score {evaluation['score']:.1f}"
            )
            return True

        # Condition 3: Score plateauing (optional, future enhancement)
        # Check if score hasn't improved significantly in recent iterations

        return False

    def _run_planning_phase(self) -> PaintingPlan:
        """
        Execute planning phase to generate or load painting plan.

        Returns:
            PaintingPlan: Complete painting plan with layers

        Raises:
            RuntimeError: If plan generation fails
        """
        plan_path = self.artwork_dir / "painting_plan.json"

        # Check if plan already exists on disk
        if plan_path.exists():
            with open(plan_path, encoding="utf-8") as f:
                plan: PaintingPlan = json.load(f)
            logger.info("Loaded existing plan from disk")
            return plan

        # Generate new plan
        logger.info("Generating new painting plan...")
        planner = PlannerLLMClient()
        plan = planner.generate_plan(
            self.artist_name, self.subject, self.expanded_subject, SUPPORTED_STROKE_TYPES
        )

        # Log plan summary
        logger.info(f"Generated plan: {plan['total_layers']} layers")
        for layer in plan["layers"]:
            logger.info(f"  Layer {layer['layer_number']}: {layer['name']}")

        return plan

    def _save_painting_plan(self, plan: PaintingPlan) -> None:
        """
        Save painting plan to disk.

        Args:
            plan (PaintingPlan): Painting plan to save
        """
        plan_path = self.artwork_dir / "painting_plan.json"
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
        logger.info(f"Saved painting plan to {plan_path}")

    def _create_output_directories(self) -> None:
        """Create all required output directories."""
        self.artwork_dir.mkdir(parents=True, exist_ok=True)

        for key, dirname in OUTPUT_STRUCTURE.items():
            if key not in [
                "metadata",
                "report",
                "final_artwork",
                "painting_plan",
            ]:  # These are files
                dir_path = self.artwork_dir / dirname
                dir_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Created output directories in {self.artwork_dir}")

    def _load_existing_state(self) -> None:
        """Load existing strokes and evaluations to resume generation."""
        # Load painting plan if present
        plan_path = self.artwork_dir / "painting_plan.json"
        if plan_path.exists():
            with open(plan_path, encoding="utf-8") as f:
                self.painting_plan = json.load(f)
            logger.info(
                f"Loaded existing painting plan with {len(self.painting_plan['layers'])} layers"
            )

        # Check if strokes directory exists and has files
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        if not strokes_dir.exists():
            logger.debug("No existing state found, starting fresh")
            return

        # Check for batch files first (new format)
        batch_files = sorted(strokes_dir.glob("iteration-*_batch.json"))

        if batch_files:
            logger.info(f"Found {len(batch_files)} batch files, loading state...")

            # Load batch metadata and replay strokes
            for batch_file in batch_files:
                try:
                    with open(batch_file, encoding="utf-8") as f:
                        batch_data = json.load(f)

                    # Update statistics from batch metadata
                    self.total_strokes_requested += batch_data["total_requested"]
                    self.total_strokes_applied += batch_data["applied_count"]
                    self.total_strokes_skipped += batch_data["skipped_count"]

                    # Replay only successful strokes
                    for result in batch_data["results"]:
                        if result["success"]:
                            stroke_idx = result["stroke_index"]
                            stroke = batch_data["strokes"][stroke_idx]
                            self.strokes.append(stroke)
                            self.canvas_manager.apply_stroke(stroke)

                            # Track stroke type
                            stroke_type = stroke["type"]
                            self.stroke_type_counts[stroke_type] = (
                                self.stroke_type_counts.get(stroke_type, 0) + 1
                            )

                except Exception as e:
                    logger.error(f"Failed to load batch from {batch_file}: {e}")
                    raise

            logger.info(
                f"Replayed {len(self.strokes)} strokes on canvas from {len(batch_files)} batches"
            )

            # Set starting iteration based on batch files
            self.starting_iteration = len(batch_files) + 1

            # Determine current layer and rebuild layer iterations from batches
            if self.painting_plan and batch_files:
                for batch_file in batch_files:
                    with open(batch_file, encoding="utf-8") as f:
                        batch_data = json.load(f)
                    layer_num = batch_data.get("layer_number")
                    if layer_num:
                        self.layer_iterations[layer_num] = (
                            self.layer_iterations.get(layer_num, 0) + 1
                        )

                # Set current layer index from most recent batch
                with open(batch_files[-1], encoding="utf-8") as f:
                    last_batch = json.load(f)
                last_layer_num = last_batch.get("layer_number")
                if last_layer_num:
                    # Find the index of this layer in the plan
                    for idx, layer in enumerate(self.painting_plan["layers"]):
                        if layer["layer_number"] == last_layer_num:
                            self.current_layer_index = idx
                            break
                    logger.info(f"Resuming on Layer {last_layer_num}")

        else:
            # Fall back to old single-stroke format for backward compatibility
            stroke_files = sorted(strokes_dir.glob("iteration-*.json"))
            if not stroke_files:
                logger.debug("No existing strokes found, starting fresh")
                return

            logger.info(
                f"Found {len(stroke_files)} existing stroke files (legacy format), loading state..."
            )

            # Load all strokes
            for stroke_file in stroke_files:
                try:
                    with open(stroke_file, encoding="utf-8") as f:
                        stroke = json.load(f)
                        self.strokes.append(stroke)
                        # Replay stroke on canvas
                        self.canvas_manager.apply_stroke(stroke)

                        # Track stroke type
                        stroke_type = stroke["type"]
                        self.stroke_type_counts[stroke_type] = (
                            self.stroke_type_counts.get(stroke_type, 0) + 1
                        )
                except Exception as e:
                    logger.error(f"Failed to load stroke from {stroke_file}: {e}")
                    raise

            logger.info(f"Replayed {len(self.strokes)} strokes on canvas")

            # Set statistics for legacy format
            self.total_strokes_applied = len(self.strokes)
            self.total_strokes_requested = len(self.strokes)  # Assume 1:1 for legacy

            # Set starting iteration to next after loaded state
            self.starting_iteration = len(self.strokes) + 1

        # Load existing evaluations
        eval_dir = self.artwork_dir / OUTPUT_STRUCTURE["evaluations"]
        if eval_dir.exists():
            eval_files = sorted(eval_dir.glob("iteration-*.json"))
            for eval_file in eval_files:
                try:
                    with open(eval_file, encoding="utf-8") as f:
                        evaluation = json.load(f)
                        self.evaluations.append(evaluation)
                except Exception as e:
                    logger.error(f"Failed to load evaluation from {eval_file}: {e}")
                    raise

            logger.info(f"Loaded {len(self.evaluations)} evaluations")

        logger.info(f"Will resume from iteration {self.starting_iteration}")

    def _log_exception(self, iteration: int, exception: Exception, error_type: str) -> None:
        """
        Log exception details to file for debugging.

        Args:
            iteration (int): Iteration number where error occurred
            exception (Exception): The exception that was raised
            error_type (str): Type of error (e.g., "evaluation", "stroke")
        """
        # Create exception log directory
        exception_log_dir = self.output_dir / "exception_logs" / self.artwork_id
        exception_log_dir.mkdir(parents=True, exist_ok=True)

        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"iteration-{iteration:03d}_{error_type}_{timestamp}.log"
        log_filepath = exception_log_dir / log_filename

        # Write exception details
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

        logger.info(f"Exception logged to: {log_filepath}")

    def _save_evaluation(self, evaluation: EvaluationResult) -> None:
        """
        Save evaluation to JSON file.

        Args:
            evaluation (EvaluationResult): Evaluation to save
        """
        eval_dir = self.artwork_dir / OUTPUT_STRUCTURE["evaluations"]
        filename = f"iteration-{evaluation['iteration']:03d}.json"
        filepath = eval_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(evaluation, f, indent=2)

        logger.debug(f"Saved evaluation: {filename}")

    def _save_stroke(self, stroke: Stroke, iteration: int) -> None:
        """
        Save individual stroke to JSON file.

        Args:
            stroke (Stroke): Stroke to save
            iteration (int): Current iteration number
        """
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        filename = f"iteration-{iteration:03d}.json"
        filepath = strokes_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(stroke, f, indent=2)

        logger.debug(f"Saved stroke: {filename}")

    def _save_stroke_batch(
        self,
        strokes: list[Stroke],
        iteration: int,
        batch_reasoning: str,
        results: list[dict[str, Any]],
        current_layer: PlanLayer | None = None,
    ) -> None:
        """
        Save batch of strokes with metadata to JSON file.

        Args:
            strokes (list[Stroke]): Strokes in batch
            iteration (int): Current iteration number
            batch_reasoning (str): VLM reasoning for this batch
            results (list[dict[str, Any]]): Application results for each stroke
            current_layer (PlanLayer | None): Current painting layer information
        """
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
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
            "results": [
                {
                    "stroke_index": i,
                    "stroke_type": strokes[r["index"]]["type"],  # Get stroke from original batch
                    "success": r["success"],
                    "error": r["error"] if not r["success"] else None,
                }
                for i, r in enumerate(results)
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, indent=2)

        logger.debug(f"Saved batch: {filename}")

    def _finalize_generation(
        self, final_iteration: int, interrupted: bool = False
    ) -> dict[str, Any]:
        """
        Finalize generation and save all artifacts.

        Args:
            final_iteration (int): Final iteration number
            interrupted (bool): Whether generation was interrupted

        Returns:
            dict[str, Any]: Generation summary
        """
        logger.info("\nFinalizing generation...")

        # Save final artwork
        final_artwork_path = self.artwork_dir / OUTPUT_STRUCTURE["final_artwork"]
        self.canvas_manager.save_final_artwork(
            output_path=final_artwork_path, formats=IMAGE_EXPORT_FORMATS
        )
        logger.info("Saved final artwork")

        # Save all strokes
        self._save_all_strokes()

        # Save viewer data for HTML Canvas viewer
        self._save_viewer_data()

        # Save all evaluations summary
        self._save_evaluations_summary()

        # Generate metadata
        metadata = self._generate_metadata(final_iteration, interrupted)
        self._save_metadata(metadata)

        # Generate human-readable report
        self._generate_report(metadata)

        # Generate timelapse GIF
        gif_generator = GifGenerator(frame_duration_ms=self.gif_frame_duration)
        snapshots_dir = self.artwork_dir / OUTPUT_STRUCTURE["snapshots"]
        gif_path = self.artwork_dir / GIF_FILENAME
        gif_result = gif_generator.generate(snapshots_dir, gif_path)
        if gif_result:
            logger.info(f"Saved timelapse GIF: {gif_result}")
        else:
            logger.warning("Could not generate timelapse GIF (no frames found)")

        # Summary
        summary = {
            "artwork_id": self.artwork_id,
            "artist_name": self.artist_name,
            "subject": self.subject,
            "total_iterations": final_iteration,
            "final_score": self.evaluations[-1]["score"] if self.evaluations else 0,
            "total_strokes": len(self.strokes),
            "interrupted": interrupted,
            "output_directory": str(self.artwork_dir),
            "timelapse_gif": str(gif_result) if gif_result else None,
        }

        logger.info("\n" + "=" * 80)
        logger.info("GENERATION SUMMARY")
        logger.info("=" * 80)
        for key, value in summary.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 80)

        return summary

    def _save_all_strokes(self) -> None:
        """Save all strokes to JSON file."""
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        filepath = strokes_dir / "all_strokes.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.strokes, f, indent=2)

        logger.info(f"Saved {len(self.strokes)} strokes")

    def _save_viewer_data(self) -> None:
        """Save enriched stroke data for the Next.js viewer app.

        Assembles stroke rendering data with iteration context, batch reasoning,
        and evaluation scores into a single ``viewer_data.json`` file. Writes to both
        the artwork's local ``viewer/`` directory (backward compatibility) and the
        Next.js app's ``public/data/`` directory.
        """
        # Build enriched strokes by cross-referencing batch files
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        batch_files = sorted(strokes_dir.glob("iteration-*_batch.json"))

        enriched_strokes: list[dict[str, Any]] = []
        global_index = 0

        for batch_file in batch_files:
            with open(batch_file, encoding="utf-8") as f:
                batch: dict[str, Any] = json.load(f)

            iteration: int = batch["iteration"]
            reasoning: str = batch.get("batch_reasoning", "")

            for i, result in enumerate(batch["results"]):
                if result["success"]:
                    stroke = batch["strokes"][result["stroke_index"]]
                    enriched_stroke: dict[str, Any] = {
                        "index": global_index,
                        "iteration": iteration,
                        "batch_position": i,
                        "batch_reasoning": reasoning,
                        "layer_number": batch.get("layer_number"),
                        "layer_name": batch.get("layer_name"),
                        **stroke,
                    }
                    enriched_strokes.append(enriched_stroke)
                    global_index += 1

        viewer_data: dict[str, Any] = {
            "metadata": {
                "artwork_id": self.artwork_id,
                "artist_name": self.artist_name,
                "subject": self.subject,
                "expanded_subject": self.expanded_subject,
                "canvas_width": CANVAS_WIDTH,
                "canvas_height": CANVAS_HEIGHT,
                "background_color": CANVAS_BACKGROUND_COLOR,
                "total_strokes": len(enriched_strokes),
                "total_iterations": len(batch_files),
                "score_progression": [e["score"] for e in self.evaluations],
                "generation_date": self.generation_start_time.isoformat(),
                "vlm_models": {
                    "stroke_generator": VLM_MODEL,
                    "evaluator": EVALUATION_VLM_MODEL,
                },
            },
            "painting_plan": self.painting_plan,
            "strokes": enriched_strokes,
        }

        # Write to artwork's own viewer/ directory (backward compat)
        local_viewer_dir = self.artwork_dir / OUTPUT_STRUCTURE["viewer"]
        local_viewer_dir.mkdir(parents=True, exist_ok=True)
        local_data_path = local_viewer_dir / VIEWER_DATA_FILENAME
        with open(local_data_path, "w", encoding="utf-8") as f:
            json.dump(viewer_data, f, indent=2)

        logger.info(
            f"Saved viewer data: {len(enriched_strokes)} enriched strokes to {local_data_path}"
        )

        # Write to Next.js public/data/<artwork_id>/
        nextjs_data_dir = NEXTJS_VIEWER_DATA_DIR / self.artwork_id
        nextjs_data_dir.mkdir(parents=True, exist_ok=True)
        nextjs_data_path = nextjs_data_dir / VIEWER_DATA_FILENAME
        with open(nextjs_data_path, "w", encoding="utf-8") as f:
            json.dump(viewer_data, f, indent=2)

        logger.info(f"Saved viewer data to Next.js app: {nextjs_data_path}")

        # Minify the Next.js viewer data file for production
        try:
            success, bytes_saved = minify_json_file(nextjs_data_path)
            if success and bytes_saved > 0:
                kb_saved = bytes_saved / 1024
                logger.info(f"Minified viewer data: {kb_saved:.1f} KB saved")
        except Exception as e:
            logger.warning(f"Failed to minify viewer data: {e}")

        # Generate and save thumbnail
        self._save_thumbnail(nextjs_data_dir / "thumbnail.png")

    def _save_thumbnail(self, dest_path: Path) -> None:
        """Save a resized thumbnail of the final artwork.

        Args:
            dest_path (Path): Destination path for the thumbnail PNG
        """
        final_png = self.artwork_dir / f"{OUTPUT_STRUCTURE['final_artwork']}.png"
        if final_png.exists():
            from PIL import Image

            img = Image.open(final_png)
            img.thumbnail((400, 400))
            img.save(dest_path, "PNG")
            logger.info(f"Saved thumbnail to {dest_path}")
        else:
            logger.debug(f"Final artwork not found at {final_png}, skipping thumbnail generation")

    def _save_evaluations_summary(self) -> None:
        """Save all evaluations to summary JSON file."""
        eval_dir = self.artwork_dir / OUTPUT_STRUCTURE["evaluations"]
        filepath = eval_dir / "all_evaluations.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.evaluations, f, indent=2)

        logger.info(f"Saved {len(self.evaluations)} evaluations")

    def _generate_metadata(self, final_iteration: int, interrupted: bool) -> dict[str, Any]:
        """
        Generate complete metadata.

        Args:
            final_iteration (int): Final iteration number
            interrupted (bool): Whether interrupted

        Returns:
            dict[str, Any]: Complete metadata
        """
        generation_end_time = datetime.now()
        duration = (generation_end_time - self.generation_start_time).total_seconds()

        # Calculate stroke statistics
        avg_applied_per_iteration = (
            self.total_strokes_applied / final_iteration if final_iteration > 0 else 0
        )

        metadata: dict[str, Any] = {
            "artwork_id": self.artwork_id,
            "artist_name": self.artist_name,
            "subject": self.subject,
            "generation_date": self.generation_start_time.isoformat(),
            "generation_end_date": generation_end_time.isoformat(),
            "generation_duration_seconds": duration,
            "total_iterations": final_iteration,
            "final_score": self.evaluations[-1]["score"] if self.evaluations else 0,
            "interrupted": interrupted,
            "canvas_dimensions": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT},
            "vlm_models": {
                "stroke_generator": VLM_MODEL,
                "evaluator": EVALUATION_VLM_MODEL,
            },
            "configuration": {
                "max_iterations": MAX_ITERATIONS,
                "target_style_score": TARGET_STYLE_SCORE,
                "min_iterations": MIN_ITERATIONS,
                "strokes_per_query": self.strokes_per_query,
            },
            "score_progression": [e["score"] for e in self.evaluations],
            "total_strokes": len(self.strokes),
            "batch_statistics": {
                "strokes_per_query_configured": self.strokes_per_query,
                "total_strokes_requested": self.total_strokes_requested,
                "total_strokes_applied": self.total_strokes_applied,
                "total_strokes_skipped": self.total_strokes_skipped,
                "average_applied_per_iteration": round(avg_applied_per_iteration, 2),
                "stroke_type_breakdown": self.stroke_type_counts,
            },
            "painting_plan": self.painting_plan,
            "layer_progression": self.layer_iterations,
            "planner_model": PLANNER_MODEL,
            "expanded_subject": self.expanded_subject,
        }

        return metadata

    def _save_metadata(self, metadata: dict[str, Any]) -> None:
        """
        Save metadata to JSON file.

        Args:
            metadata (dict[str, Any]): Metadata to save
        """
        filepath = self.artwork_dir / OUTPUT_STRUCTURE["metadata"]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info("Saved metadata")

    def _generate_report(self, metadata: dict[str, Any]) -> None:
        """
        Generate human-readable report.

        Args:
            metadata (dict[str, Any]): Generation metadata
        """
        filepath = self.artwork_dir / OUTPUT_STRUCTURE["report"]

        batch_stats = metadata["batch_statistics"]

        report = f"""# Generation Report: {self.artwork_id}

## Artwork Information
- **Artist Style**: {self.artist_name}
- **Subject**: {self.subject}"""

        if self.expanded_subject:
            report += f"\n- **Expanded Subject**: {self.expanded_subject}"

        report += f"""
- **Artwork ID**: {self.artwork_id}
"""

        if self.painting_plan:
            report += f"""
## Painting Plan
- **Total Layers**: {self.painting_plan["total_layers"]}
- **Overall Notes**: {self.painting_plan["overall_notes"]}

### Layers
"""
            for layer in self.painting_plan["layers"]:
                iterations = self.layer_iterations.get(layer["layer_number"], 0)
                report += f"""
#### Layer {layer["layer_number"]}: {layer["name"]}
- **Description**: {layer["description"]}
- **Iterations**: {iterations}
- **Palette**: {", ".join(layer["colour_palette"])}
- **Techniques**: {layer["techniques"]}
"""

        report += f"""
## Generation Details
- **Start Time**: {metadata["generation_date"]}
- **End Time**: {metadata["generation_end_date"]}
- **Duration**: {metadata["generation_duration_seconds"]:.1f} seconds
- **Total Iterations**: {metadata["total_iterations"]}
- **Total Strokes**: {metadata["total_strokes"]}
- **Interrupted**: {metadata["interrupted"]}

## Batch Statistics
- **Strokes Per Query (Configured)**: {batch_stats["strokes_per_query_configured"]}
- **Total Strokes Requested**: {batch_stats["total_strokes_requested"]}
- **Total Strokes Applied**: {batch_stats["total_strokes_applied"]}
- **Total Strokes Skipped**: {batch_stats["total_strokes_skipped"]}
- **Average Applied Per Iteration**: {batch_stats["average_applied_per_iteration"]:.2f}

### Stroke Type Breakdown
"""

        for stroke_type, count in sorted(batch_stats["stroke_type_breakdown"].items()):
            report += f"- **{stroke_type}**: {count}\n"

        report += f"""
## Results
- **Final Score**: {metadata["final_score"]:.1f}/100
- **Canvas Dimensions**: {metadata["canvas_dimensions"]["width"]}x{metadata["canvas_dimensions"]["height"]}

## Models Used
- **Stroke Generator**: {metadata["vlm_models"]["stroke_generator"]}
- **Evaluator**: {metadata["vlm_models"]["evaluator"]}

## Score Progression
"""

        for i, score in enumerate(metadata["score_progression"], 1):
            report += f"- Iteration {i}: {score:.1f}/100\n"

        report += "\n## Evaluation Feedback\n\n"
        report += f"### Final Evaluation (Iteration {metadata['total_iterations']})\n"

        if self.evaluations:
            final_eval = self.evaluations[-1]
            report += f"**Score**: {final_eval['score']:.1f}/100\n\n"
            report += f"**Feedback**: {final_eval['feedback']}\n\n"
            report += f"**Strengths**: {final_eval['strengths']}\n\n"
            report += f"**Suggestions**: {final_eval['suggestions']}\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info("Generated report")
