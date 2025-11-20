"""
Pixels-to-Actions Agent - Core SIMA 2-inspired VLM agent.

This is the heart of the refactored architecture:
- Receives raw pixel inputs (no OCR/CV preprocessing)
- Uses VLM for direct visual reasoning
- Outputs structured hierarchical decisions
- Maintains temporal awareness via filmstrip
- Self-improves through critic feedback
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image
from loguru import logger

try:
    from anthropic import Anthropic, APIError, APITimeoutError
except ImportError:
    logger.error("anthropic library not installed. Run: pip install anthropic")
    raise

from .action_schema import ActionDecision, ActionSchema, ThreatLevel
from .temporal_buffer import TemporalBuffer
from .memory_critic import MemoryCritic
from .vision_prompts import VisionPrompts


class PixelsToActionsAgent:
    """
    SIMA 2-inspired agent that maps visual inputs directly to controller actions.

    Architecture:
    1. Frame Buffer: Maintains 3-frame temporal window
    2. VLM Vision: Sends filmstrip to Claude for visual analysis
    3. Hierarchical Reasoning: Observation → Threat → Strategy → Tactic → Action
    4. Critic Loop: Learns from failures and injects lessons
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        enable_critic: bool = True,
        memory_file: str = "data/knowledge_base/lessons.json",
        thought_log: str = "logs/agent_thought_process.log"
    ):
        """
        Initialize the Pixels-to-Actions agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Max tokens for VLM responses
            temperature: Sampling temperature
            enable_critic: Enable self-improvement loop
            memory_file: Path to persistent lessons storage
            thought_log: Path to thought process log
        """
        # VLM client
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Temporal awareness
        self.temporal_buffer = TemporalBuffer(buffer_size=3, filmstrip_orientation="horizontal")

        # Memory and self-improvement
        self.memory_critic = MemoryCritic(
            anthropic_client=self.client,
            memory_file=memory_file,
            enable_critic=enable_critic
        )

        # Prompts
        self.prompts = VisionPrompts()

        # State tracking
        self.last_action: Optional[ActionDecision] = None
        self.current_objective: Optional[str] = None
        self.consecutive_low_confidence = 0
        self.total_decisions = 0
        self.thought_log = thought_log

        # Error handling
        self.api_timeout_count = 0
        self.max_retries = 3

        # Performance tracking
        self.decision_times: List[float] = []

        logger.info(f"PixelsToActionsAgent initialized: model={model}, critic={'enabled' if enable_critic else 'disabled'}")

    async def decide_action(
        self,
        current_frame: Image.Image,
        health: Optional[int] = None,
        max_health: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActionDecision:
        """
        Decide the next action based on visual input.

        This is the main decision loop:
        1. Add frame to temporal buffer
        2. Create filmstrip
        3. Build context (lessons, objectives, health)
        4. Call VLM with vision API
        5. Parse hierarchical response
        6. Log to memory

        Args:
            current_frame: Current game screenshot (PIL Image)
            health: Link's current health (hearts)
            max_health: Link's maximum health
            metadata: Additional metadata (rupees, location, etc.)

        Returns:
            ActionDecision with controller output
        """
        start_time = datetime.now()

        try:
            # Add frame to temporal buffer
            self.temporal_buffer.add_frame(current_frame)

            # Build context
            is_critical_health = self._is_critical_health(health, max_health)
            health_status = self._format_health_status(health, max_health)

            # Get relevant lessons from memory
            context_str = self._build_context_string(health_status, metadata)
            relevant_lessons = self.memory_critic.get_relevant_lessons(
                context=context_str,
                max_lessons=3
            )
            lessons_text = [lesson.lesson_text for lesson in relevant_lessons]

            # Make decision with VLM
            decision = await self._call_vlm_decision(
                previous_action=self.last_action.immediate_tactic if self.last_action else None,
                lessons=lessons_text,
                objective=self.current_objective,
                health_status=health_status,
                is_critical_health=is_critical_health
            )

            # Validate decision
            if not ActionSchema.validate_action(decision):
                logger.warning("Invalid action generated, using fallback")
                decision = self._create_safe_fallback()

            # Track confidence
            if decision.confidence < 0.5:
                self.consecutive_low_confidence += 1
                logger.warning(f"Low confidence decision: {decision.confidence:.2f} (consecutive: {self.consecutive_low_confidence})")
            else:
                self.consecutive_low_confidence = 0

            # Log to memory
            self.memory_critic.add_frame_action(
                frame=current_frame,
                action_description=decision.immediate_tactic,
                health=health,
                threat_level=decision.threat_assessment.value
            )

            # Update state
            self.last_action = decision
            self.total_decisions += 1

            # Performance tracking
            decision_time = (datetime.now() - start_time).total_seconds()
            self.decision_times.append(decision_time)

            # Log thought process
            self._log_thought_process(decision, decision_time)

            logger.info(f"Decision #{self.total_decisions}: {decision.immediate_tactic} ({decision.confidence:.2f})")

            return decision

        except APITimeoutError:
            logger.error("API timeout, using fallback action")
            self.api_timeout_count += 1
            return self._handle_timeout()
        except APIError as e:
            logger.error(f"API error: {e}")
            return self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in decide_action: {e}", exc_info=True)
            return self._create_safe_fallback()

    async def _call_vlm_decision(
        self,
        previous_action: Optional[str],
        lessons: List[str],
        objective: Optional[str],
        health_status: str,
        is_critical_health: bool
    ) -> ActionDecision:
        """
        Call VLM with vision input and get decision.

        Args:
            previous_action: Last action taken
            lessons: Relevant lessons to inject
            objective: Current objective
            health_status: Health description
            is_critical_health: Whether health is critical

        Returns:
            ActionDecision
        """
        # Create filmstrip
        filmstrip_b64 = self.temporal_buffer.get_filmstrip_base64(format="PNG")
        if filmstrip_b64 is None:
            logger.error("Failed to create filmstrip")
            return self._create_safe_fallback()

        # Build prompt
        user_prompt = self.prompts.format_decision_request(
            previous_action=previous_action,
            lessons=lessons,
            objective=objective,
            health_status=health_status,
            is_critical_health=is_critical_health
        )

        # Build messages
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": filmstrip_b64
                    }
                },
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        }]

        # Call VLM
        logger.debug(f"Calling VLM: {self.model}")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.prompts.get_system_prompt(),
            messages=messages
        )

        # Parse response
        response_text = response.content[0].text
        decision = ActionSchema.parse_vlm_response(response_text)

        # Reset timeout counter on success
        self.api_timeout_count = 0

        return decision

    def _is_critical_health(self, health: Optional[int], max_health: Optional[int]) -> bool:
        """Check if health is critical."""
        if health is None or max_health is None:
            return False
        return health <= 1 or health <= max_health * 0.2

    def _format_health_status(self, health: Optional[int], max_health: Optional[int]) -> str:
        """Format health status description."""
        if health is None:
            return "Unknown"

        if max_health is None:
            return f"{health} hearts"

        percentage = (health / max_health) * 100
        if percentage <= 10:
            return f"CRITICAL: {health}/{max_health} hearts ({percentage:.0f}%)"
        elif percentage <= 30:
            return f"Low: {health}/{max_health} hearts ({percentage:.0f}%)"
        elif percentage <= 60:
            return f"Moderate: {health}/{max_health} hearts ({percentage:.0f}%)"
        else:
            return f"Good: {health}/{max_health} hearts ({percentage:.0f}%)"

    def _build_context_string(self, health_status: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Build context string for lesson retrieval."""
        parts = [health_status]

        if metadata:
            if "location" in metadata:
                parts.append(metadata["location"])
            if "in_dungeon" in metadata and metadata["in_dungeon"]:
                parts.append("dungeon")
            if "enemies_nearby" in metadata and metadata["enemies_nearby"]:
                parts.append("combat")

        return " ".join(parts)

    def _create_safe_fallback(self) -> ActionDecision:
        """Create a safe fallback action (pause)."""
        return ActionDecision(
            visual_observation="Error occurred, pausing for safety",
            threat_assessment=ThreatLevel.NONE,
            strategic_goal="Pause and recover from error",
            immediate_tactic="Open menu to pause game",
            controller_output=ActionSchema._create_fallback_action("").controller_output,
            confidence=0.0
        )

    def _handle_timeout(self) -> ActionDecision:
        """Handle API timeout."""
        if self.last_action and self.last_action.confidence > 0.6:
            logger.info("Timeout: Repeating last successful action")
            return self.last_action
        else:
            logger.info("Timeout: Using safe fallback")
            return self._create_safe_fallback()

    def _handle_api_error(self, error: APIError) -> ActionDecision:
        """Handle API errors."""
        logger.error(f"API Error: {error}")
        return self._create_safe_fallback()

    def _log_thought_process(self, decision: ActionDecision, decision_time: float) -> None:
        """Log detailed thought process to file."""
        try:
            import os
            os.makedirs(os.path.dirname(self.thought_log), exist_ok=True)

            with open(self.thought_log, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Decision #{self.total_decisions} - {datetime.now().isoformat()}\n")
                f.write(f"Time: {decision_time:.3f}s\n")
                f.write(f"{'='*80}\n")
                f.write(f"OBSERVATION: {decision.visual_observation}\n")
                f.write(f"THREAT: {decision.threat_assessment.value.upper()} - {decision.threat_details}\n")
                f.write(f"STRATEGY: {decision.strategic_goal}\n")
                f.write(f"TACTIC: {decision.immediate_tactic}\n")
                f.write(f"ACTION: {decision.controller_output.buttons} ({decision.controller_output.duration_ms}ms)\n")
                f.write(f"CONFIDENCE: {decision.confidence:.2f}\n")
                f.write(f"\n")

        except Exception as e:
            logger.error(f"Failed to log thought process: {e}")

    async def on_death_detected(self, context: Optional[str] = None) -> None:
        """
        Handle death detection and trigger critic analysis.

        Args:
            context: Additional context about where/how death occurred
        """
        logger.warning("DEATH DETECTED - Triggering critic analysis")

        lesson = await self.memory_critic.analyze_failure(
            failure_type="death",
            context=context,
            frames_to_analyze=10
        )

        if lesson:
            logger.info(f"Lesson learned: {lesson.lesson_text}")
        else:
            logger.warning("Failed to generate lesson from death")

    def set_objective(self, objective: str) -> None:
        """
        Set the current high-level objective.

        Args:
            objective: Objective description (e.g., "Find the first dungeon")
        """
        self.current_objective = objective
        logger.info(f"Objective set: {objective}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Returns:
            Statistics dictionary
        """
        avg_decision_time = sum(self.decision_times[-100:]) / len(self.decision_times[-100:]) if self.decision_times else 0

        return {
            "model": self.model,
            "total_decisions": self.total_decisions,
            "avg_decision_time_ms": avg_decision_time * 1000,
            "api_timeout_count": self.api_timeout_count,
            "consecutive_low_confidence": self.consecutive_low_confidence,
            "current_objective": self.current_objective,
            "temporal_buffer": self.temporal_buffer.get_buffer_info(),
            "memory": self.memory_critic.get_statistics()
        }

    def export_lessons(self, output_file: str = "lessons_export.txt") -> None:
        """
        Export learned lessons to a file.

        Args:
            output_file: Path to output file
        """
        self.memory_critic.export_lessons(output_file)

    def reset_session(self) -> None:
        """Reset session state (but keep learned lessons)."""
        self.temporal_buffer.clear()
        self.memory_critic.clear_short_term_memory()
        self.last_action = None
        self.consecutive_low_confidence = 0
        logger.info("Session reset (lessons preserved)")

    async def close(self) -> None:
        """Cleanup and shutdown."""
        logger.info("Shutting down PixelsToActionsAgent")
        # Save final state
        self.memory_critic._save_lessons()
