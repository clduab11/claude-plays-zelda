"""Action planner for breaking down high-level decisions into executable actions."""

from typing import Dict, Any, List, Optional
from enum import Enum
from loguru import logger


class ActionType(Enum):
    """Types of actions the agent can perform."""

    MOVE = "move"
    ATTACK = "attack"
    USE_ITEM = "use_item"
    OPEN_MENU = "open_menu"
    WAIT = "wait"
    TALK = "talk"
    EXPLORE = "explore"
    COMBAT = "combat"
    COLLECT = "collect"


class ActionPlanner:
    """Plans and sequences actions for the agent."""

    def __init__(self):
        """Initialize action planner."""
        self.current_plan: List[Dict[str, Any]] = []
        self.plan_step = 0

        logger.info("ActionPlanner initialized")

    def create_action_sequence(
        self, high_level_action: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create a sequence of low-level actions from a high-level action.

        Args:
            high_level_action: High-level action description
            context: Current game context

        Returns:
            List of action dictionaries
        """
        try:
            action_lower = high_level_action.lower()

            # Map high-level actions to sequences
            if "explore" in action_lower:
                return self._plan_exploration(context)
            elif "combat" in action_lower or "fight" in action_lower:
                return self._plan_combat(context)
            elif "collect" in action_lower or "pickup" in action_lower:
                return self._plan_collection(context)
            elif "talk" in action_lower:
                return self._plan_dialogue(context)
            elif "heal" in action_lower:
                return self._plan_healing(context)
            else:
                # Single action
                return [self._parse_single_action(high_level_action)]

        except Exception as e:
            logger.error(f"Error creating action sequence: {e}")
            return [{"action": "wait", "parameters": {"duration": 1.0}}]

    def _plan_exploration(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan exploration actions."""
        actions = []

        # Check for unexplored directions
        observations = context.get("observations", {})
        doors = observations.get("doors", [])

        if doors:
            # Move towards nearest door
            door = doors[0]
            center = door.get("center", (0, 0))

            # Determine direction to door
            # This is simplified - actual implementation would calculate direction
            actions.append(
                {"action": "move", "parameters": {"direction": "up", "duration": 2.0, "run": False}}
            )
        else:
            # Random exploration
            import random

            direction = random.choice(["up", "down", "left", "right"])
            actions.append(
                {"action": "move", "parameters": {"direction": direction, "duration": 2.0, "run": False}}
            )

        return actions

    def _plan_combat(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan combat actions."""
        actions = []

        observations = context.get("observations", {})
        enemies = observations.get("enemies", [])

        if not enemies:
            return [{"action": "wait", "parameters": {"duration": 0.5}}]

        # Simple combat strategy
        enemy = enemies[0]  # Target first enemy

        # Approach and attack
        actions.append({"action": "attack", "parameters": {"charge": False}})

        # Dodge after attack
        import random

        dodge_direction = random.choice(["up", "down", "left", "right"])
        actions.append(
            {"action": "move", "parameters": {"direction": dodge_direction, "duration": 0.3, "run": True}}
        )

        return actions

    def _plan_collection(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan item collection actions."""
        actions = []

        observations = context.get("observations", {})
        items = observations.get("items", [])

        if items:
            # Move towards nearest item
            item = items[0]
            center = item.get("center", (0, 0))

            # Simplified - move in general direction
            actions.append(
                {"action": "move", "parameters": {"direction": "up", "duration": 1.0, "run": True}}
            )

        return actions

    def _plan_dialogue(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan NPC dialogue actions."""
        return [
            # Approach NPC
            {"action": "move", "parameters": {"direction": "up", "duration": 0.5}},
            # Talk
            {"action": "talk", "parameters": {}},
            # Wait for dialogue
            {"action": "wait", "parameters": {"duration": 2.0}},
        ]

    def _plan_healing(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan healing actions."""
        return [
            # Open menu
            {"action": "open_menu", "parameters": {}},
            # Wait for menu
            {"action": "wait", "parameters": {"duration": 1.0}},
            # Use healing item (would need menu navigation)
            {"action": "use_item", "parameters": {}},
        ]

    def _parse_single_action(self, action_str: str) -> Dict[str, Any]:
        """Parse a single action string into action dictionary."""
        # Default action
        return {"action": "wait", "parameters": {"duration": 1.0}}

    def validate_action(self, action: Dict[str, Any]) -> bool:
        """
        Validate that an action is properly formatted.

        Args:
            action: Action dictionary

        Returns:
            True if valid
        """
        if "action" not in action:
            logger.error("Action missing 'action' field")
            return False

        if "parameters" not in action:
            logger.warning("Action missing 'parameters' field, adding empty dict")
            action["parameters"] = {}

        # Validate action type
        valid_actions = [a.value for a in ActionType]
        if action["action"] not in valid_actions:
            logger.warning(f"Unknown action type: {action['action']}")

        return True

    def prioritize_actions(
        self, actions: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize actions based on current context.

        Args:
            actions: List of possible actions
            context: Current game context

        Returns:
            Sorted list of actions by priority
        """
        game_state = context.get("game_state", {})
        health_status = game_state.get("health_status", "good")

        # If health is critical, prioritize defensive actions
        if health_status == "critical":
            defensive_priority = {"wait": 0, "move": 1, "open_menu": 2}
            actions.sort(key=lambda a: defensive_priority.get(a["action"], 10))

        return actions

    def get_action_description(self, action: Dict[str, Any]) -> str:
        """
        Get human-readable description of an action.

        Args:
            action: Action dictionary

        Returns:
            Description string
        """
        action_type = action.get("action", "unknown")
        params = action.get("parameters", {})

        if action_type == "move":
            direction = params.get("direction", "?")
            run = params.get("run", False)
            return f"Move {direction}" + (" (running)" if run else "")
        elif action_type == "attack":
            charge = params.get("charge", False)
            return "Charged attack" if charge else "Quick attack"
        elif action_type == "use_item":
            return "Use current item"
        elif action_type == "wait":
            duration = params.get("duration", 1.0)
            return f"Wait {duration}s"
        else:
            return action_type.capitalize()
