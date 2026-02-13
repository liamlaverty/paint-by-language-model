"""Tests for CanvasManager batch stroke processing (Phase 3 functionality)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from config import CANVAS_HEIGHT, CANVAS_WIDTH
from services.canvas_manager import CanvasManager


class TestCanvasManagerBatch(unittest.TestCase):
    """Test suite for CanvasManager batch stroke processing."""

    def setUp(self):
        """Set up test canvas before each test."""
        self.canvas = CanvasManager(width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.temp_dir = tempfile.mkdtemp()
        self.snapshot_dir = Path(self.temp_dir) / "snapshots"

    def test_apply_strokes_empty_list(self):
        """Test applying empty stroke list."""
        results = self.canvas.apply_strokes(strokes=[], save_snapshots=False)
        self.assertEqual(len(results), 0)

    def test_apply_strokes_single_stroke(self):
        """Test applying single stroke via batch method."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            }
        ]
        results = self.canvas.apply_strokes(strokes=strokes, save_snapshots=False)

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"])
        self.assertIsNone(results[0]["error"])
        self.assertEqual(results[0]["index"], 0)
        self.assertEqual(self.canvas.stroke_count, 1)

    def test_apply_strokes_multiple_valid_strokes(self):
        """Test applying multiple valid strokes."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "circle",
                "center_x": 200,
                "center_y": 150,
                "radius": 50,
                "fill": True,
                "color_hex": "#00FF00",
                "thickness": 2,
                "opacity": 0.8,
            },
            {
                "type": "arc",
                "arc_bbox": (100, 100, 200, 200),
                "arc_start_angle": 0,
                "arc_end_angle": 180,
                "color_hex": "#0000FF",
                "thickness": 3,
                "opacity": 0.9,
            },
        ]
        results = self.canvas.apply_strokes(strokes=strokes, save_snapshots=False)

        self.assertEqual(len(results), 3)
        for i, result in enumerate(results):
            self.assertTrue(result["success"], f"Stroke {i} should succeed")
            self.assertIsNone(result["error"])
            self.assertEqual(result["index"], i)
        self.assertEqual(self.canvas.stroke_count, 3)

    def test_apply_strokes_with_invalid_stroke(self):
        """Test that invalid stroke is skipped without stopping batch."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "invalid_type",
                "start_x": 50,
                "start_y": 50,
                "color_hex": "#00FF00",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "circle",
                "center_x": 200,
                "center_y": 150,
                "radius": 50,
                "fill": True,
                "color_hex": "#0000FF",
                "thickness": 2,
                "opacity": 0.8,
            },
        ]
        results = self.canvas.apply_strokes(strokes=strokes, save_snapshots=False)

        self.assertEqual(len(results), 3)
        self.assertTrue(results[0]["success"], "First stroke should succeed")
        self.assertFalse(results[1]["success"], "Second stroke should fail")
        self.assertIsNotNone(results[1]["error"], "Should have error message")
        self.assertTrue(results[2]["success"], "Third stroke should succeed")
        self.assertEqual(
            self.canvas.stroke_count, 2, "Only 2 strokes should be applied"
        )

    def test_apply_strokes_all_fail(self):
        """Test batch where all strokes fail validation."""
        strokes = [
            {
                "type": "invalid",
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "line",
                "start_x": -10,  # Out of bounds
                "start_y": -10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#00FF00",
                "thickness": 2,
                "opacity": 1.0,
            },
        ]
        results = self.canvas.apply_strokes(strokes=strokes, save_snapshots=False)

        self.assertEqual(len(results), 2)
        self.assertFalse(results[0]["success"])
        self.assertFalse(results[1]["success"])
        self.assertEqual(self.canvas.stroke_count, 0, "No strokes should be applied")

    def test_apply_strokes_with_snapshots(self):
        """Test that snapshots are saved after each successful stroke."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "circle",
                "center_x": 200,
                "center_y": 150,
                "radius": 30,
                "fill": True,
                "color_hex": "#00FF00",
                "thickness": 2,
                "opacity": 0.8,
            },
        ]
        results = self.canvas.apply_strokes(
            strokes=strokes,
            save_snapshots=True,
            snapshot_dir=self.snapshot_dir,
            base_iteration=5,
        )

        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result["success"])
            self.assertIsNotNone(result["snapshot_path"])
            self.assertTrue(result["snapshot_path"].exists())

        # Verify snapshot filenames
        self.assertEqual(results[0]["snapshot_path"].name, "snapshot_005_00.png")
        self.assertEqual(results[1]["snapshot_path"].name, "snapshot_005_01.png")

    def test_apply_strokes_snapshots_only_for_successful(self):
        """Test that snapshots are only saved for successful strokes."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "invalid",
                "color_hex": "#00FF00",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "circle",
                "center_x": 200,
                "center_y": 150,
                "radius": 30,
                "fill": True,
                "color_hex": "#0000FF",
                "thickness": 2,
                "opacity": 0.8,
            },
        ]
        results = self.canvas.apply_strokes(
            strokes=strokes,
            save_snapshots=True,
            snapshot_dir=self.snapshot_dir,
            base_iteration=3,
        )

        self.assertEqual(len(results), 3)
        self.assertTrue(results[0]["success"])
        self.assertIsNotNone(results[0]["snapshot_path"])
        self.assertFalse(results[1]["success"])
        self.assertIsNone(results[1]["snapshot_path"])
        self.assertTrue(results[2]["success"])
        self.assertIsNotNone(results[2]["snapshot_path"])

    def test_apply_strokes_requires_snapshot_dir_if_enabled(self):
        """Test that ValueError is raised if save_snapshots=True but no snapshot_dir."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            }
        ]
        with self.assertRaises(ValueError) as context:
            self.canvas.apply_strokes(
                strokes=strokes, save_snapshots=True, snapshot_dir=None
            )
        self.assertIn("snapshot_dir is required", str(context.exception))

    def test_apply_strokes_mixed_stroke_types(self):
        """Test batch with all supported stroke types."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "arc",
                "arc_bbox": (50, 50, 150, 150),
                "arc_start_angle": 0,
                "arc_end_angle": 90,
                "color_hex": "#00FF00",
                "thickness": 3,
                "opacity": 0.8,
            },
            {
                "type": "polyline",
                "points": [(10, 10), (50, 50), (100, 30), (150, 80)],
                "color_hex": "#0000FF",
                "thickness": 2,
                "opacity": 0.9,
            },
            {
                "type": "circle",
                "center_x": 200,
                "center_y": 150,
                "radius": 40,
                "fill": False,
                "color_hex": "#FFFF00",
                "thickness": 4,
                "opacity": 0.7,
            },
            {
                "type": "splatter",
                "center_x": 300,
                "center_y": 200,
                "splatter_radius": 30,
                "splatter_count": 20,
                "dot_size_min": 2,
                "dot_size_max": 5,
                "color_hex": "#FF00FF",
                "thickness": 1,
                "opacity": 0.6,
            },
        ]
        results = self.canvas.apply_strokes(strokes=strokes, save_snapshots=False)

        self.assertEqual(len(results), 5)
        for i, result in enumerate(results):
            self.assertTrue(
                result["success"],
                f"Stroke {i} (type={strokes[i]['type']}) should succeed",
            )
            self.assertIsNone(result["error"])
        self.assertEqual(self.canvas.stroke_count, 5)

    def test_apply_strokes_maintains_result_indices(self):
        """Test that result indices match input stroke indices."""
        strokes = [
            {
                "type": "line",
                "start_x": 10,
                "start_y": 10,
                "end_x": 100,
                "end_y": 100,
                "color_hex": "#FF0000",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "invalid",  # This will fail
                "color_hex": "#00FF00",
                "thickness": 2,
                "opacity": 1.0,
            },
            {
                "type": "circle",
                "center_x": 200,
                "center_y": 150,
                "radius": 30,
                "fill": True,
                "color_hex": "#0000FF",
                "thickness": 2,
                "opacity": 0.8,
            },
        ]
        results = self.canvas.apply_strokes(strokes=strokes, save_snapshots=False)

        for i, result in enumerate(results):
            self.assertEqual(
                result["index"], i, f"Result index should match input index {i}"
            )


if __name__ == "__main__":
    unittest.main()
