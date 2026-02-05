"""Stroke type definition for canvas drawing operations."""

from typing import TypedDict


class Stroke(TypedDict):
    """
    Represents a single drawing operation on the canvas.

    Attributes:
        type (str): Stroke type - "line", "curve", or "fill"
        start_x (int): Starting X coordinate in pixels
        start_y (int): Starting Y coordinate in pixels
        end_x (int | None): Ending X coordinate (None for fill operations)
        end_y (int | None): Ending Y coordinate (None for fill operations)
        color_hex (str): Color in hex format "#RRGGBB"
        thickness (int): Line thickness in pixels (1-10)
        opacity (float): Opacity value (0.0 to 1.0)
        reasoning (str): VLM's explanation for this stroke
    """

    type: str
    start_x: int
    start_y: int
    end_x: int | None
    end_y: int | None
    color_hex: str
    thickness: int
    opacity: float
    reasoning: str
