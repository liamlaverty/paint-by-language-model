"""Evaluation result type definition for VLM style assessments."""

from typing import TypedDict


class _EvaluationResultRequired(TypedDict):
    """Required fields for EvaluationResult."""

    score: float
    feedback: str
    strengths: str
    suggestions: str
    timestamp: str
    iteration: int


class EvaluationResult(_EvaluationResultRequired, total=False):
    """
    Represents style evaluation results from a VLM.

    Attributes:
        score (float): Style similarity score (0-100 scale)
        feedback (str): Qualitative assessment from VLM
        strengths (str): What aspects work well stylistically
        suggestions (str): Areas for improvement
        timestamp (str): ISO format timestamp of evaluation
        iteration (int): Iteration number when evaluated
        layer_complete (bool): Whether the current layer is complete
        layer_number (int): The layer number being evaluated
    """

    layer_complete: bool
    layer_number: int
