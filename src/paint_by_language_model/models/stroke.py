"""Stroke type definition for canvas drawing operations."""

from typing import TypedDict


class Stroke(TypedDict, total=False):
    """
    Represents a single drawing operation on the canvas.

    Core Attributes (all stroke types):
        type (str): Stroke type - "line", "arc", "polyline", "circle", or "splatter"
        color_hex (str): Color in hex format "#RRGGBB" or "#RRGGBBAA"
        thickness (int): Line thickness in pixels (1-50)
        opacity (float): Opacity value (0.0 to 1.0)
        reasoning (str): VLM's explanation for this stroke

    Line-specific Attributes:
        start_x (int): Starting X coordinate in pixels
        start_y (int): Starting Y coordinate in pixels
        end_x (int | None): Ending X coordinate
        end_y (int | None): Ending Y coordinate

    Arc-specific Attributes:
        arc_bbox (list[int] | tuple[int, int, int, int]): Bounding box [x0, y0, x1, y1]
        arc_start_angle (int): Start angle in degrees (0° = 3 o'clock)
        arc_end_angle (int): End angle in degrees

    Polyline-specific Attributes:
        points (list[list[int]] | list[tuple[int, int]]): List of [x, y] coordinate pairs

    Circle-specific Attributes:
        center_x (int): X coordinate of circle center
        center_y (int): Y coordinate of circle center
        radius (int): Circle radius in pixels
        fill (bool): True = solid fill, False = outline only

    Splatter-specific Attributes:
        splatter_count (int): Number of dots
        splatter_radius (int): Spread radius
        dot_size_min (int): Minimum dot size
        dot_size_max (int): Maximum dot size
    """

    # Core fields (all stroke types) - marked as required
    type: str
    color_hex: str
    thickness: int
    opacity: float
    reasoning: str

    # Line-specific fields (optional)
    start_x: int
    start_y: int
    end_x: int | None
    end_y: int | None

    # Arc-specific fields (optional)
    arc_bbox: list[int] | tuple[int, int, int, int] | None
    arc_start_angle: int | None
    arc_end_angle: int | None

    # Polyline-specific fields (optional)
    points: list[list[int]] | list[tuple[int, int]] | None

    # Circle-specific fields (optional)
    center_x: int | None
    center_y: int | None
    radius: int | None
    fill: bool | None

    # Splatter-specific fields (optional)
    splatter_count: int | None
    splatter_radius: int | None
    dot_size_min: int | None
    dot_size_max: int | None
