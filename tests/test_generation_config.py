"""Tests for build_generation_config() in main.py."""

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

import config as _config
from main import build_generation_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_defaults() -> dict:  # type: ignore[type-arg]
    """Call build_generation_config with all None overrides."""
    return build_generation_config(
        provider=None,
        api_key=None,
        planner_model=None,
        max_iterations=None,
        target_score=None,
        min_strokes_per_layer=None,
    )


# ---------------------------------------------------------------------------
# Default / None-override behaviour
# ---------------------------------------------------------------------------


class TestBuildGenerationConfigDefaults:
    """build_generation_config() with all None overrides mirrors config defaults."""

    def test_provider_matches_config(self) -> None:
        """provider field equals config.PROVIDER."""
        result = _build_defaults()
        assert result["provider"] == _config.PROVIDER

    def test_api_base_url_matches_config(self) -> None:
        """api_base_url field equals config.API_BASE_URL."""
        result = _build_defaults()
        assert result["api_base_url"] == _config.API_BASE_URL

    def test_api_key_matches_config(self) -> None:
        """api_key field equals config.API_KEY."""
        result = _build_defaults()
        assert result["api_key"] == _config.API_KEY

    def test_vlm_model_matches_config(self) -> None:
        """vlm_model field equals config.VLM_MODEL."""
        result = _build_defaults()
        assert result["vlm_model"] == _config.VLM_MODEL

    def test_evaluation_vlm_model_matches_config(self) -> None:
        """evaluation_vlm_model field equals config.EVALUATION_VLM_MODEL."""
        result = _build_defaults()
        assert result["evaluation_vlm_model"] == _config.EVALUATION_VLM_MODEL

    def test_planner_model_matches_config(self) -> None:
        """planner_model field equals config.PLANNER_MODEL."""
        result = _build_defaults()
        assert result["planner_model"] == _config.PLANNER_MODEL

    def test_max_iterations_matches_config(self) -> None:
        """max_iterations field equals config.MAX_ITERATIONS."""
        result = _build_defaults()
        assert result["max_iterations"] == _config.MAX_ITERATIONS

    def test_target_style_score_matches_config(self) -> None:
        """target_style_score field equals config.TARGET_STYLE_SCORE."""
        result = _build_defaults()
        assert result["target_style_score"] == _config.TARGET_STYLE_SCORE

    def test_min_strokes_per_layer_matches_config(self) -> None:
        """min_strokes_per_layer field equals config.MIN_STROKES_PER_LAYER."""
        result = _build_defaults()
        assert result["min_strokes_per_layer"] == _config.MIN_STROKES_PER_LAYER


# ---------------------------------------------------------------------------
# Provider resolution
# ---------------------------------------------------------------------------


class TestBuildGenerationConfigProviderAnthropic:
    """provider='anthropic' sets Anthropic-specific constants."""

    def setup_method(self) -> None:
        """Build a config with provider='anthropic' once for each test method."""
        self._cfg = build_generation_config(
            provider="anthropic",
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )

    def test_provider_is_anthropic(self) -> None:
        """provider field is 'anthropic'."""
        assert self._cfg["provider"] == "anthropic"

    def test_api_base_url_is_anthropic(self) -> None:
        """api_base_url equals ANTHROPIC_BASE_URL."""
        assert self._cfg["api_base_url"] == _config.ANTHROPIC_BASE_URL

    def test_vlm_model_is_anthropic(self) -> None:
        """vlm_model equals ANTHROPIC_VLM_MODEL."""
        assert self._cfg["vlm_model"] == _config.ANTHROPIC_VLM_MODEL

    def test_evaluation_vlm_model_is_anthropic(self) -> None:
        """evaluation_vlm_model equals ANTHROPIC_EVALUATION_VLM_MODEL."""
        assert self._cfg["evaluation_vlm_model"] == _config.ANTHROPIC_EVALUATION_VLM_MODEL

    def test_planner_model_is_anthropic(self) -> None:
        """planner_model equals ANTHROPIC_PLANNER_MODEL."""
        assert self._cfg["planner_model"] == _config.ANTHROPIC_PLANNER_MODEL


