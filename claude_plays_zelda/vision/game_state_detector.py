"""Detects game state from screen (health, rupees, inventory, etc.)."""

from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np
from loguru import logger


class GameStateDetector:
    """Detects various game state elements from the screen."""

    def __init__(self):
        """Initialize game state detector."""
        # Define color ranges for different UI elements (in HSV)
        self.color_ranges = {
            # Heart colors (red for filled, darker for empty)
            "heart_full": {
                "lower": np.array([0, 100, 100]),
                "upper": np.array([10, 255, 255]),
            },
            "heart_empty": { # NES empty hearts are often white/gray or just black background
                 "lower": np.array([0, 0, 150]),
                 "upper": np.array([180, 20, 255]),
            },
            # Rupee counter (typically white/yellow text on black)
            "rupee_digit": {
                "lower": np.array([0, 0, 150]),
                "upper": np.array([180, 50, 255]),
            },
        }

        # UI element positions (relative to screen size)
        # NES Zelda HUD is at the top of the screen
        self.ui_regions = {
            "hud": (0.0, 0.0, 1.0, 0.25), # Top 25% is roughly the HUD
            "hearts": (0.65, 0.15, 0.3, 0.1),  # Hearts are on the right side of HUD
            "rupees": (0.3, 0.05, 0.15, 0.08), # Rupees near middle-left
            "item_box_b": (0.5, 0.1, 0.1, 0.1), # B Item
            "item_box_a": (0.6, 0.1, 0.1, 0.1), # A Item
            "minimap": (0.05, 0.05, 0.2, 0.15), # Minimap top left
        }

        logger.info("GameStateDetector initialized for NES")

    def detect_title_screen(self, image: np.ndarray) -> bool:
        """
        Detect if the game is at the title screen or file select.
        
        Args:
            image: Full game screen
            
        Returns:
            True if at title screen/file select
        """
        try:
            # Use OCR to look for specific text
            from claude_plays_zelda.vision.ocr import GameOCR
            ocr = GameOCR()
            
            # Check for title screen text
            # NES Zelda Title Screen has "THE LEGEND OF ZELDA"
            # File Select has "REGISTER YOUR NAME" or "ELIMINATION MODE"
            text = ocr.extract_text(image, preprocess=True)
            
            keywords = ["ZELDA", "LEGEND", "REGISTER", "ELIMINATION", "NAME", "STORY", "CONTINUE", "SAVE"]
            text_upper = text.upper()
            
            for keyword in keywords:
                if keyword in text_upper:
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error detecting title screen: {e}")
            return False

    def detect_gameplay_hud(self, image: np.ndarray) -> bool:
        """
        Detect if the gameplay HUD (hearts, rupees) is visible.
        
        Args:
            image: Full game screen
            
        Returns:
            True if HUD is detected (implies in-game)
        """
        try:
            # Check for hearts - stricter check
            hearts = self.detect_hearts(image)
            
            # Link starts with 3 hearts.
            if hearts["max_hearts"] < 3:
                return False
                
            # If we are on the title screen, we are not playing
            if self.detect_title_screen(image):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error detecting HUD: {e}")
            return False

    def get_region(self, image: np.ndarray, region_key: str) -> Optional[np.ndarray]:
        """
        Extract a UI region from the screen.

        Args:
            image: Full game screen
            region_key: Key for UI region (e.g., 'hearts', 'rupees')

        Returns:
            Cropped region or None if key invalid
        """
        if region_key not in self.ui_regions:
            logger.warning(f"Unknown region key: {region_key}")
            return None

        height, width = image.shape[:2]
        x_ratio, y_ratio, w_ratio, h_ratio = self.ui_regions[region_key]

        x = int(width * x_ratio)
        y = int(height * y_ratio)
        w = int(width * w_ratio)
        h = int(height * h_ratio)

        return image[y : y + h, x : x + w]

    def detect_hearts(self, image: np.ndarray) -> Dict[str, int]:
        """
        Detect Link's current health (hearts).

        Args:
            image: Full game screen

        Returns:
            Dictionary with 'current_hearts' and 'max_hearts'
        """
        try:
            hearts_region = self.get_region(image, "hearts")
            if hearts_region is None:
                return {"current_hearts": 0, "max_hearts": 0}

            # Convert to HSV for color detection
            hsv = cv2.cvtColor(hearts_region, cv2.COLOR_BGR2HSV)

            # Detect full hearts (red)
            mask_full = cv2.inRange(
                hsv,
                self.color_ranges["heart_full"]["lower"],
                self.color_ranges["heart_full"]["upper"],
            )

            # Detect empty hearts (often white outline or specific color in NES)
            # This might need tuning for NES palette
            mask_empty = cv2.inRange(
                hsv,
                self.color_ranges["heart_empty"]["lower"],
                self.color_ranges["heart_empty"]["upper"],
            )

            # Count heart containers based on connected components
            full_hearts = self._count_hearts(mask_full)
            # Empty heart counting might be tricky with just color, 
            # might need template matching later if this fails.
            # For now, assume if we see red hearts, we are good.
            
            # In NES Zelda, hearts are distinct sprites.
            
            return {"current_hearts": full_hearts, "max_hearts": full_hearts} # Simplified for now

        except Exception as e:
            logger.error(f"Error detecting hearts: {e}")
            return {"current_hearts": 0, "max_hearts": 0}

    def _count_hearts(self, mask: np.ndarray) -> int:
        """
        Count heart containers from a binary mask.

        Args:
            mask: Binary mask of heart region

        Returns:
            Number of hearts detected
        """
        try:
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours by size (hearts have consistent size)
            # NES resolution is low, hearts are small (8x8 roughly)
            min_area = 10
            max_area = 100
            valid_hearts = [
                c for c in contours if min_area < cv2.contourArea(c) < max_area
            ]

            return len(valid_hearts)

        except Exception as e:
            logger.error(f"Error counting hearts: {e}")
            return 0

    def detect_rupees(self, image: np.ndarray) -> int:
        """
        Detect current rupee count.

        Args:
            image: Full game screen

        Returns:
            Number of rupees (0 if detection fails)
        """
        try:
            rupee_region = self.get_region(image, "rupees")
            if rupee_region is None:
                return 0

            # Use OCR to read the number
            from claude_plays_zelda.vision.ocr import GameOCR

            ocr = GameOCR()
            # Preprocess specifically for digits?
            text = ocr.extract_text(rupee_region, preprocess=True)

            # Extract numeric value
            import re

            # Look for X followed by digits, e.g. "X 5"
            numbers = re.findall(r"\d+", text)
            if numbers:
                # If multiple numbers, take the last one (often X is read as something else)
                rupee_count = int(numbers[-1])
                logger.debug(f"Rupees detected: {rupee_count}")
                return rupee_count

            return 0

        except Exception as e:
            logger.error(f"Error detecting rupees: {e}")
            return 0

    def detect_current_item(self, image: np.ndarray) -> Optional[str]:
        """
        Detect which item is currently selected.

        Args:
            image: Full game screen

        Returns:
            Item name or None if no item detected
        """
        try:
            item_region = self.get_region(image, "item_box_b")
            if item_region is None:
                return None

            # TODO: Implement item recognition
            return None

        except Exception as e:
            logger.error(f"Error detecting current item: {e}")
            return None

    def detect_location(self, image: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect Link's location on the map using minimap.

        Args:
            image: Full game screen

        Returns:
            Tuple of (x, y) coordinates or None if detection fails
        """
        try:
            minimap_region = self.get_region(image, "minimap")
            if minimap_region is None:
                return None

            # Detect Link's position (typically a bright pixel) on minimap
            # Convert to HSV and look for bright/white pixel
            hsv = cv2.cvtColor(minimap_region, cv2.COLOR_BGR2HSV)

            # Link is usually represented by a bright/flashing pixel
            lower_bright = np.array([0, 0, 200])
            upper_bright = np.array([180, 50, 255])
            mask = cv2.inRange(hsv, lower_bright, upper_bright)

            # Find the brightest point
            moments = cv2.moments(mask)
            if moments["m00"] > 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
                return (cx, cy)

            return None

        except Exception as e:
            logger.error(f"Error detecting location: {e}")
            return None

    def get_full_game_state(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Get complete game state information.

        Args:
            image: Full game screen

        Returns:
            Dictionary with all detected game state information
        """
        state = {
            "hearts": self.detect_hearts(image),
            "rupees": self.detect_rupees(image),
            "current_item": self.detect_current_item(image),
            "location": self.detect_location(image),
            "is_title_screen": self.detect_title_screen(image),
            "is_in_game": self.detect_gameplay_hud(image),
            "timestamp": None,  # Will be set by caller
        }

        logger.debug(f"Game state: {state}")
        return state

    def is_link_alive(self, image: np.ndarray) -> bool:
        """
        Check if Link is still alive (has hearts).

        Args:
            image: Full game screen

        Returns:
            True if Link has at least one heart
        """
        hearts = self.detect_hearts(image)
        return hearts["current_hearts"] > 0

    def is_in_combat(self, image: np.ndarray, prev_image: Optional[np.ndarray] = None) -> bool:
        """
        Detect if Link is currently in combat.

        Args:
            image: Current frame
            prev_image: Previous frame for motion detection

        Returns:
            True if combat is likely occurring
        """
        try:
            # Combat indicators:
            # 1. Rapid screen changes (enemies moving, attacks)
            # 2. Health decreasing
            # 3. Specific audio cues (not implemented here)

            if prev_image is None:
                return False

            # Calculate frame difference
            diff = cv2.absdiff(image, prev_image)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

            # High amount of change suggests combat
            change_ratio = np.sum(thresh > 0) / thresh.size

            return change_ratio > 0.15  # More than 15% of screen changed

        except Exception as e:
            logger.error(f"Error detecting combat: {e}")
            return False
