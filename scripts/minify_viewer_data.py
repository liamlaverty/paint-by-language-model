#!/usr/bin/env python3
"""
Minify all viewer_data.json files in src/viewer/public/data.

This script finds all viewer_data.json files in the Next.js viewer's
public data directory and minifies them by removing whitespace and indentation.
This reduces file sizes for production deployment while maintaining valid JSON.

Usage:
    python scripts/minify_viewer_data.py
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import NEXTJS_VIEWER_DATA_DIR
from services.json_utils import minify_json_file


def minify_viewer_data_files() -> tuple[int, int, int]:
    """
    Minify all viewer_data.json files in the Next.js viewer data directory.

    Returns:
        tuple[int, int, int]: (files_processed, bytes_saved, files_with_errors)
    """
    data_dir = NEXTJS_VIEWER_DATA_DIR

    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return 0, 0, 0

    # Find all viewer_data.json files
    viewer_data_files = list(data_dir.glob("*/viewer_data.json"))

    if not viewer_data_files:
        print("No viewer_data.json files found")
        return 0, 0, 0

    files_processed = 0
    total_bytes_saved = 0
    files_with_errors = 0

    print(f"Found {len(viewer_data_files)} viewer_data.json file(s)")

    for file_path in viewer_data_files:
        try:
            success, bytes_saved = minify_json_file(file_path)

            if success:
                if bytes_saved > 0:
                    kb_saved = bytes_saved / 1024
                    reduction_pct = (bytes_saved / file_path.stat().st_size) * 100
                    print(
                        f"  ✓ {file_path.parent.name}/viewer_data.json: "
                        f"{kb_saved:.1f} KB saved ({reduction_pct:.1f}% reduction)"
                    )
                    total_bytes_saved += bytes_saved
                else:
                    print(
                        f"  ✓ {file_path.parent.name}/viewer_data.json: already minified"
                    )
                files_processed += 1

        except Exception as e:
            print(f"  ✗ {file_path.parent.name}/viewer_data.json: Error - {e}")
            files_with_errors += 1

    return files_processed, total_bytes_saved, files_with_errors


def main() -> int:
    """
    Main entry point for the minifier script.

    Returns:
        int: Exit code (0 for success, 1 for errors)
    """
    print("=" * 60)
    print("JSON Minifier - viewer_data.json files")
    print("=" * 60)

    files_processed, bytes_saved, files_with_errors = minify_viewer_data_files()

    if files_processed > 0:
        total_kb_saved = bytes_saved / 1024
        total_mb_saved = bytes_saved / (1024 * 1024)

        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  Files processed: {files_processed}")
        if bytes_saved > 0:
            if total_mb_saved >= 1:
                print(f"  Total space saved: {total_mb_saved:.2f} MB")
            else:
                print(f"  Total space saved: {total_kb_saved:.1f} KB")
        print(f"  Errors: {files_with_errors}")
        print("=" * 60)

    if files_with_errors > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
