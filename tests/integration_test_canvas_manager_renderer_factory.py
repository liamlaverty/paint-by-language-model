"""Integration test for CanvasManager with StrokeRendererFactory.

Tests that CanvasManager correctly delegates stroke rendering to the
StrokeRendererFactory and that all 5 stroke types (line, arc, polyline,
circle, splatter) render successfully. Also verifies batch processing
with apply_strokes() handles mixed valid/invalid strokes correctly.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.canvas_manager import CanvasManager

# Test 1: Verify all 5 stroke types render via factory delegation
print("Test 1: Testing all 5 stroke types individually...")
canvas = CanvasManager(width=800, height=600)

strokes = [
    {
        "type": "line",
        "start_x": 100,
        "start_y": 100,
        "end_x": 200,
        "end_y": 200,
        "color_hex": "#FF0000",
        "thickness": 3,
        "opacity": 1.0,
    },
    {
        "type": "arc",
        "arc_bbox": (150, 150, 250, 250),
        "arc_start_angle": 0,
        "arc_end_angle": 180,
        "color_hex": "#00FF00",
        "thickness": 2,
        "opacity": 0.8,
    },
    {
        "type": "polyline",
        "points": [(300, 100), (350, 150), (400, 120), (450, 180)],
        "color_hex": "#0000FF",
        "thickness": 2,
        "opacity": 0.9,
    },
    {
        "type": "circle",
        "center_x": 500,
        "center_y": 300,
        "radius": 50,
        "fill": True,
        "color_hex": "#FFFF00",
        "thickness": 2,
        "opacity": 0.7,
    },
    {
        "type": "splatter",
        "center_x": 600,
        "center_y": 400,
        "splatter_radius": 40,
        "splatter_count": 30,
        "dot_size_min": 2,
        "dot_size_max": 6,
        "color_hex": "#FF00FF",
        "thickness": 1,
        "opacity": 0.6,
    },
]

for stroke in strokes:
    try:
        canvas.apply_stroke(stroke)
        print(f"✅ {stroke['type']} stroke applied successfully")
    except Exception as e:
        print(f"❌ {stroke['type']} stroke failed: {e}")

print(f"\nTotal strokes applied: {canvas.stroke_count}")

# Test 2: Verify batch processing handles errors gracefully
# Tests that apply_strokes() continues processing after invalid strokes
print("\n\nTest 2: Testing batch processing with apply_strokes()...")
canvas2 = CanvasManager(width=800, height=600)

batch_strokes = [
    {
        "type": "line",
        "start_x": 50,
        "start_y": 50,
        "end_x": 150,
        "end_y": 150,
        "color_hex": "#FF5733",
        "thickness": 2,
        "opacity": 1.0,
    },
    {
        "type": "invalid_type",  # This should fail
        "color_hex": "#00FF00",
        "thickness": 2,
        "opacity": 1.0,
    },
    {
        "type": "circle",
        "center_x": 300,
        "center_y": 200,
        "radius": 60,
        "fill": False,
        "color_hex": "#3366FF",
        "thickness": 3,
        "opacity": 0.8,
    },
]

results = canvas2.apply_strokes(batch_strokes, save_snapshots=False)

print("\nBatch results:")
for result in results:
    status = "✅ Success" if result["success"] else f"❌ Failed: {result['error']}"
    print(f"  Stroke {result['index']}: {status}")

print(f"\nTotal successful strokes: {canvas2.stroke_count}")

print("\n✅ All integration tests completed!")
