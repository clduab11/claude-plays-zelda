"""
Adapter to integrate SIMA agent with existing codebase.

Provides a compatibility layer between the new PixelsToActionsAgent
and the existing game loop architecture.
"""

import asyncio
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np
from loguru import logger

from ..sima import PixelsToActionsAgent, ActionDecision
from .action_planner import Action, ActionType


class SimaAgentAdapter:
    """
    Adapter that wraps PixelsToActionsAgent for use with existing code.

    Converts between:
    - numpy arrays (OpenCV) ↔ PIL Images
    - SIMA ActionDecisions ↔ Legacy Action objects
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        enable_critic: bool = True,
        enable_async: bool = True
    ):
        """
        Initialize SIMA adapter.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            enable_critic: Enable self-improvement
            enable_async: Use async event loop (recommended)
        """
        # Initialize SIMA agent
        self.sima_agent = PixelsToActionsAgent(
            api_key=api_key,
            model=model,
            enable_critic=enable_critic
        )

        self.enable_async = enable_async
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

        # Create event loop if using async
        if self.enable_async:
            try:
                self.event_loop = asyncio.get_running_loop()
            except RuntimeError:
                self.event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.event_loop)

        logger.info(f"SimaAgentAdapter initialized (async={'enabled' if enable_async else 'disabled'})")

    def get_action(
        self,
        screen: np.ndarray,
        game_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get action from SIMA agent (synchronous interface).

        Converts numpy array to PIL Image, calls SIMA agent,
        and returns response in legacy format.

        Args:
            screen: Game screenshot (numpy array, BGR format)
            game_state: Game state dict (health, rupees, etc.)

        Returns:
            Dictionary with 'action' and 'reason' keys (legacy format)
        """
        try:
            # Convert numpy array to PIL Image
            frame = self._numpy_to_pil(screen)

            # Extract health info
            health = None
            max_health = None
            if game_state:
                health = game_state.get("health", game_state.get("current_hearts"))
                max_health = game_state.get("max_health", game_state.get("max_hearts"))

            # Build metadata
            metadata = self._extract_metadata(game_state)

            # Call SIMA agent
            if self.enable_async and self.event_loop:
                decision = self.event_loop.run_until_complete(
                    self.sima_agent.decide_action(
                        current_frame=frame,
                        health=health,
                        max_health=max_health,
                        metadata=metadata
                    )
                )
            else:
                # Fallback: create new event loop
                decision = asyncio.run(
                    self.sima_agent.decide_action(
                        current_frame=frame,
                        health=health,
                        max_health=max_health,
                        metadata=metadata
                    )
                )

            # Convert to legacy format
            return self._decision_to_legacy_format(decision)

        except Exception as e:
            logger.error(f"SIMA adapter error: {e}", exc_info=True)
            return {
                "action": "wait",
                "reason": f"Error: {str(e)}",
                "confidence": 0.0
            }

    def parse_action_response(self, action_response: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse action response (compatibility with legacy ClaudeClient).

        Args:
            action_response: Response from get_action()

        Returns:
            Dictionary with 'action' and 'reason' keys
        """
        return {
            "action": action_response.get("action", "wait"),
            "reason": action_response.get("reason", "No reason provided")
        }

    def convert_to_legacy_action(self, decision: ActionDecision) -> Action:
        """
        Convert SIMA ActionDecision to legacy Action object.

        Args:
            decision: SIMA ActionDecision

        Returns:
            Legacy Action object
        """
        # Map buttons to action type
        buttons = decision.controller_output.buttons
        duration_s = decision.controller_output.duration_ms / 1000.0

        # Primary button determines action type
        if not buttons:
            action_type = ActionType.WAIT
        elif "A" in buttons:
            action_type = ActionType.ATTACK
        elif "B" in buttons:
            action_type = ActionType.USE_ITEM
        elif "START" in buttons or "X" in buttons:
            action_type = ActionType.OPEN_MENU
        elif "UP" in buttons:
            action_type = ActionType.MOVE_UP
        elif "DOWN" in buttons:
            action_type = ActionType.MOVE_DOWN
        elif "LEFT" in buttons:
            action_type = ActionType.MOVE_LEFT
        elif "RIGHT" in buttons:
            action_type = ActionType.MOVE_RIGHT
        else:
            action_type = ActionType.WAIT

        return Action(
            action_type=action_type,
            duration=duration_s,
            parameters={"buttons": buttons}
        )

    def on_death_detected(self, context: Optional[str] = None) -> None:
        """
        Handle death detection.

        Args:
            context: Context about the death
        """
        if self.enable_async and self.event_loop:
            self.event_loop.run_until_complete(
                self.sima_agent.on_death_detected(context)
            )
        else:
            asyncio.run(self.sima_agent.on_death_detected(context))

    def set_objective(self, objective: str) -> None:
        """Set the current objective."""
        self.sima_agent.set_objective(objective)

    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return self.sima_agent.get_statistics()

    def _numpy_to_pil(self, image: np.ndarray) -> Image.Image:
        """
        Convert numpy array to PIL Image.

        Args:
            image: Numpy array (BGR format from OpenCV)

        Returns:
            PIL Image (RGB)
        """
        # Check if grayscale
        if len(image.shape) == 2:
            return Image.fromarray(image)

        # Convert BGR to RGB
        import cv2
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def _extract_metadata(self, game_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract metadata from game state."""
        if not game_state:
            return {}

        metadata = {}

        # Location
        if "location" in game_state:
            location = game_state["location"]
            if hasattr(location, "region"):
                metadata["location"] = location.region
            else:
                metadata["location"] = str(location)

        # Dungeon detection
        if "in_menu" in game_state:
            metadata["in_menu"] = game_state["in_menu"]

        # Enemy/item counts
        if "enemies_visible" in game_state:
            metadata["enemies_nearby"] = len(game_state["enemies_visible"]) > 0

        if "items_visible" in game_state:
            metadata["items_nearby"] = len(game_state["items_visible"]) > 0

        # Rupees
        if "rupees" in game_state:
            metadata["rupees"] = game_state["rupees"]

        return metadata

    def _decision_to_legacy_format(self, decision: ActionDecision) -> Dict[str, Any]:
        """
        Convert SIMA ActionDecision to legacy format.

        Args:
            decision: SIMA ActionDecision

        Returns:
            Legacy format dict
        """
        # Map buttons to action string
        buttons = decision.controller_output.buttons

        if not buttons:
            action_str = "wait"
        elif len(buttons) == 1:
            action_str = self._button_to_action_string(buttons[0])
        else:
            # Multiple buttons - create compound action
            action_str = " + ".join(self._button_to_action_string(b) for b in buttons)

        return {
            "action": action_str,
            "reason": decision.immediate_tactic,
            "confidence": decision.confidence,
            "threat_level": decision.threat_assessment.value,
            "strategic_goal": decision.strategic_goal,
            "buttons": buttons,
            "duration_ms": decision.controller_output.duration_ms,
            "full_decision": decision.to_dict()
        }

    def _button_to_action_string(self, button: str) -> str:
        """Convert button to action string."""
        mapping = {
            "UP": "move_up",
            "DOWN": "move_down",
            "LEFT": "move_left",
            "RIGHT": "move_right",
            "A": "attack",
            "B": "use_item",
            "X": "menu",
            "START": "menu",
            "SELECT": "map"
        }
        return mapping.get(button, button.lower())

    def reset(self) -> None:
        """Reset session state."""
        self.sima_agent.reset_session()

    def close(self) -> None:
        """Cleanup and shutdown."""
        if self.enable_async and self.event_loop:
            self.event_loop.run_until_complete(self.sima_agent.close())
        else:
            asyncio.run(self.sima_agent.close())

        if self.event_loop and not self.event_loop.is_running():
            self.event_loop.close()


# Helper function for easy integration
def create_sima_agent(api_key: str, **kwargs) -> SimaAgentAdapter:
    """
    Create a SIMA agent adapter.

    Args:
        api_key: Anthropic API key
        **kwargs: Additional arguments for SimaAgentAdapter

    Returns:
        SimaAgentAdapter instance
    """
    return SimaAgentAdapter(api_key=api_key, **kwargs)
