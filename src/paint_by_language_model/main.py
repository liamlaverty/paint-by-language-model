"""Main entry point for paint-by-language-model."""
import logging
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
    logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
    logger = logging.getLogger(__name__)

    logger.info("Paint by Language Model - Artist Analysis")
    logger.info("=" * 50)
    
    # Initialize LMStudio client
    client = LMStudioClient()
    
    # Check if LMStudio is available
    if not client.is_available():
        logger.error("LMStudio is not available.")
        logger.error("Please ensure LMStudio is running with the local server enabled.")
        return 1
    
    logger.info("✓ Connected to LMStudio")
    
    # Load artists
    try:
        artists = load_artists(ARTISTS_FILE)
        logger.info(f"✓ Loaded {len(artists)} artists from {ARTISTS_FILE}")
    except FileNotFoundError:
        logger.error(f"Artists file not found: {ARTISTS_FILE}")
        return 1
    except Exception as e:
        logger.error(f"Failed to load artists: {e}")
        return 1
    
    # Process each artist
    successful = 0
    failed = 0
    
    for i, artist in enumerate(artists, 1):
        logger.info(f"[{i}/{len(artists)}] Processing: {artist}")
        
        try:
            # Build prompt
            prompt = build_artist_prompt(artist)
            
            # Query LLM
            logger.info("  → Querying LLM...")
            response = client.query(prompt)
            
            # Parse response
            analysis = parse_response(
                artist_name=artist,
                llm_response=response,
                model_name=LMSTUDIO_MODEL,
            )
            
            # Save to file
            filepath = save_artist_result(analysis)
            logger.info(f"  ✓ Saved to: {filepath}")
            successful += 1
            
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            failed += 1
    
    # Summary
    logger.info("=" * 50)
    logger.info(f"Complete! Processed {successful} artists successfully.")
    if failed > 0:
        logger.warning(f"Failed: {failed} artists")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
