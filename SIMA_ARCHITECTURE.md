# SIMA 2-Inspired Architecture Refactor

## Overview

This document describes the architectural transformation of the `claude-plays-zelda` agent from a traditional OCR/CV pipeline to a **Vision-Language Model (VLM) based "Pixels-to-Actions" architecture**, inspired by Google DeepMind's SIMA 2 research.

## Motivation

### Problems with the Old Architecture

The original system used a brittle OCR/CV pipeline:

```
Screenshot → OpenCV (hearts detection) → Tesseract (text) → Text JSON → Claude Text API → Action
```

**Issues:**
1. **Information Loss**: Rich visual data reduced to sparse text
2. **Brittle Heuristics**: Manual color detection (hearts, enemies) breaks easily
3. **No Temporal Context**: Single frames can't detect motion/velocity
4. **Maintenance Burden**: New game elements require new CV code
5. **Scalability**: Doesn't generalize to other games

### The New Approach

Direct VLM reasoning from pixels:

```
Screenshot Buffer (3 frames) → Filmstrip → Claude Vision API → Structured Decision → Controller
```

**Benefits:**
1. **Direct Visual Reasoning**: VLM sees pixels, understands context
2. **Temporal Awareness**: Multi-frame input enables motion detection
3. **Self-Improvement**: Critic learns from failures
4. **Hierarchical Reasoning**: Explicit observation → threat → strategy → action
5. **Generalizable**: Can adapt to other games with prompt changes

## Architecture Components

### 1. Core Module: `src/sima/`

**New Files:**
- `pixels_to_actions_agent.py` - Main VLM agent
- `action_schema.py` - Structured output definitions
- `temporal_buffer.py` - 3-frame filmstrip manager
- `memory_critic.py` - Self-improvement system
- `vision_prompts.py` - System prompts

**Key Innovation:** The agent maintains a 3-frame temporal buffer and sends a "filmstrip" to the VLM, allowing it to detect:
- Enemy movement directions
- Projectile velocities
- Link's motion state
- Animation progress

### 2. Hierarchical Reasoning

The VLM outputs a structured decision chain:

```json
{
  "visual_observation": "Link in stone corridor, red Moblin 3 tiles north...",
  "threat_assessment": "high",
  "threat_details": "Moblin charging, Link at 2 hearts",
  "strategic_goal": "Exit room to the east",
  "immediate_tactic": "Dodge east while attacking",
  "controller_output": {
    "buttons": ["RIGHT", "A"],
    "duration_ms": 300,
    "hold": false
  },
  "confidence": 0.85
}
```

This mirrors human decision-making and provides explainability.

### 3. Self-Improvement (Critic Loop)

When the agent dies:
1. **Critic analyzes** the last 10 actions/frames
2. **Generates a lesson** (e.g., "Don't engage Darknuts with low health")
3. **Saves to persistent memory** (`data/knowledge_base/lessons.json`)
4. **Future decisions** retrieve relevant lessons via context matching

**Example lesson:**
> "Avoid combat when health is below 2 hearts. Retreat and find hearts first. Context: Dungeon, low health"

### 4. Legacy Code Handling

**Deprecated (moved to `src/legacy_cv/`):**
- `ocr_engine.py` - Tesseract OCR
- `game_state_analyzer.py` - OpenCV heuristics
- `object_detector.py` - Template matching
- `map_recognizer.py` - Map detection

**Why keep it?**
- A/B testing (compare legacy vs SIMA performance)
- Fallback if VLM API unavailable
- Educational reference

### 5. Integration Adapter

`src/agent/sima_adapter.py` provides a compatibility layer:

```python
# Legacy code can use SIMA agent with minimal changes
adapter = SimaAgentAdapter(api_key=api_key)

# Accepts numpy arrays (OpenCV format)
response = adapter.get_action(screen_np_array, game_state)

# Returns legacy format
# {"action": "move_up", "reason": "...", "confidence": 0.85}
```

## Usage

### Basic Example

```python
import asyncio
from PIL import Image
from src.sima import PixelsToActionsAgent

agent = PixelsToActionsAgent(
    api_key="your-anthropic-api-key",
    enable_critic=True
)

# Set objective
agent.set_objective("Find the first dungeon")

# Game loop
async def game_loop():
    screen = capture_screenshot()  # PIL Image

    decision = await agent.decide_action(
        current_frame=screen,
        health=3,
        max_health=6
    )

    execute_controller_output(decision.controller_output)

    # On death
    if detect_game_over():
        await agent.on_death_detected(context="Dungeon Level 1")

asyncio.run(game_loop())
```

### Integration with Existing Code

