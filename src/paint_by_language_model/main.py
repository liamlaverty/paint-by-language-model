"""Main entry point for paint-by-language-model."""
import sys

from config import ARTISTS_FILE, OUTPUT_DIR, LMSTUDIO_MODEL
from artist_loader import load_artists
from prompt_builder import build_artist_prompt
from lmstudio_client import LMStudioClient
from response_parser import parse_response
from file_writer import save_artist_result


def main() -> int:
    """
    Main workflow: load artists, query LLM, save results.
    
    Returns:
        (int) Exit code (0 for success, 1 for failure)
    """
    print("Paint by Language Model - Artist Analysis")
    print("=" * 50)
    
    # Initialize LMStudio client
    client = LMStudioClient()
    
    # Check if LMStudio is available
    if not client.is_available():
        print("ERROR: LMStudio is not available.")
        print("Please ensure LMStudio is running with the local server enabled.")
        return 1
    
    print("✓ Connected to LMStudio")
    
    # Load artists
    try:
        artists = load_artists(ARTISTS_FILE)
        print(f"✓ Loaded {len(artists)} artists from {ARTISTS_FILE}")
    except FileNotFoundError:
        print(f"ERROR: Artists file not found: {ARTISTS_FILE}")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to load artists: {e}")
        return 1
    
    # Process each artist
    successful = 0
    failed = 0
    
    for i, artist in enumerate(artists, 1):
        print(f"\n[{i}/{len(artists)}] Processing: {artist}")
        
        try:
            # Build prompt
            prompt = build_artist_prompt(artist)
            
            # Query LLM
            print("  → Querying LLM...")
            response = client.query(prompt)
            
            # Parse response
            analysis = parse_response(
                artist_name=artist,
                llm_response=response,
                model_name=LMSTUDIO_MODEL,
            )
            
            # Save to file
            filepath = save_artist_result(analysis)
            print(f"  ✓ Saved to: {filepath}")
            successful += 1
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Complete! Processed {successful} artists successfully.")
    if failed > 0:
        print(f"Failed: {failed} artists")
    print(f"Output directory: {OUTPUT_DIR}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
