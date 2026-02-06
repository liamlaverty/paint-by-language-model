"""Evaluation result type definition for VLM style assessments."""

from typing import TypedDict


class EvaluationResult(TypedDict):
    """
    Represents style evaluation results from a VLM.

    Attributes:
        score (float): Style similarity score (0-100 scale)
        feedback (str): Qualitative assessment from VLM
        strengths (str): What aspects work well stylistically
        suggestions (str): Areas for improvement
        timestamp (str): ISO format timestamp of evaluation
        iteration (int): Iteration number when evaluated
    """

    score: float
    feedback: str
    strengths: str
    suggestions: str
    timestamp: str
    iteration: int
