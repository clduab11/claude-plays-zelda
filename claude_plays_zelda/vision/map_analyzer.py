"""Map analysis and navigation system."""

from typing import Dict, List, Tuple, Optional, Set
import cv2
import numpy as np
from collections import deque
from loguru import logger


class MapAnalyzer:
    """Analyzes game maps and provides navigation guidance."""

    def __init__(self):
        """Initialize map analyzer."""
        self.current_room: Optional[np.ndarray] = None
        self.room_history: List[np.ndarray] = []
        self.visited_rooms: Set[str] = set()
        self.room_connections: Dict[str, List[str]] = {}

        logger.info("MapAnalyzer initialized")

    def capture_room(self, image: np.ndarray) -> str:
        """
        Capture and hash the current room for tracking.

        Args:
            image: Current game screen

        Returns:
            Hash of the room for identification
        """
        try:
            # Resize and convert to grayscale for consistent hashing
            small = cv2.resize(image, (64, 64))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            # Compute hash
            room_hash = str(hash(gray.tobytes()))

            if room_hash not in self.visited_rooms:
                self.visited_rooms.add(room_hash)
                self.room_history.append(gray)
                logger.info(f"New room discovered: {room_hash}")

            self.current_room = gray
            return room_hash

        except Exception as e:
            logger.error(f"Error capturing room: {e}")
            return ""

    def has_room_changed(self, image: np.ndarray, threshold: float = 0.3) -> bool:
        """
        Detect if Link has moved to a different room.

        Args:
            image: Current game screen
            threshold: Similarity threshold (lower = more different)

        Returns:
            True if room has changed
        """
        try:
            if self.current_room is None:
                return True

            # Prepare current frame
            small = cv2.resize(image, (64, 64))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            # Compare with stored room
            diff = cv2.absdiff(self.current_room, gray)
            similarity = 1.0 - (np.sum(diff) / (diff.size * 255))

            return similarity < threshold

        except Exception as e:
            logger.error(f"Error checking room change: {e}")
            return False

    def analyze_minimap(self, minimap: np.ndarray) -> Dict[str, any]:
        """
        Analyze the minimap to determine Link's position and surroundings.

        Args:
            minimap: Extracted minimap region

        Returns:
            Dictionary with minimap analysis
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(minimap, cv2.COLOR_BGR2GRAY)

            # Detect rooms (lighter areas on minimap)
            _, rooms = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

            # Detect Link's position (brightest pixel)
            link_y, link_x = np.unravel_index(gray.argmax(), gray.shape)

            # Detect walls and boundaries
            edges = cv2.Canny(gray, 50, 150)

            # Count connected components (rooms)
            num_labels, labels = cv2.connectedComponents(rooms)

            analysis = {
                "link_position": (link_x, link_y),
                "num_rooms_visible": num_labels - 1,  # Subtract background
                "has_walls": np.sum(edges) > 100,
            }

            logger.debug(f"Minimap analysis: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing minimap: {e}")
            return {}

    def find_path_to_target(
        self, current_pos: Tuple[int, int], target_pos: Tuple[int, int], obstacles: np.ndarray
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find a path from current position to target using A* algorithm.

        Args:
            current_pos: Current (x, y) position
            target_pos: Target (x, y) position
            obstacles: Binary mask of obstacles (0 = walkable, 255 = blocked)

        Returns:
            List of (x, y) waypoints or None if no path found
        """
        try:
            # Simple A* pathfinding
            def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
                return abs(a[0] - b[0]) + abs(a[1] - b[1])

            height, width = obstacles.shape
            open_set = [(0, current_pos)]
            came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
            g_score = {current_pos: 0}
            f_score = {current_pos: heuristic(current_pos, target_pos)}

            while open_set:
                open_set.sort(key=lambda x: x[0])
                current = open_set.pop(0)[1]

                if current == target_pos:
                    # Reconstruct path
                    path = [current]
                    while current in came_from:
                        current = came_from[current]
                        path.append(current)
                    path.reverse()
                    return path

                # Check neighbors (4-directional)
                neighbors = [
                    (current[0] + 1, current[1]),
                    (current[0] - 1, current[1]),
                    (current[0], current[1] + 1),
                    (current[0], current[1] - 1),
                ]

                for neighbor in neighbors:
                    nx, ny = neighbor

                    # Check bounds
                    if not (0 <= nx < width and 0 <= ny < height):
                        continue

                    # Check if walkable
                    if obstacles[ny, nx] > 0:
                        continue

                    tentative_g = g_score[current] + 1

                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + heuristic(neighbor, target_pos)

                        if neighbor not in [pos for _, pos in open_set]:
                            open_set.append((f_score[neighbor], neighbor))

            return None  # No path found

        except Exception as e:
            logger.error(f"Error finding path: {e}")
            return None

    def detect_obstacles(self, image: np.ndarray) -> np.ndarray:
        """
        Detect obstacles and walls in the current room.

        Args:
            image: Current game screen

        Returns:
            Binary mask where 255 = obstacle, 0 = walkable
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect dark areas (walls, obstacles)
            _, obstacles = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

            # Clean up with morphological operations
            kernel = np.ones((5, 5), np.uint8)
            obstacles = cv2.morphologyEx(obstacles, cv2.MORPH_CLOSE, kernel)
            obstacles = cv2.morphologyEx(obstacles, cv2.MORPH_OPEN, kernel)

            return obstacles

        except Exception as e:
            logger.error(f"Error detecting obstacles: {e}")
            return np.zeros((100, 100), dtype=np.uint8)

    def suggest_exploration_direction(self, visited_areas: np.ndarray) -> str:
        """
        Suggest a direction to explore based on visited areas.

        Args:
            visited_areas: Binary mask of visited areas

        Returns:
            Suggested direction ('up', 'down', 'left', 'right')
        """
        try:
            # Find unvisited areas
            unvisited = 255 - visited_areas

            # Check each direction for unvisited areas
            height, width = visited_areas.shape
            center_x, center_y = width // 2, height // 2

            directions = {
                "up": np.sum(unvisited[: center_y, :]),
                "down": np.sum(unvisited[center_y :, :]),
                "left": np.sum(unvisited[:, : center_x]),
                "right": np.sum(unvisited[:, center_x :]),
            }

            # Suggest direction with most unvisited area
            best_direction = max(directions, key=directions.get)
            logger.debug(f"Suggested exploration direction: {best_direction}")
            return best_direction

        except Exception as e:
            logger.error(f"Error suggesting direction: {e}")
            return "up"

    def get_room_exits(self, image: np.ndarray) -> List[str]:
        """
        Detect possible exits from the current room.

        Args:
            image: Current game screen

        Returns:
            List of directions where exits are detected
        """
        try:
            height, width = image.shape[:2]

            # Check edges for dark areas (doorways)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            exits = []

            # Check each edge
            edge_thickness = 10
            threshold = 50  # Dark pixel threshold

            # Top
            if np.mean(gray[:edge_thickness, :]) < threshold:
                exits.append("up")

            # Bottom
            if np.mean(gray[-edge_thickness:, :]) < threshold:
                exits.append("down")

            # Left
            if np.mean(gray[:, :edge_thickness]) < threshold:
                exits.append("left")

            # Right
            if np.mean(gray[:, -edge_thickness:]) < threshold:
                exits.append("right")

            logger.debug(f"Room exits detected: {exits}")
            return exits

        except Exception as e:
            logger.error(f"Error detecting room exits: {e}")
            return []

    def get_exploration_stats(self) -> Dict[str, any]:
        """
        Get statistics about exploration progress.

        Returns:
            Dictionary with exploration statistics
        """
        return {
            "rooms_visited": len(self.visited_rooms),
            "rooms_in_history": len(self.room_history),
        }
