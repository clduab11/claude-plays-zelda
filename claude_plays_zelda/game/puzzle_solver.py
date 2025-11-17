"""Puzzle solving logic for Zelda dungeons."""

from typing import Dict, Any, List, Optional
from enum import Enum
from loguru import logger


class PuzzleType(Enum):
    """Types of puzzles in Zelda ALTTP."""

    BLOCK_PUSHING = "block_pushing"
    SWITCH_ACTIVATION = "switch_activation"
    TORCH_LIGHTING = "torch_lighting"
    ENEMY_SEQUENCE = "enemy_sequence"
    KEY_AND_DOOR = "key_and_door"
    FLOOR_SWITCH = "floor_switch"
    CRYSTAL_SWITCH = "crystal_switch"
    UNKNOWN = "unknown"


class PuzzleSolver:
    """Solves puzzles in Zelda dungeons."""

    def __init__(self):
        """Initialize puzzle solver."""
        self.solved_puzzles: List[str] = []
        self.puzzle_attempts: Dict[str, int] = {}

        # Puzzle solution templates
        self.puzzle_templates = {
            PuzzleType.BLOCK_PUSHING: {
                "indicators": ["movable_blocks", "pressure_plates"],
                "strategy": "push_blocks_to_switches",
                "typical_solution": [
                    {"action": "move", "direction": "up"},
                    {"action": "push_block"},
                    {"action": "move", "direction": "down"},
                ],
            },
            PuzzleType.TORCH_LIGHTING: {
                "indicators": ["unlit_torches", "fire_source"],
                "strategy": "light_all_torches",
                "required_item": "lantern",
            },
            PuzzleType.SWITCH_ACTIVATION: {
                "indicators": ["switches", "locked_door"],
                "strategy": "activate_all_switches",
            },
        }

        logger.info("PuzzleSolver initialized")

    def identify_puzzle(self, observations: Dict[str, Any]) -> PuzzleType:
        """
        Identify the type of puzzle in the current room.

        Args:
            observations: Visual observations of the room

        Returns:
            PuzzleType enum
        """
        # This is simplified - would use computer vision to detect puzzle elements
        # For now, return unknown
        return PuzzleType.UNKNOWN

    def analyze_puzzle(
        self, puzzle_type: PuzzleType, observations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a puzzle and determine solution approach.

        Args:
            puzzle_type: Type of puzzle
            observations: Visual observations

        Returns:
            Analysis dictionary with solution approach
        """
        template = self.puzzle_templates.get(puzzle_type, {})

        analysis = {
            "puzzle_type": puzzle_type.value,
            "strategy": template.get("strategy", "unknown"),
            "required_item": template.get("required_item"),
            "difficulty": self._estimate_difficulty(puzzle_type, observations),
        }

        logger.debug(f"Puzzle analysis: {analysis}")
        return analysis

    def _estimate_difficulty(
        self, puzzle_type: PuzzleType, observations: Dict[str, Any]
    ) -> str:
        """Estimate puzzle difficulty."""
        # Simplified difficulty estimation
        if puzzle_type == PuzzleType.BLOCK_PUSHING:
            # More blocks = harder
            return "medium"
        elif puzzle_type == PuzzleType.TORCH_LIGHTING:
            return "easy"
        else:
            return "medium"

    def get_puzzle_solution_steps(
        self, puzzle_type: PuzzleType, observations: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get step-by-step solution for a puzzle.

        Args:
            puzzle_type: Type of puzzle
            observations: Visual observations

        Returns:
            List of action steps
        """
        if puzzle_type == PuzzleType.BLOCK_PUSHING:
            return self._solve_block_puzzle(observations)
        elif puzzle_type == PuzzleType.TORCH_LIGHTING:
            return self._solve_torch_puzzle(observations)
        elif puzzle_type == PuzzleType.SWITCH_ACTIVATION:
            return self._solve_switch_puzzle(observations)
        else:
            return self._solve_generic_puzzle(observations)

    def _solve_block_puzzle(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Solve block pushing puzzle."""
        # Simplified - would analyze block positions and switches
        return [
            {"action": "move", "parameters": {"direction": "up", "duration": 1.0}},
            {"action": "move", "parameters": {"direction": "right", "duration": 1.0}},
            {"action": "wait", "parameters": {"duration": 0.5}},
        ]

    def _solve_torch_puzzle(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Solve torch lighting puzzle."""
        # Need to light all torches
        return [
            {"action": "use_item", "parameters": {}},  # Use lantern
            {"action": "move", "parameters": {"direction": "up", "duration": 1.0}},
            {"action": "use_item", "parameters": {}},
            {"action": "move", "parameters": {"direction": "down", "duration": 1.0}},
        ]

    def _solve_switch_puzzle(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Solve switch activation puzzle."""
        return [
            {"action": "move", "parameters": {"direction": "up", "duration": 1.0}},
            {"action": "attack", "parameters": {"charge": False}},  # Hit switch
            {"action": "move", "parameters": {"direction": "left", "duration": 1.0}},
        ]

    def _solve_generic_puzzle(self, observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generic puzzle solving approach."""
        return [
            {"action": "wait", "parameters": {"duration": 1.0}},  # Observe
            {"action": "move", "parameters": {"direction": "up", "duration": 1.0}},  # Explore
        ]

    def record_puzzle_attempt(self, puzzle_id: str, success: bool):
        """
        Record an attempt at solving a puzzle.

        Args:
            puzzle_id: Unique identifier for the puzzle
            success: Whether the attempt was successful
        """
        if puzzle_id not in self.puzzle_attempts:
            self.puzzle_attempts[puzzle_id] = 0

        self.puzzle_attempts[puzzle_id] += 1

        if success:
            if puzzle_id not in self.solved_puzzles:
                self.solved_puzzles.append(puzzle_id)
                logger.info(f"Puzzle solved: {puzzle_id}")

    def is_puzzle_solved(self, puzzle_id: str) -> bool:
        """Check if a puzzle has been solved."""
        return puzzle_id in self.solved_puzzles

    def get_puzzle_hints(self, puzzle_type: PuzzleType) -> List[str]:
        """
        Get hints for solving a puzzle type.

        Args:
            puzzle_type: Type of puzzle

        Returns:
            List of hint strings
        """
        hints = {
            PuzzleType.BLOCK_PUSHING: [
                "Look for pressure plates on the floor",
                "Blocks can only be pushed, not pulled",
                "Some blocks may need to be pushed onto switches",
            ],
            PuzzleType.TORCH_LIGHTING: [
                "You need the lantern to light torches",
                "Light all torches in the room to open doors",
                "Torches may have a time limit",
            ],
            PuzzleType.SWITCH_ACTIVATION: [
                "Hit switches with your sword",
                "Some switches require standing on them",
                "Crystal switches change the state of blocks",
            ],
            PuzzleType.KEY_AND_DOOR: [
                "Small keys open locked doors",
                "Big keys are needed for special doors",
                "Look for keys in chests and from enemies",
            ],
        }

        return hints.get(puzzle_type, ["Explore carefully and observe patterns"])

    def should_use_hint(self, puzzle_id: str) -> bool:
        """
        Determine if a hint should be used.

        Args:
            puzzle_id: Puzzle identifier

        Returns:
            True if hint should be used (after multiple failed attempts)
        """
        attempts = self.puzzle_attempts.get(puzzle_id, 0)
        return attempts >= 3 and puzzle_id not in self.solved_puzzles

    def reset_puzzle_state(self):
        """Reset puzzle solving state."""
        self.solved_puzzles.clear()
        self.puzzle_attempts.clear()
        logger.info("Puzzle state reset")

    def get_puzzle_statistics(self) -> Dict[str, Any]:
        """Get puzzle solving statistics."""
        return {
            "puzzles_solved": len(self.solved_puzzles),
            "total_attempts": sum(self.puzzle_attempts.values()),
            "unique_puzzles_attempted": len(self.puzzle_attempts),
        }
