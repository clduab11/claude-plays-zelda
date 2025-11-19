"""OCR engine for reading in-game text."""

from typing import List, Optional, Tuple
import cv2
import numpy as np
import pytesseract
from loguru import logger


class OCREngine:
    """Optical Character Recognition for game text."""

    def __init__(self, language: str = "eng", confidence_threshold: int = 60):
        """
        Initialize the OCR engine.

        Args:
            language: Tesseract language code
            confidence_threshold: Minimum confidence for text detection (0-100)
        """
        self.language = language
        self.confidence_threshold = confidence_threshold

    def read_text(self, image: np.ndarray, preprocess: bool = True) -> str:
        """
        Extract text from an image.

        Args:
            image: Input image (BGR format)
            preprocess: Whether to preprocess the image

        Returns:
            str: Extracted text
        """
        try:
            if preprocess:
                image = self._preprocess_image(image)
            
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(image, lang=self.language)
            text = text.strip()
            
            logger.debug(f"OCR extracted text: {text}")
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def read_text_with_confidence(self, image: np.ndarray, preprocess: bool = True) -> List[Tuple[str, float]]:
        """
        Extract text with confidence scores.

        Args:
            image: Input image
            preprocess: Whether to preprocess the image

        Returns:
            List of (text, confidence) tuples
        """
        try:
            if preprocess:
                image = self._preprocess_image(image)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, lang=self.language, output_type=pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > self.confidence_threshold:
                    text = data['text'][i].strip()
                    if text:
                        confidence = float(data['conf'][i]) / 100.0
                        results.append((text, confidence))
            
            return results
        except Exception as e:
            logger.error(f"OCR with confidence failed: {e}")
            return []

    def detect_dialog_box(self, image: np.ndarray) -> bool:
        """
        Detect if a dialog box is present in the image.

        Args:
            image: Input image

        Returns:
            bool: True if dialog box detected
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Look for rectangular regions (dialog boxes are typically rectangular)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Dialog boxes are typically large
                if area > 5000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    # Dialog boxes are typically wide rectangles
                    if 1.5 < aspect_ratio < 4.0:
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Dialog box detection failed: {e}")
            return False

    def read_dialog(self, image: np.ndarray) -> str:
        """
        Read text from a dialog box.

        Args:
            image: Input image

        Returns:
            str: Dialog text
        """
        # Extract bottom portion where dialog typically appears in Zelda
        height = image.shape[0]
        dialog_region = image[int(height * 0.7):, :]
        
        return self.read_text(dialog_region, preprocess=True)

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.

        Args:
            image: Input image

        Returns:
            numpy.ndarray: Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Resize for better OCR (tesseract works better with larger images)
        scale = 2
        width = int(gray.shape[1] * scale)
        height = int(gray.shape[0] * scale)
        resized = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
        
        # Apply thresholding
        _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised

    def detect_numbers(self, image: np.ndarray) -> List[int]:
        """
        Detect numbers in an image (useful for health, rupees, etc.).

        Args:
            image: Input image

        Returns:
            List of detected numbers
        """
        try:
            # Configure tesseract for digits only
            custom_config = r'--oem 3 --psm 6 outputbase digits'
            text = pytesseract.image_to_string(image, config=custom_config)
            
            # Extract numbers
            numbers = []
            for word in text.split():
                try:
                    numbers.append(int(word))
                except ValueError:
                    continue
            
            return numbers
        except Exception as e:
            logger.error(f"Number detection failed: {e}")
            return []
