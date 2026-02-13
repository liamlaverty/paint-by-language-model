"""Tests for Strategy Manager with layer context."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from models.painting_plan import PlanLayer
from strategy_manager import StrategyManager


@pytest.fixture
def temp_strategy_dir() -> Path:
    """Create a temporary directory for strategy files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def strategy_manager(temp_strategy_dir: Path) -> StrategyManager:
    """Create a StrategyManager with temporary directory."""
    return StrategyManager(artwork_id="test-001", output_dir=temp_strategy_dir)


@pytest.fixture
def sample_layer() -> PlanLayer:
    """Create a sample layer for testing."""
    return {
        "layer_number": 2,
        "name": "Midground",
        "description": "Paint midground elements with organic shapes",
        "colour_palette": ["#FF5733", "#33FF57"],
        "stroke_types": ["arc", "polyline"],
        "techniques": "Curved strokes",
        "shapes": "Organic forms",
        "highlights": "Soft shadows",
    }


class TestStrategyManagerLayerContext:
    """Tests for layer context in strategy manager."""

    def test_get_recent_strategies_prepends_layer_header_when_provided(
        self, strategy_manager: StrategyManager, sample_layer: PlanLayer
    ) -> None:
        """Test that get_recent_strategies() prepends layer header when current_layer is provided."""
        strategy_manager.save_strategy(1, "First strategy")
        strategy_manager.save_strategy(2, "Second strategy")

        context = strategy_manager.get_recent_strategies(
            current_iteration=3,
            window=5,
            current_layer=sample_layer,
        )

        assert "Current Layer: 2" in context
        assert sample_layer["name"] in context
        assert "Layer Focus:" in context
        assert sample_layer["description"] in context

    def test_get_recent_strategies_includes_layer_number_and_name(
        self, strategy_manager: StrategyManager, sample_layer: PlanLayer
    ) -> None:
        """Test that layer header includes layer number and name."""
        strategy_manager.save_strategy(1, "Test strategy")

        context = strategy_manager.get_recent_strategies(
            current_iteration=2,
            current_layer=sample_layer,
        )

        assert f"Current Layer: {sample_layer['layer_number']}" in context
        assert sample_layer["name"] in context

    def test_get_recent_strategies_includes_layer_description(
        self, strategy_manager: StrategyManager, sample_layer: PlanLayer
    ) -> None:
        """Test that layer header includes layer description."""
        strategy_manager.save_strategy(1, "Test strategy")

        context = strategy_manager.get_recent_strategies(
            current_iteration=2,
            current_layer=sample_layer,
        )

        assert "Layer Focus:" in context
        assert sample_layer["description"] in context

    def test_get_recent_strategies_unchanged_when_layer_is_none(
        self, strategy_manager: StrategyManager
    ) -> None:
        """Test that get_recent_strategies() returns unchanged output when current_layer is None."""
        strategy_manager.save_strategy(1, "Strategy one")
        strategy_manager.save_strategy(2, "Strategy two")

        context = strategy_manager.get_recent_strategies(
            current_iteration=3,
            current_layer=None,
        )

        assert "Current Layer:" not in context
        assert "Layer Focus:" not in context
        # But strategies should still be there
        assert "Strategy one" in context
        assert "Strategy two" in context

    def test_get_recent_strategies_with_no_strategies_and_layer(
        self, strategy_manager: StrategyManager, sample_layer: PlanLayer
    ) -> None:
        """Test that layer header is still prepended even with no strategies."""
        context = strategy_manager.get_recent_strategies(
            current_iteration=1,
            current_layer=sample_layer,
        )

        assert "Current Layer: 2" in context
        assert sample_layer["name"] in context
        assert "No previous strategies yet." in context

    def test_get_recent_strategies_layer_header_before_strategies(
        self, strategy_manager: StrategyManager, sample_layer: PlanLayer
    ) -> None:
        """Test that layer header appears before strategy content."""
        strategy_manager.save_strategy(1, "First strategy")
        strategy_manager.save_strategy(2, "Second strategy")

        context = strategy_manager.get_recent_strategies(
            current_iteration=3,
            current_layer=sample_layer,
        )

        # Layer header should appear before first strategy
        layer_header_pos = context.find("Current Layer:")
        first_strategy_pos = context.find("Iteration 1:")

        assert layer_header_pos < first_strategy_pos
