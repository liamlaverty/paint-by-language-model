"""Canvas state type definition for tracking canvas status."""
from typing import TypedDict


class CanvasState(TypedDict):
    """
    Represents the current state of the canvas.
    
    Attributes:
        width (int): Canvas width in pixels
        height (int): Canvas height in pixels
        background_color (str): Background color in hex format
        stroke_count (int): Number of strokes applied so far
        current_iteration (int): Current iteration number
    """
    width: int
    height: int
    background_color: str
    stroke_count: int
    current_iteration: int
