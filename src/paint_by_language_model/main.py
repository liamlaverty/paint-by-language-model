"""Main entry point for paint-by-language-model application."""

import argparse
import logging
import sys

import config
from config import (
    DEFAULT_STROKES_PER_QUERY,
    GIF_FRAME_DURATION_MS,
    MAX_ITERATIONS,
    MAX_STROKES_PER_QUERY,
    MIN_STROKES_PER_LAYER,
    MIN_STROKES_PER_QUERY,
    OUTPUT_DIR,
    SUPPORTED_STROKE_TYPES,
    TARGET_STYLE_SCORE,
)
from generation_orchestrator import GenerationOrchestrator
from models import GenerationConfig

logger = logging.getLogger(__name__)


def build_generation_config(
    provider: str | None,
    api_key: str | None,
    planner_model: str | None,
    max_iterations: int | None,
    target_score: float | None,
    min_strokes_per_layer: int | None,
) -> GenerationConfig:
    """
    Resolve all runtime overrides and return a fully-populated GenerationConfig.

    Reads defaults from the ``config`` module and applies any CLI overrides on
    top. Does NOT mutate the ``config`` module.

    Args:
        provider (str | None): Provider override ("mistral", "lmstudio",
            "anthropic"), or None to use the value from config.
        api_key (str | None): API key override, or None to use config default.
        planner_model (str | None): Planner model override, or None to use
            config default.
        max_iterations (int | None): Override for MAX_ITERATIONS, or None.
        target_score (float | None): Override for TARGET_STYLE_SCORE, or None.
        min_strokes_per_layer (int | None): Override for MIN_STROKES_PER_LAYER,
            or None.

    Returns:
        GenerationConfig: Fully-resolved configuration object.
    """
    resolved_provider = config.PROVIDER
    resolved_api_base_url = config.API_BASE_URL
    resolved_api_key = config.API_KEY
    resolved_vlm_model = config.VLM_MODEL
    resolved_eval_model = config.EVALUATION_VLM_MODEL
    resolved_planner_model = config.PLANNER_MODEL

    if provider == "mistral":
        resolved_provider = "mistral"
        resolved_api_base_url = config.MISTRAL_BASE_URL
        resolved_api_key = config.MISTRAL_API_KEY
        resolved_vlm_model = config.MISTRAL_VLM_MODEL
        resolved_eval_model = config.MISTRAL_EVALUATION_VLM_MODEL
        resolved_planner_model = config.MISTRAL_PLANNER_MODEL
    elif provider == "anthropic":
        resolved_provider = "anthropic"
        resolved_api_base_url = config.ANTHROPIC_BASE_URL
        resolved_api_key = config.ANTHROPIC_API_KEY
        resolved_vlm_model = config.ANTHROPIC_VLM_MODEL
        resolved_eval_model = config.ANTHROPIC_EVALUATION_VLM_MODEL
        resolved_planner_model = config.ANTHROPIC_PLANNER_MODEL
    elif provider == "lmstudio":
        resolved_provider = "lmstudio"
        resolved_api_base_url = config.LMSTUDIO_BASE_URL
        resolved_api_key = ""
        resolved_vlm_model = config.LMSTUDIO_VLM_MODEL
        resolved_eval_model = config.LMSTUDIO_EVALUATION_VLM_MODEL
        resolved_planner_model = config.LMSTUDIO_PLANNER_MODEL
    elif provider is not None:
        raise ValueError(
            f"Unknown provider: {provider!r}. "
            "Valid values are 'mistral', 'anthropic', and 'lmstudio'."
        )

    if api_key:
        resolved_api_key = api_key
    if planner_model:
        resolved_planner_model = planner_model

    return GenerationConfig(
        provider=resolved_provider,
        api_base_url=resolved_api_base_url,
        api_key=resolved_api_key,
        vlm_model=resolved_vlm_model,
        evaluation_vlm_model=resolved_eval_model,
        planner_model=resolved_planner_model,
        max_iterations=max_iterations if max_iterations is not None else config.MAX_ITERATIONS,
        target_style_score=target_score if target_score is not None else config.TARGET_STYLE_SCORE,
        min_strokes_per_layer=(
            min_strokes_per_layer
            if min_strokes_per_layer is not None
            else config.MIN_STROKES_PER_LAYER
        ),
    )


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info(f"Logging configured at {log_level} level")


