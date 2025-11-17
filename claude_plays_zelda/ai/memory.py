"""Memory system for tracking learned strategies and game progress."""

from typing import Dict, Any, List, Optional
from collections import deque, defaultdict
from datetime import datetime
import json
from pathlib import Path
from loguru import logger


class AgentMemory:
    """Stores and manages agent's learned knowledge and experiences."""

    def __init__(self, max_history: int = 100):
        """
        Initialize agent memory.

        Args:
            max_history: Maximum number of decisions to keep in history
        """
        self.decision_history = deque(maxlen=max_history)
        self.outcomes: List[Dict[str, Any]] = []
        self.objectives: List[str] = []
        self.strategy_notes: List[str] = []
        self.learned_patterns: Dict[str, Any] = {}

        # Statistics
        self.stats = {
            "total_decisions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "deaths": 0,
            "rooms_explored": 0,
            "enemies_defeated": 0,
            "items_collected": 0,
        }

        # Location-based memory
        self.location_memory: Dict[str, Dict[str, Any]] = defaultdict(dict)

        logger.info("AgentMemory initialized")

    def add_decision(
        self, game_state: Dict[str, Any], decision: Dict[str, Any], context: Dict[str, Any]
    ):
        """
        Record a decision made by the agent.

        Args:
            game_state: Game state at time of decision
            decision: The decision made
            context: Context used for decision
        """
        self.decision_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "game_state": game_state,
                "decision": decision,
                "context": context,
            }
        )
        self.stats["total_decisions"] += 1

    def add_outcome(self, success: bool, result: Dict[str, Any], feedback: Optional[str] = None):
        """
        Record the outcome of an action.

        Args:
            success: Whether the action was successful
            result: Result details
            feedback: Optional feedback message
        """
        self.outcomes.append(
            {
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "result": result,
                "feedback": feedback,
            }
        )

        if success:
            self.stats["successful_actions"] += 1
        else:
            self.stats["failed_actions"] += 1

        # Update specific stats
        if result.get("death"):
            self.stats["deaths"] += 1
        if result.get("enemy_defeated"):
            self.stats["enemies_defeated"] += 1
        if result.get("item_collected"):
            self.stats["items_collected"] += 1

    def add_objective(self, objective: str):
        """Add a new objective."""
        if objective not in self.objectives:
            self.objectives.append(objective)
            logger.info(f"New objective added: {objective}")

    def complete_objective(self, objective: str):
        """Mark an objective as complete."""
        if objective in self.objectives:
            self.objectives.remove(objective)
            logger.info(f"Objective completed: {objective}")

    def add_strategy_note(self, note: str):
        """Add a strategy note or lesson learned."""
        self.strategy_notes.append(
            {"timestamp": datetime.now().isoformat(), "note": note}
        )
        logger.debug(f"Strategy note: {note}")

    def add_learned_pattern(self, pattern_name: str, pattern_data: Any):
        """
        Add a learned pattern (e.g., enemy behavior, puzzle solution).

        Args:
            pattern_name: Name/identifier for the pattern
            pattern_data: Data about the pattern
        """
        self.learned_patterns[pattern_name] = pattern_data
        logger.info(f"Learned pattern: {pattern_name}")

    def get_location_memory(self, location: str) -> Dict[str, Any]:
        """
        Get memory for a specific location.

        Args:
            location: Location identifier

        Returns:
            Memory dictionary for that location
        """
        return self.location_memory.get(location, {})

    def update_location_memory(self, location: str, data: Dict[str, Any]):
        """
        Update memory for a specific location.

        Args:
            location: Location identifier
            data: Data to store
        """
        self.location_memory[location].update(data)

    def get_objectives(self) -> List[str]:
        """Get current objectives."""
        return self.objectives.copy()

    def get_strategy_notes(self, limit: int = 10) -> List[str]:
        """
        Get recent strategy notes.

        Args:
            limit: Maximum number of notes to return

        Returns:
            List of note strings
        """
        recent_notes = self.strategy_notes[-limit:]
        return [note["note"] if isinstance(note, dict) else note for note in recent_notes]

    def get_learned_patterns(self) -> Dict[str, Any]:
        """Get learned patterns."""
        return self.learned_patterns.copy()

    def get_decision_count(self) -> int:
        """Get total number of decisions made."""
        return self.stats["total_decisions"]

    def get_success_rate(self) -> float:
        """Get success rate of actions."""
        total = self.stats["successful_actions"] + self.stats["failed_actions"]
        if total == 0:
            return 0.0
        return self.stats["successful_actions"] / total

    def get_statistics(self) -> Dict[str, Any]:
        """Get all statistics."""
        stats = self.stats.copy()
        stats["success_rate"] = self.get_success_rate()
        return stats

    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent decisions.

        Args:
            limit: Number of decisions to return

        Returns:
            List of decision dictionaries
        """
        return list(self.decision_history)[-limit:]

    def save_to_file(self, filepath: str):
        """
        Save memory to a JSON file.

        Args:
            filepath: Path to save file
        """
        try:
            data = {
                "stats": self.stats,
                "objectives": self.objectives,
                "strategy_notes": self.strategy_notes,
                "learned_patterns": self.learned_patterns,
                "location_memory": dict(self.location_memory),
                "recent_decisions": list(self.decision_history)[-50:],  # Save last 50
            }

            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Memory saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def load_from_file(self, filepath: str):
        """
        Load memory from a JSON file.

        Args:
            filepath: Path to load file
        """
        try:
            if not Path(filepath).exists():
                logger.warning(f"Memory file not found: {filepath}")
                return

            with open(filepath, "r") as f:
                data = json.load(f)

            self.stats = data.get("stats", self.stats)
            self.objectives = data.get("objectives", [])
            self.strategy_notes = data.get("strategy_notes", [])
            self.learned_patterns = data.get("learned_patterns", {})
            self.location_memory = defaultdict(dict, data.get("location_memory", {}))

            logger.info(f"Memory loaded from {filepath}")

        except Exception as e:
            logger.error(f"Error loading memory: {e}")

    def clear(self):
        """Clear all memory (hard reset)."""
        self.decision_history.clear()
        self.outcomes.clear()
        self.objectives.clear()
        self.strategy_notes.clear()
        self.learned_patterns.clear()
        self.location_memory.clear()

        self.stats = {
            "total_decisions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "deaths": 0,
            "rooms_explored": 0,
            "enemies_defeated": 0,
            "items_collected": 0,
        }

        logger.info("Memory cleared")

    def summarize(self) -> str:
        """
        Generate a text summary of the agent's memory.

        Returns:
            Summary string
        """
        summary_parts = [
            f"Agent Memory Summary:",
            f"- Total Decisions: {self.stats['total_decisions']}",
            f"- Success Rate: {self.get_success_rate():.1%}",
            f"- Deaths: {self.stats['deaths']}",
            f"- Enemies Defeated: {self.stats['enemies_defeated']}",
            f"- Items Collected: {self.stats['items_collected']}",
            f"- Current Objectives: {len(self.objectives)}",
            f"- Strategy Notes: {len(self.strategy_notes)}",
            f"- Learned Patterns: {len(self.learned_patterns)}",
        ]

        return "\n".join(summary_parts)
