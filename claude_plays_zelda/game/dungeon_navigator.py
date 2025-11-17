"""Dungeon navigation system for exploring dungeons and finding objectives."""

from typing import Dict, Any, List, Optional, Set, Tuple
from collections import deque
from loguru import logger


class DungeonNavigator:
    """Handles dungeon exploration and navigation."""

    def __init__(self):
        """Initialize dungeon navigator."""
        self.visited_rooms: Set[str] = set()
        self.room_connections: Dict[str, List[str]] = {}
        self.objective_locations: Dict[str, str] = {}  # objective -> room_id
        self.current_dungeon: Optional[str] = None
        self.dungeon_progress: Dict[str, Any] = {}

        # Common dungeon elements
        self.dungeon_knowledge = {
            "boss_indicators": ["large_door", "dark_room", "stairs_down"],
            "treasure_indicators": ["chest", "small_key", "big_key"],
            "puzzle_indicators": ["blocks", "switches", "torches"],
        }

        logger.info("DungeonNavigator initialized")

    def enter_dungeon(self, dungeon_name: str):
        """
        Mark entrance into a dungeon.

        Args:
            dungeon_name: Name of the dungeon
        """
        self.current_dungeon = dungeon_name
        self.visited_rooms.clear()
        self.room_connections.clear()

        self.dungeon_progress[dungeon_name] = {
            "entered": True,
            "rooms_explored": 0,
            "keys_collected": 0,
            "boss_defeated": False,
        }

        logger.info(f"Entered dungeon: {dungeon_name}")

    def exit_dungeon(self):
        """Mark exit from current dungeon."""
        if self.current_dungeon:
            logger.info(f"Exited dungeon: {self.current_dungeon}")
            self.current_dungeon = None

    def record_room(self, room_id: str, room_data: Dict[str, Any]):
        """
        Record information about a room.

        Args:
            room_id: Unique identifier for the room
            room_data: Data about the room (enemies, items, exits, etc.)
        """
        if room_id not in self.visited_rooms:
            self.visited_rooms.add(room_id)
            if self.current_dungeon:
                self.dungeon_progress[self.current_dungeon]["rooms_explored"] += 1
            logger.debug(f"New room recorded: {room_id}")

        # Record exits
        exits = room_data.get("exits", [])
        if exits:
            self.room_connections[room_id] = exits

    def get_exploration_target(self, current_room: str) -> Optional[str]:
        """
        Get the next room to explore.

        Args:
            current_room: Current room ID

        Returns:
            Target room ID or None
        """
        # Find unexplored connected rooms
        if current_room in self.room_connections:
            for connected_room in self.room_connections[current_room]:
                if connected_room not in self.visited_rooms:
                    logger.debug(f"Exploration target: {connected_room}")
                    return connected_room

        # Find any unexplored room
        all_known_rooms = set(self.room_connections.keys())
        unexplored = all_known_rooms - self.visited_rooms

        if unexplored:
            return list(unexplored)[0]

        return None

    def suggest_navigation_action(
        self,
        current_state: Dict[str, Any],
        observations: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Suggest a navigation action based on current situation.

        Args:
            current_state: Current game state
            observations: Visual observations

        Returns:
            Suggested action dictionary
        """
        doors = observations.get("doors", [])
        items = observations.get("items", [])
        enemies = observations.get("enemies", [])

        # Priority 1: Collect nearby items
        if items:
            logger.debug("Suggesting to collect item")
            return {"action": "move", "parameters": {"direction": "up", "duration": 1.0, "run": True}}

        # Priority 2: Clear enemies if blocking progress
        if enemies and len(enemies) <= 2:
            logger.debug("Suggesting combat to clear path")
            return {"action": "attack", "parameters": {"charge": False}}

        # Priority 3: Explore through doors
        if doors:
            # Choose unexplored door if possible
            door = doors[0]
            center = door.get("center", (0, 0))

            # Determine direction to door
            # Simplified - would calculate actual direction
            logger.debug("Suggesting to explore through door")
            return {"action": "move", "parameters": {"direction": "up", "duration": 2.0, "run": False}}

        # Priority 4: Search for doors
        import random
        direction = random.choice(["up", "down", "left", "right"])
        logger.debug(f"Suggesting exploratory movement: {direction}")
        return {"action": "move", "parameters": {"direction": direction, "duration": 1.5, "run": False}}

    def is_likely_boss_room(self, room_data: Dict[str, Any]) -> bool:
        """
        Determine if a room is likely a boss room.

        Args:
            room_data: Room data including visual observations

        Returns:
            True if likely boss room
        """
        # Boss rooms typically have:
        # 1. Large single enemy
        # 2. Unique room layout
        # 3. No regular enemies

        enemies = room_data.get("enemies", [])

        if len(enemies) == 1:
            enemy = enemies[0]
            area = enemy.get("area", 0)
            # Boss enemies are typically much larger
            if area > 500:
                return True

        return False

    def is_puzzle_room(self, room_data: Dict[str, Any]) -> bool:
        """
        Determine if a room contains a puzzle.

        Args:
            room_data: Room data

        Returns:
            True if likely puzzle room
        """
        # Puzzle indicators:
        # - Multiple similar objects (blocks, switches)
        # - No immediate exits visible
        # - Specific patterns

        # This is simplified - would use CV to detect puzzle elements
        return False

    def get_dungeon_progress(self, dungeon_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get progress information for a dungeon.

        Args:
            dungeon_name: Dungeon name (None = current)

        Returns:
            Progress dictionary
        """
        name = dungeon_name or self.current_dungeon
        if name and name in self.dungeon_progress:
            return self.dungeon_progress[name]
        return {}

    def mark_objective_complete(self, objective: str):
        """
        Mark an objective as complete.

        Args:
            objective: Objective identifier
        """
        if self.current_dungeon:
            if objective == "boss":
                self.dungeon_progress[self.current_dungeon]["boss_defeated"] = True
            elif objective == "key":
                self.dungeon_progress[self.current_dungeon]["keys_collected"] += 1

            logger.info(f"Objective complete: {objective}")

    def get_dungeon_map_coverage(self) -> float:
        """
        Get estimated dungeon map coverage percentage.

        Returns:
            Coverage percentage (0-100)
        """
        if not self.room_connections:
            return 0.0

        # Estimate based on visited vs total known rooms
        total_known = len(self.room_connections)
        visited = len(self.visited_rooms)

        if total_known == 0:
            return 0.0

        return (visited / total_known) * 100

    def suggest_backtrack(self) -> bool:
        """
        Suggest whether to backtrack to explore missed areas.

        Returns:
            True if should backtrack
        """
        # Backtrack if:
        # 1. All current paths explored
        # 2. Known unexplored rooms exist
        # 3. Not made progress in a while

        unexplored = set(self.room_connections.keys()) - self.visited_rooms
        return len(unexplored) > 0

    def find_path_to_objective(self, objective: str) -> Optional[List[str]]:
        """
        Find path to a specific objective.

        Args:
            objective: Objective identifier

        Returns:
            List of room IDs to reach objective, or None
        """
        if objective not in self.objective_locations:
            return None

        target_room = self.objective_locations[objective]

        # Use BFS to find path
        # Simplified - would need current room parameter
        return None

    def reset(self):
        """Reset navigation state."""
        self.visited_rooms.clear()
        self.room_connections.clear()
        self.current_dungeon = None
        logger.info("Dungeon navigation state reset")
