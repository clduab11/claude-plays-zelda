"""Memory system for storing game progress and learned information."""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class MemoryItem:
    """Represents a single memory item."""
    key: str
    value: Any
    category: str
    importance: int = 1
    timestamp: float = 0.0


class MemorySystem:
    """Manages long-term memory for the AI agent."""

    def __init__(self, persistence_file: str = "agent_memory.json"):
        """
        Initialize the memory system.

        Args:
            persistence_file: File to save/load memory
        """
        self.persistence_file = persistence_file
        self.memories: Dict[str, MemoryItem] = {}
        self.locations_visited: set = set()
        self.items_collected: List[str] = []
        self.enemies_defeated: Dict[str, int] = {}
        self.puzzles_solved: List[str] = []
        self.deaths: int = 0
        self.play_time: float = 0.0

    def store(self, key: str, value: Any, category: str = "general", 
              importance: int = 1, timestamp: float = 0.0) -> None:
        """
        Store a memory.

        Args:
            key: Memory key
            value: Memory value
            category: Memory category
            importance: Importance level (1-5)
            timestamp: Time of memory
        """
        memory = MemoryItem(
            key=key,
            value=value,
            category=category,
            importance=importance,
            timestamp=timestamp
        )
        self.memories[key] = memory
        logger.debug(f"Stored memory: {key} = {value}")

    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a memory by key.

        Args:
            key: Memory key

        Returns:
            Memory value or None
        """
        memory = self.memories.get(key)
        return memory.value if memory else None

    def retrieve_by_category(self, category: str) -> List[MemoryItem]:
        """
        Retrieve all memories in a category.

        Args:
            category: Category name

        Returns:
            List of memories in category
        """
        return [m for m in self.memories.values() if m.category == category]

    def has_visited(self, location: str) -> bool:
        """
        Check if a location has been visited.

        Args:
            location: Location identifier

        Returns:
            bool: True if visited
        """
        return location in self.locations_visited

    def mark_visited(self, location: str) -> None:
        """
        Mark a location as visited.

        Args:
            location: Location identifier
        """
        if location not in self.locations_visited:
            self.locations_visited.add(location)
            logger.info(f"New location visited: {location}")

    def add_item(self, item: str) -> None:
        """
        Record collecting an item.

        Args:
            item: Item name
        """
        self.items_collected.append(item)
        logger.info(f"Item collected: {item}")

    def has_item(self, item: str) -> bool:
        """
        Check if an item has been collected.

        Args:
            item: Item name

        Returns:
            bool: True if item collected
        """
        return item in self.items_collected

    def defeat_enemy(self, enemy_type: str) -> None:
        """
        Record defeating an enemy.

        Args:
            enemy_type: Type of enemy
        """
        self.enemies_defeated[enemy_type] = self.enemies_defeated.get(enemy_type, 0) + 1
        logger.debug(f"Enemy defeated: {enemy_type}")

    def get_enemy_defeats(self, enemy_type: str) -> int:
        """
        Get number of times an enemy type has been defeated.

        Args:
            enemy_type: Type of enemy

        Returns:
            Number of defeats
        """
        return self.enemies_defeated.get(enemy_type, 0)

    def solve_puzzle(self, puzzle_id: str) -> None:
        """
        Record solving a puzzle.

        Args:
            puzzle_id: Puzzle identifier
        """
        if puzzle_id not in self.puzzles_solved:
            self.puzzles_solved.append(puzzle_id)
            logger.info(f"Puzzle solved: {puzzle_id}")

    def is_puzzle_solved(self, puzzle_id: str) -> bool:
        """
        Check if a puzzle has been solved.

        Args:
            puzzle_id: Puzzle identifier

        Returns:
            bool: True if solved
        """
        return puzzle_id in self.puzzles_solved

    def record_death(self) -> None:
        """Record a death."""
        self.deaths += 1
        logger.warning(f"Death recorded. Total deaths: {self.deaths}")

    def update_play_time(self, duration: float) -> None:
        """
        Update total play time.

        Args:
            duration: Time to add (seconds)
        """
        self.play_time += duration

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_memories": len(self.memories),
            "locations_visited": len(self.locations_visited),
            "items_collected": len(self.items_collected),
            "unique_enemies_defeated": len(self.enemies_defeated),
            "total_enemy_defeats": sum(self.enemies_defeated.values()),
            "puzzles_solved": len(self.puzzles_solved),
            "deaths": self.deaths,
            "play_time_hours": self.play_time / 3600,
        }

    def get_summary(self) -> str:
        """
        Get a summary of game progress.

        Returns:
            Summary string
        """
        stats = self.get_statistics()
        
        summary = [
            "Game Progress Summary:",
            f"- Locations visited: {stats['locations_visited']}",
            f"- Items collected: {stats['items_collected']}",
            f"- Enemies defeated: {stats['total_enemy_defeats']}",
            f"- Puzzles solved: {stats['puzzles_solved']}",
            f"- Deaths: {stats['deaths']}",
            f"- Play time: {stats['play_time_hours']:.2f} hours",
        ]
        
        return "\n".join(summary)

    def save(self) -> bool:
        """
        Save memory to file.

        Returns:
            bool: True if saved successfully
        """
        try:
            data = {
                "memories": {k: asdict(v) for k, v in self.memories.items()},
                "locations_visited": list(self.locations_visited),
                "items_collected": self.items_collected,
                "enemies_defeated": self.enemies_defeated,
                "puzzles_solved": self.puzzles_solved,
                "deaths": self.deaths,
                "play_time": self.play_time,
            }
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Memory saved to {self.persistence_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return False

    def load(self) -> bool:
        """
        Load memory from file.

        Returns:
            bool: True if loaded successfully
        """
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
            
            # Load memories
            self.memories.clear()
            for key, mem_dict in data.get("memories", {}).items():
                self.memories[key] = MemoryItem(**mem_dict)
            
            # Load other data
            self.locations_visited = set(data.get("locations_visited", []))
            self.items_collected = data.get("items_collected", [])
            self.enemies_defeated = data.get("enemies_defeated", {})
            self.puzzles_solved = data.get("puzzles_solved", [])
            self.deaths = data.get("deaths", 0)
            self.play_time = data.get("play_time", 0.0)
            
            logger.info(f"Memory loaded from {self.persistence_file}")
            return True
        except FileNotFoundError:
            logger.info("No existing memory file found, starting fresh")
            return False
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return False

    def clear(self) -> None:
        """Clear all memory."""
        self.memories.clear()
        self.locations_visited.clear()
        self.items_collected.clear()
        self.enemies_defeated.clear()
        self.puzzles_solved.clear()
        self.deaths = 0
        self.play_time = 0.0
        logger.info("Memory cleared")

    def export_for_context(self) -> str:
        """
        Export relevant memory for AI context.

        Returns:
            Formatted memory string for context
        """
        parts = []
        
        # Important memories
        important = [m for m in self.memories.values() if m.importance >= 3]
        if important:
            parts.append("Important memories:")
            for mem in important[:5]:
                parts.append(f"- {mem.key}: {mem.value}")
        
        # Recent items
        if self.items_collected:
            recent_items = self.items_collected[-5:]
            parts.append(f"Recent items: {', '.join(recent_items)}")
        
        # Stats
        parts.append(self.get_summary())
        
        return "\n".join(parts)
