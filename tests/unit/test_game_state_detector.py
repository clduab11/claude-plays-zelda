"""Unit tests for game state detector with menu detection logic."""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch, MagicMock
from claude_plays_zelda.vision.game_state_detector import GameStateDetector


class TestGameStateDetectorWithConfig:
    """Tests for GameStateDetector with configuration support."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = Mock()
        config.game = {
            'detection': {
                'min_hearts': 3,
                'max_hearts': 20,
                'heart_min_area': 50,
                'heart_max_area': 500,
                'ocr_retry_attempts': 3,
                'ocr_retry_delay': 0.1,
                'title_screen_cache_duration': 0.5,
            },
            'combat': {
                'change_ratio_threshold': 0.15,
            }
        }
        return config

    @pytest.fixture
    def detector(self, mock_config):
        """Create a GameStateDetector with mock config."""
        return GameStateDetector(config=mock_config)

    @pytest.fixture
    def detector_no_config(self):
        """Create a GameStateDetector without config."""
        return GameStateDetector(config=None)

    @pytest.fixture
    def sample_image(self):
        """Create a sample NES-sized image."""
        return np.zeros((240, 256, 3), dtype=np.uint8)

    def test_detector_initialization_with_config(self, detector):
        """Test that detector initializes with config values."""
        assert detector.min_hearts == 3
        assert detector.max_hearts == 20
        assert detector.heart_min_area == 50
        assert detector.heart_max_area == 500
        assert detector.ocr_retry_attempts == 3
        assert detector.ocr_retry_delay == 0.1
        assert detector.title_screen_cache_duration == 0.5
        assert detector.combat_change_ratio == 0.15

    def test_detector_initialization_without_config(self, detector_no_config):
        """Test that detector uses defaults without config."""
        assert detector_no_config.min_hearts == 3
        assert detector_no_config.max_hearts == 20
        assert detector_no_config.heart_min_area == 50
        assert detector_no_config.heart_max_area == 500

    def test_ocr_instance_caching(self, detector, sample_image):
        """Test that OCR instance is cached and reused."""
        with patch('claude_plays_zelda.vision.game_state_detector.GameOCR') as mock_ocr_class:
            mock_ocr = Mock()
            mock_ocr.extract_text.return_value = "ZELDA"
            mock_ocr_class.return_value = mock_ocr

            # First call should create OCR instance
            detector.detect_title_screen(sample_image)
            assert mock_ocr_class.call_count == 1

            # Second call should reuse cached instance
            detector.detect_title_screen(sample_image, force_refresh=True)
            assert mock_ocr_class.call_count == 1  # Still 1, instance was reused

    def test_title_screen_detection_caching(self, detector, sample_image):
        """Test that title screen detection uses caching."""
        with patch.object(detector, '_detect_title_screen_with_retry') as mock_detect:
            mock_detect.return_value = True

            # First call should perform detection
            result1 = detector.detect_title_screen(sample_image)
            assert result1 is True
            assert mock_detect.call_count == 1

            # Second call within cache duration should use cache
            result2 = detector.detect_title_screen(sample_image)
            assert result2 is True
            assert mock_detect.call_count == 1  # Still 1, used cache

    def test_title_screen_detection_cache_expiration(self, detector, sample_image):
        """Test that cache expires after duration."""
        with patch.object(detector, '_detect_title_screen_with_retry') as mock_detect:
            mock_detect.return_value = True

            # First call
            detector.detect_title_screen(sample_image)
            assert mock_detect.call_count == 1

            # Simulate cache expiration
            detector._title_screen_cache_time = time.time() - 1.0  # 1 second ago

            # Second call should refresh
            detector.detect_title_screen(sample_image)
            assert mock_detect.call_count == 2

    def test_title_screen_detection_force_refresh(self, detector, sample_image):
        """Test that force_refresh bypasses cache."""
        with patch.object(detector, '_detect_title_screen_with_retry') as mock_detect:
            mock_detect.return_value = True

            # First call
            detector.detect_title_screen(sample_image)
            assert mock_detect.call_count == 1

            # Force refresh should bypass cache
            detector.detect_title_screen(sample_image, force_refresh=True)
            assert mock_detect.call_count == 2

    def test_title_screen_detection_with_retry_success(self, detector, sample_image):
        """Test retry logic succeeds on first attempt."""
        with patch.object(detector, '_get_ocr_instance') as mock_get_ocr:
            mock_ocr = Mock()
            mock_ocr.extract_text.return_value = "THE LEGEND OF ZELDA"
            mock_get_ocr.return_value = mock_ocr

            result = detector._detect_title_screen_with_retry(sample_image)
            assert result is True
            assert mock_ocr.extract_text.call_count == 1

    def test_title_screen_detection_with_retry_failure_then_success(self, detector, sample_image):
        """Test retry logic succeeds after initial failures."""
        with patch.object(detector, '_get_ocr_instance') as mock_get_ocr:
            mock_ocr = Mock()
            # Fail twice, then succeed
            mock_ocr.extract_text.side_effect = [
                Exception("OCR failed"),
                Exception("OCR failed again"),
                "ZELDA"
            ]
            mock_get_ocr.return_value = mock_ocr

            result = detector._detect_title_screen_with_retry(sample_image)
            assert result is True
            assert mock_ocr.extract_text.call_count == 3

    def test_title_screen_detection_all_retries_fail(self, detector, sample_image):
        """Test retry logic fails after max attempts."""
        with patch.object(detector, '_get_ocr_instance') as mock_get_ocr:
            mock_ocr = Mock()
            mock_ocr.extract_text.side_effect = Exception("OCR failed")
            mock_get_ocr.return_value = mock_ocr

            result = detector._detect_title_screen_with_retry(sample_image)
            assert result is False
            assert mock_ocr.extract_text.call_count == 3  # ocr_retry_attempts

    def test_title_screen_detection_keywords(self, detector, sample_image):
        """Test that all keywords trigger positive detection."""
        keywords = ["ZELDA", "LEGEND", "REGISTER", "ELIMINATION", "NAME"]

        for keyword in keywords:
            with patch.object(detector, '_get_ocr_instance') as mock_get_ocr:
                mock_ocr = Mock()
                mock_ocr.extract_text.return_value = f"Some text with {keyword.lower()} in it"
                mock_get_ocr.return_value = mock_ocr

                result = detector._detect_title_screen_with_retry(sample_image)
                assert result is True, f"Keyword '{keyword}' should trigger detection"

    def test_detect_gameplay_hud_with_valid_hearts(self, detector, sample_image):
        """Test HUD detection with valid heart count."""
        with patch.object(detector, 'detect_hearts') as mock_hearts, \
             patch.object(detector, 'detect_title_screen') as mock_title:
            mock_hearts.return_value = {"current_hearts": 5, "max_hearts": 8}
            mock_title.return_value = False

            result = detector.detect_gameplay_hud(sample_image)
            assert result is True

    def test_detect_gameplay_hud_hearts_too_low(self, detector, sample_image):
        """Test HUD detection rejects heart count below minimum."""
        with patch.object(detector, 'detect_hearts') as mock_hearts:
            mock_hearts.return_value = {"current_hearts": 1, "max_hearts": 2}

            result = detector.detect_gameplay_hud(sample_image)
            assert result is False

    def test_detect_gameplay_hud_hearts_too_high(self, detector, sample_image):
        """Test HUD detection rejects heart count above maximum."""
        with patch.object(detector, 'detect_hearts') as mock_hearts:
            mock_hearts.return_value = {"current_hearts": 25, "max_hearts": 25}

            result = detector.detect_gameplay_hud(sample_image)
            assert result is False

    def test_detect_gameplay_hud_on_title_screen(self, detector, sample_image):
        """Test HUD detection rejects if on title screen."""
        with patch.object(detector, 'detect_hearts') as mock_hearts, \
             patch.object(detector, 'detect_title_screen') as mock_title:
            mock_hearts.return_value = {"current_hearts": 5, "max_hearts": 8}
            mock_title.return_value = True  # On title screen

            result = detector.detect_gameplay_hud(sample_image)
            assert result is False

    def test_detect_gameplay_hud_exception_handling(self, detector, sample_image):
        """Test HUD detection handles exceptions gracefully."""
        with patch.object(detector, 'detect_hearts') as mock_hearts:
            mock_hearts.side_effect = Exception("Heart detection failed")

            result = detector.detect_gameplay_hud(sample_image)
            assert result is False

    def test_count_hearts_uses_config_thresholds(self, detector):
        """Test that _count_hearts uses configurable area thresholds."""
        # Create a mask with various sized contours
        mask = np.zeros((100, 100), dtype=np.uint8)

        # Draw contours of different sizes
        # Small contour (area < min_area): should be filtered out
        mask[10:15, 10:15] = 255  # area = 25 < 50

        # Valid contour (min_area < area < max_area): should be counted
        mask[30:40, 30:40] = 255  # area = 100, within [50, 500]
        mask[50:60, 50:60] = 255  # area = 100, within [50, 500]

        # Large contour (area > max_area): should be filtered out
        mask[70:95, 70:95] = 255  # area = 625 > 500

        count = detector._count_hearts(mask)
        assert count == 2  # Only the two valid-sized hearts

    def test_is_in_combat_uses_config_threshold(self, detector, sample_image):
        """Test that combat detection uses configurable threshold."""
        # Create two images with significant difference
        image1 = np.zeros((240, 256, 3), dtype=np.uint8)
        image2 = np.ones((240, 256, 3), dtype=np.uint8) * 255

        # This should trigger combat detection (100% change > 15% threshold)
        result = detector.is_in_combat(image2, image1)
        assert result is True

    def test_is_in_combat_below_threshold(self, detector, sample_image):
        """Test combat detection below threshold."""
        # Create two very similar images (minimal change)
        image1 = np.zeros((240, 256, 3), dtype=np.uint8)
        image2 = np.zeros((240, 256, 3), dtype=np.uint8)
        image2[0:5, 0:5] = 255  # Small change

        result = detector.is_in_combat(image2, image1)
        # Change ratio is very small, should be below threshold
        assert result is False

    def test_is_in_combat_no_previous_frame(self, detector, sample_image):
        """Test combat detection with no previous frame."""
        result = detector.is_in_combat(sample_image, None)
        assert result is False


class TestGameStateDetectorIntegration:
    """Integration tests for GameStateDetector."""

    def test_full_detection_pipeline(self):
        """Test complete detection pipeline."""
        detector = GameStateDetector(config=None)
        image = np.zeros((240, 256, 3), dtype=np.uint8)

        # Should not crash
        state = detector.get_full_game_state(image)
        assert state is not None
        assert "is_in_game" in state
        assert "is_title_screen" in state

    def test_custom_config_values(self):
        """Test detector with custom configuration values."""
        config = Mock()
        config.game = {
            'detection': {
                'min_hearts': 5,  # Custom minimum
                'max_hearts': 15,  # Custom maximum
                'heart_min_area': 100,
                'heart_max_area': 300,
                'ocr_retry_attempts': 5,
                'ocr_retry_delay': 0.2,
                'title_screen_cache_duration': 1.0,
            },
            'combat': {
                'change_ratio_threshold': 0.25,
            }
        }

        detector = GameStateDetector(config=config)

        assert detector.min_hearts == 5
        assert detector.max_hearts == 15
        assert detector.heart_min_area == 100
        assert detector.heart_max_area == 300
        assert detector.ocr_retry_attempts == 5
        assert detector.ocr_retry_delay == 0.2
        assert detector.title_screen_cache_duration == 1.0
        assert detector.combat_change_ratio == 0.25
