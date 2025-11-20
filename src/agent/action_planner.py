"""Action planning and execution for the AI agent."""

from typing import Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from ..emulator.input_controller import InputController, GameButton


class ActionType(Enum):
    """Types of actions the agent can take."""
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    ATTACK = "attack"
    USE_ITEM = "use_item"
    OPEN_MENU = "open_menu"
    TALK = "talk"
    SEARCH = "search"
    WAIT = "wait"
    COMBO = "combo"
    PRESS_BUTTONS = "press_buttons"


@dataclass
class Action:
    """Represents a single action."""
    action_type: ActionType
    duration: float = 0.2
    parameters: dict = None


class ActionPlanner:
    """Plans and executes actions based on AI decisions."""

    def __init__(self, input_controller: InputController):
        """
        Initialize the action planner.

        Args:
            input_controller: Controller for game input
        """
        self.input_controller = input_controller
        self.current_plan: List[Action] = []
        self.action_history: List[Tuple[Action, bool]] = []

    def parse_action(self, action_string: str) -> Optional[Action]:
        """
        Parse an action string into an Action object.

        Args:
            action_string: Action description from Claude

        Returns:
            Action object or None
        """
        action_string = action_string.lower().strip()
        
        # Map action strings to ActionType
        action_map = {
            "move_up": ActionType.MOVE_UP,
            "move up": ActionType.MOVE_UP,
            "up": ActionType.MOVE_UP,
            "move_down": ActionType.MOVE_DOWN,
            "move down": ActionType.MOVE_DOWN,
            "down": ActionType.MOVE_DOWN,
            "move_left": ActionType.MOVE_LEFT,
            "move left": ActionType.MOVE_LEFT,
            "left": ActionType.MOVE_LEFT,
            "move_right": ActionType.MOVE_RIGHT,
            "move right": ActionType.MOVE_RIGHT,
            "right": ActionType.MOVE_RIGHT,
            "attack": ActionType.ATTACK,
            "fight": ActionType.ATTACK,
            "use_item": ActionType.USE_ITEM,
            "use item": ActionType.USE_ITEM,
            "item": ActionType.USE_ITEM,
            "open_menu": ActionType.OPEN_MENU,
            "menu": ActionType.OPEN_MENU,
            "talk": ActionType.TALK,
            "speak": ActionType.TALK,
            "search": ActionType.SEARCH,
            "look": ActionType.SEARCH,
            "wait": ActionType.WAIT,
            "look": ActionType.SEARCH,
            "wait": ActionType.WAIT,
        }
        
        for key, action_type in action_map.items():
            if key in action_string:
                return Action(action_type=action_type)
        
        logger.warning(f"Unknown action: {action_string}")
        return Action(action_type=ActionType.WAIT)

    def execute_action(self, action: Action) -> bool:
        """
        Execute a single action.

        Args:
            action: Action to execute

        Returns:
            bool: True if executed successfully
        """
        try:
            logger.info(f"Executing action: {action.action_type.value}")
            
            if action.action_type == ActionType.MOVE_UP:
                self.input_controller.move_direction(GameButton.UP, action.duration)
            elif action.action_type == ActionType.MOVE_DOWN:
                self.input_controller.move_direction(GameButton.DOWN, action.duration)
            elif action.action_type == ActionType.MOVE_LEFT:
                self.input_controller.move_direction(GameButton.LEFT, action.duration)
            elif action.action_type == ActionType.MOVE_RIGHT:
                self.input_controller.move_direction(GameButton.RIGHT, action.duration)
            elif action.action_type == ActionType.ATTACK:
                self.input_controller.attack()
            elif action.action_type == ActionType.USE_ITEM:
                self.input_controller.use_item()
            elif action.action_type == ActionType.OPEN_MENU:
                self.input_controller.open_menu()
            elif action.action_type == ActionType.TALK:
                self.input_controller.tap_button(GameButton.A)
            elif action.action_type == ActionType.SEARCH:
                self.input_controller.tap_button(GameButton.A)
            elif action.action_type == ActionType.SEARCH:
                self.input_controller.tap_button(GameButton.A)
            elif action.action_type == ActionType.WAIT:
                self.input_controller.wait(action.duration)
            elif action.action_type == ActionType.PRESS_BUTTONS:
                buttons = action.parameters.get("buttons", [])
                if buttons:
                    # Convert string buttons to GameButton enum if needed
                    game_buttons = []
                    for b in buttons:
                        if isinstance(b, str):
                            # Map string to GameButton
                            btn_map = {
                                "A": GameButton.A, "B": GameButton.B,
                                "START": GameButton.START, "SELECT": GameButton.SELECT,
                                "UP": GameButton.UP, "DOWN": GameButton.DOWN,
                                "LEFT": GameButton.LEFT, "RIGHT": GameButton.RIGHT
                            }
                            if b.upper() in btn_map:
                                game_buttons.append(btn_map[b.upper()])
                        elif isinstance(b, GameButton):
                            game_buttons.append(b)
                    
                    if game_buttons:
                        # Create delays list based on duration
                        delays = [action.duration] * len(game_buttons)
                        self.input_controller.combo_move(game_buttons, delays)
            else:
                logger.warning(f"Unhandled action type: {action.action_type}")
                return False
            
            self.action_history.append((action, True))
            return True
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            self.action_history.append((action, False))
            return False

    def execute_action_sequence(self, actions: List[Action]) -> int:
        """
        Execute a sequence of actions.

        Args:
            actions: List of actions to execute

        Returns:
            Number of successfully executed actions
        """
        success_count = 0
        for action in actions:
            if self.execute_action(action):
                success_count += 1
            else:
                logger.warning("Action sequence interrupted due to failure")
                break
        return success_count

    def create_combat_sequence(self, enemy_direction: str) -> List[Action]:
        """
        Create a combat action sequence.

        Args:
            enemy_direction: Direction of enemy (up/down/left/right)

        Returns:
            List of combat actions
        """
        sequence = []
        
        # Face enemy
        direction_map = {
            "up": ActionType.MOVE_UP,
            "down": ActionType.MOVE_DOWN,
            "left": ActionType.MOVE_LEFT,
            "right": ActionType.MOVE_RIGHT,
        }
        
        if enemy_direction in direction_map:
            sequence.append(Action(
                action_type=direction_map[enemy_direction],
                duration=0.1
            ))
        
        # Attack
        sequence.append(Action(action_type=ActionType.ATTACK))
        
        # Small retreat
        retreat_map = {
            "up": ActionType.MOVE_DOWN,
            "down": ActionType.MOVE_UP,
            "left": ActionType.MOVE_RIGHT,
            "right": ActionType.MOVE_LEFT,
        }
        
        if enemy_direction in retreat_map:
            sequence.append(Action(
                action_type=retreat_map[enemy_direction],
                duration=0.15
            ))
        
        return sequence

    def create_exploration_sequence(self, direction: str, distance: int = 3) -> List[Action]:
        """
        Create an exploration movement sequence.

        Args:
            direction: Direction to explore
            distance: How many steps to take

        Returns:
            List of movement actions
        """
        direction_map = {
            "up": ActionType.MOVE_UP,
            "down": ActionType.MOVE_DOWN,
            "left": ActionType.MOVE_LEFT,
            "right": ActionType.MOVE_RIGHT,
        }
        
        if direction not in direction_map:
            return []
        
        sequence = []
        for _ in range(distance):
            sequence.append(Action(
                action_type=direction_map[direction],
                duration=0.3
            ))
            sequence.append(Action(action_type=ActionType.WAIT, duration=0.1))
        
        return sequence

    def create_item_collection_sequence(self, item_position: Tuple[int, int],
                                       player_position: Tuple[int, int]) -> List[Action]:
        """
        Create a sequence to move toward and collect an item.

        Args:
            item_position: (x, y) position of item
            player_position: (x, y) position of player

        Returns:
            List of actions to collect item
        """
        sequence = []
        
        dx = item_position[0] - player_position[0]
        dy = item_position[1] - player_position[1]
        
        # Move horizontally
        if abs(dx) > 10:
            direction = ActionType.MOVE_RIGHT if dx > 0 else ActionType.MOVE_LEFT
            steps = abs(dx) // 20
            for _ in range(min(steps, 5)):
                sequence.append(Action(action_type=direction, duration=0.2))
        
        # Move vertically
        if abs(dy) > 10:
            direction = ActionType.MOVE_DOWN if dy > 0 else ActionType.MOVE_UP
            steps = abs(dy) // 20
            for _ in range(min(steps, 5)):
                sequence.append(Action(action_type=direction, duration=0.2))
        
        return sequence

    def emergency_dodge(self, direction: str = "down") -> bool:
        """
        Execute an emergency dodge maneuver.

        Args:
            direction: Direction to dodge

        Returns:
            bool: True if successful
        """
        logger.warning("Executing emergency dodge!")
        dodge_sequence = self.create_exploration_sequence(direction, distance=2)
        return self.execute_action_sequence(dodge_sequence) > 0

    def get_action_history(self, num_recent: int = 10) -> List[Tuple[Action, bool]]:
        """
        Get recent action history.

        Args:
            num_recent: Number of recent actions to return

        Returns:
            List of (action, success) tuples
        """
        return self.action_history[-num_recent:]

    def clear_history(self) -> None:
        """Clear action history."""
        self.action_history.clear()
        logger.debug("Action history cleared")
