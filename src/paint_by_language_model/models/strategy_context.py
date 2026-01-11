"""Strategy context type definition for multi-iteration planning."""
from typing import TypedDict


class StrategyContext(TypedDict):
    """
    Strategic planning information for the VLM.
    
    Attributes:
        iteration (int): Current iteration number
        strategy_text (str): Current strategy description
        previous_strategies (list[str]): Recent strategy history
        last_updated (str): ISO format timestamp of last update
    """
    iteration: int
    strategy_text: str
    previous_strategies: list[str]
    last_updated: str
