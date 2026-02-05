"""Unit tests for CanvasManager class."""

import unittest
import tempfile
import shutil
from pathlib import Path

from PIL import Image

import sys

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.canvas_manager import CanvasManager
from models.stroke import Stroke
from config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    CANVAS_BACKGROUND_COLOR,
    MIN_STROKE_THICKNESS,
    MAX_STROKE_THICKNESS,
    MIN_STROKE_OPACITY,
    MAX_STROKE_OPACITY,
)


class TestCanvasManager(unittest.TestCase):
    """Test suite for CanvasManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.canvas = CanvasManager(width=400, height=300, background_color="#FFFFFF")

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    # ========================================================================
    # Initialization Tests
    # ========================================================================

    def test_initialization_default_values(self):
        """Test canvas initializes with correct default values."""
        canvas = CanvasManager()
        self.assertEqual(canvas.width, CANVAS_WIDTH)
        self.assertEqual(canvas.height, CANVAS_HEIGHT)
        self.assertEqual(canvas.background_color, CANVAS_BACKGROUND_COLOR)
        self.assertEqual(canvas.stroke_count, 0)
        self.assertEqual(canvas.current_iteration, 0)

    def test_initialization_custom_dimensions(self):
        """Test canvas initializes with custom dimensions."""
        canvas = CanvasManager(width=1024, height=768, background_color="#000000")
        self.assertEqual(canvas.width, 1024)
        self.assertEqual(canvas.height, 768)
        self.assertEqual(canvas.background_color, "#000000")

    def test_initialization_creates_pil_image(self):
        """Test canvas creates PIL Image object."""
        self.assertIsNotNone(self.canvas.image)
        self.assertEqual(self.canvas.image.size, (400, 300))
        self.assertEqual(self.canvas.image.mode, "RGB")

    def test_initialization_creates_draw_object(self):
        """Test canvas creates ImageDraw object."""
        self.assertIsNotNone(self.canvas.draw)

    # ========================================================================
    # Stroke Validation Tests
    # ========================================================================

    def test_validate_stroke_valid_line(self):
        """Test validation passes for valid line stroke."""
        valid_stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Test stroke",
        }
        # Should not raise
        self.canvas._validate_stroke(valid_stroke)

    def test_validate_stroke_missing_required_field(self):
        """Test validation fails for missing required field."""
        invalid_stroke: dict = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            # Missing end_x, end_y
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("end_x", str(context.exception))

    def test_validate_stroke_invalid_type(self):
        """Test validation fails for invalid stroke type."""
        invalid_stroke: Stroke = {
            "type": "invalid_type",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("Invalid stroke type", str(context.exception))

    def test_validate_stroke_coordinates_out_of_bounds(self):
        """Test validation fails for out-of-bounds coordinates."""
        # start_x out of bounds
        invalid_stroke: Stroke = {
            "type": "line",
            "start_x": -10,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("start_x", str(context.exception))
        self.assertIn("out of bounds", str(context.exception))

    def test_validate_stroke_coordinates_exceed_canvas(self):
        """Test validation fails for coordinates exceeding canvas size."""
        invalid_stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 500,  # Exceeds canvas width of 400
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("end_x", str(context.exception))
        self.assertIn("out of bounds", str(context.exception))

    def test_validate_stroke_invalid_hex_color(self):
        """Test validation fails for invalid hex color format."""
        invalid_strokes = [
            {"color_hex": "FF5733"},  # Missing #
            {"color_hex": "#FF57"},  # Too short
            {"color_hex": "#FF57339"},  # Too long
            {"color_hex": "#GGGGGG"},  # Invalid hex chars
            {"color_hex": "#ff57-3"},  # Invalid chars
        ]

        for invalid_color in invalid_strokes:
            stroke: Stroke = {
                "type": "line",
                "start_x": 50,
                "start_y": 50,
                "end_x": 150,
                "end_y": 150,
                "color_hex": invalid_color["color_hex"],
                "thickness": 3,
                "opacity": 0.8,
                "reasoning": "Test",
            }
            with self.assertRaises(ValueError) as context:
                self.canvas._validate_stroke(stroke)
            self.assertIn("hex color", str(context.exception).lower())

    def test_validate_stroke_thickness_below_minimum(self):
        """Test validation fails for thickness below minimum."""
        invalid_stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 0,  # Below MIN_STROKE_THICKNESS
            "opacity": 0.8,
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("Thickness", str(context.exception))
        self.assertIn("out of range", str(context.exception))

    def test_validate_stroke_thickness_above_maximum(self):
        """Test validation fails for thickness above maximum."""
        invalid_stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 15,  # Above MAX_STROKE_THICKNESS
            "opacity": 0.8,
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("Thickness", str(context.exception))
        self.assertIn("out of range", str(context.exception))

    def test_validate_stroke_opacity_below_minimum(self):
        """Test validation fails for opacity below minimum."""
        invalid_stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.05,  # Below MIN_STROKE_OPACITY
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("Opacity", str(context.exception))
        self.assertIn("out of range", str(context.exception))

    def test_validate_stroke_opacity_above_maximum(self):
        """Test validation fails for opacity above maximum."""
        invalid_stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 1.5,  # Above MAX_STROKE_OPACITY
            "reasoning": "Test",
        }
        with self.assertRaises(ValueError) as context:
            self.canvas._validate_stroke(invalid_stroke)
        self.assertIn("Opacity", str(context.exception))
        self.assertIn("out of range", str(context.exception))

    def test_validate_stroke_edge_case_max_values(self):
        """Test validation passes for maximum valid values."""
        valid_stroke: Stroke = {
            "type": "line",
            "start_x": 399,  # Max valid for 400px width
            "start_y": 299,  # Max valid for 300px height
            "end_x": 399,
            "end_y": 299,
            "color_hex": "#FFFFFF",
            "thickness": MAX_STROKE_THICKNESS,
            "opacity": MAX_STROKE_OPACITY,
            "reasoning": "Test max values",
        }
        # Should not raise
        self.canvas._validate_stroke(valid_stroke)

    def test_validate_stroke_edge_case_min_values(self):
        """Test validation passes for minimum valid values."""
        valid_stroke: Stroke = {
            "type": "line",
            "start_x": 0,
            "start_y": 0,
            "end_x": 0,
            "end_y": 0,
            "color_hex": "#000000",
            "thickness": MIN_STROKE_THICKNESS,
            "opacity": MIN_STROKE_OPACITY,
            "reasoning": "Test min values",
        }
        # Should not raise
        self.canvas._validate_stroke(valid_stroke)

    # ========================================================================
    # Stroke Application Tests
    # ========================================================================

    def test_apply_stroke_increments_count(self):
        """Test applying stroke increments stroke count."""
        initial_count = self.canvas.stroke_count

        stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Test stroke",
        }

        self.canvas.apply_stroke(stroke)
        self.assertEqual(self.canvas.stroke_count, initial_count + 1)

    def test_apply_stroke_multiple_strokes(self):
        """Test applying multiple strokes increments count correctly."""
        stroke1: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "First stroke",
        }

        stroke2: Stroke = {
            "type": "line",
            "start_x": 100,
            "start_y": 100,
            "end_x": 200,
            "end_y": 200,
            "color_hex": "#3498DB",
            "thickness": 2,
            "opacity": 0.6,
            "reasoning": "Second stroke",
        }

        self.canvas.apply_stroke(stroke1)
        self.canvas.apply_stroke(stroke2)

        self.assertEqual(self.canvas.stroke_count, 2)

    def test_apply_stroke_invalid_raises_error(self):
        """Test applying invalid stroke raises ValueError."""
        invalid_stroke: Stroke = {
            "type": "line",
            "start_x": -10,  # Invalid coordinate
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Invalid stroke",
        }

        with self.assertRaises(ValueError):
            self.canvas.apply_stroke(invalid_stroke)

    def test_apply_stroke_unsupported_type(self):
        """Test applying unsupported stroke type raises ValueError."""
        unsupported_stroke: Stroke = {
            "type": "curve",  # Not yet supported
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Curve stroke",
        }

        with self.assertRaises(ValueError) as context:
            self.canvas.apply_stroke(unsupported_stroke)
        self.assertIn("Unsupported stroke type", str(context.exception))

    def test_apply_stroke_modifies_image(self):
        """Test applying stroke modifies the canvas image."""
        # Get initial image state
        initial_pixels = self.canvas.image.copy()

        stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF0000",  # Red
            "thickness": 5,
            "opacity": 1.0,
            "reasoning": "Visible stroke",
        }

        self.canvas.apply_stroke(stroke)

        # Image should be different after applying stroke
        self.assertNotEqual(
            list(initial_pixels.getdata()), list(self.canvas.image.getdata())
        )

    # ========================================================================
    # File I/O Tests
    # ========================================================================

    def test_save_snapshot_creates_file(self):
        """Test save_snapshot creates PNG file."""
        filepath = self.canvas.save_snapshot(1, self.test_dir)

        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.suffix, ".png")
        self.assertEqual(filepath.name, "iteration-001.png")

    def test_save_snapshot_creates_directory(self):
        """Test save_snapshot creates output directory if needed."""
        nested_dir = self.test_dir / "snapshots" / "nested"
        filepath = self.canvas.save_snapshot(1, nested_dir)

        self.assertTrue(nested_dir.exists())
        self.assertTrue(filepath.exists())

    def test_save_snapshot_multiple_iterations(self):
        """Test saving multiple snapshots with different iterations."""
        filepath1 = self.canvas.save_snapshot(1, self.test_dir)
        filepath2 = self.canvas.save_snapshot(5, self.test_dir)
        filepath3 = self.canvas.save_snapshot(100, self.test_dir)

        self.assertTrue(filepath1.exists())
        self.assertTrue(filepath2.exists())
        self.assertTrue(filepath3.exists())

        self.assertEqual(filepath1.name, "iteration-001.png")
        self.assertEqual(filepath2.name, "iteration-005.png")
        self.assertEqual(filepath3.name, "iteration-100.png")

    def test_save_snapshot_returns_correct_path(self):
        """Test save_snapshot returns the correct Path object."""
        expected_path = self.test_dir / "iteration-042.png"
        actual_path = self.canvas.save_snapshot(42, self.test_dir)

        self.assertEqual(actual_path, expected_path)

    def test_save_snapshot_valid_png(self):
        """Test saved snapshot is a valid PNG image."""
        filepath = self.canvas.save_snapshot(1, self.test_dir)

        # Should be able to load with PIL
        loaded_image = Image.open(filepath)
        self.assertEqual(loaded_image.size, (self.canvas.width, self.canvas.height))
        self.assertEqual(loaded_image.mode, "RGB")

    def test_get_image_bytes_returns_bytes(self):
        """Test get_image_bytes returns bytes object."""
        image_bytes = self.canvas.get_image_bytes()

        self.assertIsInstance(image_bytes, bytes)
        self.assertGreater(len(image_bytes), 0)

    def test_get_image_bytes_valid_png(self):
        """Test get_image_bytes returns valid PNG data."""
        image_bytes = self.canvas.get_image_bytes(format="PNG")

        # Should be able to load with PIL
        from io import BytesIO

        loaded_image = Image.open(BytesIO(image_bytes))

        self.assertEqual(loaded_image.size, (self.canvas.width, self.canvas.height))

    def test_get_image_bytes_different_formats(self):
        """Test get_image_bytes works with different formats."""
        png_bytes = self.canvas.get_image_bytes(format="PNG")
        jpeg_bytes = self.canvas.get_image_bytes(format="JPEG")

        self.assertIsInstance(png_bytes, bytes)
        self.assertIsInstance(jpeg_bytes, bytes)
        # Different formats should produce different bytes
        self.assertNotEqual(png_bytes, jpeg_bytes)

    def test_save_final_artwork_default_format(self):
        """Test save_final_artwork saves PNG by default."""
        base_path = self.test_dir / "final_artwork"
        saved_paths = self.canvas.save_final_artwork(base_path)

        self.assertEqual(len(saved_paths), 1)
        self.assertTrue(saved_paths[0].exists())
        self.assertEqual(saved_paths[0].suffix, ".png")

    def test_save_final_artwork_multiple_formats(self):
        """Test save_final_artwork saves multiple formats."""
        base_path = self.test_dir / "final_artwork"
        saved_paths = self.canvas.save_final_artwork(base_path, formats=["PNG", "JPEG"])

        self.assertEqual(len(saved_paths), 2)
        self.assertTrue(all(p.exists() for p in saved_paths))

        extensions = {p.suffix for p in saved_paths}
        self.assertEqual(extensions, {".png", ".jpeg"})

    # ========================================================================
    # State Management Tests
    # ========================================================================

    def test_get_state_returns_correct_structure(self):
        """Test get_state returns CanvasState TypedDict."""
        state = self.canvas.get_state()

        self.assertIn("width", state)
        self.assertIn("height", state)
        self.assertIn("background_color", state)
        self.assertIn("stroke_count", state)
        self.assertIn("current_iteration", state)

    def test_get_state_returns_correct_values(self):
        """Test get_state returns correct current values."""
        state = self.canvas.get_state()

        self.assertEqual(state["width"], 400)
        self.assertEqual(state["height"], 300)
        self.assertEqual(state["background_color"], "#FFFFFF")
        self.assertEqual(state["stroke_count"], 0)
        self.assertEqual(state["current_iteration"], 0)

    def test_get_state_after_strokes(self):
        """Test get_state reflects changes after applying strokes."""
        stroke: Stroke = {
            "type": "line",
            "start_x": 50,
            "start_y": 50,
            "end_x": 150,
            "end_y": 150,
            "color_hex": "#FF5733",
            "thickness": 3,
            "opacity": 0.8,
            "reasoning": "Test stroke",
        }

        self.canvas.apply_stroke(stroke)
        self.canvas.apply_stroke(stroke)

        state = self.canvas.get_state()
        self.assertEqual(state["stroke_count"], 2)

    # ========================================================================
    # Helper Method Tests
    # ========================================================================

    def test_hex_to_rgb_conversion(self):
        """Test _hex_to_rgb converts colors correctly."""
        test_cases = [
            ("#FF0000", (255, 0, 0)),  # Red
            ("#00FF00", (0, 255, 0)),  # Green
            ("#0000FF", (0, 0, 255)),  # Blue
            ("#FFFFFF", (255, 255, 255)),  # White
            ("#000000", (0, 0, 0)),  # Black
            ("#FF5733", (255, 87, 51)),  # Custom color
        ]

        for hex_color, expected_rgb in test_cases:
            result = self.canvas._hex_to_rgb(hex_color)
            self.assertEqual(result, expected_rgb)

    def test_hex_to_rgb_lowercase(self):
        """Test _hex_to_rgb handles lowercase hex values."""
        result = self.canvas._hex_to_rgb("#ff5733")
        self.assertEqual(result, (255, 87, 51))

    def test_hex_to_rgb_without_hash(self):
        """Test _hex_to_rgb handles colors without leading #."""
        result = self.canvas._hex_to_rgb("FF5733")
        self.assertEqual(result, (255, 87, 51))


if __name__ == "__main__":
    unittest.main()
