"""Manual test for Evaluation VLM Client."""

import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.canvas_manager import CanvasManager
from services.evaluation_vlm_client import EvaluationVLMClient


def main() -> None:
    """Run manual test of Evaluation VLM Client."""
    print("=== Evaluation VLM Client Manual Test ===\n")

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

    # Save test canvas
    test_output_dir = Path("./test_output")
    test_output_dir.mkdir(exist_ok=True)
    canvas_path = canvas.save_snapshot(1, test_output_dir)
    print(f"Saved test canvas to: {canvas_path}\n")

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
        print("\n=== Test Completed Successfully ===")

    except ConnectionError as e:
        print(f"\nConnection Error: {e}")
        print("Make sure LMStudio is running on http://localhost:1234")
    except ValueError as e:
        print(f"\nValue Error: {e}")
        print("The VLM response could not be parsed correctly")
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
