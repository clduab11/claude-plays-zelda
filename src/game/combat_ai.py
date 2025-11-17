"""Combat AI for fighting enemies strategically."""

from typing import List, Optional, Tuple
from enum import Enum
from loguru import logger

from ..cv.object_detector import DetectedObject, ObjectType
from ..cv.game_state_analyzer import GameState


class CombatStrategy(Enum):
    """Combat strategy types."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    BALANCED = "balanced"
    RANGED = "ranged"


class CombatAI:
    """AI system for combat decisions."""

    def __init__(self, aggressive_mode: bool = False, dodge_priority: str = "high"):
        """
        Initialize combat AI.

        Args:
            aggressive_mode: Whether to prioritize offense
            dodge_priority: Priority for dodging (low/medium/high)
        """
        self.aggressive_mode = aggressive_mode
        self.dodge_priority = dodge_priority
        self.current_strategy = CombatStrategy.BALANCED
        
        # Dodge thresholds based on priority
        self.dodge_thresholds = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7,
        }

    def analyze_combat_situation(self, game_state: GameState) -> dict:
        """
        Analyze the combat situation.

        Args:
            game_state: Current game state

        Returns:
            Dictionary with combat analysis
        """
        analysis = {
            "threat_level": 0.0,
            "recommended_action": "none",
            "priority_target": None,
            "should_dodge": False,
            "safe_to_engage": True,
        }
        
        if not game_state.enemies_visible:
            return analysis
        
        # Calculate threat level
        num_enemies = len(game_state.enemies_visible)
        health_ratio = game_state.health / max(game_state.max_health, 1)
        
        threat_level = min(1.0, (num_enemies * 0.3) + (1.0 - health_ratio) * 0.5)
        analysis["threat_level"] = threat_level
        
        # Check if we should dodge
        dodge_threshold = self.dodge_thresholds.get(self.dodge_priority, 0.5)
        analysis["should_dodge"] = threat_level > dodge_threshold and health_ratio < 0.5
        
        # Find priority target
        if game_state.player_position:
            priority_target = self._find_priority_target(
                game_state.enemies_visible,
                game_state.player_position
            )
            analysis["priority_target"] = priority_target
        
        # Determine if safe to engage
        analysis["safe_to_engage"] = health_ratio > 0.3 and num_enemies <= 3
        
        # Recommend action
        analysis["recommended_action"] = self._recommend_combat_action(analysis, game_state)
        
        return analysis

    def _find_priority_target(self, enemies: List[DetectedObject],
                             player_position: Tuple[int, int]) -> Optional[DetectedObject]:
        """
        Find the priority target to attack.

        Args:
            enemies: List of visible enemies
            player_position: Player's position

        Returns:
            Priority enemy or None
        """
        if not enemies:
            return None
        
        # Find closest enemy
        min_distance = float('inf')
        closest = None
        
        for enemy in enemies:
            dx = enemy.position[0] - player_position[0]
            dy = enemy.position[1] - player_position[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest = enemy
        
        return closest

    def _recommend_combat_action(self, analysis: dict, game_state: GameState) -> str:
        """
        Recommend a combat action.

        Args:
            analysis: Combat analysis
            game_state: Current game state

        Returns:
            Action recommendation
        """
        # Check if we should dodge
        if analysis["should_dodge"]:
            return "dodge"
        
        # If low health, try to collect hearts
        health_ratio = game_state.health / max(game_state.max_health, 1)
        if health_ratio < 0.3 and game_state.items_visible:
            hearts = [item for item in game_state.items_visible 
                     if item.object_type == ObjectType.HEART]
            if hearts:
                return "collect_heart"
        
        # If no enemies, explore
        if not game_state.enemies_visible:
            return "explore"
        
        # If safe to engage, attack
        if analysis["safe_to_engage"]:
            if analysis["priority_target"]:
                return "attack_target"
            return "attack"
        
        # If not safe, retreat
        return "retreat"

    def get_attack_direction(self, player_position: Tuple[int, int],
                           target_position: Tuple[int, int]) -> str:
        """
        Get the direction to attack a target.

        Args:
            player_position: Player's position
            target_position: Target's position

        Returns:
            Direction string (up/down/left/right)
        """
        dx = target_position[0] - player_position[0]
        dy = target_position[1] - player_position[1]
        
        # Determine primary direction
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    def get_retreat_direction(self, player_position: Tuple[int, int],
                            enemies: List[DetectedObject]) -> str:
        """
        Get the best direction to retreat from enemies.

        Args:
            player_position: Player's position
            enemies: List of enemies

        Returns:
            Direction string
        """
        if not enemies:
            return "down"
        
        # Calculate average enemy position
        avg_x = sum(e.position[0] for e in enemies) / len(enemies)
        avg_y = sum(e.position[1] for e in enemies) / len(enemies)
        
        # Move away from average enemy position
        dx = player_position[0] - avg_x
        dy = player_position[1] - avg_y
        
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    def should_use_item(self, game_state: GameState) -> bool:
        """
        Determine if we should use an item (bomb, arrow, etc.).

        Args:
            game_state: Current game state

        Returns:
            bool: True if should use item
        """
        # Use items if many enemies or low health
        num_enemies = len(game_state.enemies_visible)
        health_ratio = game_state.health / max(game_state.max_health, 1)
        
        # Use items if surrounded
        if num_enemies >= 4:
            return game_state.bombs > 0
        
        # Use items if low health and need to clear room quickly
        if health_ratio < 0.4 and num_enemies >= 2:
            return game_state.arrows > 0 or game_state.bombs > 0
        
        return False

    def calculate_damage_risk(self, player_position: Tuple[int, int],
                             enemies: List[DetectedObject]) -> float:
        """
        Calculate risk of taking damage.

        Args:
            player_position: Player's position
            enemies: List of enemies

        Returns:
            Risk level (0-1)
        """
        if not enemies:
            return 0.0
        
        risk = 0.0
        for enemy in enemies:
            dx = enemy.position[0] - player_position[0]
            dy = enemy.position[1] - player_position[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            # Closer enemies = higher risk
            if distance < 50:
                risk += 0.4
            elif distance < 100:
                risk += 0.2
            else:
                risk += 0.1
        
        return min(1.0, risk)

    def set_strategy(self, strategy: CombatStrategy) -> None:
        """
        Set the combat strategy.

        Args:
            strategy: Combat strategy to use
        """
        self.current_strategy = strategy
        logger.info(f"Combat strategy set to: {strategy.value}")

    def is_boss_fight(self, game_state: GameState) -> bool:
        """
        Detect if currently in a boss fight.

        Args:
            game_state: Current game state

        Returns:
            bool: True if boss fight detected
        """
        # Boss fights typically have specific characteristics
        # - One large enemy
        # - Specific room layouts
        # - Cannot leave room
        
        if not game_state.enemies_visible:
            return False
        
        # Check for large enemy (boss)
        for enemy in game_state.enemies_visible:
            x, y, w, h = enemy.bounding_box
            area = w * h
            if area > 2000:  # Large enemy
                return True
        
        return False
