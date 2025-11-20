"""
SIMA 2-Inspired Pixels-to-Actions Architecture

This module implements a VLM-based agent that reasons directly from visual inputs,
replacing the traditional OCR/CV pipeline with multimodal foundation models.

Core Principles:
- Pixels-to-Actions: VLM receives raw frames, not text descriptions
- Hierarchical Reasoning: Observation → Reasoning → Planning → Action
- Self-Improvement: Critic system learns from failures
- Temporal Awareness: Filmstrip input for motion detection
"""

from .action_schema import ActionDecision, ActionSchema, ControllerOutput
from .pixels_to_actions_agent import PixelsToActionsAgent
from .temporal_buffer import TemporalBuffer
from .memory_critic import MemoryCritic
from .vision_prompts import VisionPrompts

__all__ = [
    "PixelsToActionsAgent",
    "ActionDecision",
    "ActionSchema",
    "ControllerOutput",
    "TemporalBuffer",
    "MemoryCritic",
    "VisionPrompts",
]
