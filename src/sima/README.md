# SIMA 2-Inspired Pixels-to-Actions Architecture

## Overview

This module implements a **Vision-Language Model (VLM) based agent** that plays Zelda by reasoning directly from pixel inputs, inspired by Google DeepMind's SIMA 2 research.

## Architecture Principles

### 1. Pixels-to-Actions Core

**No intermediate representations.** The VLM receives raw screenshots, not text descriptions.

```
Traditional (Deprecated):
Screenshot → OCR → Text → LLM → Action

SIMA 2 (This Module):
Screenshot → VLM → Action
```

### 2. Hierarchical Reasoning

The agent outputs a **structured reasoning chain**:

```json
{
  "visual_observation": "What I see (Link, enemies, environment)",
  "threat_assessment": "none | low | medium | high | critical",
  "threat_details": "Specific threats and their states",
  "strategic_goal": "High-level objective",
  "immediate_tactic": "Short-term action to achieve goal",
  "controller_output": {
    "buttons": ["UP", "A"],
    "duration_ms": 300,
    "hold": false
  },
  "confidence": 0.85
}
```

This mirrors human decision-making: **Observe → Assess → Plan → Act**

### 3. Temporal Awareness (Filmstrip)

**Single frames lack motion data.** The agent receives a **filmstrip of 3 consecutive frames**:

```
[Frame T-2 | Frame T-1 | Frame T]
```

This allows the VLM to detect:
- Enemy movement directions
- Projectile velocities
- Link's motion state
- Animation progress

### 4. Self-Improvement (Critic Loop)

When the agent dies, the **Critic** analyzes the failure:

1. Review last 10 actions and frames
2. Identify the mistake
3. Generate a lesson
4. Save to persistent memory (`data/knowledge_base/lessons.json`)
5. Inject relevant lessons into future decisions

**Example lesson:**
> "Don't engage Darknuts in narrow corridors when health is below 2 hearts. Retreat and find health first."

## Module Structure

```
src/sima/
├── __init__.py                      # Public API
├── pixels_to_actions_agent.py       # Main agent (start here)
├── action_schema.py                 # Structured output definitions
├── temporal_buffer.py               # 3-frame filmstrip manager
├── memory_critic.py                 # Self-improvement system
├── vision_prompts.py                # System prompts for VLM
└── README.md                        # This file
```

## Quick Start

### Basic Usage

```python
import asyncio
from PIL import Image
from src.sima import PixelsToActionsAgent

# Initialize agent
agent = PixelsToActionsAgent(
    api_key="your-anthropic-api-key",
    model="claude-3-5-sonnet-20241022",
    enable_critic=True
)

# Set objective
agent.set_objective("Find the first dungeon")

# Game loop
async def game_loop():
    while True:
        # Capture screenshot
        screen = capture_game_screen()  # PIL Image

        # Get decision from VLM
        decision = await agent.decide_action(
            current_frame=screen,
            health=3,
            max_health=6,
            metadata={"location": "Overworld", "in_dungeon": False}
        )

        # Execute action
        execute_buttons(
            buttons=decision.controller_output.buttons,
            duration_ms=decision.controller_output.duration_ms
        )

        # Check for death
        if detect_game_over(screen):
            await agent.on_death_detected(context="Dungeon Level 1")

asyncio.run(game_loop())
```

### Integration with Existing Code

See `main.py` for full integration example. The agent can coexist with legacy CV code for A/B testing.

## API Reference

### PixelsToActionsAgent

**Main agent class.**

```python
agent = PixelsToActionsAgent(
    api_key: str,                    # Anthropic API key
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 2048,
    temperature: float = 0.7,
    enable_critic: bool = True,      # Enable self-improvement
    memory_file: str = "data/knowledge_base/lessons.json",
    thought_log: str = "logs/agent_thought_process.log"
)
```

**Methods:**

- `decide_action(frame, health, max_health, metadata)` → `ActionDecision`
  - Main decision method
  - Returns structured action with reasoning

- `on_death_detected(context)` → `None`
  - Trigger critic analysis after death
  - Generates and saves lesson

- `set_objective(objective)` → `None`
  - Set high-level goal (e.g., "Find dungeon")

- `get_statistics()` → `Dict`
  - Get performance stats

- `export_lessons(output_file)` → `None`
  - Export learned lessons to file

### ActionDecision

**Structured decision output.**

```python
@dataclass
class ActionDecision:
    visual_observation: str          # What the agent sees
    threat_assessment: ThreatLevel   # none|low|medium|high|critical
    threat_details: str              # Specific threat info
    strategic_goal: str              # High-level goal
    immediate_tactic: str            # Short-term action
    controller_output: ControllerOutput
    confidence: float                # 0.0-1.0
    reasoning_trace: str             # Full VLM response
```

### ControllerOutput

