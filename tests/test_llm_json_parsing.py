"""Tests for LLM JSON parsing utilities."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from utils.json_utils import clean_and_parse_json, fix_multiline_strings_in_json


def test_clean_json_with_markdown_blocks() -> None:
    """Test cleaning JSON wrapped in markdown code blocks."""
    response = """```json
{
  "test": "value"
}
```"""
    result = clean_and_parse_json(response)
    assert result == {"test": "value"}


def test_clean_json_with_comments() -> None:
    """Test cleaning JSON with comments."""
    response = """{
  // This is a comment
  "test": "value",  // inline comment
  /* multi-line
     comment */
  "other": "data"
}"""
    result = clean_and_parse_json(response)
    assert result == {"test": "value", "other": "data"}


def test_clean_json_with_multiline_strings() -> None:
    """Test fixing multi-line strings in JSON."""
    response = """{
  "description": "This is a long
description that spans
multiple lines",
  "other": "value"
}"""
    result = clean_and_parse_json(response)
    # Newlines should be replaced with spaces
    assert (
        "This is a long description that spans multiple lines" in result["description"]
    )
    assert result["other"] == "value"


def test_clean_json_with_escaped_quotes() -> None:
    """Test that escaped quotes within strings are handled correctly."""
    response = r"""{
  "quote": "She said \"hello\" to me",
  "other": "value"
}"""
    result = clean_and_parse_json(response)
    assert result["quote"] == 'She said "hello" to me'
    assert result["other"] == "value"


def test_clean_json_with_trailing_commas() -> None:
    """Test removing trailing commas."""
    response = """{
  "test": "value",
  "array": [1, 2, 3,],
  "nested": {"key": "val",},
}"""
    result = clean_and_parse_json(response)
    assert result == {"test": "value", "array": [1, 2, 3], "nested": {"key": "val"}}


def test_clean_json_with_extra_text() -> None:
    """Test extracting JSON from text with extra content."""
    response = """Here is the JSON you requested:
{
  "test": "value"
}
That's all!"""
    result = clean_and_parse_json(response)
    assert result == {"test": "value"}


def test_clean_json_complex_nested_structure() -> None:
    """Test cleaning complex nested JSON with multiple issues."""
    response = """```json
{
  "artist": "Vincent van Gogh",
  // His famous style
  "description": "Known for bold
brushwork and vivid colors",
  "works": [
    {
      "title": "Starry Night",
      "year": 1889,
    },
    /* Another masterpiece */
    {
      "title": "Sunflowers",
      "year": 1888,
    }
  ],
}
```"""
    result = clean_and_parse_json(response)
    assert result["artist"] == "Vincent van Gogh"
    assert "bold brushwork and vivid colors" in result["description"]
    assert len(result["works"]) == 2
    assert result["works"][0]["title"] == "Starry Night"


def test_fix_multiline_strings_basic() -> None:
    """Test basic multi-line string fixing."""
    json_text = '"This is a\nmulti-line\nstring"'
    result = fix_multiline_strings_in_json(json_text)
    assert result == '"This is a multi-line string"'


def test_fix_multiline_strings_preserves_escaped_newlines() -> None:
    """Test that properly escaped newlines are preserved."""
    json_text = r'"This has an escaped \\n newline"'
    result = fix_multiline_strings_in_json(json_text)
    # The escaped newline should remain as \\n
    assert r"\\n" in result or r"\n" in result  # May be simplified by parser


def test_fix_multiline_strings_handles_escaped_quotes() -> None:
    """Test that escaped quotes don't break the parser."""
    # Use a string with a literal newline (not escaped \n)
    json_text = '"She said \\"hello\nworld\\" to me"'
    result = fix_multiline_strings_in_json(json_text)
    # Should replace the literal newline with space but keep the escaped quotes
    assert '\\"hello world\\"' in result


def test_fix_multiline_strings_in_complex_json() -> None:
    """Test fixing multi-line strings in a complete JSON structure."""
    json_text = """{
  "normal": "value",
  "multiline": "This has
a newline",
  "number": 123,
  "another": "single line"
}"""
    result = fix_multiline_strings_in_json(json_text)
    # Should be valid JSON after fixing
    parsed = json.loads(result)
    assert "This has a newline" in parsed["multiline"]
    assert parsed["number"] == 123


def test_clean_json_invalid_json_raises_error() -> None:
    """Test that truly invalid JSON raises an error."""
    response = """{
  "test": "value"
  "missing": "comma"
}"""
    with pytest.raises(json.JSONDecodeError):
        clean_and_parse_json(response)


def test_clean_json_empty_string() -> None:
    """Test handling of empty string."""
    with pytest.raises(json.JSONDecodeError):
        clean_and_parse_json("")


def test_clean_json_no_json_object() -> None:
    """Test handling text with no JSON object."""
    response = "This is just plain text without any JSON"
    with pytest.raises(json.JSONDecodeError):
        clean_and_parse_json(response)


def test_clean_json_real_world_llm_response() -> None:
    """Test with a realistic LLM response that has multiple issues."""
    response = """Sure, here's the painting plan:

```json
{
  "artist_name": "Post-Impressionist",
  "subject": "A bustling Parisian café",
  // This is the expanded description
  "expanded_subject": "A vibrant café where
the sunlight casts warm golden hues on cobblestone
streets and outdoor tables.",
  "total_layers": 3,
  "layers": [
    {
      "layer_number": 1,
      "name": "Background",
      "description": "Sky and street background with
warm evening light",
      "colour_palette": ["#FFD700", "#FF8C00"],
      "stroke_types": ["line", "arc"],
    },
  ],
}
```

I hope this helps!"""
    result = clean_and_parse_json(response)
    assert result["artist_name"] == "Post-Impressionist"
    assert result["total_layers"] == 3
    assert len(result["layers"]) == 1
    # Multi-line strings should be on one line now
    assert "\n" not in result["expanded_subject"]
    assert "warm golden hues" in result["expanded_subject"]


def test_clean_json_with_carriage_returns() -> None:
    """Test handling JSON with carriage return characters."""
    response = '{\r\n  "test": "value with\r\nnewlines",\r\n  "other": "data"\r\n}'
    result = clean_and_parse_json(response)
    assert result["test"] == "value with  newlines"  # \r\n replaced with spaces
    assert result["other"] == "data"


def test_clean_json_deeply_nested() -> None:
    """Test deeply nested JSON with multiple issues."""
    response = """{
  "level1": {
    // Comment at level 1
    "level2": {
      "level3": {
        "description": "This is
a multi-line
nested string",
        "value": 123,
      },
    },
  },
}"""
    result = clean_and_parse_json(response)
    nested_desc = result["level1"]["level2"]["level3"]["description"]
    assert "This is a multi-line nested string" in nested_desc
    assert result["level1"]["level2"]["level3"]["value"] == 123
