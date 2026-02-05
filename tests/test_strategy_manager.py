"""Unit tests for Strategy Manager."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from strategy_manager import StrategyManager


class TestStrategyManager(unittest.TestCase):
    """Test suite for StrategyManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.artwork_id = "test-artwork-001"
        self.manager = StrategyManager(
            artwork_id=self.artwork_id, output_dir=self.test_dir
        )

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_initialization_creates_directory(self) -> None:
        """Test manager creates strategy directory."""
        expected_path = self.test_dir / self.artwork_id / "strategies"
        self.assertTrue(expected_path.exists())
        self.assertTrue(expected_path.is_dir())

    def test_save_strategy_creates_file(self) -> None:
        """Test saving strategy creates markdown file."""
        strategy = "Focus on establishing sky composition"
        filepath = self.manager.save_strategy(1, strategy)

        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.name, "iteration-001.md")

    def test_save_strategy_correct_content(self) -> None:
        """Test saved strategy has correct content."""
        strategy = "Build foreground details"
        filepath = self.manager.save_strategy(5, strategy)

        self.assertIsNotNone(filepath)
        with open(filepath, "r") as f:
            content = f.read()

        self.assertIn("Strategy - Iteration 5", content)
        self.assertIn(strategy, content)

    def test_get_strategy_retrieves_saved(self) -> None:
        """Test retrieving saved strategy."""
        strategy = "Add texture to buildings"
        self.manager.save_strategy(3, strategy)

        retrieved = self.manager.get_strategy(3)
        self.assertEqual(retrieved, strategy)

    def test_get_strategy_missing_returns_none(self) -> None:
        """Test retrieving nonexistent strategy returns None."""
        result = self.manager.get_strategy(999)
        self.assertIsNone(result)

    def test_get_recent_strategies_window(self) -> None:
        """Test recent strategies respects window size."""
        strategies = {
            1: "Strategy 1",
            2: "Strategy 2",
            3: "Strategy 3",
            4: "Strategy 4",
            5: "Strategy 5",
            6: "Strategy 6",
        }

        for iteration, strategy in strategies.items():
            self.manager.save_strategy(iteration, strategy)

        # Get recent with window of 3, current iteration 7
        recent = self.manager.get_recent_strategies(current_iteration=7, window=3)

        # Should include iterations 4, 5, 6
        self.assertIn("Iteration 4", recent)
        self.assertIn("Iteration 5", recent)
        self.assertIn("Iteration 6", recent)
        self.assertNotIn("Iteration 1", recent)
        self.assertNotIn("Iteration 2", recent)

    def test_get_recent_strategies_no_strategies(self) -> None:
        """Test recent strategies with no saved strategies."""
        recent = self.manager.get_recent_strategies(1)
        self.assertEqual(recent, "No previous strategies yet.")

    def test_get_latest_strategy(self) -> None:
        """Test getting latest strategy."""
        self.manager.save_strategy(1, "First")
        self.manager.save_strategy(5, "Fifth")
        self.manager.save_strategy(3, "Third")

        latest = self.manager.get_latest_strategy()
        self.assertIsNotNone(latest)
        self.assertEqual(latest[0], 5)
        self.assertEqual(latest[1], "Fifth")

    def test_get_latest_strategy_empty(self) -> None:
        """Test getting latest strategy when none exist."""
        latest = self.manager.get_latest_strategy()
        self.assertIsNone(latest)

    def test_save_empty_strategy_skips(self) -> None:
        """Test saving empty strategy is skipped."""
        result = self.manager.save_strategy(1, "")
        self.assertIsNone(result)
        self.assertNotIn(1, self.manager.strategies)

    def test_load_existing_strategies(self) -> None:
        """Test loading existing strategies from disk."""
        # Save some strategies
        self.manager.save_strategy(1, "First strategy")
        self.manager.save_strategy(2, "Second strategy")

        # Create new manager (should load existing)
        new_manager = StrategyManager(
            artwork_id=self.artwork_id, output_dir=self.test_dir
        )

        self.assertEqual(len(new_manager.strategies), 2)
        self.assertEqual(new_manager.get_strategy(1), "First strategy")
        self.assertEqual(new_manager.get_strategy(2), "Second strategy")

    def test_get_all_strategies(self) -> None:
        """Test getting all strategies."""
        strategies = {
            1: "Strategy 1",
            3: "Strategy 3",
            5: "Strategy 5",
        }

        for iteration, strategy in strategies.items():
            self.manager.save_strategy(iteration, strategy)

        all_strategies = self.manager.get_all_strategies()
        self.assertEqual(len(all_strategies), 3)
        self.assertEqual(all_strategies, strategies)

    def test_clear_strategies(self) -> None:
        """Test clearing strategies."""
        self.manager.save_strategy(1, "Test")
        self.assertEqual(len(self.manager.strategies), 1)

        self.manager.clear_strategies()
        self.assertEqual(len(self.manager.strategies), 0)

    def test_save_current_strategy_link(self) -> None:
        """Test saving current strategy link."""
        self.manager.save_strategy(1, "First")
        self.manager.save_strategy(3, "Third")

        current_path = self.manager.save_current_strategy_link()

        self.assertIsNotNone(current_path)
        self.assertTrue(current_path.exists())
        self.assertEqual(current_path.name, "current-strategy.md")

        with open(current_path, "r") as f:
            content = f.read()

        self.assertIn("Current Strategy (Iteration 3)", content)
        self.assertIn("Third", content)

    def test_save_current_strategy_link_no_strategies(self) -> None:
        """Test saving current strategy link with no strategies."""
        result = self.manager.save_current_strategy_link()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
