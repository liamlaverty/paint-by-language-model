"""Generation Orchestrator for iterative image generation."""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from config import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    EVALUATION_VLM_MODEL,
    IMAGE_EXPORT_FORMATS,
    MAX_ITERATIONS,
    MIN_ITERATIONS,
    OUTPUT_DIR,
    OUTPUT_STRUCTURE,
    TARGET_STYLE_SCORE,
    VLM_MODEL,
)
from models import EvaluationResult, Stroke
from services import CanvasManager, EvaluationVLMClient, StrokeVLMClient
from strategy_manager import StrategyManager

logger = logging.getLogger(__name__)


class GenerationOrchestrator:
    """Orchestrates the iterative image generation process."""

    def __init__(
        self,
        artist_name: str,
        subject: str,
        artwork_id: str,
        output_dir: Path = OUTPUT_DIR,
    ) -> None:
        """
        Initialize Generation Orchestrator.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject to paint
            artwork_id (str): Unique artwork identifier
            output_dir (Path): Base output directory
        """
        self.artist_name = artist_name
        self.subject = subject
        self.artwork_id = artwork_id
        self.output_dir = output_dir
        self.artwork_dir = output_dir / artwork_id

        # Initialize components
        logger.info(f"Initializing generation for '{subject}' in style of {artist_name}")

        self.canvas_manager = CanvasManager()
        self.stroke_vlm = StrokeVLMClient()
        self.eval_vlm = EvaluationVLMClient()
        self.strategy_manager = StrategyManager(artwork_id=artwork_id, output_dir=output_dir)

        # Tracking
        self.evaluations: list[EvaluationResult] = []
        self.strokes: list[Stroke] = []
        self.generation_start_time = datetime.now()
        self.starting_iteration = 1

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

        try:
            # Main iteration loop
            iteration = 1
            for iteration in range(self.starting_iteration, MAX_ITERATIONS + 1):
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Iteration {iteration}/{MAX_ITERATIONS}")
                logger.info(f"{'=' * 80}")

                # Execute single iteration
                should_stop = self._execute_iteration(iteration)

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

    def _execute_iteration(self, iteration: int) -> bool:
        """
        Execute a single iteration of generation.

        Args:
            iteration (int): Current iteration number

        Returns:
            bool: True if should stop, False to continue
        """
        try:
            # Step 1: Get strategy context
            strategy_context = self.strategy_manager.get_recent_strategies(
                current_iteration=iteration
            )
            logger.debug(f"Strategy context: {strategy_context[:100]}...")

            # Step 2: Get canvas image bytes
            canvas_bytes = self.canvas_manager.get_image_bytes()
            logger.debug(f"Canvas image: {len(canvas_bytes)} bytes")

            # Step 3: Query Stroke VLM for next stroke
            logger.info("Requesting stroke suggestion from VLM...")
            try:
                stroke_response = self.stroke_vlm.suggest_stroke(
                    canvas_image=canvas_bytes,
                    artist_name=self.artist_name,
                    subject=self.subject,
                    iteration=iteration,
                    strategy_context=strategy_context,
                )

                # TODO (Task 10): Handle multiple strokes properly
                stroke = stroke_response["strokes"][0]  # Get first stroke for backward compatibility
            except (ValueError, RuntimeError) as e:
                # Stroke VLM failed - log and skip this iteration
                logger.error(f"Stroke generation failed in iteration {iteration}: {e}")
                self._log_exception(iteration, e, "stroke_generation")
                logger.warning("Skipping this iteration and continuing...")
                return False  # Continue to next iteration
            logger.info(f"Received stroke batch: {stroke_response['batch_reasoning']}")

            # Step 4: Apply stroke to canvas
            self.canvas_manager.apply_stroke(stroke)
            self.strokes.append(stroke)
            logger.info(f"Applied stroke (total: {len(self.strokes)})")

            # Step 4b: Save individual stroke
            self._save_stroke(stroke, iteration)

            # Also save as current stroke for easy viewing
            strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
            current_stroke_path = strokes_dir / "current-stroke.json"
            with open(current_stroke_path, "w", encoding="utf-8") as f:
                json.dump(stroke, f, indent=2)
            logger.debug("Updated current-stroke.json")

            # Step 5: Save canvas snapshot
            snapshot_dir = self.artwork_dir / OUTPUT_STRUCTURE["snapshots"]
            snapshot_path = self.canvas_manager.save_snapshot(
                iteration=iteration, output_dir=snapshot_dir
            )
            logger.info(f"Saved snapshot: {snapshot_path.name}")

            # Also save as current iteration for easy viewing
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

    def _create_output_directories(self) -> None:
        """Create all required output directories."""
        self.artwork_dir.mkdir(parents=True, exist_ok=True)

        for key, dirname in OUTPUT_STRUCTURE.items():
            if key not in ["metadata", "report", "final_artwork"]:  # These are files
                dir_path = self.artwork_dir / dirname
                dir_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Created output directories in {self.artwork_dir}")

    def _load_existing_state(self) -> None:
        """Load existing strokes and evaluations to resume generation."""
        # Check if strokes directory exists and has files
        strokes_dir = self.artwork_dir / OUTPUT_STRUCTURE["strokes"]
        if not strokes_dir.exists():
            logger.debug("No existing state found, starting fresh")
            return

        # Load existing strokes
        stroke_files = sorted(strokes_dir.glob("iteration-*.json"))
        if not stroke_files:
            logger.debug("No existing strokes found, starting fresh")
            return

        logger.info(f"Found {len(stroke_files)} existing stroke files, loading state...")

        # Load all strokes
        for stroke_file in stroke_files:
            try:
                with open(stroke_file, encoding="utf-8") as f:
                    stroke = json.load(f)
                    self.strokes.append(stroke)
                    # Replay stroke on canvas
                    self.canvas_manager.apply_stroke(stroke)
            except Exception as e:
                logger.error(f"Failed to load stroke from {stroke_file}: {e}")
                raise

        logger.info(f"Replayed {len(self.strokes)} strokes on canvas")

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

        # Set starting iteration to next after loaded state
        if self.strokes:
            # Determine the highest iteration from loaded strokes
            max_iteration = len(self.strokes)
            self.starting_iteration = max_iteration + 1
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

        # Save all evaluations summary
        self._save_evaluations_summary()

        # Generate metadata
        metadata = self._generate_metadata(final_iteration, interrupted)
        self._save_metadata(metadata)

        # Generate human-readable report
        self._generate_report(metadata)

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
            },
            "score_progression": [e["score"] for e in self.evaluations],
            "total_strokes": len(self.strokes),
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

        report = f"""# Generation Report: {self.artwork_id}

## Artwork Information
- **Artist Style**: {self.artist_name}
- **Subject**: {self.subject}
- **Artwork ID**: {self.artwork_id}

## Generation Details
- **Start Time**: {metadata["generation_date"]}
- **End Time**: {metadata["generation_end_date"]}
- **Duration**: {metadata["generation_duration_seconds"]:.1f} seconds
- **Total Iterations**: {metadata["total_iterations"]}
- **Total Strokes**: {metadata["total_strokes"]}
- **Interrupted**: {metadata["interrupted"]}

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
