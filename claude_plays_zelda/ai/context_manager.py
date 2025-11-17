"""Context manager for building and maintaining conversation context."""

from typing import Dict, Any, List, Optional
from collections import deque
from loguru import logger


class ContextManager:
    """Manages context window for Claude API calls."""

    def __init__(self, max_recent_actions: int = 10):
        """
        Initialize context manager.

        Args:
            max_recent_actions: Maximum number of recent actions to include
        """
        self.max_recent_actions = max_recent_actions
        self.action_history = deque(maxlen=max_recent_actions)

        logger.info("ContextManager initialized")

    def build_context(
        self,
        game_state: Dict[str, Any],
        observations: Dict[str, Any],
        recent_actions: List[str],
        memory: Any,  # AgentMemory instance
    ) -> Dict[str, Any]:
        """
        Build context dictionary for Claude API.

        Args:
            game_state: Current game state
            observations: Visual observations
            recent_actions: Recent actions taken
            memory: Agent memory instance

        Returns:
            Context dictionary
        """
        context = {
            "game_state": self._format_game_state(game_state),
            "observations": self._format_observations(observations),
            "recent_actions": recent_actions[-self.max_recent_actions :],
            "objectives": memory.get_objectives(),
            "strategy_notes": memory.get_strategy_notes(),
            "learned_patterns": memory.get_learned_patterns(),
        }

        return context

    def _format_game_state(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Format game state for context."""
        formatted = {
            "hearts": game_state.get("hearts", {}),
            "rupees": game_state.get("rupees", 0),
            "current_item": game_state.get("current_item"),
            "location": game_state.get("location"),
        }

        # Add health status
        hearts = formatted["hearts"]
        if hearts:
            current = hearts.get("current_hearts", 0)
            maximum = hearts.get("max_hearts", 1)
            health_percentage = (current / maximum) * 100 if maximum > 0 else 0

            if health_percentage < 25:
                formatted["health_status"] = "critical"
            elif health_percentage < 50:
                formatted["health_status"] = "low"
            elif health_percentage < 75:
                formatted["health_status"] = "moderate"
            else:
                formatted["health_status"] = "good"

        return formatted

    def _format_observations(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Format observations for context."""
        formatted = {
            "enemies": observations.get("enemies", []),
            "items": observations.get("items", []),
            "doors": observations.get("doors", []),
            "npcs": observations.get("npcs", []),
        }

        # Add threat assessment
        num_enemies = len(formatted["enemies"])
        if num_enemies == 0:
            formatted["threat_level"] = "none"
        elif num_enemies <= 2:
            formatted["threat_level"] = "low"
        elif num_enemies <= 4:
            formatted["threat_level"] = "moderate"
        else:
            formatted["threat_level"] = "high"

        return formatted

    def add_action(self, action: str):
        """Add an action to the history."""
        self.action_history.append(action)

    def get_recent_actions(self) -> List[str]:
        """Get recent actions."""
        return list(self.action_history)

    def summarize_session(self) -> Dict[str, Any]:
        """Summarize the current session."""
        return {
            "total_actions": len(self.action_history),
            "recent_actions": list(self.action_history),
        }

    def clear(self):
        """Clear context history."""
        self.action_history.clear()
        logger.info("Context cleared")
