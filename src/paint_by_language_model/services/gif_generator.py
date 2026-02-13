"""
GIF timelapse generator for artwork creation process.

This module provides functionality to create animated GIFs from iteration
snapshots, showing the progression of artwork generation stroke-by-stroke.
"""

import logging
import re
from pathlib import Path

from PIL import Image

from config import (
    GIF_FINAL_FRAME_HOLD_MS,
    GIF_FRAME_DURATION_MS,
    GIF_LOOP_COUNT,
    GIF_MAX_DIMENSION,
)

logger = logging.getLogger(__name__)


class GifGenerator:
    """Generates animated GIF timelapses from iteration snapshots."""

    def __init__(
        self,
        frame_duration_ms: int = GIF_FRAME_DURATION_MS,
        final_frame_hold_ms: int = GIF_FINAL_FRAME_HOLD_MS,
        max_dimension: int = GIF_MAX_DIMENSION,
        loop_count: int = GIF_LOOP_COUNT,
    ):
        """
        Initialize the GIF generator.

        Args:
            frame_duration_ms (int): Duration of each frame in milliseconds
            final_frame_hold_ms (int): Duration to hold the final frame
            max_dimension (int): Maximum width or height for resized frames
            loop_count (int): Number of times to loop (0 = infinite)
        """
        self.frame_duration_ms = frame_duration_ms
        self.final_frame_hold_ms = final_frame_hold_ms
        self.max_dimension = max_dimension
        self.loop_count = loop_count

    def generate(self, snapshots_dir: Path, output_path: Path) -> Path | None:
        """
        Generate an animated GIF from snapshot images.

        Args:
            snapshots_dir (Path): Directory containing snapshot PNGs
            output_path (Path): Path to save the output GIF

        Returns:
            Path | None: Path to generated GIF, or None if generation failed
        """
        # Collect and sort frame paths
        frame_paths = self._collect_frames(snapshots_dir)

        if len(frame_paths) < 2:
            logger.warning(f"Need at least 2 frames to generate GIF, found {len(frame_paths)}")
            return None

        logger.info(f"Generating GIF from {len(frame_paths)} frames...")

        # Load and resize frames
        frames: list[Image.Image] = []
        for frame_path in frame_paths:
            try:
                image = Image.open(frame_path)
                resized = self._resize_frame(image)
                # Convert to RGB mode for GIF compatibility
                if resized.mode not in ("RGB", "P"):
                    resized = resized.convert("RGB")
                frames.append(resized)
            except Exception as e:
                logger.warning(f"Failed to load frame {frame_path}: {e}")
                continue

        if len(frames) < 2:
            logger.warning(f"Only {len(frames)} frames loaded successfully, need at least 2")
            return None

        # Build duration list
        durations = self._build_durations(len(frames))

        # Save animated GIF
        try:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=self.loop_count,
                optimize=False,  # Faster save, slightly larger file
            )
            logger.info(f"GIF saved: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save GIF: {e}")
            return None

    def _collect_frames(self, snapshots_dir: Path) -> list[Path]:
        """
        Collect and sort snapshot files in chronological order.

        Prefers per-stroke batch snapshots (snapshot_NNN_MM.png) for smoother
        animation. Falls back to per-iteration snapshots (iteration-NNN.png)
        if batch snapshots are unavailable.

        Args:
            snapshots_dir (Path): Directory containing snapshot PNGs

        Returns:
            list[Path]: Sorted list of snapshot file paths
        """
        if not snapshots_dir.exists():
            logger.warning(f"Snapshots directory does not exist: {snapshots_dir}")
            return []

        # Try batch snapshots first (snapshot_001_00.png)
        batch_pattern = re.compile(r"snapshot_(\d+)_(\d+)\.png")
        batch_snapshots = []

        for path in snapshots_dir.glob("snapshot_*_*.png"):
            match = batch_pattern.match(path.name)
            if match:
                iteration = int(match.group(1))
                stroke_index = int(match.group(2))
                batch_snapshots.append((iteration, stroke_index, path))

        if batch_snapshots:
            # Sort by iteration, then stroke index
            batch_snapshots.sort(key=lambda x: (x[0], x[1]))
            frame_paths = [path for _, _, path in batch_snapshots]
            logger.debug(f"Using {len(frame_paths)} batch snapshots for GIF generation")
            return frame_paths

        # Fallback to per-iteration snapshots (iteration-001.png)
        iteration_pattern = re.compile(r"iteration-(\d+)\.png")
        iteration_snapshots = []

        for path in snapshots_dir.glob("iteration-*.png"):
            # Exclude current-iteration.png (temp file)
            if path.name == "current-iteration.png":
                continue

            match = iteration_pattern.match(path.name)
            if match:
                iteration = int(match.group(1))
                iteration_snapshots.append((iteration, path))

        if iteration_snapshots:
            # Sort by iteration number
            iteration_snapshots.sort(key=lambda x: x[0])
            frame_paths = [path for _, path in iteration_snapshots]
            logger.debug(f"Using {len(frame_paths)} iteration snapshots for GIF generation")
            return frame_paths

        logger.warning(f"No snapshot files found in {snapshots_dir}")
        return []

    def _resize_frame(self, image: Image.Image) -> Image.Image:
        """
        Resize a frame to fit within max_dimension, preserving aspect ratio.

        Args:
            image (Image.Image): Original frame image

        Returns:
            Image.Image: Resized frame image
        """
        width, height = image.size

        # Check if resizing is needed
        if width <= self.max_dimension and height <= self.max_dimension:
            return image

        # Calculate new dimensions preserving aspect ratio
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))

        # Resize using high-quality resampling
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return resized

    def _build_durations(self, frame_count: int) -> list[int]:
        """
        Build per-frame duration list with extended hold on final frame.

        Args:
            frame_count (int): Total number of frames

        Returns:
            list[int]: Duration in milliseconds for each frame
        """
        # All frames use standard duration except the last
        durations = [self.frame_duration_ms] * frame_count

        # Extend duration on final frame so viewers can appreciate the result
        if frame_count > 0:
            durations[-1] = self.final_frame_hold_ms

        return durations
