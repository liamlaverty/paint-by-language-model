"""Quick verification test for the stroke renderer framework."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "paint_by_language_model"))

from services.renderers import StrokeRenderer, StrokeRendererFactory  # noqa: E402


def test_factory_unsupported_type() -> None:
    """Test that factory raises ValueError for unsupported stroke types."""
    try:
        StrokeRendererFactory.get_renderer("unsupported_type")
        print("❌ FAIL: Should have raised ValueError for unsupported type")
    except ValueError as e:
        print(f"✓ PASS: Factory correctly raised ValueError: {e}")


def test_factory_no_renderers() -> None:
    """Test that factory provides helpful message when no renderers registered."""
    try:
        StrokeRendererFactory.get_renderer("line")
        print(
            "❌ FAIL: Should have raised ValueError since no renderers registered yet"
        )
    except ValueError as e:
        error_msg = str(e)
        if (
            "none registered" in error_msg.lower()
            or "supported types:" in error_msg.lower()
        ):
            print(f"✓ PASS: Factory message mentions no registered types: {e}")
        else:
            print(f"⚠ PARTIAL: Factory raised error but message could be clearer: {e}")


def test_abstract_class() -> None:
    """Test that StrokeRenderer is properly abstract."""
    try:
        # Try to instantiate abstract class directly
        StrokeRenderer()  # type: ignore
        print("❌ FAIL: Should not be able to instantiate abstract class")
    except TypeError as e:
        if "abstract" in str(e).lower():
            print(f"✓ PASS: Cannot instantiate abstract class: {e}")
        else:
            print(f"⚠ PARTIAL: TypeError but not clear it's about abstract: {e}")


if __name__ == "__main__":
    print("=== Stroke Renderer Framework Tests ===\n")

    print("Test 1: Factory rejects unsupported types")
    test_factory_unsupported_type()

    print("\nTest 2: Factory message when no renderers registered")
    test_factory_no_renderers()

    print("\nTest 3: Abstract class cannot be instantiated")
    test_abstract_class()

    print("\n=== All Tests Complete ===")
