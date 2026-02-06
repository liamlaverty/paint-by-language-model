"""Strategy Manager for multi-iteration context management."""

import logging
import re
from pathlib import Path

from config import STRATEGY_CONTEXT_WINDOW

logger = logging.getLogger(__name__)


class StrategyManager:
    """Manages strategic planning context across iterations."""

    def __init__(self, artwork_id: str, output_dir: Path):
        """
        Initialize Strategy Manager.

        Args:
            artwork_id (str): Unique identifier for this artwork
            output_dir (Path): Base output directory for artwork files
        """
        self.artwork_id = artwork_id
        self.output_dir = output_dir
        self.strategy_dir = output_dir / artwork_id / "strategies"
        self.strategies: dict[int, str] = {}

        # Create strategy directory
        self.strategy_dir.mkdir(parents=True, exist_ok=True)

        # Load existing strategies if any
        self._load_existing_strategies()

        logger.info(f"Initialized StrategyManager for artwork: {artwork_id}")

    def save_strategy(self, iteration: int, strategy: str) -> Path | None:
        """
        Save strategy update for a specific iteration.

        Args:
            iteration (int): Iteration number
            strategy (str): Strategy text to save

        Returns:
            Path | None: Path to saved strategy file or None if empty

        Raises:
            IOError: If file cannot be written
        """
        if not strategy or not strategy.strip():
            logger.warning(f"Empty strategy for iteration {iteration}, skipping save")
            return None

        # Generate filename
        filename = f"iteration-{iteration:03d}.md"
        filepath = self.strategy_dir / filename

        # Write strategy file
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Strategy - Iteration {iteration}\n\n")
                f.write(strategy.strip())
                f.write("\n")

            # Update in-memory cache
            self.strategies[iteration] = strategy.strip()

            logger.info(f"Saved strategy for iteration {iteration} to {filepath}")
            return filepath

        except OSError as e:
            logger.error(f"Failed to save strategy: {e}")
            raise

    def get_strategy(self, iteration: int) -> str | None:
        """
        Get strategy for a specific iteration.

        Args:
            iteration (int): Iteration number

        Returns:
            str | None: Strategy text or None if not found
        """
        return self.strategies.get(iteration)

    def get_recent_strategies(
        self, current_iteration: int, window: int = STRATEGY_CONTEXT_WINDOW
    ) -> str:
        """
        Get recent strategy context for VLM prompt.

        Args:
            current_iteration (int): Current iteration number
            window (int): Number of recent strategies to include

        Returns:
            str: Formatted string with recent strategies
        """
        if not self.strategies:
            return "No previous strategies yet."

        # Get iterations within window
        start_iteration = max(1, current_iteration - window)
        relevant_iterations = [
            i for i in range(start_iteration, current_iteration) if i in self.strategies
        ]

        if not relevant_iterations:
            return "No previous strategies yet."

        # Format strategies
        context_parts = []
        for iteration in relevant_iterations:
            strategy = self.strategies[iteration]
            context_parts.append(f"Iteration {iteration}: {strategy}")

        return "\n".join(context_parts)

    def get_latest_strategy(self) -> tuple[int, str] | None:
        """
        Get the most recent strategy.

        Returns:
            tuple[int, str] | None: (iteration, strategy_text) or None
        """
        if not self.strategies:
            return None

        latest_iteration = max(self.strategies.keys())
        return (latest_iteration, self.strategies[latest_iteration])

    def _load_existing_strategies(self) -> None:
        """Load existing strategy files from disk."""
        if not self.strategy_dir.exists():
            return

        # Find all strategy files
        strategy_files = sorted(self.strategy_dir.glob("iteration-*.md"))

        for filepath in strategy_files:
            # Extract iteration number from filename
            match = re.search(r"iteration-(\d+)\.md", filepath.name)
            if not match:
                continue

            iteration = int(match.group(1))

            # Read strategy content
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()

                # Remove markdown header if present
                content = re.sub(r"^#\s+Strategy\s+-\s+Iteration\s+\d+\s*\n+", "", content)

                self.strategies[iteration] = content.strip()
                logger.debug(f"Loaded strategy for iteration {iteration}")

            except OSError as e:
                logger.warning(f"Could not load strategy file {filepath}: {e}")

        if self.strategies:
            logger.info(f"Loaded {len(self.strategies)} existing strategies")

    def save_current_strategy_link(self) -> Path | None:
        """
        Save link to current strategy as 'current-strategy.md'.

        Returns:
            Path | None: Path to current strategy file or None
        """
        latest = self.get_latest_strategy()
        if not latest:
            return None

        iteration, strategy = latest
        current_strategy_path = self.strategy_dir / "current-strategy.md"

        # Write current strategy file
        try:
            with open(current_strategy_path, "w", encoding="utf-8") as f:
                f.write(f"# Current Strategy (Iteration {iteration})\n\n")
                f.write(strategy)
                f.write("\n")

            logger.debug(f"Updated current-strategy.md with iteration {iteration}")
            return current_strategy_path

        except OSError as e:
            logger.warning(f"Could not save current-strategy.md: {e}")
            return None

    def get_all_strategies(self) -> dict[int, str]:
        """
        Get all strategies.

        Returns:
            Dict[int, str]: All strategies keyed by iteration
        """
        return self.strategies.copy()

    def clear_strategies(self) -> None:
        """Clear in-memory strategy cache."""
        self.strategies.clear()
        logger.debug("Cleared strategy cache")
