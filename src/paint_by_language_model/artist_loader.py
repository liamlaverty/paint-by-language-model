"""Load artist names from JSON file."""
import json
from pathlib import Path


def load_artists(file_path: Path) -> list[str]:
    """
    Load artist names from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing artist names
        
    Returns:
        List of artist name strings
        
    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the JSON is not an array
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        artists = json.load(f)
    
    if not isinstance(artists, list):
        raise ValueError("Artists file must contain a JSON array")
    
    return artists
