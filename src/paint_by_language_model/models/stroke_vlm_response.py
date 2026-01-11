"""Stroke VLM response type definition."""
from typing import TypedDict
from .stroke import Stroke


class StrokeVLMResponse(TypedDict):
    """
    Complete response from the Stroke VLM.
    
    Attributes:
        stroke (Stroke): The stroke to apply to the canvas
        updated_strategy (str | None): Optional strategy update for future iterations
    """
    stroke: Stroke
    updated_strategy: str | None
