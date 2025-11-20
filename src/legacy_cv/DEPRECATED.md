# DEPRECATED: Legacy Computer Vision Module

**Status**: This module is deprecated as of the SIMA 2-inspired refactor.

**Reason**: Replaced by VLM-based "Pixels-to-Actions" architecture in `src/sima/`

## Why This Was Deprecated

The original architecture used a traditional OCR/CV pipeline:

```
Screenshot → OpenCV → Tesseract → Text JSON → Claude Text API → Action
```

**Problems with this approach:**
1. **Brittle Heuristics**: Manual color detection for hearts, enemies, Link's position
2. **Loss of Information**: Converting rich visual data to sparse text loses critical context
3. **Maintenance Burden**: Each new game element requires new CV code
4. **No Temporal Context**: Single frames can't detect motion/velocity

## The New SIMA 2 Architecture

Replaced by:
```
Screenshot Buffer (3 frames) → Filmstrip → Claude Vision API →
{observation, reasoning, plan, action} → Controller
```

**Benefits:**
1. **Direct Visual Reasoning**: VLM sees pixels, no preprocessing needed
2. **Temporal Awareness**: 3-frame filmstrip enables motion detection
3. **Self-Improvement**: Critic system learns from failures
4. **Hierarchical Reasoning**: Explicit observation → threat → strategy → action chain

## Migration Guide

**Old code:**
```python
from src.cv import GameStateAnalyzer

analyzer = GameStateAnalyzer()
game_state = analyzer.analyze(screen)  # Returns text summary
state_summary = analyzer.get_state_summary(game_state)
```

**New code:**
```python
from src.sima import PixelsToActionsAgent

agent = PixelsToActionsAgent(api_key=api_key)
decision = await agent.decide_action(
    current_frame=screen,  # Sends image directly to VLM
    health=3,
    max_health=6
)
# Returns ActionDecision with controller output
```

## Legacy Files

- `ocr_engine.py`: Tesseract-based text extraction (pytesseract)
- `game_state_analyzer.py`: OpenCV heuristics for hearts, enemies, etc.
- `object_detector.py`: Template matching for game objects
- `map_recognizer.py`: Map location identification

## Keeping Legacy Code

This code is preserved (not deleted) for:
1. **A/B Testing**: Compare legacy vs SIMA performance
2. **Fallback**: If VLM API is unavailable
3. **Reference**: Educational comparison of approaches

## References

- **New Architecture**: `src/sima/`
- **Documentation**: `src/sima/README.md`
- **Research**: SIMA 2 (Google DeepMind) - Multimodal agents for game playing

---

**Last Updated**: 2025-11-20
**Deprecated By**: SIMA 2-inspired refactor
