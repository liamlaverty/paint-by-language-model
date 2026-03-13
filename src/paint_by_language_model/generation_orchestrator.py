"""Generation Orchestrator for iterative image generation."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from config import (
    CANVAS_BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_STROKES_PER_QUERY,
    GIF_FILENAME,
    GIF_FRAME_DURATION_MS,
    IMAGE_EXPORT_FORMATS,
    MIN_ITERATIONS,
    NEXTJS_VIEWER_DATA_DIR,
    OUTPUT_DIR,
    OUTPUT_STRUCTURE,
    SUPPORTED_STROKE_TYPES,
    VIEWER_DATA_FILENAME,
)
from models import EvaluationResult, GenerationConfig, PaintingPlan, PlanLayer, Stroke
from services import (
    ArtworkPersistence,
    ArtworkStateLoader,
    CanvasManager,
    EvaluationVLMClient,
    PlannerLLMClient,
    StrokeVLMClient,
)
from services.gif_generator import GifGenerator
from services.prompt_logger import PromptLogger
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
        generation_config: GenerationConfig,
        output_dir: Path = OUTPUT_DIR,
        strokes_per_query: int = DEFAULT_STROKES_PER_QUERY,
        gif_frame_duration: int = GIF_FRAME_DURATION_MS,
        expanded_subject: str | None = None,
        allowed_stroke_types: list[str] | None = None,
    ) -> None:
        """
        Initialize Generation Orchestrator.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject to paint
            artwork_id (str): Unique artwork identifier
            generation_config (GenerationConfig): Fully-resolved runtime configuration
                for the generation run, including provider, API credentials, model
                identifiers, and iteration limits.
            output_dir (Path): Base output directory
            strokes_per_query (int): Number of strokes to request per VLM query
            gif_frame_duration (int): GIF frame duration in milliseconds
            expanded_subject (str | None): Detailed description of the final image
            allowed_stroke_types (list[str] | None): Restrict the stroke types the
                VLM may suggest.  When ``None`` all supported types are available
                (existing behaviour preserved).

        Raises:
            ValueError: If ``generation_config`` contains invalid values (empty
                ``api_base_url``, missing API key for authenticated providers, or
                ``min_strokes_per_layer < 1``).
        """
        # Validate config before anything else
        if not generation_config["api_base_url"]:
            raise ValueError("GenerationConfig.api_base_url must not be empty")
        if (
            generation_config["provider"] in ("mistral", "anthropic")
            and not generation_config["api_key"]
        ):
            raise ValueError(
                f"Provider '{generation_config['provider']}' requires an API key "
                "(set via --api-key or the relevant env var)"
            )
        if generation_config["min_strokes_per_layer"] < 1:
            raise ValueError("GenerationConfig.min_strokes_per_layer must be >= 1")

        self.artist_name = artist_name
        self.subject = subject
        self.expanded_subject = expanded_subject
        self.artwork_id = artwork_id
        self.output_dir = output_dir
        self.artwork_dir = output_dir / artwork_id
        self.strokes_per_query = strokes_per_query
        self.gif_frame_duration = gif_frame_duration
        self.allowed_stroke_types = allowed_stroke_types

        # Store runtime scalars from config
        self.max_iterations = generation_config["max_iterations"]
        self.target_style_score = generation_config["target_style_score"]
        self.min_strokes_per_layer = generation_config["min_strokes_per_layer"]
        self.provider = generation_config["provider"]
        self.vlm_model = generation_config["vlm_model"]
        self.evaluation_vlm_model = generation_config["evaluation_vlm_model"]
        self.planner_model = generation_config["planner_model"]

        # Initialize components
        logger.info(f"Initializing generation for '{subject}' in style of {artist_name}")

        self.prompt_logger = PromptLogger(artwork_dir=self.artwork_dir)
        self.canvas_manager = CanvasManager()
        self.stroke_vlm = StrokeVLMClient(
            base_url=generation_config["api_base_url"],
            model=generation_config["vlm_model"],
            api_key=generation_config["api_key"],
            prompt_logger=self.prompt_logger,
            allowed_stroke_types=self.allowed_stroke_types,
            min_strokes_per_layer=generation_config["min_strokes_per_layer"],
        )
        self.eval_vlm = EvaluationVLMClient(
            base_url=generation_config["api_base_url"],
            model=generation_config["evaluation_vlm_model"],
            api_key=generation_config["api_key"],
            prompt_logger=self.prompt_logger,
        )
        self.planner_vlm = PlannerLLMClient(
            base_url=generation_config["api_base_url"],
            model=generation_config["planner_model"],
            api_key=generation_config["api_key"],
            prompt_logger=self.prompt_logger,
            min_strokes_per_layer=generation_config["min_strokes_per_layer"],
        )
        self.strategy_manager = StrategyManager(artwork_id=artwork_id, output_dir=output_dir)

        # Persistence service
        self.persistence = ArtworkPersistence(
            artwork_dir=self.artwork_dir,
            artwork_id=self.artwork_id,
            output_dir=self.output_dir,
        )

        # Log provider information
        logger.info(f"Using provider: {self.provider} ({generation_config['api_base_url']})")

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
        loader = ArtworkStateLoader(artwork_dir=self.artwork_dir)
        state = loader.load(canvas_manager=self.canvas_manager)
        self.strokes = state["strokes"]
        self.evaluations = state["evaluations"]
        self.starting_iteration = state["starting_iteration"]
        self.total_strokes_applied = state["total_strokes_applied"]
        self.total_strokes_requested = state["total_strokes_requested"]
        self.total_strokes_skipped = state["total_strokes_skipped"]
        self.stroke_type_counts = state["stroke_type_counts"]
        self.current_layer_index = state["current_layer_index"]
        self.layer_iterations = state["layer_iterations"]
        self.painting_plan = state["painting_plan"]

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
            for iteration in range(self.starting_iteration, self.max_iterations + 1):
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Iteration {iteration}/{self.max_iterations}")
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
            final_iteration = min(iteration, self.max_iterations)
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
            current_layer_iteration_count = 0
            if current_layer:
                layer_num = current_layer["layer_number"]
                current_layer_iteration_count = self.layer_iterations.get(layer_num, 0)
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
                    layer_iteration_count=current_layer_iteration_count,
                )
                strokes_batch = stroke_response["strokes"]
                batch_reasoning = stroke_response.get("batch_reasoning", "")
            except (ValueError, RuntimeError) as e:
                # Stroke VLM failed - log and skip this iteration
                logger.error(f"Stroke generation failed in iteration {iteration}: {e}")
                self.persistence.log_exception(
                    iteration,
                    e,
                    "stroke_generation",
                    raw_response=self.stroke_vlm.last_raw_response,
                )
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
                self.persistence.log_exception(iteration, e, "stroke_batch_application")
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
            self.persistence.save_stroke_batch(
                strokes_batch,
                iteration,
                batch_reasoning,
                results,
                current_layer,
                layer_complete=stroke_response.get("layer_complete"),
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

            # Check for layer advancement (from stroke VLM)
            layer_complete_signal = stroke_response.get("layer_complete", False)
            if (
                layer_complete_signal
                and self.painting_plan is not None
                and self.current_layer_index < len(self.painting_plan["layers"]) - 1
            ):
                # Only advance if the minimum iterations for this layer have been met
                layer_num = current_layer["layer_number"] if current_layer else 0
                layer_iters = (
                    self.layer_iterations.get(layer_num, 0) + 1
                )  # +1 for current iteration
                if layer_iters >= self.min_strokes_per_layer:
                    self.current_layer_index += 1
                    next_layer = self.painting_plan["layers"][self.current_layer_index]
                    logger.info(
                        f"Advancing to Layer {next_layer['layer_number']}: {next_layer['name']} "
                        f"(after {layer_iters} iterations on layer {layer_num})"
                    )
                    # Update current_layer so evaluation uses the new layer
                    current_layer = next_layer
                else:
                    logger.info(
                        f"Layer complete signal received but ignored — only "
                        f"{layer_iters}/{self.min_strokes_per_layer} iterations completed "
                        f"for layer {layer_num}"
                    )

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
                self.persistence.save_evaluation(evaluation)

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

                # Check for graceful stop when the final layer signals completion
                if (
                    layer_complete_signal
                    and self.painting_plan is not None
                    and self.current_layer_index >= len(self.painting_plan["layers"]) - 1
                ):
                    layer_num = current_layer["layer_number"] if current_layer else 0
                    layer_iters = self.layer_iterations.get(
                        layer_num, 0
                    )  # Already incremented above
                    if layer_iters >= self.min_strokes_per_layer:
                        logger.info(
                            f"Final layer {layer_num} marked complete after {layer_iters} iterations "
                            f"— ending generation"
                        )
                        return True

                # Step 10: Check stopping conditions
                should_stop = self._check_stopping_conditions(iteration, evaluation)

            except (ValueError, RuntimeError) as e:
                # VLM evaluation failed - log and continue
                logger.error(f"Evaluation failed in iteration {iteration}: {e}")
                self.persistence.log_exception(
                    iteration,
                    e,
                    "evaluation",
                    raw_response=self.eval_vlm.last_raw_response,
                )
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
        if iteration >= self.max_iterations:
            logger.info(f"Max iterations ({self.max_iterations}) reached")
            return True

        # Condition 2: Target score achieved (after minimum iterations)
        if iteration >= MIN_ITERATIONS and evaluation["score"] >= self.target_style_score:
            logger.info(
                f"Target score ({self.target_style_score}) reached with score {evaluation['score']:.1f}"
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
        effective_stroke_types = self.allowed_stroke_types or SUPPORTED_STROKE_TYPES
        plan = self.planner_vlm.generate_plan(
            self.artist_name, self.subject, self.expanded_subject, effective_stroke_types
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
            ]:  # These are files, not directories
                dir_path = self.artwork_dir / dirname
                dir_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Created output directories in {self.artwork_dir}")

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
        self.persistence.save_all_strokes(self.strokes)

        # Save viewer data for HTML Canvas viewer
        self._save_viewer_data()

        # Save all evaluations summary
        self.persistence.save_evaluations_summary(self.evaluations)

        # Generate metadata
        metadata = self._generate_metadata(final_iteration, interrupted)
        self.persistence.save_metadata(metadata)

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
                    "stroke_generator": self.vlm_model,
                    "evaluator": self.evaluation_vlm_model,
                },
            },
            "painting_plan": self.painting_plan,
            "strokes": enriched_strokes,
            "evaluations": [
                {
                    "iteration": e["iteration"],
                    "score": e["score"],
                    "feedback": e["feedback"],
                    "strengths": e["strengths"],
                    "suggestions": e["suggestions"],
                }
                for e in self.evaluations
            ],
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
                "stroke_generator": self.vlm_model,
                "evaluator": self.evaluation_vlm_model,
            },
            "configuration": {
                "max_iterations": self.max_iterations,
                "target_style_score": self.target_style_score,
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
            "planner_model": self.planner_model,
            "expanded_subject": self.expanded_subject,
        }

        return metadata

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
