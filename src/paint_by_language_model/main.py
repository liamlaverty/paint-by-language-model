"""Main entry point for paint-by-language-model application."""

import argparse
import logging
import sys

from config import (
    DEFAULT_STROKES_PER_QUERY,
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
    """
    logger.info("Starting image generation")
    logger.info("=" * 80)
    logger.info(f"Artist: {artist}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Output ID: {output_id}")
    logger.info(f"Strokes per query: {strokes_per_query}")
    logger.info(f"Max iterations: {max_iterations or MAX_ITERATIONS}")
    logger.info(f"Target score: {target_score or TARGET_STYLE_SCORE}")

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
  # Generate artwork with default settings
  python main.py \\
    --artist "Vincent van Gogh" \\
    --subject "Starry Night Landscape" \\
    --output-id vangogh-001

  # Generate with 10 strokes per query
  python main.py \\
    --artist "Claude Monet" \\
    --subject "Water Lilies" \\
    --output-id monet-001 \\
    -n 10

  # Generate with custom iterations and stroke count
  python main.py \\
    --artist "Pablo Picasso" \\
    --subject "Abstract Portrait" \\
    --output-id picasso-001 \\
    --strokes-per-query 3 \\
    -i 50

  # Generate with specific stroke types only
  python main.py \\
    --artist "Jackson Pollock" \\
    --subject "Abstract Expression" \\
    --output-id pollock-001 \\
    --stroke-types "line,splatter"
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
    )


if __name__ == "__main__":
    main()
