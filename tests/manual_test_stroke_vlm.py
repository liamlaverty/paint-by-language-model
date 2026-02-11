"""Manual test for Stroke VLM Client."""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

import config
from services.canvas_manager import CanvasManager
from services.stroke_vlm_client import StrokeVLMClient


def main():
    """Run manual test of Stroke VLM Client."""
    # Track run start time for folder structure
    run_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print("Stroke VLM Client - Manual Test")
    print("=" * 60)
    print(f"Run ID: {run_datetime}\n")

    # Initialize canvas
    print("\n1. Initializing canvas...")
    canvas = CanvasManager()

    # Apply a test stroke to give VLM something to work with
    print("2. Applying initial test stroke...")
    initial_stroke = {
        "type": "line",
        "start_x": 100,
        "start_y": 100,
        "end_x": 200,
        "end_y": 200,
        "color_hex": "#0000FF",
        "thickness": 5,
        "opacity": 1.0,
        "reasoning": "Initial test stroke",
    }
    canvas.apply_stroke(initial_stroke)

    # Get canvas bytes
    print("3. Converting canvas to bytes for VLM...")
    canvas_bytes = canvas.get_image_bytes()
    print(f"   Canvas size: {len(canvas_bytes)} bytes")

    # Initialize VLM client
    print("\n4. Initializing VLM client...")
    vlm_client = StrokeVLMClient()

    # Request stroke suggestion
    print("\n5. Requesting stroke suggestion from VLM...")
    print("   (This may take 20-60 seconds...)")
    try:
        response = vlm_client.suggest_stroke(
            canvas_image=canvas_bytes,
            artist_name="Vincent van Gogh",
            subject="Starry Night Landscape",
            iteration=2,
            strategy_context="Building foundation with broad strokes",
        )

        print("\n" + "=" * 60)
        print("SUCCESS! Stroke Suggestion Received:")
        print("=" * 60)
        print(f"  Type: {response['stroke']['type']}")
        print(
            f"  Position: ({response['stroke']['start_x']}, {response['stroke']['start_y']}) "
            f"to ({response['stroke']['end_x']}, {response['stroke']['end_y']})"
        )
        print(f"  Color: {response['stroke']['color_hex']}")
        print(f"  Thickness: {response['stroke']['thickness']}")
        print(f"  Opacity: {response['stroke']['opacity']}")
        print(f"  Reasoning: {response['stroke']['reasoning']}")

        if response["updated_strategy"]:
            print(f"\nUpdated Strategy: {response['updated_strategy']}")
        else:
            print("\nNo strategy update provided.")

        # Apply suggested stroke
        print("\n6. Applying suggested stroke to canvas...")
        canvas.apply_stroke(response["stroke"])

        # Create output directories
        iteration_datetime = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
            :-3
        ]  # Include milliseconds
        output_base = Path("./test_output")
        output_base.mkdir(exist_ok=True)

        # Save to regular location
        snapshot_path = canvas.save_snapshot(2, output_base)
        print(f"\n7a. Snapshot saved to: {snapshot_path}")

        # Save to date-based location
        dated_output = output_base / "by_date" / run_datetime
        dated_output.mkdir(parents=True, exist_ok=True)
        dated_snapshot_path = dated_output / f"iteration-{iteration_datetime}.png"
        canvas.image.save(dated_snapshot_path)
        print(f"7b. Snapshot saved to: {dated_snapshot_path}")

        # Save interaction history to JSON
        history = vlm_client.get_interaction_history()
        history_file = dated_output / f"interaction-{iteration_datetime}.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"7c. Interaction history saved to: {history_file}")

        # Display interaction history summary
        print("\n8. Checking interaction history...")
        print(f"   Total interactions recorded: {len(history)}")
        if history:
            latest = history[-1]
            print(f"   Latest interaction timestamp: {latest['timestamp']}")
            print(f"   Model used: {latest['model']}")
            print(f"   Raw response length: {len(latest['raw_response'])} characters")

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
        print("\nThe VLM response could not be parsed.")
        print("Check the error output above for the raw response.")
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
