"""Combat AI for fighting enemies in Zelda."""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from loguru import logger


class EnemyType(Enum):
    """Known enemy types in Zelda ALTTP."""

    SOLDIER = "soldier"
    OCTOROK = "octorok"
    MOBLIN = "moblin"
    STALFOS = "stalfos"
    DARKNUT = "darknut"
    BOSS = "boss"
    UNKNOWN = "unknown"


class CombatAI:
    """AI system for combat strategies and enemy handling."""

    def __init__(self):
        """Initialize combat AI."""
        # Enemy patterns and strategies
        self.enemy_strategies = {
            EnemyType.SOLDIER: {
                "attack_pattern": "straight_line",
                "dodge_direction": "perpendicular",
                "weak_to": "sword",
                "strategy": "hit_and_run",
            },
            EnemyType.OCTOROK: {
                "attack_pattern": "projectile",
                "dodge_direction": "lateral",
                "weak_to": "shield",
                "strategy": "deflect_projectiles",
            },
            EnemyType.MOBLIN: {
                "attack_pattern": "charge",
                "dodge_direction": "backward",
                "weak_to": "arrows",
                "strategy": "kite_and_attack",
            },
            EnemyType.STALFOS: {
                "attack_pattern": "melee",
                "dodge_direction": "circular",
                "weak_to": "sword",
                "strategy": "combo_attacks",
            },
        }

        self.combat_stats = {
            "enemies_encountered": 0,
            "enemies_defeated": 0,
            "damage_taken": 0,
            "attacks_landed": 0,
        }

        logger.info("CombatAI initialized")

    def analyze_combat_situation(
        self, enemies: List[Dict[str, Any]], game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the combat situation.

        Args:
            enemies: List of detected enemies
            game_state: Current game state

        Returns:
            Analysis dictionary
        """
        hearts = game_state.get("hearts", {})
        current_hearts = hearts.get("current_hearts", 0)
        max_hearts = hearts.get("max_hearts", 1)
        health_percentage = (current_hearts / max_hearts) * 100 if max_hearts > 0 else 0

        num_enemies = len(enemies)

        # Determine threat level
        if num_enemies == 0:
            threat = "none"
        elif num_enemies == 1 and health_percentage > 50:
            threat = "low"
        elif num_enemies <= 2 and health_percentage > 30:
            threat = "moderate"
        else:
            threat = "high"

        # Recommend strategy
        if health_percentage < 25:
            recommendation = "retreat"
        elif threat == "high":
            recommendation = "defensive"
        elif threat == "moderate":
            recommendation = "balanced"
        else:
            recommendation = "aggressive"

        analysis = {
            "threat_level": threat,
            "num_enemies": num_enemies,
            "health_percentage": health_percentage,
            "recommended_strategy": recommendation,
            "can_engage": health_percentage > 20 and num_enemies <= 3,
        }

        logger.debug(f"Combat analysis: {analysis}")
        return analysis

    def get_combat_action(
        self,
        enemies: List[Dict[str, Any]],
        game_state: Dict[str, Any],
        link_position: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Decide combat action based on enemies and game state.

        Args:
            enemies: List of detected enemies
            game_state: Current game state
            link_position: Link's current position (x, y)

        Returns:
            Action dictionary
        """
        if not enemies:
            return {"action": "wait", "parameters": {"duration": 0.5}}

        analysis = self.analyze_combat_situation(enemies, game_state)

        if not analysis["can_engage"]:
            # Retreat if health is low or too many enemies
            return self._get_retreat_action(enemies, link_position)

        if analysis["recommended_strategy"] == "retreat":
            return self._get_retreat_action(enemies, link_position)
        elif analysis["recommended_strategy"] == "defensive":
            return self._get_defensive_action(enemies, link_position)
        elif analysis["recommended_strategy"] == "aggressive":
            return self._get_aggressive_action(enemies, link_position)
        else:
            return self._get_balanced_action(enemies, link_position)

    def _get_retreat_action(
        self, enemies: List[Dict[str, Any]], link_position: Optional[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """Get action to retreat from enemies."""
        if not enemies or not link_position:
            return {"action": "move", "parameters": {"direction": "down", "duration": 1.0}}

        # Move away from nearest enemy
        nearest_enemy = enemies[0]
        enemy_pos = nearest_enemy.get("center", (0, 0))

        # Calculate escape direction (opposite of enemy)
        dx = link_position[0] - enemy_pos[0]
        dy = link_position[1] - enemy_pos[1]

        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "down" if dy > 0 else "up"

        logger.debug(f"Retreating {direction} from enemy")
        return {"action": "move", "parameters": {"direction": direction, "duration": 1.0}}

    def _get_defensive_action(
        self, enemies: List[Dict[str, Any]], link_position: Optional[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """Get defensive combat action."""
        # Quick attack and dodge
        return {"action": "attack", "parameters": {}}

    def _get_aggressive_action(
        self, enemies: List[Dict[str, Any]], link_position: Optional[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """Get aggressive combat action."""
        # Charged attack for more damage
        return {"action": "attack", "parameters": {}}

    def _get_balanced_action(
        self, enemies: List[Dict[str, Any]], link_position: Optional[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """Get balanced combat action."""
        # Mix of attacks and positioning
        import random

        if random.random() < 0.7:
            return {"action": "attack", "parameters": {}}
        else:
            direction = random.choice(["up", "down", "left", "right"])
            return {"action": "move", "parameters": {"direction": direction, "duration": 0.3}}

    def identify_enemy_type(self, enemy: Dict[str, Any]) -> EnemyType:
        """
        Identify enemy type from visual features.

        Args:
            enemy: Enemy detection dictionary

        Returns:
            EnemyType enum
        """
        # This is a placeholder - would use ML/CV to identify
        # For now, return unknown
        return EnemyType.UNKNOWN

    def get_enemy_strategy(self, enemy_type: EnemyType) -> Dict[str, Any]:
        """
        Get combat strategy for specific enemy type.

        Args:
            enemy_type: Type of enemy

        Returns:
            Strategy dictionary
        """
        return self.enemy_strategies.get(enemy_type, {
            "attack_pattern": "unknown",
            "strategy": "cautious",
        })

    def should_use_item(self, game_state: Dict[str, Any], enemies: List[Dict[str, Any]]) -> bool:
        """
        Determine if Link should use a special item in combat.

        Args:
            game_state: Current game state
            enemies: List of enemies

        Returns:
            True if should use item
        """
        # Use items if:
        # 1. Many enemies (3+)
        # 2. Low health and items might help
        # 3. Specific enemy weaknesses

        if len(enemies) >= 3:
            return True

        hearts = game_state.get("hearts", {})
        health_percentage = (
            (hearts.get("current_hearts", 0) / hearts.get("max_hearts", 1)) * 100
            if hearts.get("max_hearts", 1) > 0
            else 0
        )

        if health_percentage < 30 and len(enemies) > 1:
            return True

        return False

    def update_combat_stats(
        self, enemies_defeated: int = 0, damage_taken: int = 0, attacks_landed: int = 0
    ):
        """
        Update combat statistics.

        Args:
            enemies_defeated: Number of enemies defeated
            damage_taken: Damage taken (in half-hearts)
            attacks_landed: Number of successful attacks
        """
        self.combat_stats["enemies_defeated"] += enemies_defeated
        self.combat_stats["damage_taken"] += damage_taken
        self.combat_stats["attacks_landed"] += attacks_landed

    def get_combat_stats(self) -> Dict[str, Any]:
        """Get combat statistics."""
        stats = self.combat_stats.copy()

        # Calculate efficiency
        if self.combat_stats["enemies_defeated"] > 0:
            stats["avg_damage_per_enemy"] = (
                self.combat_stats["damage_taken"] / self.combat_stats["enemies_defeated"]
            )
        else:
            stats["avg_damage_per_enemy"] = 0

        return stats

    def reset_stats(self):
        """Reset combat statistics."""
        self.combat_stats = {
            "enemies_encountered": 0,
            "enemies_defeated": 0,
            "damage_taken": 0,
            "attacks_landed": 0,
        }
        logger.info("Combat stats reset")
