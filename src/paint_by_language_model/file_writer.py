"""Write artist analysis results to JSON files."""
import json
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR


def sanitize_filename(name: str) -> str:
    """
    Convert an artist name to a safe filename.
    
    Args:
        name (str): The artist's name
        
    Returns:
        (str): A filesystem-safe filename (without extension)
    """
    # Replace spaces with underscores, convert to lowercase
    safe_name = name.lower().replace(' ', '_')
    # Remove any characters that aren't alphanumeric or underscore
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
    return safe_name


def save_artist_result(
    data: dict[str, Any],
    output_dir: Path = OUTPUT_DIR,
) -> Path:
    """
    Save an artist analysis result to a JSON file.
    
    Args:
        data (dict[str, Any]): The artist analysis data to save
        output_dir (Path): Directory to save the file in
        
    Returns:
        Path: Path to the saved file
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename from artist name
    filename = f"{sanitize_filename(data['artist_name'])}.json"
    filepath = output_dir / filename
    
    # Write JSON file with pretty printing
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath
