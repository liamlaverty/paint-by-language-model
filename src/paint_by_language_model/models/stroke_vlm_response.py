"""Stroke VLM response type definition."""

from typing import TypedDict

from .stroke import Stroke


class _StrokeVLMResponseRequired(TypedDict):
    strokes: list[Stroke]
    updated_strategy: str | None
    batch_reasoning: str


class StrokeVLMResponse(_StrokeVLMResponseRequired, total=False):
    """
    Complete response from the Stroke VLM.

    Attributes:
        strokes (list[Stroke]): List of strokes to apply to the canvas
        updated_strategy (str | None): Optional strategy update for future iterations
        batch_reasoning (str): Explanation for the entire batch of strokes
        layer_complete (bool): Whether the current layer's objectives are complete;
            only present when a painting plan and current layer are active
    """

    layer_complete: bool
