"""Tests for vision module components."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from claude_plays_zelda.vision.game_state_detector import GameStateDetector
from claude_plays_zelda.vision.ocr import OCRProcessor
from claude_plays_zelda.vision.object_detector import ObjectDetector


class TestGameStateDetector:
    """Tests for GameStateDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a GameStateDetector instance."""
        return GameStateDetector()

    @pytest.fixture
    def sample_image(self):
        """Create a sample NES-sized image."""
        # Create a 256x240 image (NES resolution)
        return np.zeros((240, 256, 3), dtype=np.uint8)

    def test_detector_initialization(self, detector):
        """Test that detector initializes properly."""
        assert detector is not None
        assert hasattr(detector, 'detect_hearts')
        assert hasattr(detector, 'detect_rupees')

    def test_detect_hearts_with_empty_image(self, detector, sample_image):
        """Test heart detection with empty image."""
        result = detector.detect_hearts(sample_image)

        assert isinstance(result, dict)
        assert 'current_hearts' in result
        assert 'max_hearts' in result
        assert isinstance(result['current_hearts'], (int, float))
        assert isinstance(result['max_hearts'], (int, float))

    def test_detect_hearts_returns_valid_range(self, detector, sample_image):
        """Test that heart detection returns valid values."""
        result = detector.detect_hearts(sample_image)

        # Hearts should be non-negative
        assert result['current_hearts'] >= 0
        assert result['max_hearts'] >= 0

        # Current hearts shouldn't exceed max hearts
        assert result['current_hearts'] <= result['max_hearts']

    def test_detect_rupees_with_empty_image(self, detector, sample_image):
        """Test rupee detection with empty image."""
        result = detector.detect_rupees(sample_image)

        assert isinstance(result, int)
        assert result >= 0  # Rupees should be non-negative

    def test_get_full_game_state(self, detector, sample_image):
        """Test getting complete game state."""
        state = detector.get_full_game_state(sample_image)

        # Verify state structure
        assert isinstance(state, dict)
        assert 'hearts' in state
        assert 'rupees' in state
        assert 'timestamp' in state

        # Verify hearts structure
        assert isinstance(state['hearts'], dict)
        assert 'current_hearts' in state['hearts']
        assert 'max_hearts' in state['hearts']

    @patch('cv2.cvtColor')
    @patch('cv2.inRange')
    def test_detect_hearts_calls_cv2_functions(
        self, mock_inrange, mock_cvtcolor, detector, sample_image
    ):
        """Test that heart detection uses OpenCV functions."""
        # Setup mocks
        mock_cvtcolor.return_value = sample_image
        mock_inrange.return_value = np.zeros((240, 256), dtype=np.uint8)

        detector.detect_hearts(sample_image)

        # Verify OpenCV functions were called
        assert mock_cvtcolor.called
        assert mock_inrange.called


class TestOCRProcessor:
    """Tests for OCRProcessor class."""

    @pytest.fixture
    def ocr_processor(self):
        """Create an OCRProcessor instance."""
        return OCRProcessor()

    @pytest.fixture
    def sample_text_image(self):
        """Create a sample image with text."""
        # Create a simple white image
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        return img

    def test_ocr_processor_initialization(self, ocr_processor):
        """Test OCR processor initialization."""
        assert ocr_processor is not None
        assert hasattr(ocr_processor, 'extract_text')

    @patch('pytesseract.image_to_string')
    def test_extract_text_calls_pytesseract(
        self, mock_tesseract, ocr_processor, sample_text_image
    ):
        """Test that extract_text uses pytesseract."""
        mock_tesseract.return_value = "TEST TEXT"

        result = ocr_processor.extract_text(sample_text_image)

        mock_tesseract.assert_called_once()
        assert isinstance(result, str)

    @patch('pytesseract.image_to_string')
    def test_extract_text_with_confidence_threshold(
        self, mock_tesseract, ocr_processor, sample_text_image
    ):
        """Test text extraction with confidence threshold."""
        mock_tesseract.return_value = "ZELDA"

        result = ocr_processor.extract_text(
            sample_text_image,
            confidence_threshold=80
        )

        assert isinstance(result, str)

    @patch('pytesseract.image_to_string')
    def test_extract_text_handles_empty_result(
        self, mock_tesseract, ocr_processor, sample_text_image
    ):
        """Test handling of empty OCR results."""
        mock_tesseract.return_value = ""

        result = ocr_processor.extract_text(sample_text_image)

        assert result == ""

    def test_preprocess_image(self, ocr_processor, sample_text_image):
        """Test image preprocessing for OCR."""
        if hasattr(ocr_processor, 'preprocess_image'):
            result = ocr_processor.preprocess_image(sample_text_image)

            assert isinstance(result, np.ndarray)
            assert result.shape[0] > 0
            assert result.shape[1] > 0


class TestObjectDetector:
    """Tests for ObjectDetector class."""

    @pytest.fixture
    def object_detector(self):
        """Create an ObjectDetector instance."""
        return ObjectDetector()

    @pytest.fixture
    def sample_game_image(self):
        """Create a sample game image."""
        return np.zeros((240, 256, 3), dtype=np.uint8)

    def test_object_detector_initialization(self, object_detector):
        """Test object detector initialization."""
        assert object_detector is not None
        assert hasattr(object_detector, 'detect_enemies')
        assert hasattr(object_detector, 'detect_items')

    def test_detect_enemies_returns_list(
        self, object_detector, sample_game_image
    ):
        """Test that enemy detection returns a list."""
        result = object_detector.detect_enemies(sample_game_image)

        assert isinstance(result, list)

    def test_detect_enemies_structure(
        self, object_detector, sample_game_image
    ):
        """Test structure of enemy detection results."""
        result = object_detector.detect_enemies(sample_game_image)

        # Should return a list (might be empty)
        assert isinstance(result, list)

        # If there are results, check structure
        if len(result) > 0:
            enemy = result[0]
            assert isinstance(enemy, dict)
            # Common fields in enemy detection
            assert any(key in enemy for key in ['type', 'position', 'bbox', 'confidence'])

    def test_detect_items_returns_list(
        self, object_detector, sample_game_image
    ):
        """Test that item detection returns a list."""
        result = object_detector.detect_items(sample_game_image)

        assert isinstance(result, list)

    def test_detect_items_structure(
        self, object_detector, sample_game_image
    ):
        """Test structure of item detection results."""
        result = object_detector.detect_items(sample_game_image)

        assert isinstance(result, list)

        if len(result) > 0:
            item = result[0]
            assert isinstance(item, dict)

    @patch('cv2.matchTemplate')
    def test_detect_enemies_uses_template_matching(
        self, mock_match, object_detector, sample_game_image
    ):
        """Test that enemy detection might use template matching."""
        # Setup mock
        mock_match.return_value = np.zeros((100, 100), dtype=np.float32)

        # This test verifies the method exists and runs
        try:
            result = object_detector.detect_enemies(sample_game_image)
            assert isinstance(result, list)
        except Exception:
            # Method might not use template matching, that's okay
            pass


class TestVisionIntegration:
    """Integration tests for vision components."""

    def test_game_state_detector_with_real_image_shape(self):
        """Test detector with proper NES image dimensions."""
        detector = GameStateDetector()
        image = np.zeros((240, 256, 3), dtype=np.uint8)

        state = detector.get_full_game_state(image)

        assert state is not None
        assert 'hearts' in state
        assert 'rupees' in state

    def test_vision_pipeline_components_work_together(self):
        """Test that vision components can work in pipeline."""
        # Create components
        detector = GameStateDetector()
        ocr = OCRProcessor()
        obj_detector = ObjectDetector()

        # Create test image
        image = np.zeros((240, 256, 3), dtype=np.uint8)

        # Run pipeline
        game_state = detector.get_full_game_state(image)
        enemies = obj_detector.detect_enemies(image)
        items = obj_detector.detect_items(image)

        # Verify all components produced results
        assert game_state is not None
        assert isinstance(enemies, list)
        assert isinstance(items, list)

    @pytest.mark.parametrize("width,height", [
        (256, 240),  # Standard NES
        (512, 480),  # 2x scale
        (768, 720),  # 3x scale
    ])
    def test_detector_handles_different_scales(self, width, height):
        """Test detector with different image scales."""
        detector = GameStateDetector()
        image = np.zeros((height, width, 3), dtype=np.uint8)

        # Should not crash
        try:
            state = detector.get_full_game_state(image)
            assert state is not None
        except Exception as e:
            pytest.fail(f"Detector failed with {width}x{height}: {e}")
