"""Canvas management for image generation."""

import logging
import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from config import (
    CANVAS_BACKGROUND_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    MAX_STROKE_OPACITY,
    MAX_STROKE_THICKNESS,
    MIN_STROKE_OPACITY,
    MIN_STROKE_THICKNESS,
)
from models import CanvasState, Stroke

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
            ValueError: If stroke parameters are invalid
        """
        # Validate stroke
        self._validate_stroke(stroke)

        if stroke["type"] == "line":
            self._draw_line(stroke)
        else:
            raise ValueError(f"Unsupported stroke type: {stroke['type']}")

        self.stroke_count += 1
        logger.info(f"Applied stroke {self.stroke_count}: {stroke['reasoning']}")

    def _validate_stroke(self, stroke: Stroke) -> None:
        """
        Validate stroke parameters before applying.

        Args:
            stroke (Stroke): Stroke to validate

        Raises:
            ValueError: If any validation fails with descriptive message
        """
        # Validate required fields are present
        required_fields = ["type", "start_x", "start_y", "color_hex", "thickness", "opacity"]
        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Missing required field: {field}")

        # Validate stroke type
        if stroke["type"] not in ["line", "curve", "fill"]:
            raise ValueError(f"Invalid stroke type: {stroke['type']}")

        # Validate coordinates for line strokes
        if stroke["type"] == "line":
            if "end_x" not in stroke or "end_y" not in stroke:
                raise ValueError("Line stroke requires end_x and end_y")

            start_x = stroke["start_x"]
            start_y = stroke["start_y"]
            end_x = stroke.get("end_x")
            end_y = stroke.get("end_y")

            if not (0 <= start_x < self.width):
                raise ValueError(f"start_x {start_x} out of bounds [0, {self.width})")
            if not (0 <= start_y < self.height):
                raise ValueError(f"start_y {start_y} out of bounds [0, {self.height})")
            if end_x is not None and not (0 <= end_x < self.width):
                raise ValueError(f"end_x {end_x} out of bounds [0, {self.width})")
            if end_y is not None and not (0 <= end_y < self.height):
                raise ValueError(f"end_y {end_y} out of bounds [0, {self.height})")

        # Validate color format
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        if not hex_pattern.match(stroke["color_hex"]):
            raise ValueError(f"Invalid hex color format: {stroke['color_hex']}")

        # Validate thickness
        if not (MIN_STROKE_THICKNESS <= stroke["thickness"] <= MAX_STROKE_THICKNESS):
            raise ValueError(
                f"Thickness {stroke['thickness']} out of range "
                f"[{MIN_STROKE_THICKNESS}, {MAX_STROKE_THICKNESS}]"
            )

        # Validate opacity
        if not (MIN_STROKE_OPACITY <= stroke["opacity"] <= MAX_STROKE_OPACITY):
            raise ValueError(
                f"Opacity {stroke['opacity']} out of range "
                f"[{MIN_STROKE_OPACITY}, {MAX_STROKE_OPACITY}]"
            )

    def _draw_line(self, stroke: Stroke) -> None:
        """
        Draw a line on the canvas.

        Args:
            stroke (Stroke): Stroke containing line parameters
        """
        # Convert hex color to RGB tuple
        color = self._hex_to_rgb(stroke["color_hex"])

        # Apply opacity by converting to RGBA
        color_rgba = color + (int(stroke["opacity"] * 255),)

        # Draw line - ensure coordinates are integers
        start_x = stroke["start_x"]
        start_y = stroke["start_y"]
        end_x = stroke.get("end_x")
        end_y = stroke.get("end_y")

        if end_x is None or end_y is None:
            raise ValueError("Line stroke requires end_x and end_y")

        self.draw.line(
            [(start_x, start_y), (end_x, end_y)],
            fill=color_rgba,
            width=stroke["thickness"],
        )

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """
        Convert hex color string to RGB tuple.

        Args:
            hex_color (str): Hex color string (e.g., "#FF5733")

        Returns:
            tuple[int, int, int]: RGB tuple (e.g., (255, 87, 51))
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)

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
