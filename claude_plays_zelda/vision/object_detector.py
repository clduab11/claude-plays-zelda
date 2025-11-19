"""Object detection for enemies, items, NPCs, and interactive elements."""

from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from pathlib import Path
from loguru import logger


class ObjectDetector:
    """Detects game objects like enemies, items, NPCs, and doors."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize object detector.

        Args:
            template_dir: Directory containing template images for matching
        """
        self.template_dir = template_dir
        self.templates: Dict[str, np.ndarray] = {}
        self.detection_threshold = 0.7  # Confidence threshold for template matching

        if template_dir:
            self._load_templates()

        logger.info("ObjectDetector initialized")

    def _load_templates(self):
        """Load template images from the template directory."""
        try:
            template_path = Path(self.template_dir)
            if not template_path.exists():
                logger.warning(f"Template directory not found: {self.template_dir}")
                return

            # Load all PNG images as templates
            for img_file in template_path.glob("*.png"):
                template = cv2.imread(str(img_file))
                if template is not None:
                    name = img_file.stem
                    self.templates[name] = template
                    logger.debug(f"Loaded template: {name}")

            logger.info(f"Loaded {len(self.templates)} templates")

        except Exception as e:
            logger.error(f"Error loading templates: {e}")

    def detect_by_template(
        self, image: np.ndarray, template_name: str, threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect objects using template matching.

        Args:
            image: Input image to search
            template_name: Name of template to match
            threshold: Confidence threshold (None = use default)

        Returns:
            List of detections with 'bbox', 'confidence', and 'center' keys
        """
        try:
            if template_name not in self.templates:
                logger.warning(f"Template not found: {template_name}")
                return []

            template = self.templates[template_name]
            threshold = threshold or self.detection_threshold

            # Perform template matching
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

            # Find locations above threshold
            locations = np.where(result >= threshold)

            detections = []
            h, w = template.shape[:2]

            for pt in zip(*locations[::-1]):
                confidence = result[pt[1], pt[0]]
                bbox = (pt[0], pt[1], w, h)
                center = (pt[0] + w // 2, pt[1] + h // 2)

                detections.append(
                    {"bbox": bbox, "confidence": float(confidence), "center": center, "type": template_name}
                )

            # Apply non-maximum suppression to remove overlapping detections
            detections = self._non_max_suppression(detections)

            logger.debug(f"Detected {len(detections)} instances of {template_name}")
            return detections

        except Exception as e:
            logger.error(f"Error in template matching: {e}")
            return []

    def detect_enemies_by_color(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect enemies using color-based segmentation.

        Args:
            image: Input game screen

        Returns:
            List of detected enemy locations
        """
        try:
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define color ranges for common enemy colors in Zelda
            # Red enemies (common in dungeons)
            red_lower1 = np.array([0, 100, 100])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 100, 100])
            red_upper2 = np.array([180, 255, 255])

            # Green enemies
            green_lower = np.array([40, 50, 50])
            green_upper = np.array([80, 255, 255])

            # Create masks
            mask_red1 = cv2.inRange(hsv, red_lower1, red_upper1)
            mask_red2 = cv2.inRange(hsv, red_lower2, red_upper2)
            mask_red = cv2.bitwise_or(mask_red1, mask_red2)
            mask_green = cv2.inRange(hsv, green_lower, green_upper)

            # Combine masks
            mask_enemies = cv2.bitwise_or(mask_red, mask_green)

            # Find contours
            contours, _ = cv2.findContours(mask_enemies, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            enemies = []
            for contour in contours:
                area = cv2.contourArea(contour)
                # Filter by size (enemies are typically 20-500 pixels)
                if 20 < area < 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    center = (x + w // 2, y + h // 2)

                    enemies.append(
                        {
                            "bbox": (x, y, w, h),
                            "center": center,
                            "area": area,
                            "type": "enemy",
                        }
                    )

            logger.debug(f"Detected {len(enemies)} potential enemies")
            return enemies

        except Exception as e:
            logger.error(f"Error detecting enemies by color: {e}")
            return []

    def detect_doors(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect doors and entrances.

        Args:
            image: Input game screen

        Returns:
            List of detected doors
        """
        try:
            # Doors in Zelda are typically darker rectangular regions
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Look for dark rectangular regions
            _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            doors = []
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # Doors are typically rectangular (4 vertices)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / float(h)

                    # Filter by aspect ratio and size
                    if 0.5 < aspect_ratio < 2.0 and w > 30 and h > 30:
                        doors.append(
                            {
                                "bbox": (x, y, w, h),
                                "center": (x + w // 2, y + h // 2),
                                "type": "door",
                            }
                        )

            logger.debug(f"Detected {len(doors)} potential doors")
            return doors

        except Exception as e:
            logger.error(f"Error detecting doors: {e}")
            return []

    def detect_items(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect collectible items (rupees, hearts, keys, etc.).

        Args:
            image: Input game screen

        Returns:
            List of detected items
        """
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define color ranges for common items
            item_colors = {
                "rupee_green": (np.array([40, 50, 50]), np.array([80, 255, 255])),
                "rupee_blue": (np.array([100, 50, 50]), np.array([130, 255, 255])),
                "rupee_red": (np.array([0, 100, 100]), np.array([10, 255, 255])),
                "heart": (np.array([0, 100, 100]), np.array([10, 255, 255])),
            }

            items = []
            for item_type, (lower, upper) in item_colors.items():
                mask = cv2.inRange(hsv, lower, upper)

                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    # Items are typically small (10-100 pixels)
                    if 10 < area < 100:
                        x, y, w, h = cv2.boundingRect(contour)
                        items.append(
                            {
                                "bbox": (x, y, w, h),
                                "center": (x + w // 2, y + h // 2),
                                "type": item_type,
                                "area": area,
                            }
                        )

            logger.debug(f"Detected {len(items)} potential items")
            return items

        except Exception as e:
            logger.error(f"Error detecting items: {e}")
            return []

    def detect_npcs(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect NPCs and interactive characters.

        Args:
            image: Input game screen

        Returns:
            List of detected NPCs
        """
        try:
            # NPCs are typically stationary and have distinct colors
            # This is a simplified detection - could be improved with templates
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Use blob detection for NPCs
            params = cv2.SimpleBlobDetector_Params()
            params.filterByArea = True
            params.minArea = 100
            params.maxArea = 1000
            params.filterByCircularity = False

            detector = cv2.SimpleBlobDetector_create(params)
            keypoints = detector.detect(gray)

            npcs = []
            for kp in keypoints:
                x, y = int(kp.pt[0]), int(kp.pt[1])
                size = int(kp.size)
                npcs.append(
                    {
                        "center": (x, y),
                        "bbox": (x - size // 2, y - size // 2, size, size),
                        "type": "npc",
                    }
                )

            logger.debug(f"Detected {len(npcs)} potential NPCs")
            return npcs

        except Exception as e:
            logger.error(f"Error detecting NPCs: {e}")
            return []

    def detect_all_objects(self, image: np.ndarray) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect all types of objects in the image.

        Args:
            image: Input game screen

        Returns:
            Dictionary with object types as keys and detection lists as values
        """
        return {
            "enemies": self.detect_enemies_by_color(image),
            "doors": self.detect_doors(image),
            "items": self.detect_items(image),
            "npcs": self.detect_npcs(image),
        }

    def _non_max_suppression(
        self, detections: List[Dict[str, Any]], overlap_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Apply non-maximum suppression to remove overlapping detections.

        Args:
            detections: List of detections with 'bbox' and 'confidence' keys
            overlap_threshold: IoU threshold for considering boxes as overlapping

        Returns:
            Filtered list of detections
        """
        if not detections:
            return []

        # Sort by confidence
        detections = sorted(detections, key=lambda x: x.get("confidence", 1.0), reverse=True)

        keep = []
        while detections:
            current = detections.pop(0)
            keep.append(current)

            # Remove overlapping detections
            detections = [
                det
                for det in detections
                if self._calculate_iou(current["bbox"], det["bbox"]) < overlap_threshold
            ]

        return keep

    def _calculate_iou(self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.

        Args:
            box1: First box as (x, y, w, h)
            box2: Second box as (x, y, w, h)

        Returns:
            IoU value between 0 and 1
        """
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)

        # Calculate union
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0

    def visualize_detections(
        self, image: np.ndarray, detections: Dict[str, List[Dict[str, Any]]]
    ) -> np.ndarray:
        """
        Draw bounding boxes on image for all detections.

        Args:
            image: Input image
            detections: Dictionary of detections from detect_all_objects()

        Returns:
            Image with bounding boxes drawn
        """
        output = image.copy()

        colors = {
            "enemies": (0, 0, 255),  # Red
            "doors": (255, 0, 0),  # Blue
            "items": (0, 255, 0),  # Green
            "npcs": (255, 255, 0),  # Cyan
        }

        for obj_type, obj_list in detections.items():
            color = colors.get(obj_type, (255, 255, 255))

            for obj in obj_list:
                x, y, w, h = obj["bbox"]
                cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    output,
                    obj["type"],
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )

        return output