**Low-level controller output.**

```python
@dataclass
class ControllerOutput:
    buttons: List[str]               # ["UP", "A", ...]
    duration_ms: int = 200           # Hold duration
    hold: bool = False               # Hold vs tap
```

## Configuration

### Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional
export SIMA_LOG_LEVEL="INFO"
export SIMA_CRITIC_ENABLED="true"
```

### Files

- `data/knowledge_base/lessons.json` - Persistent lessons storage
- `logs/agent_thought_process.log` - Detailed reasoning traces

## Performance

**API Calls:**
- 1 call per decision (typical: 1-3 seconds)
- Includes base64-encoded filmstrip (~50-100KB)

**Recommendations:**
- Decision interval: 0.5-1.0 seconds
- Use async to prevent blocking
- Enable caching for repeated frames

## Comparison: Legacy vs SIMA

| Aspect | Legacy CV | SIMA 2 |
|--------|-----------|--------|
| Input | Text summary | Raw pixels (filmstrip) |
| Preprocessing | OCR + OpenCV | None |
| Motion Detection | ❌ | ✅ (3-frame buffer) |
| Self-Improvement | ❌ | ✅ (Critic loop) |
| Maintenance | High (new CV code per feature) | Low (VLM adapts) |
| Reasoning | Implicit | Explicit (hierarchical) |
| API Calls | Text-only | Vision API |
| Cost per Decision | ~$0.001 | ~$0.01-0.02 |

## Debugging

### Enable Verbose Logging

```python
import logging
logging.getLogger("src.sima").setLevel(logging.DEBUG)
```

### Inspect Thought Process

```bash
tail -f logs/agent_thought_process.log
```

Example output:
```
================================================================================
Decision #42 - 2025-11-20T12:34:56
Time: 1.234s
================================================================================
OBSERVATION: Link faces north in stone corridor. Red Moblin 3 tiles ahead.
THREAT: HIGH - Moblin charging pattern, Link at 2 hearts
STRATEGY: Survive and exit room via east door
TACTIC: Dodge east while attacking
ACTION: ['RIGHT', 'A'] (300ms)
CONFIDENCE: 0.82
```

### Visualize Filmstrip

```python
filmstrip = agent.temporal_buffer.create_annotated_filmstrip()
filmstrip.save("debug_filmstrip.png")
```

## Lessons System

### View Learned Lessons

```python
agent.export_lessons("my_lessons.txt")
```

### Manual Lesson Addition

```python
from src.sima.memory_critic import Lesson
from datetime import datetime

lesson = Lesson(
    lesson_text="Avoid water without flippers",
    context="Overworld exploration",
    cause_of_failure="Drowned in lake",
    timestamp=datetime.now()
)
agent.memory_critic.add_lesson(lesson)
```

### Lesson Retrieval

Lessons are auto-retrieved based on:
- Context similarity (keyword matching)
- Confidence scores
- Usage frequency (diversity)

## Advanced Topics

### Custom Prompts

```python
from src.sima import VisionPrompts

# Override system prompt
custom_prompts = VisionPrompts()
agent.prompts = custom_prompts
```

### Error Handling

The agent has built-in fallbacks:
- **API Timeout**: Repeat last successful action
- **Parse Error**: Pause game (press START)
- **Low Confidence**: Conservative defensive actions

### Async Best Practices

```python
# Good: Non-blocking
decision = await agent.decide_action(frame)

# Bad: Blocking (don't use)
# decision = asyncio.run(agent.decide_action(frame))
```

## Testing

```bash
# Run tests
pytest tests/unit/test_sima_agent.py

# Test with mock VLM
pytest tests/unit/test_sima_agent.py --mock-vlm
```

## Troubleshooting

**"No JSON found in response"**
- VLM sometimes adds preamble text
- ActionSchema.parse_vlm_response handles this
- Check logs/agent_thought_process.log for raw response

**High API costs**
- Reduce decision frequency (increase decision_interval)
- Lower max_tokens (default 2048)
- Use smaller filmstrip (reduce buffer_size to 2)

**Low confidence decisions**
- Normal for ambiguous situations
- Agent automatically uses defensive actions
- Check if lessons are relevant (may need better context strings)

## Future Enhancements

- [ ] Vector embeddings for lesson retrieval (semantic search)
- [ ] Multi-frame history analysis (5-10 frames)
- [ ] Reward shaping from game state improvements
- [ ] Hierarchical planning (long-term goal trees)
- [ ] Transfer learning across Zelda dungeons

## References

- **SIMA 2**: Google DeepMind's multimodal game-playing agents
- **Claude Vision API**: https://docs.anthropic.com/claude/docs/vision
- **Original Research**: [Insert SIMA 2 paper link when available]

## License

Same as parent project.

---

**Questions?** Check the thought process logs first, then open an issue.
