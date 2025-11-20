"""
Memory and Critic system for self-improvement.

Implements the "Critic Loop" from SIMA 2:
1. Detects failures (death, stuck states)
2. Analyzes what went wrong
3. Generates lessons
4. Stores lessons in persistent memory
5. Retrieves relevant lessons for context injection
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os
from collections import deque
from loguru import logger
from PIL import Image

try:
    from anthropic import Anthropic, APIError
except ImportError:
    logger.warning("Anthropic library not available for MemoryCritic")
    Anthropic = None


@dataclass
class FrameActionPair:
    """Pair of frame and action taken."""
    frame: Optional[Image.Image]
    action_description: str
    timestamp: datetime
    health: Optional[int] = None
    threat_level: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding frame image)."""
        return {
            "action_description": self.action_description,
            "timestamp": self.timestamp.isoformat(),
            "health": self.health,
            "threat_level": self.threat_level
        }


@dataclass
class Lesson:
    """A lesson learned from failure."""
    lesson_text: str
    context: str  # Where/when this lesson applies
    cause_of_failure: str
    timestamp: datetime
    confidence: float = 1.0
    times_referenced: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lesson_text": self.lesson_text,
            "context": self.context,
            "cause_of_failure": self.cause_of_failure,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "times_referenced": self.times_referenced
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lesson':
        """Create from dictionary."""
        return cls(
            lesson_text=data.get("lesson_text", ""),
            context=data.get("context", ""),
            cause_of_failure=data.get("cause_of_failure", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            confidence=data.get("confidence", 1.0),
            times_referenced=data.get("times_referenced", 0)
        )


class MemoryCritic:
    """
    Self-improvement system through failure analysis.

    Maintains:
    - Short-term memory: Recent frames and actions
    - Long-term memory: Lessons learned from failures
    - Context retrieval: Get relevant lessons for current situation
    """

    def __init__(
        self,
        anthropic_client: Optional[Any] = None,
        memory_file: str = "data/knowledge_base/lessons.json",
        short_term_size: int = 100,
        enable_critic: bool = True
    ):
        """
        Initialize memory and critic system.

        Args:
            anthropic_client: Anthropic client for failure analysis
            memory_file: Path to persistent lessons storage
            short_term_size: Size of short-term memory buffer
            enable_critic: Whether to enable automatic failure analysis
        """
        self.client = anthropic_client
        self.memory_file = memory_file
        self.enable_critic = enable_critic and anthropic_client is not None

        # Short-term memory (recent gameplay)
        self.short_term_memory: deque[FrameActionPair] = deque(maxlen=short_term_size)

        # Long-term memory (lessons learned)
        self.lessons: List[Lesson] = []

        # Statistics
        self.total_failures = 0
        self.total_lessons = 0

        # Load existing lessons
        self._load_lessons()

        logger.info(f"MemoryCritic initialized: {len(self.lessons)} lessons loaded, critic={'enabled' if self.enable_critic else 'disabled'}")

    def add_frame_action(
        self,
        frame: Optional[Image.Image],
        action_description: str,
        health: Optional[int] = None,
        threat_level: Optional[str] = None
    ) -> None:
        """
        Add a frame-action pair to short-term memory.

        Args:
            frame: Game frame (PIL Image)
            action_description: Text description of action taken
            health: Link's current health
            threat_level: Current threat assessment
        """
        pair = FrameActionPair(
            frame=frame,
            action_description=action_description,
            timestamp=datetime.now(),
            health=health,
            threat_level=threat_level
        )
        self.short_term_memory.append(pair)

    async def analyze_failure(
        self,
        failure_type: str = "death",
        context: Optional[str] = None,
        frames_to_analyze: int = 10
    ) -> Optional[Lesson]:
        """
        Analyze a failure and generate a lesson.

        Args:
            failure_type: Type of failure ("death", "stuck", "damage")
            context: Additional context about the failure
            frames_to_analyze: Number of recent frames to analyze

        Returns:
            Generated Lesson or None
        """
        if not self.enable_critic:
            logger.info("Critic disabled, skipping failure analysis")
            return None

        if not self.short_term_memory:
            logger.warning("No short-term memory to analyze")
            return None

        self.total_failures += 1

        logger.info(f"Analyzing {failure_type} failure (frames: {frames_to_analyze})")

        try:
            # Get recent history
            recent_history = list(self.short_term_memory)[-frames_to_analyze:]

            # Create analysis prompt
            history_text = self._format_history_for_analysis(recent_history)

            prompt = f"""**FAILURE ANALYSIS**

Failure Type: {failure_type}
Context: {context or 'Unknown'}

**Recent Actions:**
{history_text}

**Task**: Analyze what went wrong and generate a lesson to prevent this in the future.

Output JSON:
{{
  "cause_of_failure": "Immediate cause (e.g., 'Moblin charge attack')",
  "mistake": "What decision was wrong (e.g., 'Engaged enemy with critical health')",
  "lesson": "Concise lesson (1-2 sentences, e.g., 'Avoid combat when health is critical. Retreat to find hearts first.')",
  "context": "When this applies (e.g., 'Low health in dungeon')"
}}"""

            # Call VLM for analysis (text-only, no images for now)
            response = await self._call_critic_llm(prompt)

            # Parse response
            lesson = self._parse_lesson_response(response, context or failure_type)

            if lesson:
                self.add_lesson(lesson)
                logger.info(f"Generated lesson: {lesson.lesson_text}")
                return lesson
            else:
                logger.warning("Failed to generate lesson from analysis")
                return None

        except Exception as e:
            logger.error(f"Failure analysis error: {e}")
            return None

    def _format_history_for_analysis(self, history: List[FrameActionPair]) -> str:
        """Format history for text-based analysis."""
        lines = []
        for i, pair in enumerate(history):
            health_str = f"HP:{pair.health}" if pair.health is not None else "HP:?"
            threat_str = f"Threat:{pair.threat_level}" if pair.threat_level else ""
            lines.append(f"{i+1}. {pair.action_description} [{health_str} {threat_str}]")
        return "\n".join(lines)

    async def _call_critic_llm(self, prompt: str) -> str:
        """
        Call the VLM for failure analysis.

        Args:
            prompt: Analysis prompt

        Returns:
            VLM response text
        """
        if self.client is None:
            raise ValueError("No Anthropic client available")

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.3,  # Lower temperature for analytical tasks
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Critic LLM call failed: {e}")
            raise

    def _parse_lesson_response(self, response: str, default_context: str) -> Optional[Lesson]:
        """Parse VLM response into a Lesson."""
        import re

        try:
            # Extract JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                logger.warning("No JSON found in lesson response")
                return None

            data = json.loads(json_match.group(0))

            lesson = Lesson(
                lesson_text=data.get("lesson", ""),
                context=data.get("context", default_context),
                cause_of_failure=data.get("cause_of_failure", "Unknown"),
                timestamp=datetime.now(),
                confidence=0.8  # Initial confidence
            )

            return lesson

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse lesson JSON: {e}")
            return None

    def add_lesson(self, lesson: Lesson) -> None:
        """
        Add a lesson to long-term memory.

        Args:
            lesson: Lesson to add
        """
        self.lessons.append(lesson)
        self.total_lessons += 1
        self._save_lessons()
        logger.info(f"Added lesson to memory: {lesson.lesson_text[:50]}...")

    def get_relevant_lessons(
        self,
        context: str,
        max_lessons: int = 3,
        min_confidence: float = 0.5
    ) -> List[Lesson]:
        """
        Retrieve relevant lessons for current context.

        Args:
            context: Current situation description
            max_lessons: Maximum number of lessons to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of relevant lessons
        """
        if not self.lessons:
            return []

        # Simple keyword-based retrieval (can be upgraded to embeddings later)
        context_lower = context.lower()
        scored_lessons = []

        for lesson in self.lessons:
            if lesson.confidence < min_confidence:
                continue

            # Calculate relevance score
            score = 0.0

            # Check context match
            if lesson.context.lower() in context_lower or context_lower in lesson.context.lower():
                score += 2.0

            # Check keyword overlap
            lesson_words = set(lesson.lesson_text.lower().split())
            context_words = set(context_lower.split())
            overlap = len(lesson_words & context_words)
            score += overlap * 0.1

            # Boost by confidence
            score *= lesson.confidence

            # Penalize overused lessons (diversity)
            score /= (1 + lesson.times_referenced * 0.1)

            scored_lessons.append((score, lesson))

        # Sort by score and return top lessons
        scored_lessons.sort(key=lambda x: x[0], reverse=True)
        relevant = [lesson for score, lesson in scored_lessons[:max_lessons]]

        # Increment reference count
        for lesson in relevant:
            lesson.times_referenced += 1

        logger.debug(f"Retrieved {len(relevant)} relevant lessons for context: {context[:50]}")
        return relevant

    def format_lessons_for_context(self, lessons: List[Lesson]) -> str:
        """
        Format lessons for injection into VLM context.

        Args:
            lessons: List of lessons

        Returns:
            Formatted string
        """
        if not lessons:
            return ""

        lines = ["**LESSONS LEARNED** (from past failures):"]
        for i, lesson in enumerate(lessons, 1):
            lines.append(f"{i}. {lesson.lesson_text} [Context: {lesson.context}]")

        return "\n".join(lines)

    def _save_lessons(self) -> None:
        """Save lessons to persistent storage."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

            # Convert lessons to dictionaries
            data = {
                "lessons": [lesson.to_dict() for lesson in self.lessons],
                "metadata": {
                    "total_failures": self.total_failures,
                    "total_lessons": self.total_lessons,
                    "last_updated": datetime.now().isoformat()
                }
            }

            # Write to file
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.lessons)} lessons to {self.memory_file}")

        except Exception as e:
            logger.error(f"Failed to save lessons: {e}")

    def _load_lessons(self) -> None:
        """Load lessons from persistent storage."""
        try:
            if not os.path.exists(self.memory_file):
                logger.info(f"No existing lesson file at {self.memory_file}")
                return

            with open(self.memory_file, 'r') as f:
                data = json.load(f)

            # Load lessons
            lessons_data = data.get("lessons", [])
            self.lessons = [Lesson.from_dict(ld) for ld in lessons_data]

            # Load metadata
            metadata = data.get("metadata", {})
            self.total_failures = metadata.get("total_failures", 0)
            self.total_lessons = metadata.get("total_lessons", len(self.lessons))

            logger.info(f"Loaded {len(self.lessons)} lessons from storage")

        except Exception as e:
            logger.error(f"Failed to load lessons: {e}")
            self.lessons = []

    def clear_short_term_memory(self) -> None:
        """Clear short-term memory buffer."""
        self.short_term_memory.clear()
        logger.debug("Cleared short-term memory")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_failures": self.total_failures,
            "total_lessons": self.total_lessons,
            "lessons_in_memory": len(self.lessons),
            "short_term_buffer_size": len(self.short_term_memory),
            "critic_enabled": self.enable_critic
        }

    def export_lessons(self, output_file: str) -> None:
        """
        Export lessons to a file.

        Args:
            output_file: Path to output file
        """
        try:
            with open(output_file, 'w') as f:
                for lesson in self.lessons:
                    f.write(f"[{lesson.timestamp.strftime('%Y-%m-%d %H:%M')}] {lesson.context}\n")
                    f.write(f"  {lesson.lesson_text}\n")
                    f.write(f"  Cause: {lesson.cause_of_failure}\n")
                    f.write(f"  Confidence: {lesson.confidence:.2f} | References: {lesson.times_referenced}\n")
                    f.write("\n")
            logger.info(f"Exported {len(self.lessons)} lessons to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export lessons: {e}")
