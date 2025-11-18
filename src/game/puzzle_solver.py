"""Puzzle solving logic for Zelda puzzles."""

from typing import List, Optional, Dict, Tuple
from enum import Enum
from loguru import logger

from ..cv.game_state_analyzer import GameState


class PuzzleType(Enum):
    """Types of puzzles in Zelda."""
    SWITCH = "switch"
    BLOCK_PUSH = "block_push"
    TORCH = "torch"
    KEY_DOOR = "key_door"
    PATTERN = "pattern"
    SEQUENCE = "sequence"
    UNKNOWN = "unknown"


class PuzzleSolver:
    """AI system for solving Zelda puzzles."""

    def __init__(self):
        """Initialize the puzzle solver."""
        self.active_puzzle: Optional[PuzzleType] = None
        self.puzzle_attempts: Dict[str, int] = {}
        self.solved_puzzles: List[str] = []

    def identify_puzzle(self, game_state: GameState) -> Optional[PuzzleType]:
        """
        Identify the type of puzzle in current room.

        Args:
            game_state: Current game state

        Returns:
            Puzzle type or None
        """
        # Placeholder implementation
        # Real implementation would use computer vision to detect puzzle elements
        
        # Check for switches (typically on floor or walls)
        # Check for movable blocks
        # Check for torches
        # Check for locked doors
        
        return None

    def solve_switch_puzzle(self, game_state: GameState) -> List[str]:
        """
        Solve a switch/pressure plate puzzle.

        Args:
            game_state: Current game state

        Returns:
            List of actions to solve puzzle
        """
        actions = []
        
        # Strategy: Find all switches and activate them
        # 1. Search the room systematically
        actions.extend(["search", "move_up", "search", "move_right", "search"])
        
        # 2. When switch found, activate it
        actions.append("attack")  # Many switches are activated by attacking
        
        logger.info("Attempting switch puzzle solution")
        return actions

    def solve_block_push_puzzle(self, game_state: GameState) -> List[str]:
        """
        Solve a block pushing puzzle.

        Args:
            game_state: Current game state

        Returns:
            List of actions to solve puzzle
        """
        actions = []
        
        # Strategy: Find blocks and push them to correct positions
        # This typically requires trial and error
        
        # 1. Find movable blocks (they usually look different)
        # 2. Push blocks in different directions to find solution
        actions.extend([
            "move_up", "move_up",  # Get to block
            "move_down", "move_down",  # Push block down
        ])
        
        logger.info("Attempting block push puzzle solution")
        return actions

    def solve_torch_puzzle(self, game_state: GameState) -> List[str]:
        """
        Solve a torch lighting puzzle.

        Args:
            game_state: Current game state

        Returns:
            List of actions to solve puzzle
        """
        actions = []
        
        # Strategy: Light all torches in the room
        # Usually requires lamp or fire arrows
        
        # 1. Find all torches
        # 2. Light each one
        actions.extend([
            "use_item",  # Use lamp/fire arrows
            "move_up",
            "use_item",
            "move_right",
            "use_item",
        ])
        
        logger.info("Attempting torch puzzle solution")
        return actions

    def solve_key_door_puzzle(self, game_state: GameState) -> List[str]:
        """
        Solve a locked door puzzle (find key).

        Args:
            game_state: Current game state

        Returns:
            List of actions to solve puzzle
        """
        actions = []
        
        # Strategy: Find the key in the room
        if game_state.keys > 0:
            # Already have key, go to door
            actions.extend(["move_up", "move_up", "move_up"])
        else:
            # Need to find key - search room
            actions.extend([
                "search", "move_left", "search",
                "move_down", "search", "move_right", "search"
            ])
        
        logger.info("Attempting key door puzzle solution")
        return actions

    def solve_pattern_puzzle(self, pattern: List[str]) -> List[str]:
        """
        Solve a pattern-based puzzle.

        Args:
            pattern: The pattern to follow

        Returns:
            List of actions matching the pattern
        """
        actions = []
        
        # Pattern puzzles often require specific sequence of switches/torches
        # or walking in specific pattern
        
        for step in pattern:
            if step in ["up", "down", "left", "right"]:
                actions.append(f"move_{step}")
            elif step == "attack":
                actions.append("attack")
            elif step == "item":
                actions.append("use_item")
        
        logger.info(f"Solving pattern puzzle: {pattern}")
        return actions

    def solve_sequence_puzzle(self, game_state: GameState) -> List[str]:
        """
        Solve a sequence/timing puzzle.

        Args:
            game_state: Current game state

        Returns:
            List of actions to solve puzzle
        """
        actions = []
        
        # Sequence puzzles require actions in specific order or timing
        # Example: hitting switches in specific order
        
        actions.extend([
            "attack",  # First switch
            "move_right", "move_right",
            "attack",  # Second switch
            "move_up", "move_up",
            "attack",  # Third switch
        ])
        
        logger.info("Attempting sequence puzzle solution")
        return actions

    def get_puzzle_hints(self, puzzle_type: PuzzleType) -> str:
        """
        Get hints for a puzzle type.

        Args:
            puzzle_type: Type of puzzle

        Returns:
            Hint string
        """
        hints = {
            PuzzleType.SWITCH: "Look for switches on the floor or walls. Try attacking or standing on them.",
            PuzzleType.BLOCK_PUSH: "Find movable blocks and push them onto pressure plates or into specific positions.",
            PuzzleType.TORCH: "Light all torches in the room. You may need the lamp or fire arrows.",
            PuzzleType.KEY_DOOR: "Search the room thoroughly for a key. Check chests, defeat enemies, or solve other puzzles.",
            PuzzleType.PATTERN: "Follow the pattern shown. It might be visual cues or sounds.",
            PuzzleType.SEQUENCE: "Perform actions in the correct order. Pay attention to clues in the environment.",
        }
        
        return hints.get(puzzle_type, "Explore the room and interact with objects.")

    def record_attempt(self, puzzle_id: str) -> None:
        """
        Record a puzzle attempt.

        Args:
            puzzle_id: Identifier for the puzzle
        """
        self.puzzle_attempts[puzzle_id] = self.puzzle_attempts.get(puzzle_id, 0) + 1
        logger.debug(f"Puzzle {puzzle_id} attempts: {self.puzzle_attempts[puzzle_id]}")

    def mark_solved(self, puzzle_id: str) -> None:
        """
        Mark a puzzle as solved.

        Args:
            puzzle_id: Identifier for the puzzle
        """
        if puzzle_id not in self.solved_puzzles:
            self.solved_puzzles.append(puzzle_id)
            logger.info(f"Puzzle solved: {puzzle_id}")

    def is_solved(self, puzzle_id: str) -> bool:
        """
        Check if a puzzle has been solved.

        Args:
            puzzle_id: Identifier for the puzzle

        Returns:
            bool: True if solved
        """
        return puzzle_id in self.solved_puzzles

    def should_give_up(self, puzzle_id: str, max_attempts: int = 10) -> bool:
        """
        Determine if we should give up on a puzzle.

        Args:
            puzzle_id: Identifier for the puzzle
            max_attempts: Maximum attempts before giving up

        Returns:
            bool: True if should give up
        """
        attempts = self.puzzle_attempts.get(puzzle_id, 0)
        return attempts >= max_attempts

    def get_generic_solution(self, game_state: GameState) -> List[str]:
        """
        Get a generic puzzle-solving approach.

        Args:
            game_state: Current game state

        Returns:
            List of actions to try
        """
        # Generic approach: systematic exploration and interaction
        actions = [
            "search",
            "move_up", "search",
            "move_right", "search",
            "move_down", "search",
            "move_left", "search",
            "attack",  # Try attacking
            "use_item",  # Try using equipped item
        ]
        
        return actions

    def analyze_puzzle_progress(self, prev_state: GameState, 
                               curr_state: GameState) -> bool:
        """
        Analyze if puzzle progress has been made.

        Args:
            prev_state: Previous game state
            curr_state: Current game state

        Returns:
            bool: True if progress detected
        """
        # Check for changes that indicate puzzle progress:
        # - Door opened
        # - New area accessible
        # - Item obtained
        # - Enemy defeated
        # - Visual changes
        
        # Simple heuristic: check if location changed
        if prev_state.location and curr_state.location:
            if prev_state.location != curr_state.location:
                return True
        
        # Check if items changed
        if prev_state.items_visible != curr_state.items_visible:
            return True
        
        return False
