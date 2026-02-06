"""Generation metadata type definition for artwork sessions."""

from typing import Any, TypedDict


class GenerationMetadata(TypedDict):
    """
    Complete metadata for an artwork generation session.

    Attributes:
        artwork_id (str): Unique identifier for this artwork
        artist_name (str): Target artist name
        subject (str): Subject being painted
        generation_date (str): ISO format timestamp of generation start
        total_iterations (int): Number of iterations completed
        final_score (float): Final evaluation score
        canvas_dimensions (dict[str, int]): Canvas width and height
        vlm_models (dict[str, str]): VLM model names used
        configuration (dict[str, Any]): Generation settings used
        score_progression (list[float]): Evaluation scores from each iteration
        total_strokes (int): Total number of strokes applied
    """

    artwork_id: str
    artist_name: str
    subject: str
    generation_date: str
    total_iterations: int
    final_score: float
    canvas_dimensions: dict[str, int]
    vlm_models: dict[str, str]
    configuration: dict[str, Any]
    score_progression: list[float]
    total_strokes: int
