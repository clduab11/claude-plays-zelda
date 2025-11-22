# refactor: Improve game start logic robustness and add configuration options

## Summary

This PR improves the game start menu detection and navigation logic by making it more configurable, robust, and testable. The changes address several hardcoded values and potential edge cases identified in recent commits.

### Key Improvements

- **Configuration-driven**: All magic numbers moved to `config.yaml` for easy tuning
- **Performance**: OCR instance caching and title screen detection caching (0.5s)
- **Reliability**: Retry logic for transient OCR failures (up to 3 attempts)
- **Observability**: Enhanced debug logging for state transitions
- **Testability**: Comprehensive unit tests (600+ lines) covering edge cases

## Problem Statement

The current implementation had several hardcoded values and potential edge cases:

### Hardcoded Values
- Heart count range (3-20) hardcoded in `game_state_detector.py:92`
- Stability threshold (10 frames) hardcoded in `game_loop.py:83`
- Button delays (0.5s, 2.0s) hardcoded in `game_loop.py:103, 107`
- Heart contour area (50-500) hardcoded in `game_state_detector.py:196-197`
- Combat change ratio (0.15) hardcoded in `game_state_detector.py:370`

### Performance Issues
- New `GameOCR()` instance created on every `detect_title_screen()` call
- Title screen detection runs every frame with expensive OCR preprocessing
- No caching of OCR results despite infrequent title screen changes

### Reliability Issues
- No retry logic for transient OCR failures
- OCR may misread pixelated NES graphics
- Emulator lag could cause false negatives

### Testing Gaps
- No tests for `detect_title_screen()` or `detect_gameplay_hud()`
- No tests for state machine transitions
- Limited edge case coverage

## Changes Made

See full details in PR_DESCRIPTION.md
