"""Tests verifying that GenerationConfig values thread correctly into GenerationOrchestrator."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from generation_orchestrator import GenerationOrchestrator
from models import GenerationConfig


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_valid_config(
    *,
    provider: str = "lmstudio",
    api_base_url: str = "http://localhost:1234/v1",
    api_key: str = "",
    vlm_model: str = "test-model",
    evaluation_vlm_model: str = "test-model",
    planner_model: str = "test-model",
    max_iterations: int = 10,
    target_style_score: float = 70.0,
    min_strokes_per_layer: int = 5,
) -> GenerationConfig:
    """
    Return a minimal GenerationConfig suitable for unit tests.

    Defaults to the lmstudio provider so no API key is required.  Individual
    fields can be overridden via keyword arguments.

    Args:
        provider (str): VLM provider string.
        api_base_url (str): Base URL for the VLM API.
        api_key (str): Authentication key (empty for lmstudio).
        vlm_model (str): Model identifier for stroke queries.
        evaluation_vlm_model (str): Model identifier for evaluation queries.
        planner_model (str): Model identifier for the planner.
        max_iterations (int): Maximum generation iterations.
        target_style_score (float): Target style score (0–100).
        min_strokes_per_layer (int): Minimum iterations per layer before advancing.

    Returns:
        GenerationConfig: Populated configuration object.
    """
    return GenerationConfig(
        provider=provider,
        api_base_url=api_base_url,
        api_key=api_key,
        vlm_model=vlm_model,
        evaluation_vlm_model=evaluation_vlm_model,
        planner_model=planner_model,
        max_iterations=max_iterations,
        target_style_score=target_style_score,
        min_strokes_per_layer=min_strokes_per_layer,
    )


def _make_orchestrator(
    tmp_path: Path,
    generation_config: GenerationConfig,
) -> GenerationOrchestrator:
    """
    Create a GenerationOrchestrator pointing at a temporary directory.

    No live API calls are made; all network-dependent services are simply
    constructed (not queried) during orchestrator initialisation.

    Args:
        tmp_path (Path): Temporary directory for output artifacts.
        generation_config (GenerationConfig): Configuration to use.

    Returns:
        GenerationOrchestrator: Fully-initialised orchestrator instance.
    """
    return GenerationOrchestrator(
        artist_name="Test Artist",
        subject="Test Subject",
        artwork_id="test-config-propagation",
        output_dir=tmp_path,
        generation_config=generation_config,
    )


# ---------------------------------------------------------------------------
# Instance attribute propagation
# ---------------------------------------------------------------------------


class TestOrchestratorStoresConfigValues:
    """GenerationOrchestrator stores config scalars on self."""

    def test_min_strokes_per_layer_stored(self, tmp_path: Path) -> None:
        """self.min_strokes_per_layer equals the value passed in the config."""
        cfg = _make_valid_config(min_strokes_per_layer=3)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.min_strokes_per_layer == 3

    def test_max_iterations_stored(self, tmp_path: Path) -> None:
        """self.max_iterations equals the value passed in the config."""
        cfg = _make_valid_config(max_iterations=5)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.max_iterations == 5

    def test_min_strokes_per_layer_uses_config_not_module_default(
        self, tmp_path: Path
    ) -> None:
        """Orchestrator uses the provided min_strokes_per_layer, not config.MIN_STROKES_PER_LAYER."""
        # Use a value unlikely to match the module default (15)
        cfg = _make_valid_config(min_strokes_per_layer=3)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.min_strokes_per_layer == 3

    def test_max_iterations_uses_config_not_module_default(
        self, tmp_path: Path
    ) -> None:
        """Orchestrator uses the provided max_iterations, not config.MAX_ITERATIONS."""
        # Use a value unlikely to match the module default (150)
        cfg = _make_valid_config(max_iterations=5)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.max_iterations == 5

    def test_provider_stored(self, tmp_path: Path) -> None:
        """self.provider equals the value passed in the config."""
        cfg = _make_valid_config(provider="lmstudio")
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.provider == "lmstudio"


# ---------------------------------------------------------------------------
# Value propagation into StrokeVLMClient
# ---------------------------------------------------------------------------


class TestStrokeVlmClientPropagation:
    """Config values flow into the constructed StrokeVLMClient."""

    def test_stroke_vlm_min_strokes_per_layer(self, tmp_path: Path) -> None:
        """orchestrator.stroke_vlm.min_strokes_per_layer equals the config value."""
        cfg = _make_valid_config(min_strokes_per_layer=3)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.stroke_vlm.min_strokes_per_layer == 3

    def test_stroke_vlm_min_strokes_per_layer_different_value(
        self, tmp_path: Path
    ) -> None:
        """stroke_vlm.min_strokes_per_layer reflects a different config value."""
        cfg = _make_valid_config(min_strokes_per_layer=7)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.stroke_vlm.min_strokes_per_layer == 7


# ---------------------------------------------------------------------------
# Value propagation into PlannerLLMClient
# ---------------------------------------------------------------------------


class TestPlannerVlmClientPropagation:
    """Config values flow into the constructed PlannerLLMClient."""

    def test_planner_vlm_min_strokes_per_layer(self, tmp_path: Path) -> None:
        """orchestrator.planner_vlm.min_strokes_per_layer equals the config value."""
        cfg = _make_valid_config(min_strokes_per_layer=3)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.planner_vlm.min_strokes_per_layer == 3

    def test_planner_vlm_min_strokes_per_layer_different_value(
        self, tmp_path: Path
    ) -> None:
        """planner_vlm.min_strokes_per_layer reflects a different config value."""
        cfg = _make_valid_config(min_strokes_per_layer=9)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.planner_vlm.min_strokes_per_layer == 9


# ---------------------------------------------------------------------------
# Input validation — ValueError on invalid configs
# ---------------------------------------------------------------------------


class TestOrchestratorValidation:
    """GenerationOrchestrator raises ValueError for invalid GenerationConfig values."""

    def test_empty_api_base_url_raises_value_error(self, tmp_path: Path) -> None:
        """api_base_url='' raises ValueError."""
        cfg = _make_valid_config(api_base_url="")
        with pytest.raises(ValueError, match="api_base_url"):
            _make_orchestrator(tmp_path, cfg)

    def test_anthropic_empty_api_key_raises_value_error(self, tmp_path: Path) -> None:
        """provider='anthropic' with api_key='' raises ValueError."""
        cfg = _make_valid_config(
            provider="anthropic",
            api_base_url="https://api.anthropic.com/v1",
            api_key="",
        )
        with pytest.raises(ValueError, match="API key"):
            _make_orchestrator(tmp_path, cfg)

    def test_mistral_empty_api_key_raises_value_error(self, tmp_path: Path) -> None:
        """provider='mistral' with api_key='' raises ValueError."""
        cfg = _make_valid_config(
            provider="mistral",
            api_base_url="https://api.mistral.ai/v1",
            api_key="",
        )
        with pytest.raises(ValueError, match="API key"):
            _make_orchestrator(tmp_path, cfg)

    def test_min_strokes_per_layer_zero_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """min_strokes_per_layer=0 raises ValueError."""
        cfg = _make_valid_config(min_strokes_per_layer=0)
        with pytest.raises(ValueError, match="min_strokes_per_layer"):
            _make_orchestrator(tmp_path, cfg)

    def test_min_strokes_per_layer_negative_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """min_strokes_per_layer=-1 raises ValueError."""
        cfg = _make_valid_config(min_strokes_per_layer=-1)
        with pytest.raises(ValueError, match="min_strokes_per_layer"):
            _make_orchestrator(tmp_path, cfg)

    def test_lmstudio_empty_api_key_is_valid(self, tmp_path: Path) -> None:
        """provider='lmstudio' with api_key='' does NOT raise (no auth required)."""
        cfg = _make_valid_config(provider="lmstudio", api_key="")
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.provider == "lmstudio"

    def test_min_strokes_per_layer_one_is_valid(self, tmp_path: Path) -> None:
        """min_strokes_per_layer=1 is the minimum allowed value and does not raise."""
        cfg = _make_valid_config(min_strokes_per_layer=1)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.min_strokes_per_layer == 1


# ---------------------------------------------------------------------------
# Consistency between orchestrator attribute and client attribute
# ---------------------------------------------------------------------------


class TestOrchestratorClientConsistency:
    """Orchestrator instance attribute and client attribute stay in sync."""

    def test_orchestrator_and_stroke_vlm_min_strokes_match(
        self, tmp_path: Path
    ) -> None:
        """orch.min_strokes_per_layer and orch.stroke_vlm.min_strokes_per_layer are equal."""
        cfg = _make_valid_config(min_strokes_per_layer=4)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.min_strokes_per_layer == orch.stroke_vlm.min_strokes_per_layer

    def test_orchestrator_and_planner_vlm_min_strokes_match(
        self, tmp_path: Path
    ) -> None:
        """orch.min_strokes_per_layer and orch.planner_vlm.min_strokes_per_layer are equal."""
        cfg = _make_valid_config(min_strokes_per_layer=4)
        orch = _make_orchestrator(tmp_path, cfg)
        assert orch.min_strokes_per_layer == orch.planner_vlm.min_strokes_per_layer
