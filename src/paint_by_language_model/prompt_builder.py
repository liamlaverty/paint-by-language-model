"""Build prompts for LLM queries about artists."""
from config import PROMPT_TEMPLATE


def build_artist_prompt(artist_name: str) -> str:
    """
    Build a prompt asking about an artist's notable features.
    
    Args:
        artist_name: The name of the artist to query about
        
    Returns:
        Formatted prompt string
    """
    return PROMPT_TEMPLATE.format(artist_name=artist_name)
