"""Unit tests for GIF generator."""

import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from services.gif_generator import GifGenerator


@pytest.fixture
def temp_snapshots_dir():
    """Create a temporary directory for test snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    img = Image.new("RGB", (800, 600), color=(255, 0, 0))
    return img


def test_generate_from_batch_snapshots(temp_snapshots_dir):
    """Test GIF generation from batch snapshots."""
    # Create batch snapshot files with different colors
    snapshot_files = [
        ("snapshot_001_00.png", (255, 0, 0)),
        ("snapshot_001_01.png", (0, 255, 0)),
        ("snapshot_002_00.png", (0, 0, 255)),
    ]

    for filename, color in snapshot_files:
        img = Image.new("RGB", (800, 600), color=color)
        img.save(temp_snapshots_dir / filename)

    # Generate GIF
    generator = GifGenerator()
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is not None
    assert output_path.exists()

    # Verify it's a valid GIF with correct frame count
    with Image.open(output_path) as gif:
        assert gif.format == "GIF"
        # PIL GIFs may have n_frames attribute
        if hasattr(gif, "n_frames"):
            assert gif.n_frames == 3
        else:
            # Fallback: count frames
            frame_count = 0
            try:
                while True:
                    gif.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            assert frame_count == 3


def test_generate_from_iteration_snapshots(temp_snapshots_dir, sample_image):
    """Test GIF generation from iteration snapshots."""
    # Create iteration snapshot files
    snapshot_files = [
        "iteration-001.png",
        "iteration-002.png",
        "iteration-003.png",
    ]

    for filename in snapshot_files:
        sample_image.save(temp_snapshots_dir / filename)

    # Generate GIF
    generator = GifGenerator()
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is not None
    assert output_path.exists()


def test_prefers_batch_over_iteration_snapshots(temp_snapshots_dir):
    """Test that batch snapshots are preferred over iteration snapshots."""
    # Create both types with different colors
    batch_files = [
        ("snapshot_001_00.png", (255, 0, 0)),
        ("snapshot_001_01.png", (0, 255, 0)),
    ]
    iteration_files = [
        ("iteration-001.png", (0, 0, 255)),
        ("iteration-002.png", (255, 255, 0)),
        ("iteration-003.png", (255, 0, 255)),
    ]

    for filename, color in batch_files + iteration_files:
        img = Image.new("RGB", (800, 600), color=color)
        img.save(temp_snapshots_dir / filename)

    # Generate GIF
    generator = GifGenerator()
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is not None

    # Verify frame count matches batch snapshots (2), not iteration (3)
    with Image.open(output_path) as gif:
        if hasattr(gif, "n_frames"):
            assert gif.n_frames == 2
        else:
            frame_count = 0
            try:
                while True:
                    gif.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            assert frame_count == 2


def test_excludes_current_iteration(temp_snapshots_dir):
    """Test that current-iteration.png is excluded from frames."""
    # Create iteration snapshots including current-iteration.png with different colors
    snapshot_files = [
        ("iteration-001.png", (255, 0, 0)),
        ("iteration-002.png", (0, 255, 0)),
        ("current-iteration.png", (0, 0, 255)),  # Should be excluded
    ]

    for filename, color in snapshot_files:
        img = Image.new("RGB", (800, 600), color=color)
        img.save(temp_snapshots_dir / filename)

    # Generate GIF
    generator = GifGenerator()
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is not None

    # Verify only 2 frames (current-iteration excluded)
    with Image.open(output_path) as gif:
        if hasattr(gif, "n_frames"):
            assert gif.n_frames == 2
        else:
            frame_count = 0
            try:
                while True:
                    gif.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            assert frame_count == 2


def test_returns_none_for_empty_directory(temp_snapshots_dir):
    """Test that empty directory returns None."""
    generator = GifGenerator()
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is None
    assert not output_path.exists()


def test_returns_none_for_single_frame(temp_snapshots_dir, sample_image):
    """Test that single frame returns None (need minimum 2)."""
    # Create only one snapshot
    sample_image.save(temp_snapshots_dir / "iteration-001.png")

    generator = GifGenerator()
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is None
    assert not output_path.exists()


def test_frame_ordering(temp_snapshots_dir, sample_image):
    """Test that frames are sorted correctly by iteration then stroke index."""
    # Create batch snapshots in non-sequential order
    snapshot_files = [
        "snapshot_002_00.png",
        "snapshot_001_01.png",
        "snapshot_001_00.png",
        "snapshot_002_01.png",
    ]

    # Create images with different colors to verify order
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    for filename, color in zip(snapshot_files, colors):
        img = Image.new("RGB", (800, 600), color=color)
        img.save(temp_snapshots_dir / filename)

    # Collect frames using the generator's method
    generator = GifGenerator()
    frames = generator._collect_frames(temp_snapshots_dir)

    # Verify correct order: 001_00, 001_01, 002_00, 002_01
    assert len(frames) == 4
    assert frames[0].name == "snapshot_001_00.png"
    assert frames[1].name == "snapshot_001_01.png"
    assert frames[2].name == "snapshot_002_00.png"
    assert frames[3].name == "snapshot_002_01.png"


def test_resize_preserves_aspect_ratio(temp_snapshots_dir):
    """Test that resizing preserves aspect ratio."""
    # Create 800x600 image
    img = Image.new("RGB", (800, 600), color=(255, 0, 0))

    generator = GifGenerator(max_dimension=400)
    resized = generator._resize_frame(img)

    # Should be resized to 400x300 (preserving 4:3 ratio)
    assert resized.size == (400, 300)

    # Test portrait orientation
    img_portrait = Image.new("RGB", (600, 800), color=(0, 255, 0))
    resized_portrait = generator._resize_frame(img_portrait)

    # Should be resized to 300x400 (preserving 3:4 ratio)
    assert resized_portrait.size == (300, 400)


def test_resize_no_op_for_small_images(temp_snapshots_dir):
    """Test that images smaller than max dimension are not resized."""
    # Create 200x150 image (smaller than max 400)
    img = Image.new("RGB", (200, 150), color=(255, 0, 0))

    generator = GifGenerator(max_dimension=400)
    resized = generator._resize_frame(img)

    # Should remain unchanged
    assert resized.size == (200, 150)


def test_custom_frame_duration(temp_snapshots_dir, sample_image):
    """Test that custom frame duration is applied."""
    # Create snapshots
    for i in range(3):
        sample_image.save(temp_snapshots_dir / f"iteration-{i + 1:03d}.png")

    # Generate with custom duration
    custom_duration = 250
    generator = GifGenerator(frame_duration_ms=custom_duration, final_frame_hold_ms=500)
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is not None

    # Verify durations were built correctly
    durations = generator._build_durations(3)
    assert durations[0] == custom_duration
    assert durations[1] == custom_duration
    assert durations[2] == 500  # Final frame hold


def test_final_frame_hold(temp_snapshots_dir):
    """Test that final frame has extended hold duration."""
    generator = GifGenerator(frame_duration_ms=150, final_frame_hold_ms=1500)

    # Test with various frame counts
    for frame_count in [2, 5, 10]:
        durations = generator._build_durations(frame_count)

        assert len(durations) == frame_count
        # All frames except last should have standard duration
        for i in range(frame_count - 1):
            assert durations[i] == 150
        # Last frame should have extended duration
        assert durations[-1] == 1500


def test_build_durations_empty():
    """Test duration building with zero frames."""
    generator = GifGenerator()
    durations = generator._build_durations(0)

    assert durations == []


def test_generate_handles_corrupt_frames(temp_snapshots_dir):
    """Test that corrupt frames are skipped gracefully."""
    # Create valid snapshots with different colors
    img1 = Image.new("RGB", (800, 600), color=(255, 0, 0))
    img1.save(temp_snapshots_dir / "iteration-001.png")

    img2 = Image.new("RGB", (800, 600), color=(0, 255, 0))
    img2.save(temp_snapshots_dir / "iteration-003.png")

    # Create corrupt file
    corrupt_file = temp_snapshots_dir / "iteration-002.png"
    with open(corrupt_file, "w") as f:
        f.write("not an image")

    # Generate GIF - should skip corrupt frame
    generator = GifGenerator()
    output_path = temp_snapshots_dir / "test.gif"
    result = generator.generate(temp_snapshots_dir, output_path)

    assert result is not None

    # Should have 2 frames (corrupt one skipped)
    with Image.open(output_path) as gif:
        if hasattr(gif, "n_frames"):
            assert gif.n_frames == 2
        else:
            frame_count = 0
            try:
                while True:
                    gif.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            assert frame_count == 2


def test_nonexistent_directory():
    """Test that nonexistent directory is handled gracefully."""
    generator = GifGenerator()
    nonexistent = Path("/nonexistent/path/to/snapshots")
    output_path = Path("/tmp/test.gif")

    result = generator.generate(nonexistent, output_path)

    assert result is None
