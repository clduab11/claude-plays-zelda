"""Detects game state from screen (health, rupees, inventory, etc.)."""

from typing import Dict, Any, Optional, Tuple
import time
import cv2
import numpy as np
from loguru import logger


class GameStateDetector:
    """Detects various game state elements from the screen."""

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize game state detector.

        Args:
            config: Optional configuration object with detection parameters
        """
        # Define color ranges for different UI elements (in HSV)
        self.color_ranges = {
            # Heart colors (red for filled, darker for empty)
            "heart_full": {
                "lower": np.array([0, 100, 100]),
                "upper": np.array([10, 255, 255]),
            },
            "heart_empty": {
                "lower": np.array([0, 0, 50]),
                "upper": np.array([10, 50, 150]),
            },
            # Rupee counter (typically green or yellow)
            "rupee_digit": {
                "lower": np.array([35, 50, 50]),
                "upper": np.array([85, 255, 255]),
            },
        }

        # UI element positions (relative to screen size)
        # These are approximate for Zelda ALTTP
        self.ui_regions = {
            "hearts": (0.05, 0.85, 0.3, 0.1),  # (x, y, width, height) as ratios
            "rupees": (0.05, 0.05, 0.15, 0.08),
            "item_box": (0.75, 0.05, 0.2, 0.15),
            "minimap": (0.02, 0.02, 0.15, 0.15),
        }

        # Load configuration values or use defaults
        self.config = config
        if config and hasattr(config, 'game'):
            game_config = config.game
            self.min_hearts = game_config.get('detection', {}).get('min_hearts', 3)
            self.max_hearts = game_config.get('detection', {}).get('max_hearts', 20)
            self.heart_min_area = game_config.get('detection', {}).get('heart_min_area', 50)
            self.heart_max_area = game_config.get('detection', {}).get('heart_max_area', 500)
            self.ocr_retry_attempts = game_config.get('detection', {}).get('ocr_retry_attempts', 3)
            self.ocr_retry_delay = game_config.get('detection', {}).get('ocr_retry_delay', 0.1)
            self.title_screen_cache_duration = game_config.get('detection', {}).get('title_screen_cache_duration', 0.5)
            self.combat_change_ratio = game_config.get('combat', {}).get('change_ratio_threshold', 0.15)
        else:
            # Default values
            self.min_hearts = 3
            self.max_hearts = 20
            self.heart_min_area = 50
            self.heart_max_area = 500
            self.ocr_retry_attempts = 3
            self.ocr_retry_delay = 0.1
            self.title_screen_cache_duration = 0.5
            self.combat_change_ratio = 0.15

        # Cache for OCR instance (expensive to create)
        self._ocr_instance = None

        # Cache for title screen detection (expensive OCR operation)
        self._title_screen_cache = None
        self._title_screen_cache_time = 0

        logger.info(f"GameStateDetector initialized with min_hearts={self.min_hearts}, max_hearts={self.max_hearts}")

    def _get_ocr_instance(self):
        """
        Get cached OCR instance to avoid creating new instances repeatedly.

        Returns:
            GameOCR instance
        """
        if self._ocr_instance is None:
            from claude_plays_zelda.vision.ocr import GameOCR
            self._ocr_instance = GameOCR()
            logger.debug("Created new OCR instance")
        return self._ocr_instance

    def detect_title_screen(self, image: np.ndarray, force_refresh: bool = False) -> bool:
        """
        Detect if the game is at the title screen or file select.

        Uses caching to avoid expensive OCR operations on every frame.
        Cache is invalidated after title_screen_cache_duration seconds.

        Args:
            image: Full game screen
            force_refresh: If True, bypass cache and force fresh detection

        Returns:
            True if at title screen/file select

        Edge Cases:
            - OCR may misread pixelated NES text
            - Emulator lag could cause cached results to be stale
            - Different Zelda games may have different title text
        """
        current_time = time.time()

        # Check cache first (unless force_refresh is True)
        if not force_refresh and self._title_screen_cache is not None:
            cache_age = current_time - self._title_screen_cache_time
            if cache_age < self.title_screen_cache_duration:
                logger.debug(f"Using cached title screen result: {self._title_screen_cache} (age: {cache_age:.2f}s)")
                return self._title_screen_cache

        # Perform detection with retry logic
        result = self._detect_title_screen_with_retry(image)

        # Update cache
        self._title_screen_cache = result
        self._title_screen_cache_time = current_time

        return result

    def _detect_title_screen_with_retry(self, image: np.ndarray) -> bool:
        """
        Detect title screen with retry logic for OCR failures.

        Args:
            image: Full game screen

        Returns:
            True if at title screen/file select
        """
        for attempt in range(self.ocr_retry_attempts):
            try:
                # Use cached OCR instance
                ocr = self._get_ocr_instance()

                # Check for title screen text
                # "ZELDA" is usually prominent, or "REGISTER YOUR NAME"
                text = ocr.extract_text(image, preprocess=True)

                keywords = ["ZELDA", "LEGEND", "REGISTER", "ELIMINATION", "NAME"]
                text_upper = text.upper()

                for keyword in keywords:
                    if keyword in text_upper:
                        logger.debug(f"Title screen detected: found keyword '{keyword}' in text: {text}")
                        return True

                # If we successfully extracted text but didn't find keywords, return False
                return False

            except Exception as e:
                logger.warning(f"Error detecting title screen (attempt {attempt + 1}/{self.ocr_retry_attempts}): {e}")
                if attempt < self.ocr_retry_attempts - 1:
                    time.sleep(self.ocr_retry_delay)
                else:
                    logger.error(f"Failed to detect title screen after {self.ocr_retry_attempts} attempts")
                    return False

        return False

    def detect_gameplay_hud(self, image: np.ndarray) -> bool:
        """
        Detect if the gameplay HUD (hearts, rupees) is visible.

        Uses a two-stage detection process:
        1. Check if heart count is within valid gameplay range
        2. Verify we're not on the title screen (uses cached OCR)

        Args:
            image: Full game screen

        Returns:
            True if HUD is detected (implies in-game)

        Edge Cases:
            - Title screen may show decorative hearts (false positive)
            - Game over screen may still show HUD briefly
            - Heart count range is game-specific (configurable via config)
            - Emulator lag could cause transient detection failures

        Performance:
            - Title screen detection is cached to avoid repeated OCR
            - OCR instance is reused across calls
        """
        try:
            # Check for hearts - stricter check
            hearts = self.detect_hearts(image)

            # Link starts with 3 hearts (default), max is usually 16-20.
            # Heart count outside this range suggests false positive or not in game.
            # Note: These values are configurable for different Zelda games.
            if hearts["max_hearts"] < self.min_hearts or hearts["max_hearts"] > self.max_hearts:
                logger.debug(f"Heart count {hearts['max_hearts']} outside valid range [{self.min_hearts}, {self.max_hearts}]")
                return False

            # Secondary check: Verify we're not on the title screen
            # The title screen may have decorative hearts that look like HUD
            # This uses cached OCR to avoid performance penalty
            if self.detect_title_screen(image):
                logger.debug("Title screen detected, HUD check returns False")
                return False

            logger.debug(f"HUD detected: hearts={hearts}")
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

            # Detect empty hearts (darker red/gray)
            mask_empty = cv2.inRange(
                hsv,
                self.color_ranges["heart_empty"]["lower"],
                self.color_ranges["heart_empty"]["upper"],
            )

            # Count heart containers based on connected components
            full_hearts = self._count_hearts(mask_full)
            empty_hearts = self._count_hearts(mask_empty)

            max_hearts = full_hearts + empty_hearts

            result = {"current_hearts": full_hearts, "max_hearts": max_hearts}
            logger.debug(f"Hearts detected: {result}")
            return result

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

        Note:
            Heart size thresholds are configurable via config.yaml
            to support different screen resolutions and games.
        """
        try:
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours by size (hearts have consistent size)
            # Uses configurable thresholds for flexibility
            valid_hearts = [
                c for c in contours
                if self.heart_min_area < cv2.contourArea(c) < self.heart_max_area
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
            text = ocr.extract_text(rupee_region, preprocess=True)

            # Extract numeric value
            import re

            numbers = re.findall(r"\d+", text)
            if numbers:
                rupee_count = int(numbers[0])
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
            item_region = self.get_region(image, "item_box")
            if item_region is None:
                return None

            # Use template matching or color detection to identify items
            # For now, return a placeholder
            # TODO: Implement item recognition using templates or CNN

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

        Note:
            Combat detection uses screen change ratio threshold
            which is configurable via config.yaml combat.change_ratio_threshold
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

            # Use configurable threshold
            return change_ratio > self.combat_change_ratio

        except Exception as e:
            logger.error(f"Error detecting combat: {e}")
            return False
