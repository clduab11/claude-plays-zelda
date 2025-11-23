"""OCR system for reading in-game text and dialogue."""

import re
from typing import Optional, List, Dict, Any
import cv2
import numpy as np
import pytesseract
from PIL import Image
from loguru import logger


class GameOCR:
    """Handles text extraction from game screens using OCR."""

    def __init__(
        self,
        tesseract_config: str = "--psm 6 --oem 3",
        preprocess: bool = True,
    ):
        """
        Initialize OCR system.

        Args:
            tesseract_config: Configuration string for Tesseract
            preprocess: Whether to preprocess images before OCR
        """
        self.tesseract_config = tesseract_config
        self.preprocess = preprocess
        self.last_dialogue = ""
        
        # Auto-detect Tesseract path if not in PATH
        self._configure_tesseract()
        
        logger.info("GameOCR initialized")

    def _configure_tesseract(self):
        """Configure Tesseract path if not found in PATH."""
        import shutil
        import os
        
        # Check if tesseract is in PATH
        if shutil.which("tesseract"):
            return
            
        # Common installation paths on Windows
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Found Tesseract at: {path}")
                pytesseract.pytesseract.tesseract_cmd = path
                return
                
        logger.warning("Tesseract not found in PATH or common locations. OCR may fail.")

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.

        Args:
            image: Input image (BGR format)

        Returns:
            Preprocessed image
        """
        try:
            # Scale up the image (4x) using Nearest Neighbor to preserve pixel edges
            # This is crucial for NES pixel fonts
            scale = 4
            height, width = image.shape[:2]
            scaled = cv2.resize(image, (width * scale, height * scale), interpolation=cv2.INTER_NEAREST)

            # Convert to grayscale
            gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)

            # Apply thresholding to get black text on white background
            # Otsu's binarization
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Invert if text is white on black (common in NES)
            # Check average brightness - if low (dark), invert
            if np.mean(thresh) < 127:
                thresh = cv2.bitwise_not(thresh)

            # Denoise
            denoised = cv2.fastNlMeansDenoising(thresh)

            return denoised

        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image

    def extract_text(self, image: np.ndarray, preprocess: Optional[bool] = None) -> str:
        """
        Extract text from an image.

        Args:
            image: Input image (BGR or grayscale)
            preprocess: Whether to preprocess (None = use default)

        Returns:
            Extracted text string
        """
        try:
            should_preprocess = preprocess if preprocess is not None else self.preprocess

            if should_preprocess:
                processed = self.preprocess_image(image)
            else:
                processed = image

            # Convert to PIL Image if needed
            if isinstance(processed, np.ndarray):
                if len(processed.shape) == 2:  # Grayscale
                    pil_image = Image.fromarray(processed)
                else:  # BGR
                    rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb)
            else:
                pil_image = processed

            # Run OCR
            text = pytesseract.image_to_string(pil_image, config=self.tesseract_config)

            # Clean up text
            text = text.strip()

            return text

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""

    def extract_dialogue(self, image: np.ndarray, dialogue_region: Optional[tuple] = None) -> str:
        """
        Extract dialogue text from the dialogue box.

        Args:
            image: Full game screen
            dialogue_region: Tuple of (x, y, width, height) for dialogue box

        Returns:
            Extracted dialogue text
        """
        try:
            # Default dialogue box region for NES Zelda (Play area, below HUD)
            if dialogue_region is None:
                height, width = image.shape[:2]
                # HUD is top 25%, so look at the rest
                dialogue_region = (0, int(height * 0.25), width, int(height * 0.75))

            x, y, w, h = dialogue_region
            dialogue_box = image[y : y + h, x : x + w]

            # Extract text with custom config for dialogue
            text = self.extract_text(dialogue_box, preprocess=True)

            # Clean up common OCR errors in Zelda dialogue
            text = self._clean_dialogue_text(text)

            if text and text != self.last_dialogue:
                logger.info(f"Dialogue detected: {text}")
                self.last_dialogue = text

            return text

        except Exception as e:
            logger.error(f"Error extracting dialogue: {e}")
            return ""

    def _clean_dialogue_text(self, text: str) -> str:
        """
        Clean up OCR errors common in game dialogue.

        Args:
            text: Raw OCR text

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove common OCR artifacts
        text = text.replace("|", "I")
        text = text.replace("0", "O")  # In context of words

        # Remove non-printable characters
        text = re.sub(r"[^\x20-\x7E]", "", text)

        return text.strip()

    def detect_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect regions of text in the image.

        Args:
            image: Input image

        Returns:
            List of dictionaries with 'bbox' and 'text' keys
        """
        try:
            # Use Tesseract's data output to get bounding boxes
            # Preprocess first for better detection
            processed = self.preprocess_image(image)
            
            data = pytesseract.image_to_data(
                processed, config=self.tesseract_config, output_type=pytesseract.Output.DICT
            )

            text_regions = []
            n_boxes = len(data["text"])
            
            # Note: Bounding boxes will be in the scaled coordinate space!
            # We need to scale them back down if we want original coordinates.
            scale = 4 # Must match preprocess_image scale

            for i in range(n_boxes):
                # Only include regions with actual text
                if int(data["conf"][i]) > 0:
                    text = data["text"][i].strip()
                    if text:
                        text_regions.append(
                            {
                                "bbox": (
                                    int(data["left"][i] / scale),
                                    int(data["top"][i] / scale),
                                    int(data["width"][i] / scale),
                                    int(data["height"][i] / scale),
                                ),
                                "text": text,
                                "confidence": data["conf"][i],
                            }
                        )

            return text_regions

        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
            return []

    def read_menu_text(self, image: np.ndarray) -> List[str]:
        """
        Read menu items from the screen.

        Args:
            image: Image of menu screen

        Returns:
            List of menu item texts
        """
        text_regions = self.detect_text_regions(image)

        # Sort by vertical position (top to bottom)
        text_regions.sort(key=lambda r: r["bbox"][1])

        menu_items = [region["text"] for region in text_regions if region["confidence"] > 60]

        return menu_items

    def is_text_present(self, image: np.ndarray, target_text: str, threshold: float = 0.8) -> bool:
        """
        Check if specific text is present in the image.

        Args:
            image: Input image
            target_text: Text to search for
            threshold: Similarity threshold (0-1)

        Returns:
            True if text is found
        """
        extracted = self.extract_text(image)
        extracted_lower = extracted.lower()
        target_lower = target_text.lower()

        # Simple substring match
        if target_lower in extracted_lower:
            return True

        # Fuzzy match for OCR errors
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, extracted_lower, target_lower).ratio()
        return similarity >= threshold
