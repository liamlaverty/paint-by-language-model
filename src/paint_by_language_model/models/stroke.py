"""Stroke type definition for canvas drawing operations."""

from typing import Literal, TypedDict

# Define supported stroke types
StrokeType = Literal[
    "line",
    "arc",
    "polyline",
    "circle",
    "splatter",
    "dry-brush",
    "chalk",
    "wet-brush",
    "burn",
    "dodge",
]


class Stroke(TypedDict, total=False):
    """
    Represents a single drawing operation on the canvas.

    Core Attributes (all stroke types):
        type (StrokeType): Stroke type - "line", "arc", "polyline", "circle", "splatter",
            "dry-brush", "chalk", "wet-brush", "burn", or "dodge"
        color_hex (str): Color in hex format "#RRGGBB" or "#RRGGBBAA"
        thickness (int): Line thickness in pixels (1-50)
        opacity (float): Opacity value (0.0 to 1.0)

    Note: The 'reasoning' field has been moved to batch-level in StrokeVLMResponse.
          Individual strokes no longer have reasoning - use batch_reasoning instead.

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

    Dry-brush-specific Attributes:
        brush_width (int): Total width of brush perpendicular to stroke direction (4-100 px)
        bristle_count (int): Number of parallel bristle lines (3-20)
        gap_probability (float): Probability of bristle segment being skipped (0.0-0.7)

    Chalk-specific Attributes:
        chalk_width (int): Width of chalk mark perpendicular to path (2-60 px)
        grain_density (int): Number of random dots per sample point along path (1-8)

    Wet-brush-specific Attributes:
        softness (int): Gaussian blur radius for edge bleed (1-30 px)
        flow (float): Paint density/concentration multiplied with opacity (0.1-1.0)

    Burn/Dodge-specific Attributes:
        center_x (int): Center X coordinate (shared with circle)
        center_y (int): Center Y coordinate (shared with circle)
        radius (int): Radius of affected region (shared with circle, 5-300 px for burn/dodge)
        intensity (float): Amount of darkening (burn) or lightening (dodge) (0.05-0.8)
    """

    # Core fields (all stroke types)
    type: StrokeType
    color_hex: str
    thickness: int
    opacity: float

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

    # Dry-brush-specific fields (optional)
    brush_width: int | None
    bristle_count: int | None
    gap_probability: float | None

    # Chalk-specific fields (optional)
    chalk_width: int | None
    grain_density: int | None

    # Wet-brush-specific fields (optional)
    softness: int | None
    flow: float | None

    # Burn/Dodge-specific fields (optional)
    # Note: center_x, center_y, radius are already defined above (shared with circle)
    intensity: float | None
