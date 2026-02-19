"""Main entry point for paint-by-language-model application."""

import argparse
import logging
import sys

from config import (
    DEFAULT_STROKES_PER_QUERY,
    GIF_FRAME_DURATION_MS,
    MAX_ITERATIONS,
    MAX_STROKES_PER_QUERY,
    MIN_STROKES_PER_QUERY,
    OUTPUT_DIR,
    SUPPORTED_STROKE_TYPES,
    TARGET_STYLE_SCORE,
)
from generation_orchestrator import GenerationOrchestrator

logger = logging.getLogger(__name__)


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
    """
    import config

    # Apply provider override
    if provider:
        config.PROVIDER = provider
        if provider == "mistral":
            config.API_BASE_URL = config.MISTRAL_BASE_URL
            config.API_KEY = config.MISTRAL_API_KEY
            config.DEFAULT_MODEL = config.MISTRAL_DEFAULT_MODEL
            config.VLM_MODEL = config.MISTRAL_VLM_MODEL
            config.EVALUATION_VLM_MODEL = config.MISTRAL_EVALUATION_VLM_MODEL
        elif provider == "anthropic":
            config.API_BASE_URL = config.ANTHROPIC_BASE_URL
            config.API_KEY = config.ANTHROPIC_API_KEY
            config.DEFAULT_MODEL = config.ANTHROPIC_DEFAULT_MODEL
            config.VLM_MODEL = config.ANTHROPIC_VLM_MODEL
            config.EVALUATION_VLM_MODEL = config.ANTHROPIC_EVALUATION_VLM_MODEL
            config.PLANNER_MODEL = config.ANTHROPIC_PLANNER_MODEL
        else:  # lmstudio
            config.API_BASE_URL = config.LMSTUDIO_BASE_URL
            config.API_KEY = ""
            config.DEFAULT_MODEL = config.LMSTUDIO_MODEL
            config.VLM_MODEL = config.LMSTUDIO_VLM_MODEL
            config.EVALUATION_VLM_MODEL = config.LMSTUDIO_EVALUATION_VLM_MODEL

    # Apply API key override (overrides both env var and provider default)
    if api_key:
        config.API_KEY = api_key

    # Apply planner model override
    if planner_model:
        config.PLANNER_MODEL = planner_model

    # Validate that Mistral has an API key
    if config.PROVIDER == "mistral" and not config.API_KEY:
        logger.error(
            "Mistral provider requires an API key. Set MISTRAL_API_KEY in .env or pass --api-key."
        )
        sys.exit(1)

    # Validate that Anthropic has an API key
    if config.PROVIDER == "anthropic" and not config.API_KEY:
        logger.error(
            "ANTHROPIC_API_KEY not found in environment. "
            "Set ANTHROPIC_API_KEY in .env or pass --api-key."
        )
        sys.exit(1)

    logger.info("Starting image generation")
    logger.info("=" * 80)
    logger.info(f"Provider: {config.PROVIDER}")
    logger.info(f"API Base URL: {config.API_BASE_URL}")
    logger.info(f"VLM Model: {config.VLM_MODEL}")
    logger.info(f"Artist: {artist}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Output ID: {output_id}")
    logger.info(f"Strokes per query: {strokes_per_query}")
    logger.info(f"Max iterations: {max_iterations or MAX_ITERATIONS}")
    logger.info(f"Target score: {target_score or TARGET_STYLE_SCORE}")
    logger.info(f"Planner model: {config.PLANNER_MODEL}")

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
            output_dir=OUTPUT_DIR,
            strokes_per_query=strokes_per_query,
            gif_frame_duration=gif_frame_duration,
            expanded_subject=expanded_subject,
        )
        logger.info("Orchestrator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)

    # Apply overrides if provided
    if max_iterations:
        import config

        config.MAX_ITERATIONS = max_iterations
    if target_score:
        import config

        config.TARGET_STYLE_SCORE = target_score

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
    )


if __name__ == "__main__":
    main()
