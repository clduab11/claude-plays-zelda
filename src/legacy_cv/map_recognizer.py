"""Map recognition and location tracking."""

from typing import Tuple, Optional, List
import cv2
import numpy as np
from dataclasses import dataclass
from loguru import logger


@dataclass
class Location:
    """Represents a location in the game."""
    x: int
    y: int
    region: str
    dungeon: Optional[str] = None
    room_id: Optional[int] = None


class MapRecognizer:
    """Recognizes and tracks location in the game world."""

    def __init__(self):
        """Initialize the map recognizer."""
        self.current_location: Optional[Location] = None
        self.visited_rooms: set = set()
        self.world_map: dict = {}
        
        # Known regions in A Link to the Past
        self.regions = {
            "light_world": "Light World",
            "dark_world": "Dark World",
            "dungeon": "Dungeon",
            "house": "House/Shop",
        }

    def identify_location(self, image: np.ndarray) -> Optional[Location]:
        """
        Identify the current location from the screen.

        Args:
            image: Current game screen

        Returns:
            Location object or None
        """
        try:
            # Extract minimap region (typically top-right corner)
            minimap = self._extract_minimap(image)
            
            if minimap is not None:
                location = self._analyze_minimap(minimap)
                if location:
                    self.current_location = location
                    self._add_to_visited(location)
                    return location
            
            # Fallback: analyze full screen
            location = self._analyze_screen(image)
            if location:
                self.current_location = location
            
            return location
        except Exception as e:
            logger.error(f"Location identification failed: {e}")
            return None

    def _extract_minimap(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract the minimap from the screen.

        Args:
            image: Full game screen

        Returns:
            Minimap region or None
        """
        try:
            height, width = image.shape[:2]
            # Minimap is typically in top-left corner
            minimap_x = int(width * 0.02)
            minimap_y = int(height * 0.02)
            minimap_w = int(width * 0.15)
            minimap_h = int(height * 0.15)
            
            minimap = image[minimap_y:minimap_y+minimap_h, minimap_x:minimap_x+minimap_w]
            return minimap
        except Exception as e:
            logger.error(f"Minimap extraction failed: {e}")
            return None

    def _analyze_minimap(self, minimap: np.ndarray) -> Optional[Location]:
        """
        Analyze minimap to determine location.

        Args:
            minimap: Minimap image

        Returns:
            Location or None
        """
        # Placeholder implementation
        # Real implementation would use template matching or feature detection
        return None

    def _analyze_screen(self, image: np.ndarray) -> Optional[Location]:
        """
        Analyze full screen to determine location.

        Args:
            image: Full screen image

        Returns:
            Location or None
        """
        # Check for dungeon indicators (darker colors, specific patterns)
        is_dungeon = self._is_dungeon(image)
        
        if is_dungeon:
            return Location(0, 0, "dungeon", dungeon="unknown")
        
        # Check for dark world (different color palette)
        is_dark_world = self._is_dark_world(image)
        
        if is_dark_world:
            return Location(0, 0, "dark_world")
        
        return Location(0, 0, "light_world")

    def _is_dungeon(self, image: np.ndarray) -> bool:
        """
        Detect if player is in a dungeon.

        Args:
            image: Game screen

        Returns:
            bool: True if in dungeon
        """
        try:
            # Dungeons typically have darker colors
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            
            # Dungeons are generally darker (lower brightness)
            return mean_brightness < 80
        except Exception as e:
            logger.error(f"Dungeon detection failed: {e}")
            return False

    def _is_dark_world(self, image: np.ndarray) -> bool:
        """
        Detect if player is in the dark world.

        Args:
            image: Game screen

        Returns:
            bool: True if in dark world
        """
        try:
            # Dark world has a different color palette (more purple/red tones)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Check for purple/red hues
            purple_mask = cv2.inRange(hsv, np.array([140, 50, 50]), np.array([170, 255, 255]))
            purple_ratio = np.count_nonzero(purple_mask) / purple_mask.size
            
            return purple_ratio > 0.1
        except Exception as e:
            logger.error(f"Dark world detection failed: {e}")
            return False

    def _add_to_visited(self, location: Location) -> None:
        """
        Add location to visited rooms.

        Args:
            location: Location to add
        """
        room_key = (location.x, location.y, location.region)
        if room_key not in self.visited_rooms:
            self.visited_rooms.add(room_key)
            logger.info(f"New room visited: {location.region} ({location.x}, {location.y})")

    def get_unvisited_directions(self) -> List[str]:
        """
        Get list of directions that might lead to unvisited rooms.

        Returns:
            List of direction strings
        """
        if not self.current_location:
            return ["up", "down", "left", "right"]
        
        # Check which adjacent rooms haven't been visited
        unvisited = []
        current_key = (self.current_location.x, self.current_location.y, self.current_location.region)
        
        adjacent = [
            ("up", (self.current_location.x, self.current_location.y - 1, self.current_location.region)),
            ("down", (self.current_location.x, self.current_location.y + 1, self.current_location.region)),
            ("left", (self.current_location.x - 1, self.current_location.y, self.current_location.region)),
            ("right", (self.current_location.x + 1, self.current_location.y, self.current_location.region)),
        ]
        
        for direction, room_key in adjacent:
            if room_key not in self.visited_rooms:
                unvisited.append(direction)
        
        return unvisited if unvisited else ["up", "down", "left", "right"]

    def detect_transition(self, prev_image: np.ndarray, curr_image: np.ndarray) -> bool:
        """
        Detect screen transition (moving between rooms).

        Args:
            prev_image: Previous frame
            curr_image: Current frame

        Returns:
            bool: True if transition detected
        """
        try:
            # Screen transitions often involve fading or scrolling
            # Simple implementation: check for large brightness change
            prev_gray = cv2.cvtColor(prev_image, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(curr_image, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(prev_gray, curr_gray)
            transition_amount = np.mean(diff)
            
            return transition_amount > 50  # Threshold for transition
        except Exception as e:
            logger.error(f"Transition detection failed: {e}")
            return False

    def reset_exploration(self) -> None:
        """Reset exploration data."""
        self.visited_rooms.clear()
        self.current_location = None
        logger.info("Exploration data reset")
