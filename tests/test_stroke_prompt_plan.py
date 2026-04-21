"""Tests for stroke prompt with painting plan context."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from models.painting_plan import PaintingPlan
from services.clients.stroke_vlm_client import StrokeVLMClient


@pytest.fixture
def mock_vlm_client() -> Mock:
    """Create a mock VLMClient."""
    with patch("services.clients.stroke_vlm_client.VLMClient") as mock_client_class:
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def stroke_client(mock_vlm_client: Mock) -> StrokeVLMClient:
    """Create a StrokeVLMClient with mocked VLMClient."""
    return StrokeVLMClient(
        base_url="http://test.com",
        model="test-model",
        timeout=60,
        api_key="test_key",
        temperature=0.7,
    )


@pytest.fixture
def sample_plan() -> PaintingPlan:
    """Create a sample painting plan for testing."""
    return {
        "artist_name": "Test Artist",
        "subject": "Test Subject",
        "expanded_subject": "Detailed test description",
        "total_layers": 2,
        "layers": [
            {
                "layer_number": 1,
                "name": "Background",
                "description": "Paint a blue background",
                "colour_palette": ["#0000FF", "#4444FF"],
                "stroke_types": ["line", "arc"],
                "techniques": "Broad strokes",
                "shapes": "Horizontal bands",
                "highlights": "Even lighting",
            },
            {
                "layer_number": 2,
                "name": "Foreground",
                "description": "Paint foreground details",
                "colour_palette": ["#FF0000"],
                "stroke_types": ["circle"],
                "techniques": "Fine detail",
                "shapes": "Small circles",
                "highlights": "Center focus",
            },
        ],
        "overall_notes": "Test plan",
    }


class TestPlanContextInPrompt:
    """Tests for plan context inclusion in stroke prompt."""

    def test_prompt_includes_full_plan_json(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes full plan JSON when painting_plan is provided."""
        current_layer = sample_plan["layers"][0]

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "=== PAINTING PLAN ===" in user_prompt
        assert json.dumps(sample_plan, indent=2) in user_prompt

    def test_prompt_includes_current_focus_section(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes 'CURRENT FOCUS' section with active layer details."""
        current_layer = sample_plan["layers"][0]

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "=== CURRENT FOCUS ===" in user_prompt
        assert 'Layer 1: "Background"' in user_prompt

    def test_prompt_includes_layer_description(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer description."""
        current_layer = sample_plan["layers"][0]

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["description"] in user_prompt

    def test_prompt_includes_layer_palette(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer colour palette."""
        current_layer = sample_plan["layers"][0]

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        for color in current_layer["colour_palette"]:
            assert color in user_prompt

    def test_prompt_includes_layer_techniques(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer techniques."""
        current_layer = sample_plan["layers"][0]

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["techniques"] in user_prompt

    def test_prompt_includes_layer_shapes(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer shapes."""
        current_layer = sample_plan["layers"][0]

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["shapes"] in user_prompt

    def test_prompt_includes_layer_highlights(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer highlights."""
        current_layer = sample_plan["layers"][0]

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert current_layer["highlights"] in user_prompt

    def test_prompt_unchanged_when_plan_is_none(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that prompt is unchanged when painting_plan is None."""
        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=None,
            current_layer=None,
        )

        assert "=== PAINTING PLAN ===" not in user_prompt
        assert "=== CURRENT FOCUS ===" not in user_prompt


class TestExpandedSubjectInPrompt:
    """Tests for expanded subject inclusion in stroke prompt."""

    def test_prompt_includes_expanded_subject_when_provided(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that prompt includes 'Detailed description:' when expanded_subject is provided."""
        expanded = "A very detailed description of the painting"

        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            expanded_subject=expanded,
        )

        assert "Detailed description:" in user_prompt
        assert expanded in user_prompt

    def test_prompt_omits_expanded_subject_when_none(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that prompt omits expanded subject when None."""
        _system_prompt, user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            expanded_subject=None,
        )

        assert "Detailed description:" not in user_prompt


class TestLayerCompleteInPromptAndParsing:
    """Tests for layer_complete field in stroke prompt and response parsing."""

    def test_stroke_prompt_includes_layer_complete_field_when_layer_provided(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt includes layer_complete field when current_layer is provided."""
        current_layer = sample_plan["layers"][0]

        system_prompt, _user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=current_layer,
        )

        assert "layer_complete" in system_prompt

    def test_stroke_prompt_excludes_layer_complete_when_no_layer(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt does NOT include layer_complete when current_layer is None."""
        system_prompt, _user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=None,
            current_layer=None,
        )

        assert "layer_complete" not in system_prompt

    def test_stroke_prompt_excludes_layer_complete_when_plan_provided_but_no_layer(
        self, stroke_client: StrokeVLMClient, sample_plan: PaintingPlan
    ) -> None:
        """Test that prompt does NOT include layer_complete when painting_plan is set but current_layer is None."""
        system_prompt, _user_prompt = stroke_client._build_stroke_prompts(
            artist_name="Test Artist",
            subject="Test Subject",
            iteration=1,
            strategy_context="",
            num_strokes=5,
            painting_plan=sample_plan,
            current_layer=None,
        )

        assert "layer_complete" not in system_prompt

    def test_parse_stroke_response_with_layer_complete_true(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that parser.parse() returns layer_complete True when present."""
        import json

        response_text = json.dumps(
            {
                "strokes": [],
                "updated_strategy": None,
                "batch_reasoning": "Test reasoning",
                "layer_complete": True,
            }
        )

        result = stroke_client.parser.parse(response_text)

        assert result.get("layer_complete") is True

    def test_parse_stroke_response_with_layer_complete_false(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that parser.parse() returns layer_complete False when present."""
        import json

        response_text = json.dumps(
            {
                "strokes": [],
                "updated_strategy": None,
                "batch_reasoning": "Test reasoning",
                "layer_complete": False,
            }
        )

        result = stroke_client.parser.parse(response_text)

        assert result.get("layer_complete") is False

    def test_parse_stroke_response_without_layer_complete(
        self, stroke_client: StrokeVLMClient
    ) -> None:
        """Test that parser.parse() omits layer_complete when absent in response."""
        import json

        response_text = json.dumps(
            {
                "strokes": [],
                "updated_strategy": None,
                "batch_reasoning": "Test reasoning",
            }
        )

        result = stroke_client.parser.parse(response_text)

        assert "layer_complete" not in result


# ============================================================================
# Tests for Consider-line filtering by allowed_stroke_types
# ============================================================================


def _build_system_prompt_for(allowed: list[str] | None) -> str:
    """Build the system stroke prompt using a client limited to the given stroke types."""
    client = StrokeVLMClient(allowed_stroke_types=allowed)
    system_prompt, _user_prompt = client._build_stroke_prompts(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )
    return system_prompt


# Keep legacy helper for backward-compat tests that need the combined prompt
def _build_prompt_for(allowed: list[str] | None) -> str:
    """Build a stroke prompt using a client limited to the given stroke types."""
    client = StrokeVLMClient(allowed_stroke_types=allowed)
    return client._build_stroke_prompt(
        artist_name="Test Artist",
        subject="Test Subject",
        iteration=1,
        strategy_context="",
        num_strokes=3,
    )


def test_consider_wet_brush_line_present_when_wet_brush_allowed() -> None:
    """Consider line for wet-brush is present when wet-brush is in allowed_stroke_types.

    When ``allowed_stroke_types=["wet-brush"]`` is set, the system prompt should contain
    the wet-brush Consider line but not the dry-brush/chalk Consider line.
    """
    system_prompt = _build_system_prompt_for(["wet-brush"])

    assert (
        "Use wet-brush for soft watercolour bleeds and ink-wash effects"
        in system_prompt
    ), "wet-brush Consider line should appear when wet-brush is allowed"
    assert (
        "Use dry-brush and chalk for textured, painterly effects" not in system_prompt
    ), "dry-brush/chalk Consider line should not appear when neither is allowed"


def test_consider_lines_absent_when_only_line_allowed() -> None:
    """Both specialist Consider lines are absent when only 'line' is allowed.

    When ``allowed_stroke_types=["line"]``, neither the dry-brush/chalk nor the
    wet-brush Consider lines should appear in the system prompt.
    """
    system_prompt = _build_system_prompt_for(["line"])

    assert (
        "Use dry-brush and chalk for textured, painterly effects" not in system_prompt
    ), "dry-brush/chalk Consider line should not appear when neither is allowed"
    assert (
        "Use wet-brush for soft watercolour bleeds and ink-wash effects"
        not in system_prompt
    ), "wet-brush Consider line should not appear when wet-brush is not allowed"


def test_consider_lines_both_present_when_allowed_stroke_types_is_none() -> None:
    """Both specialist Consider lines appear when allowed_stroke_types is None.

    Preserves backward-compatibility: omitting ``allowed_stroke_types`` must
    keep both Consider lines in the system prompt.
    """
    system_prompt = _build_system_prompt_for(None)

    assert "Use dry-brush and chalk for textured, painterly effects" in system_prompt, (
        "dry-brush/chalk Consider line should appear when all types are allowed"
    )
    assert (
        "Use wet-brush for soft watercolour bleeds and ink-wash effects"
        in system_prompt
    ), "wet-brush Consider line should appear when all types are allowed"


# ============================================================================
# Tests added for Task 3b — template extraction
# ============================================================================


def test_build_stroke_prompt_contains_expected_substrings() -> None:
    """_build_stroke_prompt returns a string containing required content substrings.

    Calls ``_build_stroke_prompt`` with ``allowed_stroke_types=None`` (all types
    included) and a representative set of inputs, then asserts that the returned
    string contains a representative set of known substrings:
    - the artist name
    - canvas dimension numbers
    - the ``AVAILABLE STROKE TYPES:`` heading
    - the respond-only instruction
    """
    client = StrokeVLMClient(allowed_stroke_types=None)
    prompt = client._build_stroke_prompt(
        artist_name="Vincent van Gogh",
        subject="Starry Night",
        iteration=3,
        strategy_context="",
        num_strokes=4,
    )

    assert "Vincent van Gogh" in prompt, "Artist name must appear in the prompt"
    assert "800" in prompt, "Canvas width (800) must appear in the prompt"
    assert "600" in prompt, "Canvas height (600) must appear in the prompt"
    assert "AVAILABLE STROKE TYPES:" in prompt, (
        "Stroke types heading must appear in the prompt"
    )
    assert "IMPORTANT: Respond ONLY with valid JSON" in prompt, (
        "JSON-only instruction must appear in the prompt"
    )


def test_missing_template_file_raises_file_not_found_error() -> None:
    """Instantiating StrokeVLMClient with a missing template file raises FileNotFoundError.

    Patches ``_STROKE_PROMPT_TEMPLATE_PATH`` to point at a non-existent path so
    that ``__init__`` triggers ``Path.read_text`` on a file that does not exist.
    This guards against missing template deployments.
    """
    missing_path = Path("/nonexistent/path/stroke_prompt.txt")

    with patch(
        "services.clients.stroke_vlm_client._STROKE_PROMPT_TEMPLATE_PATH", missing_path
    ):
        with pytest.raises(FileNotFoundError):
            StrokeVLMClient(
                base_url="http://test.com",
                model="test-model",
                timeout=60,
                api_key="test_key",
            )
