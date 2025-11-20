"""
Structured action schema for VLM outputs.

Defines the hierarchical reasoning structure and controller output format
for the SIMA 2-inspired agent.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from loguru import logger


class ThreatLevel(Enum):
    """Threat assessment levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GameButton(Enum):
    """Available game controller buttons."""
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    A = "A"  # Attack/Confirm
    B = "B"  # Use item/Cancel
    X = "X"  # Menu
    Y = "Y"  # Map
    L = "L"
    R = "R"
    START = "START"
    SELECT = "SELECT"


@dataclass
class ControllerOutput:
    """Low-level controller output."""
    buttons: List[str]
    duration_ms: int = 200
    hold: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "buttons": self.buttons,
            "duration_ms": self.duration_ms,
            "hold": self.hold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ControllerOutput':
        """Create from dictionary."""
        return cls(
            buttons=data.get("buttons", []),
            duration_ms=data.get("duration_ms", 200),
            hold=data.get("hold", False)
        )


@dataclass
class ActionDecision:
    """
    Hierarchical action decision from the VLM.

    Follows SIMA 2-inspired structure:
    Observation → Reasoning → Planning → Action
    """
    # Visual understanding
    visual_observation: str = ""

    # Threat analysis
    threat_assessment: ThreatLevel = ThreatLevel.NONE
    threat_details: str = ""

    # Strategic layer
    strategic_goal: str = ""

    # Tactical layer
    immediate_tactic: str = ""

    # Controller output
    controller_output: ControllerOutput = field(default_factory=lambda: ControllerOutput(buttons=[]))

    # Metadata
    confidence: float = 0.0
    reasoning_trace: str = ""
    frame_analysis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "visual_observation": self.visual_observation,
            "threat_assessment": self.threat_assessment.value,
            "threat_details": self.threat_details,
            "strategic_goal": self.strategic_goal,
            "immediate_tactic": self.immediate_tactic,
            "controller_output": self.controller_output.to_dict(),
            "confidence": self.confidence,
            "reasoning_trace": self.reasoning_trace,
            "frame_analysis": self.frame_analysis
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionDecision':
        """Create ActionDecision from dictionary."""
        threat_str = data.get("threat_assessment", "none").upper()
        try:
            threat = ThreatLevel[threat_str]
        except KeyError:
            threat = ThreatLevel.NONE
            logger.warning(f"Unknown threat level: {threat_str}, defaulting to NONE")

        controller_data = data.get("controller_output", {})
        if isinstance(controller_data, dict):
            controller = ControllerOutput.from_dict(controller_data)
        else:
            controller = ControllerOutput(buttons=[])

        return cls(
            visual_observation=data.get("visual_observation", ""),
            threat_assessment=threat,
            threat_details=data.get("threat_details", ""),
            strategic_goal=data.get("strategic_goal", ""),
            immediate_tactic=data.get("immediate_tactic", ""),
            controller_output=controller,
            confidence=data.get("confidence", 0.0),
            reasoning_trace=data.get("reasoning_trace", ""),
            frame_analysis=data.get("frame_analysis")
        )