class TestBuildGenerationConfigProviderMistral:
    """provider='mistral' sets Mistral-specific constants."""

    def setup_method(self) -> None:
        """Build a config with provider='mistral' once for each test method."""
        self._cfg = build_generation_config(
            provider="mistral",
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )

    def test_provider_is_mistral(self) -> None:
        """provider field is 'mistral'."""
        assert self._cfg["provider"] == "mistral"

    def test_api_base_url_is_mistral(self) -> None:
        """api_base_url equals MISTRAL_BASE_URL."""
        assert self._cfg["api_base_url"] == _config.MISTRAL_BASE_URL

    def test_vlm_model_is_mistral(self) -> None:
        """vlm_model equals MISTRAL_VLM_MODEL."""
        assert self._cfg["vlm_model"] == _config.MISTRAL_VLM_MODEL

    def test_evaluation_vlm_model_is_mistral(self) -> None:
        """evaluation_vlm_model equals MISTRAL_EVALUATION_VLM_MODEL."""
        assert self._cfg["evaluation_vlm_model"] == _config.MISTRAL_EVALUATION_VLM_MODEL

    def test_planner_model_is_mistral(self) -> None:
        """planner_model equals MISTRAL_PLANNER_MODEL."""
        assert self._cfg["planner_model"] == _config.MISTRAL_PLANNER_MODEL


class TestBuildGenerationConfigProviderLmstudio:
    """provider='lmstudio' sets LMStudio-specific constants and empty api_key."""

    def setup_method(self) -> None:
        """Build a config with provider='lmstudio' once for each test method."""
        self._cfg = build_generation_config(
            provider="lmstudio",
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )

    def test_provider_is_lmstudio(self) -> None:
        """provider field is 'lmstudio'."""
        assert self._cfg["provider"] == "lmstudio"

    def test_api_base_url_is_lmstudio(self) -> None:
        """api_base_url equals LMSTUDIO_BASE_URL."""
        assert self._cfg["api_base_url"] == _config.LMSTUDIO_BASE_URL

    def test_vlm_model_is_lmstudio(self) -> None:
        """vlm_model equals LMSTUDIO_VLM_MODEL."""
        assert self._cfg["vlm_model"] == _config.LMSTUDIO_VLM_MODEL

    def test_evaluation_vlm_model_is_lmstudio(self) -> None:
        """evaluation_vlm_model equals LMSTUDIO_EVALUATION_VLM_MODEL."""
        assert self._cfg["evaluation_vlm_model"] == _config.LMSTUDIO_EVALUATION_VLM_MODEL

    def test_planner_model_is_lmstudio(self) -> None:
        """planner_model equals LMSTUDIO_PLANNER_MODEL."""
        assert self._cfg["planner_model"] == _config.LMSTUDIO_PLANNER_MODEL

    def test_api_key_is_empty_string(self) -> None:
        """api_key is '' (no authentication required for LMStudio)."""
        assert self._cfg["api_key"] == ""


# ---------------------------------------------------------------------------
# CLI override propagation
# ---------------------------------------------------------------------------


class TestBuildGenerationConfigOverrides:
    """Explicit override arguments are reflected in the returned config."""

    def test_min_strokes_per_layer_override(self) -> None:
        """min_strokes_per_layer=5 overrides config.MIN_STROKES_PER_LAYER."""
        result = build_generation_config(
            provider=None,
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=5,
        )
        assert result["min_strokes_per_layer"] == 5

    def test_min_strokes_per_layer_override_ignores_config_value(self) -> None:
        """Override of min_strokes_per_layer is independent of config.MIN_STROKES_PER_LAYER."""
        # This assertion holds whether or not config.MIN_STROKES_PER_LAYER == 5.
        result = build_generation_config(
            provider=None,
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=5,
        )
        assert result["min_strokes_per_layer"] == 5

    def test_max_iterations_override(self) -> None:
        """max_iterations=50 overrides config.MAX_ITERATIONS."""
        result = build_generation_config(
            provider=None,
            api_key=None,
            planner_model=None,
            max_iterations=50,
            target_score=None,
            min_strokes_per_layer=None,
        )
        assert result["max_iterations"] == 50

    def test_max_iterations_override_ignores_config_value(self) -> None:
        """Override of max_iterations is independent of config.MAX_ITERATIONS."""
        result = build_generation_config(
            provider=None,
            api_key=None,
            planner_model=None,
            max_iterations=50,
            target_score=None,
            min_strokes_per_layer=None,
        )
        assert result["max_iterations"] == 50

    def test_planner_model_override(self) -> None:
        """Explicit planner_model string overrides config default."""
        result = build_generation_config(
            provider=None,
            api_key=None,
            planner_model="my-custom-model",
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )
        assert result["planner_model"] == "my-custom-model"

    def test_api_key_override(self) -> None:
        """Explicit api_key overrides whatever is resolved from config/provider."""
        result = build_generation_config(
            provider=None,
            api_key="override-key-xyz",
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )
        assert result["api_key"] == "override-key-xyz"


