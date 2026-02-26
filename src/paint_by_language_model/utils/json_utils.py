"""Utilities for parsing and cleaning JSON responses from LLMs/VLMs."""

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def clean_and_parse_json(response_text: str) -> dict[str, Any]:
    """
    Parse JSON from LLM/VLM response with robust error handling.

    This handles common issues like:
    - Markdown code blocks (```json ... ```)
    - JSON comments (// and /* */)
    - Multi-line strings with literal newlines
    - Extra text before/after JSON
    - Trailing commas

    Args:
        response_text (str): Raw response text from LLM/VLM

    Returns:
        dict[str, Any]: Parsed JSON object

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed after cleaning
    """
    # Step 1: Remove markdown code blocks
    cleaned_text = re.sub(r"```(?:json)?\s*", "", response_text)
    cleaned_text = re.sub(r"```\s*$", "", cleaned_text)

    # Step 2: Try to extract JSON object (find outermost braces)
    json_match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
    json_text = json_match.group(0) if json_match else cleaned_text

    # Step 3: Remove JSON comments
    # Remove single-line comments: // comment
    json_text = re.sub(r"//.*?(?=\n|$)", "", json_text)
    # Remove multi-line comments: /* comment */
    json_text = re.sub(r"/\*.*?\*/", "", json_text, flags=re.DOTALL)

    # Step 4: Fix multi-line strings (the tricky part)
    # We need to handle strings that contain literal newlines
    # Strategy: Find all string values and replace internal newlines with spaces
    json_text = fix_multiline_strings_in_json(json_text)

    # Step 4.5: Fix missing commas between consecutive key-value pairs.
    # Some local models omit commas, e.g.:
    #   {"key1": "value1"
    #    "key2": "value2"}
    # A closing quote/digit/}/] followed by a newline and then a quote is
    # unambiguously missing a comma.  Only insert when there isn't one already.
    json_text = re.sub(r'(["\d\}\]])\s*\n(\s*")', r"\1,\n\2", json_text)

    # Step 5: Remove trailing commas before closing braces/brackets
    # LLMs sometimes add these
    json_text = re.sub(r",\s*([\]}])", r"\1", json_text)

    # Step 6: Parse JSON
    try:
        data = json.loads(json_text)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON after cleaning: {e}")
        logger.error(f"Cleaned JSON (first 1000 chars): {json_text[:1000]}")
        # Try to show the area around the error
        if hasattr(e, "pos") and e.pos:
            start = max(0, e.pos - 100)
            end = min(len(json_text), e.pos + 100)
            logger.error(f"Error context: ...{json_text[start:end]}...")
        raise


def fix_multiline_strings_in_json(json_text: str) -> str:
    """
    Fix multi-line strings in JSON by replacing literal newlines with spaces.

    This is more robust than a simple regex - it properly handles:
    - Escaped quotes within strings
    - Nested structures
    - Edge cases with quotes

    Args:
        json_text (str): JSON text potentially containing multi-line strings

    Returns:
        str: JSON text with multi-line strings fixed
    """
    result = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(json_text):
        char = json_text[i]

        if escape_next:
            # This character is escaped, just add it and move on
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == "\\":
            # Next character is escaped
            result.append(char)
            escape_next = True
            i += 1
            continue

        if char == '"':
            # Start or end of string
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        if in_string and (char == "\n" or char == "\r"):
            # Replace newlines within strings with space
            result.append(" ")
            i += 1
            continue

        # Normal character
        result.append(char)
        i += 1

    return "".join(result)


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON object or array from text that may contain other content.

    Args:
        text (str): Text potentially containing JSON

    Returns:
        str: Extracted JSON string, or original text if no JSON found
    """
    # Try to find a JSON object
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json_match.group(0)

    # Try to find a JSON array
    json_match = re.search(r"\[.*\]", text, re.DOTALL)
    if json_match:
        return json_match.group(0)

    return text


# ----------------------------------------------------------------------------
# JSON File Minification Utilities
# ----------------------------------------------------------------------------


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
        with open(file_path, encoding="utf-8") as f:
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
