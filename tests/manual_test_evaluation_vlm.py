"""Manual test for Evaluation VLM Client."""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

import config
from services.canvas_manager import CanvasManager
from services.evaluation_vlm_client import EvaluationVLMClient


def main() -> None:
    """Run manual test of Evaluation VLM Client."""
    # Track run start time for folder structure
    run_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print("Evaluation VLM Client - Manual Test")
    print("=" * 60)
    print(f"Run ID: {run_datetime}\n")

    # Create canvas with some test strokes
    print("Creating canvas with test strokes...")
    canvas = CanvasManager()

    test_strokes = [
        {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 350,
            "end_y": 100,
            "color_hex": "#0066CC",
            "thickness": 8,
            "opacity": 0.8,
            "reasoning": "Sky blue stroke",
        },
        {
            "type": "line",
            "start_x": 100,
            "start_y": 200,
            "end_x": 300,
            "end_y": 250,
            "color_hex": "#FFCC00",
            "thickness": 6,
            "opacity": 0.9,
            "reasoning": "Yellow ochre stroke",
        },
        {
            "type": "line",
            "start_x": 150,
            "start_y": 150,
            "end_x": 200,
            "end_y": 300,
            "color_hex": "#228B22",
            "thickness": 5,
            "opacity": 0.7,
            "reasoning": "Green accent",
        },
    ]

    for stroke in test_strokes:
        canvas.apply_stroke(stroke)
    print(f"Applied {len(test_strokes)} test strokes\n")

    # Get canvas bytes
    canvas_bytes = canvas.get_image_bytes()

    # Initialize evaluation client
    print("Initializing Evaluation VLM Client...")
    eval_client = EvaluationVLMClient()
    print()

    # Evaluate style
    print("Querying VLM for style evaluation...")
    try:
        evaluation = eval_client.evaluate_style(
            canvas_image=canvas_bytes,
            artist_name="Vincent van Gogh",
            subject="Landscape",
            iteration=1,
        )

        print("\n=== Style Evaluation Results ===")
        print(f"Score: {evaluation['score']:.1f}/100")
        print(f"Iteration: {evaluation['iteration']}")
        print(f"Timestamp: {evaluation['timestamp']}")
        print(f"\nFeedback:\n{evaluation['feedback']}")
        print(f"\nStrengths:\n{evaluation['strengths']}")
        print(f"\nSuggestions:\n{evaluation['suggestions']}")

        # Create output directories with date-based structure
        iteration_datetime = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
            :-3
        ]  # Include milliseconds
        output_base = Path("./test_output")
        output_base.mkdir(exist_ok=True)

        # Save to date-based location
        dated_output = output_base / "by_date" / run_datetime
        dated_output.mkdir(parents=True, exist_ok=True)

        # Save canvas snapshot
        dated_snapshot_path = dated_output / f"evaluation-{iteration_datetime}.png"
        canvas.image.save(dated_snapshot_path)
        print(f"\nCanvas snapshot saved to: {dated_snapshot_path}")

        # Save interaction history to JSON
        history = eval_client.get_interaction_history()
        history_file = dated_output / f"evaluation-{iteration_datetime}.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"Interaction history saved to: {history_file}")

        # Display interaction history summary
        print("\n=== Interaction History ===")
        print(f"Total interactions recorded: {len(history)}")
        if history:
            print(f"Last interaction timestamp: {history[-1]['timestamp']}")
            print(f"Last interaction model: {history[-1]['model']}")

        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)

    except ConnectionError as e:
        print("\n" + "=" * 60)
        print("CONNECTION ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        print(f"\nCannot connect to VLM API at {config.API_BASE_URL}")
        if config.PROVIDER == "mistral":
            print("Check your MISTRAL_API_KEY in .env or pass --api-key")
        else:
            print("Make sure LMStudio is running with the local server enabled")
        return 1
    except ValueError as e:
        print("\n" + "=" * 60)
        print("PARSING ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nThe VLM response could not be parsed correctly")
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print("UNEXPECTED ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
