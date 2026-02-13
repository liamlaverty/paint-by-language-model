"""Stroke VLM response type definition."""

from typing import TypedDict

from .stroke import Stroke


class StrokeVLMResponse(TypedDict):
    """
    Complete response from the Stroke VLM.

    Phase 3 changes:
    - Changed from single stroke to list of strokes (supports batch operations)
    - Added batch_reasoning for explaining the entire set of strokes
    - Individual strokes no longer have reasoning field

    Attributes:
        strokes (list[Stroke]): List of strokes to apply to the canvas
        updated_strategy (str | None): Optional strategy update for future iterations
        batch_reasoning (str): Explanation for the entire batch of strokes
    """

    strokes: list[Stroke]
    updated_strategy: str | None
    batch_reasoning: str
