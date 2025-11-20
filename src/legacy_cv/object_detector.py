"""Object detection for enemies, items, and game elements."""

from typing import List, Tuple, Optional
import cv2
import numpy as np
from enum import Enum
from loguru import logger


class ObjectType(Enum):
    """Types of objects that can be detected."""
    ENEMY = "enemy"
    ITEM = "item"
    CHEST = "chest"
    DOOR = "door"
    HEART = "heart"
    RUPEE = "rupee"
    KEY = "key"
    UNKNOWN = "unknown"


class DetectedObject:
    """Represents a detected object in the game."""

    def __init__(self, object_type: ObjectType, position: Tuple[int, int], 
                 confidence: float, bounding_box: Tuple[int, int, int, int]):
        """
        Initialize a detected object.

        Args:
            object_type: Type of object
            position: (x, y) position
            confidence: Detection confidence (0-1)
            bounding_box: (x, y, width, height)
        """
        self.object_type = object_type
        self.position = position
        self.confidence = confidence
        self.bounding_box = bounding_box


class ObjectDetector:
    """Detects enemies, items, and other game objects."""

    def __init__(self, confidence_threshold: float = 0.5, nms_threshold: float = 0.4):
        """
        Initialize the object detector.

        Args:
            confidence_threshold: Minimum confidence for detection
            nms_threshold: Non-maximum suppression threshold
        """
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        
        # Color ranges for different objects (HSV format)
        self.color_ranges = {
            ObjectType.HEART: ([0, 100, 100], [10, 255, 255]),  # Red
            ObjectType.RUPEE: ([35, 100, 100], [85, 255, 255]),  # Green
            ObjectType.KEY: ([20, 100, 100], [30, 255, 255]),    # Yellow
        }

    def detect_objects(self, image: np.ndarray) -> List[DetectedObject]:
        """
        Detect all objects in the image.

        Args:
            image: Input image (BGR format)

        Returns:
            List of detected objects
        """
        detected_objects = []
        
        # Detect objects by color
        for obj_type, (lower, upper) in self.color_ranges.items():
            objects = self._detect_by_color(image, obj_type, lower, upper)
            detected_objects.extend(objects)
        
        # Detect enemies by motion/shape
        enemies = self._detect_enemies(image)
        detected_objects.extend(enemies)
        
        # Apply non-maximum suppression to remove overlapping detections
        detected_objects = self._apply_nms(detected_objects)
        
        return detected_objects

    def _detect_by_color(self, image: np.ndarray, object_type: ObjectType,
                        lower_bound: List[int], upper_bound: List[int]) -> List[DetectedObject]:
        """
        Detect objects by color range.

        Args:
            image: Input image
            object_type: Type of object to detect
            lower_bound: Lower HSV bound
            upper_bound: Upper HSV bound

        Returns:
            List of detected objects
        """
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Create mask
            lower = np.array(lower_bound)
            upper = np.array(upper_bound)
            mask = cv2.inRange(hsv, lower, upper)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            objects = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 50:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    center = (x + w // 2, y + h // 2)
                    confidence = min(area / 1000.0, 1.0)  # Simple confidence based on size
                    
                    obj = DetectedObject(object_type, center, confidence, (x, y, w, h))
                    objects.append(obj)
            
            return objects
        except Exception as e:
            logger.error(f"Color detection failed: {e}")
            return []

    def _detect_enemies(self, image: np.ndarray) -> List[DetectedObject]:
        """
        Detect enemies using pattern matching.

        Args:
            image: Input image

        Returns:
            List of detected enemies
        """
        # Placeholder for enemy detection
        # In a real implementation, this would use template matching or ML
        return []

    def detect_chests(self, image: np.ndarray) -> List[DetectedObject]:
        """
        Detect treasure chests.

        Args:
            image: Input image

        Returns:
            List of detected chests
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find rectangular objects (chests are typically rectangular)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            chests = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 200 < area < 2000:  # Chest size range
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h if h > 0 else 0
                    
                    # Chests are roughly square
                    if 0.8 < aspect_ratio < 1.2:
                        center = (x + w // 2, y + h // 2)
                        confidence = 0.7
                        obj = DetectedObject(ObjectType.CHEST, center, confidence, (x, y, w, h))
                        chests.append(obj)
            
            return chests
        except Exception as e:
            logger.error(f"Chest detection failed: {e}")
            return []

    def detect_doors(self, image: np.ndarray) -> List[DetectedObject]:
        """
        Detect doors/exits.

        Args:
            image: Input image

        Returns:
            List of detected doors
        """
        # Placeholder for door detection
        return []

    def _apply_nms(self, objects: List[DetectedObject]) -> List[DetectedObject]:
        """
        Apply non-maximum suppression to remove overlapping detections.

        Args:
            objects: List of detected objects

        Returns:
            Filtered list of objects
        """
        if not objects:
            return []
        
        # Simple NMS based on overlap
        filtered = []
        for obj in objects:
            overlapping = False
            for existing in filtered:
                if self._is_overlapping(obj.bounding_box, existing.bounding_box):
                    if obj.confidence > existing.confidence:
                        filtered.remove(existing)
                    else:
                        overlapping = True
                        break
            
            if not overlapping:
                filtered.append(obj)
        
        return filtered

    def _is_overlapping(self, box1: Tuple[int, int, int, int], 
                       box2: Tuple[int, int, int, int]) -> bool:
        """
        Check if two bounding boxes overlap.

        Args:
            box1: First bounding box (x, y, w, h)
            box2: Second bounding box (x, y, w, h)

        Returns:
            bool: True if boxes overlap
        """
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

    def get_closest_object(self, objects: List[DetectedObject], 
                          reference_point: Tuple[int, int]) -> Optional[DetectedObject]:
        """
        Get the closest object to a reference point.

        Args:
            objects: List of detected objects
            reference_point: (x, y) reference position

        Returns:
            Closest object or None
        """
        if not objects:
            return None
        
        min_distance = float('inf')
        closest = None
        
        for obj in objects:
            dx = obj.position[0] - reference_point[0]
            dy = obj.position[1] - reference_point[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest = obj
        
        return closest
