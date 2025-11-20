"""Analyzes overall game state from screen captures."""

from typing import Dict, Optional, List
import cv2
import numpy as np
from dataclasses import dataclass, field
from loguru import logger

from .ocr_engine import OCREngine
from .object_detector import ObjectDetector, DetectedObject
from .map_recognizer import MapRecognizer, Location


@dataclass
class GameState:
    """Represents the current game state."""
    health: int = 0
    max_health: int = 0
    rupees: int = 0
    bombs: int = 0
    arrows: int = 0
    keys: int = 0
    location: Optional[Location] = None
    enemies_visible: List[DetectedObject] = field(default_factory=list)
    items_visible: List[DetectedObject] = field(default_factory=list)
    in_dialog: bool = False
    dialog_text: str = ""
    in_menu: bool = False
    player_position: Optional[tuple] = None


class GameStateAnalyzer:
    """Analyzes game screen to extract complete game state."""

    def __init__(self):
        """Initialize the game state analyzer."""
        self.ocr_engine = OCREngine()
        self.object_detector = ObjectDetector()
        self.map_recognizer = MapRecognizer()
        self.last_state: Optional[GameState] = None

    def analyze(self, image: np.ndarray) -> GameState:
        """
        Analyze the game screen and extract complete state.

        Args:
            image: Current game screen (BGR format)

        Returns:
            GameState object with extracted information
        """
        state = GameState()
        
        try:
            # Detect location
            state.location = self.map_recognizer.identify_location(image)
            
            # Detect objects
            objects = self.object_detector.detect_objects(image)
            state.enemies_visible = [obj for obj in objects if obj.object_type.value == "enemy"]
            state.items_visible = [obj for obj in objects if obj.object_type.value in ["item", "heart", "rupee"]]
            
            # Check for dialog
            state.in_dialog = self.ocr_engine.detect_dialog_box(image)
            if state.in_dialog:
                state.dialog_text = self.ocr_engine.read_dialog(image)
            
            # Extract HUD information
            hud_info = self._extract_hud_info(image)
            state.health = hud_info.get("health", 0)
            state.max_health = hud_info.get("max_health", 0)
            state.rupees = hud_info.get("rupees", 0)
            state.bombs = hud_info.get("bombs", 0)
            state.arrows = hud_info.get("arrows", 0)
            state.keys = hud_info.get("keys", 0)
            
            # Detect menu
            state.in_menu = self._is_in_menu(image)
            
            # Detect player position
            state.player_position = self._detect_player_position(image)
            
            self.last_state = state
            return state
        except Exception as e:
            logger.error(f"Game state analysis failed: {e}")
            return state

    def _extract_hud_info(self, image: np.ndarray) -> Dict[str, int]:
        """
        Extract information from the HUD.

        Args:
            image: Game screen

        Returns:
            Dictionary with HUD information
        """
        info = {
            "health": 0,
            "max_health": 0,
            "rupees": 0,
            "bombs": 0,
            "arrows": 0,
            "keys": 0,
        }
        
        try:
            height, width = image.shape[:2]
            
            # NES HUD is the top ~25% of the screen
            # Hearts are in the middle-right of the HUD
            hearts_region = image[int(height*0.15):int(height*0.25), int(width*0.6):int(width*0.9)]
            hearts = self._count_hearts(hearts_region)
            info["health"] = hearts.get("current", 0)
            info["max_health"] = hearts.get("max", 0)
            
            # Rupees/Keys/Bombs are in the middle-left of the HUD
            items_region = image[int(height*0.15):int(height*0.25), int(width*0.2):int(width*0.5)]
            numbers = self.ocr_engine.detect_numbers(items_region)
            if numbers:
                info["rupees"] = numbers[0] if len(numbers) > 0 else 0
                # Note: NES HUD has specific slots for Keys/Bombs, would need precise coordinates
            
            return info
        except Exception as e:
            logger.error(f"HUD extraction failed: {e}")
            return info

    def _count_hearts(self, hearts_region: np.ndarray) -> Dict[str, int]:
        """
        Count hearts in the HUD.

        Args:
            hearts_region: Image region containing hearts

        Returns:
            Dictionary with current and max hearts
        """
        try:
            # Detect red (full hearts) and outline (empty hearts)
            hsv = cv2.cvtColor(hearts_region, cv2.COLOR_BGR2HSV)
            
            # Full hearts (red)
            lower_red = np.array([0, 100, 100])
            upper_red = np.array([10, 255, 255])
            red_mask = cv2.inRange(hsv, lower_red, upper_red)
            
            # Count contours (each heart container)
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Simple approximation
            full_hearts = len([c for c in contours if cv2.contourArea(c) > 20])
            
            return {"current": full_hearts, "max": full_hearts}
        except Exception as e:
            logger.error(f"Heart counting failed: {e}")
            return {"current": 0, "max": 0}

    def _is_in_menu(self, image: np.ndarray) -> bool:
        """
        Detect if the game menu is open.

        Args:
            image: Game screen

        Returns:
            bool: True if menu is open
        """
        try:
            # Menu typically has a distinct layout with inventory grid
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Check for grid pattern (menu has regular grid)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            if lines is not None and len(lines) > 20:
                return True
            
            return False
        except Exception as e:
            logger.error(f"Menu detection failed: {e}")
            return False

    def _detect_player_position(self, image: np.ndarray) -> Optional[tuple]:
        """
        Detect the player's position on screen.

        Args:
            image: Game screen

        Returns:
            (x, y) position or None
        """
        try:
            # Link typically wears green - detect green blob in center area
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # NES Link is a distinct green/brown
            # Green color range for Link's tunic (NES palette is simpler)
            lower_green = np.array([40, 100, 100])
            upper_green = np.array([80, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get largest contour (likely the player)
                largest = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
            
            # Default to center if not detected
            height, width = image.shape[:2]
            return (width // 2, height // 2)
        except Exception as e:
            logger.error(f"Player position detection failed: {e}")
            return None

    def get_state_summary(self, state: Optional[GameState] = None) -> str:
        """
        Get a human-readable summary of the game state.

        Args:
            state: GameState to summarize (uses last state if None)

        Returns:
            String summary
        """
        if state is None:
            state = self.last_state
        
        if state is None:
            return "No game state available"
        
        summary = []
        summary.append(f"Health: {state.health}/{state.max_health}")
        summary.append(f"Rupees: {state.rupees}")
        
        if state.location:
            summary.append(f"Location: {state.location.region}")
        
        if state.enemies_visible:
            summary.append(f"Enemies visible: {len(state.enemies_visible)}")
        
        if state.items_visible:
            summary.append(f"Items visible: {len(state.items_visible)}")
        
        if state.in_dialog:
            summary.append(f"Dialog: {state.dialog_text[:50]}...")
        
        return " | ".join(summary)

    def has_state_changed(self, threshold: float = 0.1) -> bool:
        """
        Check if the game state has changed significantly.

        Args:
            threshold: Change threshold

        Returns:
            bool: True if state changed significantly
        """
        # Placeholder for state change detection
        return True
