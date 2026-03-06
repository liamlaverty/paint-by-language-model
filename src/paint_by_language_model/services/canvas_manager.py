"""Canvas management for image generation."""

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from config import (
    CANVAS_BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
)
from models import CanvasState, Stroke
from services.renderers import StrokeRendererFactory

logger = logging.getLogger(__name__)


class CanvasManager:
    """Manages the image canvas for iterative stroke application."""

    def __init__(
        self,
        width: int = CANVAS_WIDTH,
        height: int = CANVAS_HEIGHT,
        background_color: str = CANVAS_BACKGROUND_COLOR,
    ):
        """
        Initialize a new canvas with specified dimensions and background.

        Args:
            width (int): Canvas width in pixels
            height (int): Canvas height in pixels
            background_color (str): Background color in hex format "#RRGGBB"
        """
        self.width = width
        self.height = height
        self.background_color = background_color

        # Create PIL Image
        self.image = Image.new("RGB", (width, height), background_color)
        self.draw = ImageDraw.Draw(self.image, "RGBA")  # RGBA for opacity support

        self.stroke_count = 0
        self.current_iteration = 0

        logger.info(f"Initialized canvas: {width}x{height}, background={background_color}")

    def apply_stroke(self, stroke: Stroke) -> None:
        """
        Apply a single stroke to the canvas.

        Args:
            stroke (Stroke): Stroke TypedDict containing stroke parameters

        Raises:
            ValueError: If stroke validation fails
            RuntimeError: If canvas is not initialized
        """
        if self.image is None:
            raise RuntimeError("Canvas is not initialized")

        # Get appropriate renderer for stroke type
        renderer = StrokeRendererFactory.get_renderer(stroke["type"])

        # Validate stroke using renderer's validation
        renderer.validate(stroke, (self.width, self.height))

        # Render stroke using renderer
        if renderer.needs_image_access:
            self.image = renderer.render_to_image(stroke, self.image)
            # Re-create ImageDraw since the underlying image may have changed
            self.draw = ImageDraw.Draw(self.image, "RGBA")
        else:
            renderer.render(stroke, self.draw)

        self.stroke_count += 1
        logger.info(f"Applied stroke {self.stroke_count}: type={stroke['type']}")

    def apply_strokes(
        self,
        strokes: list[Stroke],
        save_snapshots: bool = True,
        snapshot_dir: Path | None = None,
        base_iteration: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Apply multiple strokes to the canvas with optional snapshots.

        Applies strokes in order. Failed strokes are skipped without
        stopping the batch.

        Args:
            strokes (list[Stroke]): Strokes to apply in order
            save_snapshots (bool): Save snapshot after each successful stroke
            snapshot_dir (Path | None): Directory for snapshots
            base_iteration (int): Base iteration number for snapshot naming

        Returns:
            list[dict[str, Any]]: Results for each stroke with keys:
                - "index": int - Position in input list
                - "success": bool - Whether stroke was applied
                - "error": str | None - Error message if failed
                - "snapshot_path": Path | None - Path to snapshot if saved

        Raises:
            RuntimeError: If canvas is not initialized
            ValueError: If save_snapshots=True but snapshot_dir is None
        """
        if self.image is None:
            raise RuntimeError("Canvas is not initialized")

        if save_snapshots and snapshot_dir is None:
            raise ValueError("snapshot_dir is required when save_snapshots=True")

        results: list[dict[str, Any]] = []

        for idx, stroke in enumerate(strokes):
            result: dict[str, Any] = {
                "index": idx,
                "success": False,
                "error": None,
                "snapshot_path": None,
            }

            try:
                # Apply stroke using renderer factory
                self.apply_stroke(stroke)
                result["success"] = True

                # Save snapshot if requested
                if save_snapshots and snapshot_dir is not None:
                    snapshot_path = self._save_batch_snapshot(base_iteration, idx, snapshot_dir)
                    result["snapshot_path"] = snapshot_path

                logger.info(
                    f"Stroke {idx + 1}/{len(strokes)} applied successfully "
                    f"(type={stroke.get('type', 'unknown')})"
                )

            except Exception as e:
                # Log error and skip stroke without stopping batch
                error_msg = str(e)
                result["error"] = error_msg
                logger.warning(
                    f"Stroke {idx + 1}/{len(strokes)} failed: {error_msg} "
                    f"(type={stroke.get('type', 'unknown')})"
                )

            results.append(result)

        # Log batch summary
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        logger.info(
            f"Batch complete: {successful} successful, {failed} failed "
            f"out of {len(strokes)} strokes"
        )

        return results

    def _save_batch_snapshot(
        self, base_iteration: int, stroke_index: int, output_dir: Path
    ) -> Path:
        """
        Save a snapshot during batch stroke processing.

        Args:
            base_iteration (int): Base iteration number
            stroke_index (int): Index of stroke within batch
            output_dir (Path): Directory to save snapshot in

        Returns:
            Path: Path to saved snapshot file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"snapshot_{base_iteration:03d}_{stroke_index:02d}.png"
        filepath = output_dir / filename

        self.image.save(filepath, format="PNG")
        logger.debug(f"Saved batch snapshot to {filepath}")

        return filepath

    def save_snapshot(self, iteration: int, output_dir: Path) -> Path:
        """
        Save current canvas state as PNG image.

        Args:
            iteration (int): Current iteration number
            output_dir (Path): Directory to save snapshot in

        Returns:
            Path: Path to saved snapshot file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"iteration-{iteration:03d}.png"
        filepath = output_dir / filename

        self.image.save(filepath, format="PNG")
        logger.info(f"Saved snapshot to {filepath}")

        return filepath

    def get_image_bytes(self, format: str = "PNG") -> bytes:
        """
        Convert canvas to bytes for VLM queries.

        Args:
            format (str): Image format (default: "PNG")

        Returns:
            bytes: Image as bytes
        """
        buffer = BytesIO()
        self.image.save(buffer, format=format)
        return buffer.getvalue()

    def get_state(self) -> CanvasState:
        """
        Get current canvas state as TypedDict.

        Returns:
            CanvasState: Current canvas state
        """
        return {
            "width": self.width,
            "height": self.height,
            "background_color": self.background_color,
            "stroke_count": self.stroke_count,
            "current_iteration": self.current_iteration,
        }

    def save_final_artwork(self, output_path: Path, formats: list[str] | None = None) -> list[Path]:
        """
        Save final artwork in multiple formats.

        Args:
            output_path (Path): Base path for output file (without extension)
            formats (list[str] | None): List of formats to save (default: ["PNG"])

        Returns:
            list[Path]: List of paths to saved files
        """
        if formats is None:
            formats = ["PNG"]

        saved_paths = []

        for fmt in formats:
            filepath = output_path.with_suffix(f".{fmt.lower()}")
            self.image.save(filepath, format=fmt)
            saved_paths.append(filepath)
            logger.info(f"Saved final artwork to {filepath}")

        return saved_paths