# ---------------------------------------------------------------------------
# Config module immutability
# ---------------------------------------------------------------------------


class TestBuildGenerationConfigNoMutation:
    """build_generation_config() must not mutate the config module."""

    def test_max_iterations_not_mutated(self) -> None:
        """config.MAX_ITERATIONS is unchanged after build_generation_config(max_iterations=99)."""
        before = _config.MAX_ITERATIONS
        build_generation_config(
            provider=None,
            api_key=None,
            planner_model=None,
            max_iterations=99,
            target_score=None,
            min_strokes_per_layer=None,
        )
        assert _config.MAX_ITERATIONS == before

    def test_min_strokes_per_layer_not_mutated(self) -> None:
        """config.MIN_STROKES_PER_LAYER is unchanged after an override call."""
        before = _config.MIN_STROKES_PER_LAYER
        build_generation_config(
            provider=None,
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=1,
        )
        assert _config.MIN_STROKES_PER_LAYER == before

    def test_target_style_score_not_mutated(self) -> None:
        """config.TARGET_STYLE_SCORE is unchanged after an override call."""
        before = _config.TARGET_STYLE_SCORE
        build_generation_config(
            provider=None,
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=99.0,
            min_strokes_per_layer=None,
        )
        assert _config.TARGET_STYLE_SCORE == before

    def test_provider_constant_not_mutated(self) -> None:
        """config.PROVIDER is unchanged after calling with provider='lmstudio'."""
        before = _config.PROVIDER
        build_generation_config(
            provider="lmstudio",
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )
        assert _config.PROVIDER == before

    def test_api_base_url_not_mutated(self) -> None:
        """config.API_BASE_URL is unchanged after calling with a different provider."""
        before = _config.API_BASE_URL
        build_generation_config(
            provider="lmstudio",
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )
        assert _config.API_BASE_URL == before


# ---------------------------------------------------------------------------
# Return type sanity
# ---------------------------------------------------------------------------


class TestBuildGenerationConfigReturnType:
    """build_generation_config() returns a dict-like GenerationConfig with correct keys."""

    def test_returns_all_nine_keys(self) -> None:
        """All nine required fields are present in the returned config."""
        result = _build_defaults()
        required_keys = {
            "provider",
            "api_base_url",
            "api_key",
            "vlm_model",
            "evaluation_vlm_model",
            "planner_model",
            "max_iterations",
            "target_style_score",
            "min_strokes_per_layer",
        }
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    @pytest.mark.parametrize("provider", ["mistral", "lmstudio", "anthropic"])
    def test_all_providers_return_nine_keys(self, provider: str) -> None:
        """All nine fields are present regardless of the specified provider."""
        result = build_generation_config(
            provider=provider,
            api_key=None,
            planner_model=None,
            max_iterations=None,
            target_score=None,
            min_strokes_per_layer=None,
        )
        required_keys = {
            "provider",
            "api_base_url",
            "api_key",
            "vlm_model",
            "evaluation_vlm_model",
            "planner_model",
            "max_iterations",
            "target_style_score",
            "min_strokes_per_layer",
        }
        for key in required_keys:
            assert key in result, f"Missing key '{key}' for provider='{provider}'"
