"""Unit tests for JSON utility functions."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.json_utils import minify_json_file, minify_json_files_in_directory


class TestMinifyJsonFile:
    """Test suite for minify_json_file function."""

    def test_minify_reduces_file_size(self) -> None:
        """Test that minifying a formatted JSON file reduces its size."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "test.json"

        # Create a formatted JSON file
        data = {
            "key": "value",
            "nested": {"a": 1, "b": 2, "c": 3},
            "list": [1, 2, 3, 4, 5],
        }
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        original_size = test_file.stat().st_size

        # Minify the file
        success, bytes_saved = minify_json_file(test_file)

        assert success is True
        assert bytes_saved > 0
        assert test_file.stat().st_size < original_size

        # Verify JSON is still valid
        with open(test_file, encoding="utf-8") as f:
            loaded_data = json.load(f)
        assert loaded_data == data

    def test_minify_already_minified_file(self) -> None:
        """Test minifying an already minified file."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "test.json"

        # Create an already minified JSON file
        data = {"key": "value"}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))

        # Minify the file
        success, bytes_saved = minify_json_file(test_file)

        assert success is True
        assert bytes_saved == 0  # No bytes saved

    def test_minify_invalid_json(self) -> None:
        """Test minifying a file with invalid JSON raises error."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "invalid.json"

        # Create invalid JSON
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            minify_json_file(test_file)

    def test_minify_nonexistent_file(self) -> None:
        """Test minifying a nonexistent file raises error."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            minify_json_file(test_file)

    def test_minify_preserves_unicode(self) -> None:
        """Test that minification preserves unicode characters."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "unicode.json"

        # Create JSON with unicode
        data = {"emoji": "🎨", "accent": "café", "chinese": "中文"}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Minify
        success, bytes_saved = minify_json_file(test_file)

        assert success is True

        # Verify unicode is preserved
        with open(test_file, encoding="utf-8") as f:
            loaded_data = json.load(f)
        assert loaded_data == data


class TestMinifyJsonFilesInDirectory:
    """Test suite for minify_json_files_in_directory function."""

    def test_minify_multiple_files(self) -> None:
        """Test minifying multiple JSON files in a directory."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create multiple formatted JSON files
        for i in range(3):
            test_file = tmpdir / f"test{i}.json"
            data = {"index": i, "nested": {"a": 1, "b": 2}}
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        # Minify directory
        files_processed, bytes_saved, errors = minify_json_files_in_directory(tmpdir)

        assert files_processed == 3
        assert bytes_saved > 0
        assert errors == 0

    def test_minify_nonexistent_directory(self) -> None:
        """Test minifying nonexistent directory returns zero counts."""
        tmpdir = Path(tempfile.mkdtemp())
        nonexistent = tmpdir / "nonexistent"

        files_processed, bytes_saved, errors = minify_json_files_in_directory(nonexistent)

        assert files_processed == 0
        assert bytes_saved == 0
        assert errors == 0

    def test_minify_empty_directory(self) -> None:
        """Test minifying empty directory returns zero counts."""
        tmpdir = Path(tempfile.mkdtemp())

        files_processed, bytes_saved, errors = minify_json_files_in_directory(tmpdir)

        assert files_processed == 0
        assert bytes_saved == 0
        assert errors == 0

    def test_minify_with_pattern(self) -> None:
        """Test minifying files with a specific pattern."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create different JSON files
        for i in range(2):
            test_file = tmpdir / f"viewer_data_{i}.json"
            data = {"index": i}
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        other_file = tmpdir / "other.json"
        with open(other_file, "w", encoding="utf-8") as f:
            json.dump({"other": True}, f, indent=2)

        # Minify only viewer_data files
        files_processed, bytes_saved, errors = minify_json_files_in_directory(
            tmpdir, "viewer_data_*.json"
        )

        assert files_processed == 2
        assert bytes_saved > 0
        assert errors == 0

    def test_minify_with_invalid_files(self) -> None:
        """Test minifying directory with some invalid JSON files."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create valid file
        valid_file = tmpdir / "valid.json"
        with open(valid_file, "w", encoding="utf-8") as f:
            json.dump({"valid": True}, f, indent=2)

        # Create invalid file
        invalid_file = tmpdir / "invalid.json"
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("{ invalid }")

        # Minify directory
        files_processed, bytes_saved, errors = minify_json_files_in_directory(tmpdir)

        assert files_processed == 1  # Only valid file processed
        assert bytes_saved > 0
        assert errors == 1  # One error for invalid file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
