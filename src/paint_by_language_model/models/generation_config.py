"""Runtime configuration object passed through the generation stack."""

from typing import TypedDict


class GenerationConfig(TypedDict):
    """
    Fully-resolved runtime configuration for a single generation run.

    All values are resolved in ``main.py`` before the orchestrator is created.
    Passing this object explicitly through the constructor chain removes the need
    to mutate ``config`` module attributes at runtime.

    Attributes:
        provider (str): Active VLM provider ("mistral", "lmstudio", "anthropic").
        api_base_url (str): Base URL for VLM API requests.
        api_key (str): API key for authentication.
        vlm_model (str): Model identifier used by StrokeVLMClient.
        evaluation_vlm_model (str): Model identifier used by EvaluationVLMClient.
        planner_model (str): Model identifier used by PlannerLLMClient.
        max_iterations (int): Maximum generation iterations before stopping.
        target_style_score (float): Style similarity score at which generation
            ends early.
        min_strokes_per_layer (int): Minimum VLM iterations on a layer before
            ``layer_complete: true`` is honoured.
    """

    provider: str
    api_base_url: str
    api_key: str
    vlm_model: str
    evaluation_vlm_model: str
    planner_model: str
    max_iterations: int
    target_style_score: float
    min_strokes_per_layer: int