class ActionSchema:
    """
    Provides schema definitions and parsing utilities for VLM outputs.
    """

    @staticmethod
    def get_json_schema() -> Dict[str, Any]:
        """
        Get JSON schema for VLM response.

        Returns:
            JSON schema dictionary
        """
        return {
            "type": "object",
            "required": ["visual_observation", "controller_output"],
            "properties": {
                "visual_observation": {
                    "type": "string",
                    "description": "Detailed description of what you see in the game frames (enemies, Link's position, items, environment)"
                },
                "threat_assessment": {
                    "type": "string",
                    "enum": ["none", "low", "medium", "high", "critical"],
                    "description": "Current threat level based on enemy positions and Link's health"
                },
                "threat_details": {
                    "type": "string",
                    "description": "Specific details about threats (enemy types, distances, attack patterns)"
                },
                "strategic_goal": {
                    "type": "string",
                    "description": "High-level objective (e.g., 'Reach dungeon entrance', 'Defeat enemies in room')"
                },
                "immediate_tactic": {
                    "type": "string",
                    "description": "Short-term tactic to achieve goal (e.g., 'Dodge projectile', 'Circle enemy')"
                },
                "controller_output": {
                    "type": "object",
                    "required": ["buttons"],
                    "properties": {
                        "buttons": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "X", "Y", "L", "R", "START", "SELECT"]
                            },
                            "description": "List of buttons to press (e.g., ['RIGHT', 'A'] for attack while moving)"
                        },
                        "duration_ms": {
                            "type": "integer",
                            "description": "How long to hold the buttons in milliseconds (100-1000)",
                            "minimum": 50,
                            "maximum": 2000
                        },
                        "hold": {
                            "type": "boolean",
                            "description": "Whether to hold buttons (true) or tap (false)"
                        }
                    }
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence in this decision (0.0-1.0)"
                }
            }
        }

    @staticmethod
    def get_example_output() -> str:
        """
        Get example output for VLM prompt.

        Returns:
            Example JSON string
        """
        example = {
            "visual_observation": "Link is in a stone corridor. A red Moblin is 2 tiles north, moving toward me. Health shows 1 heart remaining (critical). Door visible to the east.",
            "threat_assessment": "high",
            "threat_details": "Moblin has predictable charge pattern. One hit will kill Link at current health.",
            "strategic_goal": "Survive and exit the room to the east",
            "immediate_tactic": "Dodge east to avoid combat, preserve critical health",
            "controller_output": {
                "buttons": ["RIGHT"],
                "duration_ms": 400,
                "hold": True
            },
            "confidence": 0.85
        }
        return json.dumps(example, indent=2)

    @staticmethod
    def parse_vlm_response(response_text: str) -> ActionDecision:
        """
        Parse VLM response into ActionDecision.

        Args:
            response_text: Raw text response from VLM

        Returns:
            ActionDecision object
        """
        try:
            # Try to extract JSON from response
            # VLM might wrap JSON in markdown code blocks
            import re

            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```"):
                # Extract content between ```json and ```
                match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
                if match:
                    text = match.group(1)

            # Try to find JSON object
            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                raise ValueError("No JSON object found in response")

            json_str = json_match.group(0)
            data = json.loads(json_str)

            decision = ActionDecision.from_dict(data)

            # Store full response as reasoning trace
            decision.reasoning_trace = response_text

            logger.debug(f"Parsed action: {decision.controller_output.buttons}")
            return decision

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return ActionSchema._create_fallback_action(response_text)
        except Exception as e:
            logger.error(f"Failed to parse VLM response: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return ActionSchema._create_fallback_action(response_text)

    @staticmethod
    def _create_fallback_action(response_text: str) -> ActionDecision:
        """
        Create a safe fallback action when parsing fails.

        Args:
            response_text: Original response text

        Returns:
            Safe ActionDecision (pause game)
        """
        logger.warning("Creating fallback action: PAUSE")
        return ActionDecision(
            visual_observation="Failed to parse response",
            threat_assessment=ThreatLevel.NONE,
            strategic_goal="Pause and recover",
            immediate_tactic="Open menu to pause game",
            controller_output=ControllerOutput(
                buttons=["START"],
                duration_ms=100,
                hold=False
            ),
            confidence=0.0,
            reasoning_trace=response_text[:500]
        )

    @staticmethod
    def validate_action(decision: ActionDecision) -> bool:
        """
        Validate an ActionDecision.

        Args:
            decision: ActionDecision to validate

        Returns:
            True if valid, False otherwise
        """
        # Check if buttons are valid
        valid_buttons = {b.value for b in GameButton}
        for button in decision.controller_output.buttons:
            if button not in valid_buttons:
                logger.warning(f"Invalid button: {button}")
                return False

        # Check duration is reasonable
        if not (50 <= decision.controller_output.duration_ms <= 2000):
            logger.warning(f"Invalid duration: {decision.controller_output.duration_ms}")
            return False

        # Check confidence is in range
        if not (0.0 <= decision.confidence <= 1.0):
            logger.warning(f"Invalid confidence: {decision.confidence}")
            return False

        return True
