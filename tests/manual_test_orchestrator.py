"""Manual test script for Generation Orchestrator.

Run this script to test the complete iterative image generation workflow.

Prerequisites:
    - VLM API access (Mistral API key or LMStudio running locally)
    - For LMStudio: Vision Language Model loaded (e.g., LLaVA, MiniStral)
    - For Mistral: MISTRAL_API_KEY set in .env or passed via --api-key
    - Model name in config.py matches loaded model

Usage:
    python tests/manual_test_orchestrator.py

Press Ctrl+C to interrupt generation early.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

import config
from generation_orchestrator import GenerationOrchestrator

# Configuration
ARTIST_NAME = "a childlike style"
SUBJECT = "A stick figure person standing next to a simple house with a tree, under a bright sun in the sky"
ARTWORK_ID = "child-painting-test-001"
OUTPUT_DIR = Path("test_output")

if __name__ == "__main__":
    print("=" * 80)
    print("Generation Orchestrator Manual Test")
    print("=" * 80)
    print(f"Artist: {ARTIST_NAME}")
    print(f"Subject: {SUBJECT}")
    print(f"Artwork ID: {ARTWORK_ID}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 80)
    print("\nPress Ctrl+C at any time to interrupt generation gracefully.\n")

    try:
        # Initialize orchestrator
        orchestrator = GenerationOrchestrator(
            artist_name=ARTIST_NAME,
            subject=SUBJECT,
            artwork_id=ARTWORK_ID,
            output_dir=OUTPUT_DIR,
        )

        # Run generation
        summary = orchestrator.generate()

        # Print results
        print("\n" + "=" * 80)
        print("✓ Generation Complete!")
        print("=" * 80)
        print(f"Final Score: {summary['final_score']:.1f}/100")
        print(f"Total Iterations: {summary['total_iterations']}")
        print(f"Total Strokes: {summary['total_strokes']}")
        print(f"Interrupted: {summary['interrupted']}")
        print(f"Output Directory: {summary['output_directory']}")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
    except ConnectionError as e:
        print(f"\n\n✗ Connection error: {e}")
        print(f"Cannot connect to VLM API at {config.API_BASE_URL}")
        if config.PROVIDER == "mistral":
            print("Check your MISTRAL_API_KEY in .env or pass --api-key")
        else:
            print("Make sure LMStudio is running with a VLM loaded!")
    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
