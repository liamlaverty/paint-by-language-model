"""JSON utility functions for file operations."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def minify_json_file(file_path: Path) -> tuple[bool, int]:
    """
    Minify a JSON file by removing whitespace and indentation.

    Reads a JSON file, parses it, and rewrites it in compact format
    (no indentation, minimal separators). This reduces file size while
    maintaining valid JSON.

    Args:
        file_path (Path): Path to the JSON file to minify

    Returns:
        tuple[bool, int]: (success, bytes_saved)
            - success: True if minification succeeded, False otherwise
            - bytes_saved: Number of bytes saved (negative if file grew)

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        # Read original file
        original_size = file_path.stat().st_size
        with open(file_path, "r", encoding="utf-8") as f:
            data: Any = json.load(f)

        # Write minified (no indentation, no extra whitespace)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"), ensure_ascii=False)

        # Calculate space saved
        new_size = file_path.stat().st_size
        bytes_saved = original_size - new_size

        if bytes_saved > 0:
            kb_saved = bytes_saved / 1024
            reduction_pct = (bytes_saved / original_size) * 100
            logger.debug(
                f"Minified {file_path.name}: {kb_saved:.1f} KB saved ({reduction_pct:.1f}% reduction)"
            )
        else:
            logger.debug(f"File {file_path.name} was already minified or grew")

        return True, bytes_saved

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to minify {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error minifying {file_path}: {e}")
        raise


def minify_json_files_in_directory(
    directory: Path, filename_pattern: str = "*.json"
) -> tuple[int, int, int]:
    """
    Minify all JSON files matching a pattern in a directory.

    Args:
        directory (Path): Directory to search for JSON files
        filename_pattern (str): Glob pattern for matching files (default: "*.json")

    Returns:
        tuple[int, int, int]: (files_processed, bytes_saved, files_with_errors)
    """
    if not directory.exists():
        logger.warning(f"Directory not found: {directory}")
        return 0, 0, 0

    json_files = list(directory.glob(filename_pattern))
    if not json_files:
        logger.info(f"No files matching '{filename_pattern}' found in {directory}")
        return 0, 0, 0

    files_processed = 0
    total_bytes_saved = 0
    files_with_errors = 0

    for file_path in json_files:
        try:
            success, bytes_saved = minify_json_file(file_path)
            if success:
                files_processed += 1
                total_bytes_saved += bytes_saved
        except Exception:
            files_with_errors += 1

    return files_processed, total_bytes_saved, files_with_errors
