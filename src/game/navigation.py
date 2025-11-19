"""Navigation and pathfinding for game world exploration."""

from typing import List, Tuple, Optional, Set
from enum import Enum
from collections import deque
from loguru import logger

from ..cv.map_recognizer import Location


class Direction(Enum):
    """Cardinal directions."""
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)


class Navigator:
    """Navigation system for pathfinding and exploration."""

    def __init__(self, pathfinding_algorithm: str = "a_star", revisit_threshold: int = 3):
        """
        Initialize the navigator.

        Args:
            pathfinding_algorithm: Algorithm to use (a_star, bfs, dfs)
            revisit_threshold: Max times to revisit a location
        """
        self.algorithm = pathfinding_algorithm
        self.revisit_threshold = revisit_threshold
        self.room_graph: dict = {}  # Graph of connected rooms
        self.visit_counts: dict = {}  # Times each room has been visited
        self.current_path: List[Direction] = []
        self.exploration_strategy = "depth_first"  # or "breadth_first"

    def find_path(self, start: Location, goal: Location) -> List[str]:
        """
        Find a path from start to goal.

        Args:
            start: Starting location
            goal: Goal location

        Returns:
            List of direction strings
        """
        if self.algorithm == "a_star":
            return self._a_star_search(start, goal)
        elif self.algorithm == "bfs":
            return self._bfs_search(start, goal)
        else:
            return self._dfs_search(start, goal)

    def _a_star_search(self, start: Location, goal: Location) -> List[str]:
        """
        A* pathfinding algorithm.

        Args:
            start: Starting location
            goal: Goal location

        Returns:
            List of direction strings
        """
        # Simplified A* implementation
        # In a real implementation, this would use proper A* with heuristics
        
        path = []
        current = (start.x, start.y)
        target = (goal.x, goal.y)
        
        # Manhattan distance heuristic
        while current != target:
            dx = target[0] - current[0]
            dy = target[1] - current[1]
            
            if abs(dx) > abs(dy):
                if dx > 0:
                    path.append("right")
                    current = (current[0] + 1, current[1])
                else:
                    path.append("left")
                    current = (current[0] - 1, current[1])
            else:
                if dy > 0:
                    path.append("down")
                    current = (current[0], current[1] + 1)
                else:
                    path.append("up")
                    current = (current[0], current[1] - 1)
            
            # Prevent infinite loops
            if len(path) > 100:
                logger.warning("Path too long, stopping")
                break
        
        logger.info(f"A* path found: {len(path)} steps")
        return path

    def _bfs_search(self, start: Location, goal: Location) -> List[str]:
        """
        Breadth-first search pathfinding.

        Args:
            start: Starting location
            goal: Goal location

        Returns:
            List of direction strings
        """
        # BFS finds shortest path in unweighted graph
        queue = deque([(start, [])])
        visited = set()
        visited.add((start.x, start.y))
        
        while queue:
            current, path = queue.popleft()
            
            if current.x == goal.x and current.y == goal.y:
                return path
            
            # Explore neighbors
            neighbors = [
                (current.x, current.y - 1, "up"),
                (current.x, current.y + 1, "down"),
                (current.x - 1, current.y, "left"),
                (current.x + 1, current.y, "right"),
            ]
            
            for nx, ny, direction in neighbors:
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    new_location = Location(nx, ny, current.region)
                    queue.append((new_location, path + [direction]))
        
        logger.warning("No path found")
        return []

    def _dfs_search(self, start: Location, goal: Location) -> List[str]:
        """
        Depth-first search pathfinding.

        Args:
            start: Starting location
            goal: Goal location

        Returns:
            List of direction strings
        """
        # DFS explores deeply before backtracking
        stack = [(start, [])]
        visited = set()
        
        while stack:
            current, path = stack.pop()
            
            if (current.x, current.y) in visited:
                continue
            
            visited.add((current.x, current.y))
            
            if current.x == goal.x and current.y == goal.y:
                return path
            
            # Explore neighbors
            neighbors = [
                (current.x, current.y - 1, "up"),
                (current.x, current.y + 1, "down"),
                (current.x - 1, current.y, "left"),
                (current.x + 1, current.y, "right"),
            ]
            
            for nx, ny, direction in neighbors:
                if (nx, ny) not in visited:
                    new_location = Location(nx, ny, current.region)
                    stack.append((new_location, path + [direction]))
        
        logger.warning("No path found")
        return []

    def get_exploration_direction(self, current_location: Location,
                                  visited_locations: Set[Tuple[int, int]]) -> str:
        """
        Get the next direction for exploration.

        Args:
            current_location: Current location
            visited_locations: Set of visited (x, y) coordinates

        Returns:
            Direction string
        """
        current_pos = (current_location.x, current_location.y)
        
        # Check adjacent rooms
        adjacent = [
            ((current_location.x, current_location.y - 1), "up"),
            ((current_location.x, current_location.y + 1), "down"),
            ((current_location.x - 1, current_location.y), "left"),
            ((current_location.x + 1, current_location.y), "right"),
        ]
        
        # Find unvisited adjacent rooms
        unvisited = [direction for pos, direction in adjacent 
                    if pos not in visited_locations]
        
        if unvisited:
            # Prefer unvisited rooms
            direction = unvisited[0]
            logger.info(f"Exploring unvisited direction: {direction}")
            return direction
        
        # All adjacent rooms visited, find least visited
        visit_counts = {direction: self.visit_counts.get(pos, 0) 
                       for pos, direction in adjacent}
        
        min_visits = min(visit_counts.values())
        least_visited = [d for d, v in visit_counts.items() if v == min_visits]
        
        if least_visited:
            return least_visited[0]
        
        # Default to random direction
        return "up"

    def record_visit(self, location: Location) -> None:
        """
        Record visiting a location.

        Args:
            location: Location visited
        """
        key = (location.x, location.y, location.region)
        self.visit_counts[key] = self.visit_counts.get(key, 0) + 1
        logger.debug(f"Location {key} visited {self.visit_counts[key]} times")

    def should_backtrack(self, location: Location) -> bool:
        """
        Determine if we should backtrack from this location.

        Args:
            location: Current location

        Returns:
            bool: True if should backtrack
        """
        key = (location.x, location.y, location.region)
        visits = self.visit_counts.get(key, 0)
        
        # Backtrack if visited too many times
        return visits >= self.revisit_threshold

    def get_backtrack_direction(self, current_location: Location,
                               previous_direction: str) -> str:
        """
        Get direction to backtrack.

        Args:
            current_location: Current location
            previous_direction: Direction we came from

        Returns:
            Opposite direction
        """
        opposite = {
            "up": "down",
            "down": "up",
            "left": "right",
            "right": "left",
        }
        
        return opposite.get(previous_direction, "down")

    def add_room_connection(self, room1: Location, room2: Location, 
                          direction: str) -> None:
        """
        Add a connection between two rooms to the graph.

        Args:
            room1: First room
            room2: Second room
            direction: Direction from room1 to room2
        """
        key1 = (room1.x, room1.y, room1.region)
        key2 = (room2.x, room2.y, room2.region)
        
        if key1 not in self.room_graph:
            self.room_graph[key1] = {}
        
        self.room_graph[key1][direction] = key2
        logger.debug(f"Added connection: {key1} -> {direction} -> {key2}")

    def get_unexplored_directions(self, location: Location) -> List[str]:
        """
        Get directions that haven't been explored from this location.

        Args:
            location: Current location

        Returns:
            List of unexplored directions
        """
        key = (location.x, location.y, location.region)
        explored = self.room_graph.get(key, {}).keys()
        
        all_directions = ["up", "down", "left", "right"]
        unexplored = [d for d in all_directions if d not in explored]
        
        return unexplored

    def estimate_distance(self, loc1: Location, loc2: Location) -> int:
        """
        Estimate distance between two locations (Manhattan distance).

        Args:
            loc1: First location
            loc2: Second location

        Returns:
            Estimated distance
        """
        return abs(loc1.x - loc2.x) + abs(loc1.y - loc2.y)

    def is_dead_end(self, location: Location) -> bool:
        """
        Check if a location is a dead end.

        Args:
            location: Location to check

        Returns:
            bool: True if dead end
        """
        unexplored = self.get_unexplored_directions(location)
        
        # Dead end if no unexplored directions and all visited multiple times
        if unexplored:
            return False
        
        key = (location.x, location.y, location.region)
        visits = self.visit_counts.get(key, 0)
        
        return visits >= 2

    def reset_exploration(self) -> None:
        """Reset exploration data."""
        self.room_graph.clear()
        self.visit_counts.clear()
        self.current_path.clear()
        logger.info("Navigation data reset")

    def get_statistics(self) -> dict:
        """
        Get navigation statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "rooms_mapped": len(self.room_graph),
            "total_visits": sum(self.visit_counts.values()),
            "unique_rooms_visited": len(self.visit_counts),
        }