**Option 1: Direct replacement** (in `main.py`):
```python
# Old
from src.agent import ClaudeClient
client = ClaudeClient(api_key)
action = client.get_action(state_summary, context)

# New
from src.agent.sima_adapter import SimaAgentAdapter
adapter = SimaAgentAdapter(api_key)
action = adapter.get_action(screen, game_state)
```

**Option 2: A/B testing** (run both agents):
```python
legacy_action = legacy_client.get_action(state_summary)
sima_action = sima_adapter.get_action(screen, game_state)

# Choose based on config/performance
action = sima_action if use_sima else legacy_action
```

## Configuration

### Environment Variables
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SIMA_CRITIC_ENABLED="true"
```

### Config File (`config.yaml`)

Add SIMA section:
```yaml
agent:
  type: "sima"  # or "legacy" for old agent
  sima:
    model: "claude-3-5-sonnet-20241022"
    enable_critic: true
    buffer_size: 3
    decision_interval: 0.5
  legacy:
    # ... existing config
```

## Performance Characteristics

| Metric | Legacy | SIMA |
|--------|--------|------|
| API Call Type | Text | Vision |
| Cost per Decision | ~$0.001 | ~$0.01-0.02 |
| Decision Time | 0.5-1s | 1-3s |
| Preprocessing | Heavy (OCR/CV) | None |
| Temporal Awareness | ❌ | ✅ (3 frames) |
| Self-Improvement | ❌ | ✅ (Critic) |
| Explainability | Low | High (hierarchical) |

**Recommendations:**
- Decision interval: 0.5-1.0 seconds
- Use async to prevent blocking
- Enable critic after initial testing

## File Structure

```
src/
├── sima/                          # NEW: SIMA 2 architecture
│   ├── pixels_to_actions_agent.py # Main agent
│   ├── action_schema.py           # Structured outputs
│   ├── temporal_buffer.py         # Filmstrip manager
│   ├── memory_critic.py           # Self-improvement
│   ├── vision_prompts.py          # Prompts
│   └── README.md                  # Documentation
├── legacy_cv/                     # MOVED: Legacy CV code
│   ├── ocr_engine.py
│   ├── game_state_analyzer.py
│   └── DEPRECATED.md              # Migration guide
├── agent/
│   ├── sima_adapter.py            # NEW: Integration adapter
│   └── ...                        # Existing agent code
└── ...

data/knowledge_base/               # NEW: Persistent memory
└── lessons.json                   # Learned lessons

logs/
└── agent_thought_process.log      # NEW: Detailed reasoning traces
```

## Testing

### Unit Tests
```bash
pytest tests/unit/test_sima_agent.py
```

### Integration Test
```bash
python examples/sima_agent_demo.py
```

### A/B Comparison
```bash
python scripts/compare_agents.py --legacy --sima --episodes 10
```

## Debugging

### Thought Process Logs
```bash
tail -f logs/agent_thought_process.log
```

Example output:
```
================================================================================
Decision #42 - 2025-11-20T12:34:56
Time: 1.234s
================================================================================
OBSERVATION: Link faces north in stone corridor. Red Moblin 3 tiles ahead, moving south.
THREAT: HIGH - Moblin charging pattern detected across frames
STRATEGY: Exit room to preserve health
TACTIC: Dodge east toward door
ACTION: ['RIGHT'] (400ms)
CONFIDENCE: 0.82
```

### Visualize Filmstrip
```python
filmstrip = agent.temporal_buffer.create_annotated_filmstrip()
filmstrip.save("debug_filmstrip.png")
```

### View Learned Lessons
```python
agent.export_lessons("my_lessons.txt")
```

## Migration Checklist

- [x] Create SIMA architecture modules
- [x] Move legacy CV to `src/legacy_cv/`
- [x] Add deprecation notices
- [x] Create integration adapter
- [x] Update documentation
- [ ] Update `main.py` with SIMA support
- [ ] Update `config.yaml` with SIMA options
- [ ] Add A/B testing script
- [ ] Update tests
- [ ] Performance benchmarking

## Future Enhancements

1. **Vector Embeddings**: Semantic search for lesson retrieval
2. **Multi-Agent**: Separate agents for combat, exploration, puzzles
3. **Reward Shaping**: Learn from positive outcomes (not just failures)
4. **Hierarchical Planning**: Long-term goal trees
5. **Transfer Learning**: Apply lessons across different Zelda dungeons

## References

- **SIMA 2 Research**: Google DeepMind (multimodal game agents)
- **Claude Vision API**: https://docs.anthropic.com/claude/docs/vision
- **Original Repo**: https://github.com/clduab11/claude-plays-zelda

## Questions & Support

- **Documentation**: `src/sima/README.md`
- **Examples**: `examples/sima_agent_demo.py`
- **Issues**: GitHub Issues

---

**Status**: ✅ Phase 1 Complete (Core Architecture)
**Next**: Integration testing and performance optimization
**Last Updated**: 2025-11-20