def run_generation(
    artist: str,
    subject: str,
    output_id: str,
    max_iterations: int | None = None,
    target_score: float | None = None,
    strokes_per_query: int = DEFAULT_STROKES_PER_QUERY,
    stroke_types: list[str] | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    gif_frame_duration: int = GIF_FRAME_DURATION_MS,
    expanded_subject: str | None = None,
    planner_model: str | None = None,
    min_strokes_per_layer: int | None = None,
) -> None:
    """
    Run image generation mode.

    Generates artwork in the style of specified artist.

    Args:
        artist (str): Artist name
        subject (str): Subject to paint
        output_id (str): Unique artwork identifier
        max_iterations (int | None): Override MAX_ITERATIONS
        target_score (float | None): Override TARGET_STYLE_SCORE
        strokes_per_query (int): Number of strokes to request per VLM query
        stroke_types (list[str] | None): Allowed stroke types filter
        provider (str | None): VLM provider ("mistral", "lmstudio", or "anthropic")
        api_key (str | None): API key for VLM provider
        gif_frame_duration (int): GIF frame duration in milliseconds
        expanded_subject (str | None): Detailed description of the final image
        planner_model (str | None): Override the planner LLM model
        min_strokes_per_layer (int | None): Override MIN_STROKES_PER_LAYER
    """
    generation_cfg = build_generation_config(
        provider=provider,
        api_key=api_key,
        planner_model=planner_model,
        max_iterations=max_iterations,
        target_score=target_score,
        min_strokes_per_layer=min_strokes_per_layer,
    )

    logger.info("Starting image generation")
    logger.info("=" * 80)
    logger.info(f"Provider: {generation_cfg['provider']}")
    logger.info(f"API Base URL: {generation_cfg['api_base_url']}")
    logger.info(f"VLM Model: {generation_cfg['vlm_model']}")
    logger.info(f"Artist: {artist}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Output ID: {output_id}")
    logger.info(f"Strokes per query: {strokes_per_query}")
    logger.info(f"Max iterations: {generation_cfg['max_iterations']}")
    logger.info(f"Target score: {generation_cfg['target_style_score']}")
    logger.info(f"Planner model: {generation_cfg['planner_model']}")

    if expanded_subject:
        logger.info(f"Expanded subject: {expanded_subject}")

    if stroke_types:
        logger.info(f"Allowed stroke types: {', '.join(stroke_types)}")
    else:
        logger.info(f"Allowed stroke types: all ({', '.join(SUPPORTED_STROKE_TYPES)})")

    logger.info("=" * 80)

    # Initialize orchestrator
    try:
        orchestrator = GenerationOrchestrator(
            artist_name=artist,
            subject=subject,
            artwork_id=output_id,
            generation_config=generation_cfg,
            output_dir=OUTPUT_DIR,
            strokes_per_query=strokes_per_query,
            gif_frame_duration=gif_frame_duration,
            expanded_subject=expanded_subject,
            allowed_stroke_types=stroke_types,
        )
        logger.info("Orchestrator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)

    # Run generation
    try:
        summary = orchestrator.generate()

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("GENERATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Artwork ID: {summary['artwork_id']}")
        logger.info(f"Total Iterations: {summary['total_iterations']}")
        logger.info(f"Final Score: {summary['final_score']:.1f}/100")
        logger.info(f"Total Strokes: {summary['total_strokes']}")
        logger.info(f"Output Directory: {summary['output_directory']}")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("\nGeneration interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Paint by Language Model - AI-driven art generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate using Mistral (default)
  python main.py \\
    --artist "Vincent van Gogh" \\
    --subject "Starry Night Landscape" \\
    --output-id vangogh-001

  # Generate using LMStudio (local)
  python main.py \\
    --artist "Claude Monet" \\
    --subject "Water Lilies" \\
    --output-id monet-001 \\
    --provider lmstudio

  # Override API key at runtime
  python main.py \\
    --artist "Pablo Picasso" \\
    --subject "Abstract Portrait" \\
    --output-id picasso-001 \\
    --api-key sk-your-key-here

  # Generate with custom iterations and stroke count
  python main.py \\
    --artist "Georgia O'Keeffe" \\
    --subject "Flower Close-up" \\
    --output-id okeeffe-001 \\
    --strokes-per-query 3 \\
    -i 50

  # Generate with specific stroke types only
  python main.py \\
    --artist "Jackson Pollock" \\
    --subject "Abstract Expression" \\
    --output-id pollock-001 \\
    --stroke-types "line,splatter"

  # Generate with an expanded subject description
  python main.py \\
    --artist "Claude Monet" \\
    --subject "Water Lilies" \\
    --output-id monet-002 \\
    --expanded-subject "A serene pond with floating water lilies, soft reflections of willow trees, dappled sunlight on the water surface"

  # Generate using Anthropic (Claude)
  python main.py \\
    --artist "Salvador Dali" \\
    --subject "Melting Clocks" \\
    --output-id dali-002 \\
    --provider anthropic
        """,
    )

    # Required arguments
    parser.add_argument("--artist", type=str, required=True, help="Target artist name")

    parser.add_argument("--subject", type=str, required=True, help="Subject to paint")

    parser.add_argument("--output-id", type=str, required=True, help="Unique artwork identifier")

    # Optional arguments
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--strokes-per-query",
        "-n",
        type=int,
        default=DEFAULT_STROKES_PER_QUERY,
        help=f"Number of strokes per VLM query (default: {DEFAULT_STROKES_PER_QUERY}, range: {MIN_STROKES_PER_QUERY}-{MAX_STROKES_PER_QUERY})",
    )

    parser.add_argument(
        "--max-iterations",
        "-i",
        type=int,
        help=f"Maximum VLM query iterations (default: {MAX_ITERATIONS})",
    )

    parser.add_argument(
        "--target-score",
        "-t",
        type=float,
        help=f"Target style score to stop (default: {TARGET_STYLE_SCORE})",
    )

    parser.add_argument(
        "--stroke-types",
        type=str,
        default=None,
        help=f"Comma-separated list of allowed stroke types (default: all types). Supported: {', '.join(SUPPORTED_STROKE_TYPES)}",
    )

    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=["mistral", "lmstudio", "anthropic"],
        help="VLM provider: 'mistral' (Mistral API), 'lmstudio' (local), or 'anthropic' (Anthropic API). Default: from PROVIDER env var or 'mistral'",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for VLM provider (overrides MISTRAL_API_KEY env var)",
    )

    parser.add_argument(
        "--gif-frame-duration",
        type=int,
        default=GIF_FRAME_DURATION_MS,
        help=f"GIF frame duration in milliseconds (default: {GIF_FRAME_DURATION_MS})",
    )

    parser.add_argument(
        "--expanded-subject",
        type=str,
        default=None,
        help="Detailed description of what the final image should look like",
    )

    parser.add_argument(
        "--planner-model",
        type=str,
        default=None,
        help="Override the planner LLM model (e.g. mistral-large-latest)",
    )

    parser.add_argument(
        "--min-strokes-per-layer",
        type=int,
        default=None,
        help=(
            f"Minimum VLM iterations per painting layer before the layer can be marked "
            f"complete (default: {MIN_STROKES_PER_LAYER} from config)"
        ),
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> list[str] | None:
    """
    Validate command-line arguments.

    Args:
        args (argparse.Namespace): Parsed arguments

    Returns:
        list[str] | None: Parsed stroke types list if provided, None otherwise

    Raises:
        SystemExit: If arguments invalid
    """
    # Validate ranges
    if args.max_iterations and args.max_iterations <= 0:
        logger.error("--max-iterations must be positive")
        sys.exit(1)

    if args.target_score and not (0 <= args.target_score <= 100):
        logger.error("--target-score must be between 0 and 100")
        sys.exit(1)

    # Validate strokes per query
    if not (MIN_STROKES_PER_QUERY <= args.strokes_per_query <= MAX_STROKES_PER_QUERY):
        logger.error(
            f"--strokes-per-query must be between {MIN_STROKES_PER_QUERY} "
            f"and {MAX_STROKES_PER_QUERY}"
        )
        sys.exit(1)

    # Validate stroke types if specified
    stroke_types = None
    if args.stroke_types:
        types = [t.strip() for t in args.stroke_types.split(",")]
        invalid = [t for t in types if t not in SUPPORTED_STROKE_TYPES]
        if invalid:
            logger.error(
                f"Invalid stroke types: {', '.join(invalid)}. "
                f"Supported types: {', '.join(SUPPORTED_STROKE_TYPES)}"
            )
            sys.exit(1)
        stroke_types = types

    return stroke_types


def main() -> None:
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    setup_logging(args.log_level)

    # Validate arguments
    stroke_types = validate_arguments(args)

    # Run generation
    run_generation(
        artist=args.artist,
        subject=args.subject,
        output_id=args.output_id,
        max_iterations=args.max_iterations,
        target_score=args.target_score,
        strokes_per_query=args.strokes_per_query,
        stroke_types=stroke_types,
        provider=args.provider,
        api_key=args.api_key,
        gif_frame_duration=args.gif_frame_duration,
        expanded_subject=args.expanded_subject,
        planner_model=args.planner_model,
        min_strokes_per_layer=args.min_strokes_per_layer,
    )


if __name__ == "__main__":
    main()
