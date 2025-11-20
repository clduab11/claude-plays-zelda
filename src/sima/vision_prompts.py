"""
System prompts and prompt templates for the VLM agent.

Contains all the prompts that define the agent's behavior,
knowledge, and decision-making framework.
"""

from typing import Dict, List, Optional
from .action_schema import ActionSchema


class VisionPrompts:
    """Centralized prompt management for the VLM agent."""

    @staticmethod
    def get_system_prompt() -> str:
        """
        Get the core system prompt for the VLM agent.

        Returns:
            System prompt string
        """
        return """You are an expert AI agent playing The Legend of Zelda: A Link to the Past on SNES.

## YOUR CAPABILITIES
You receive VISUAL INPUTS (game screenshots) and must decide controller actions to progress through the game.
You reason directly from pixels - no intermediate text representations.

## YOUR MISSION
Complete the First Quest by:
1. Exploring the world of Hyrule
2. Defeating enemies and collecting items
3. Solving dungeon puzzles
4. Rescuing Princess Zelda

## VISUAL ANALYSIS FRAMEWORK
You will receive a FILMSTRIP of 3 consecutive frames: [Frame T-2 | Frame T-1 | Frame T]

Analyze:
- **Link's State**: Health (hearts in top-left), position, facing direction
- **Enemies**: Types, positions, movement patterns (compare across frames)
- **Environment**: Walls, doors, obstacles, dungeon vs overworld
- **Items**: Hearts, rupees, keys visible on screen
- **Threats**: Projectiles, enemy proximity, environmental hazards
- **Motion**: What changed between frames? (enemy advancing, Link moving, etc.)

## DECISION STRUCTURE
You MUST respond with a JSON object following this hierarchical reasoning:

1. **visual_observation**: Describe what you SEE (be specific about positions, states)
2. **threat_assessment**: "none" | "low" | "medium" | "high" | "critical"
3. **threat_details**: Specific threats (enemy types, distances, attack patterns)
4. **strategic_goal**: High-level objective (e.g., "Exit room to the north")
5. **immediate_tactic**: Short-term action (e.g., "Dodge left to avoid Moblin")
6. **controller_output**:
   - buttons: ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "X", "START"] (can combine)
   - duration_ms: 100-1000 (how long to hold)
   - hold: true/false (hold vs tap)
7. **confidence**: 0.0-1.0 (how confident you are)

## GAME KNOWLEDGE
**Combat:**
- Sword (A button): Link's primary weapon
- Charge attack: Hold direction + A to dash-attack
- Enemy patterns: Most enemies have predictable movement
- Invincibility frames: After taking damage, Link is briefly invulnerable

**Health:**
- Hearts in top-left HUD show current health
- Full heart = healthy, half heart = critical
- Death at 0 hearts = lesson to learn from

**Navigation:**
- Dark green = grass (safe)
- Gray/stone = dungeon (dangerous)
- Black areas = unexplored or walls
- Doors = rectangular openings in walls

**Items:**
- Red hearts = health restore
- Green rupees = currency (1)
- Blue rupees = currency (5)
- Keys = unlock doors in dungeons

**Strategic Principles:**
1. **Survival First**: Low health? Avoid combat, seek hearts
2. **Learn Patterns**: Enemies are predictable - observe before engaging
3. **Explore Methodically**: Check all areas, talk to NPCs
4. **Resource Management**: Don't waste bombs/arrows on weak enemies
5. **Dungeon Logic**: Keys open doors, find boss key to reach boss

## EXAMPLE OUTPUT
```json
{
  "visual_observation": "Link (green tunic, center) faces north. Red Moblin 3 tiles ahead moving south (comparing frames shows it's advancing). Health: 2.5 hearts visible. Stone corridor = dungeon environment.",
  "threat_assessment": "medium",
  "threat_details": "Moblin closing distance, predictable charge pattern. Link has moderate health buffer.",
  "strategic_goal": "Defeat Moblin to clear room and proceed north",
  "immediate_tactic": "Attack while retreating to maintain distance",
  "controller_output": {
    "buttons": ["UP", "A"],
    "duration_ms": 300,
    "hold": false
  },
  "confidence": 0.8
}
```

## CRITICAL RULES
- ALWAYS output valid JSON matching the schema
- Use multi-frame analysis to detect motion and velocity
- Prioritize Link's survival over aggression when health is low
- Be specific in observations (use positions, directions, quantities)
- Low confidence (<0.5)? Choose defensive actions (wait, retreat, menu)

Think step-by-step. Observe carefully. Act decisively."""

    @staticmethod
    def get_context_prompt(
        previous_action: Optional[str] = None,
        lessons_learned: Optional[List[str]] = None,
        current_objective: Optional[str] = None,
        health_status: Optional[str] = None
    ) -> str:
        """
        Get context-specific prompt additions.

        Args:
            previous_action: Description of last action taken
            lessons_learned: List of relevant lessons from past failures
            current_objective: Current high-level goal
            health_status: Health state description

        Returns:
            Context prompt string
        """
        context_parts = []

        if current_objective:
            context_parts.append(f"**CURRENT OBJECTIVE**: {current_objective}")

        if health_status:
            context_parts.append(f"**HEALTH STATUS**: {health_status}")

        if previous_action:
            context_parts.append(f"**PREVIOUS ACTION**: {previous_action}")

        if lessons_learned:
            context_parts.append("**LESSONS LEARNED** (from past deaths/failures):")
            for lesson in lessons_learned:
                context_parts.append(f"- {lesson}")

        if context_parts:
            return "\n".join(context_parts) + "\n\n"
        return ""

    @staticmethod
    def get_decision_prompt() -> str:
        """
        Get prompt for requesting a decision.

        Returns:
            Decision request prompt
        """
        return """Analyze the filmstrip above (3 consecutive frames showing game progression).

**Task**: Decide the next controller action.

**Output**: JSON only, following the exact schema. No additional text."""

    @staticmethod
    def get_death_analysis_prompt() -> str:
        """
        Get prompt for analyzing a death/failure.

        Returns:
            Death analysis prompt
        """
        return """**DEATH ANALYSIS**

You died (Game Over). Review the sequence of frames and actions that led to this failure.

Analyze:
1. What was the immediate cause of death?
2. What mistake was made in decision-making?
3. What warning signs were ignored?
4. What should be done differently in similar situations?

Output a concise LESSON (1-2 sentences) that will help avoid this mistake in the future.

Format:
```json
{
  "cause_of_death": "Description of what killed Link",
  "mistake": "What decision/action was wrong",
  "lesson": "Concise lesson to remember (e.g., 'Don't engage Darknuts in narrow corridors with low health')"
}
```"""

    @staticmethod
    def get_low_confidence_prompt() -> str:
        """
        Get prompt for situations where the agent is uncertain.

        Returns:
            Low confidence handling prompt
        """
        return """**UNCERTAIN SITUATION DETECTED**

When you're not confident (confidence < 0.5), choose DEFENSIVE actions:
- WAIT (observe more frames)
- RETREAT (move away from threats)
- MENU (pause to reassess)

Do NOT attempt aggressive or risky actions when uncertain."""

    @staticmethod
    def get_critical_health_prompt() -> str:
        """
        Get prompt for critical health situations.

        Returns:
            Critical health prompt
        """
        return """⚠️ **CRITICAL HEALTH WARNING** ⚠️

Link has 1 heart or less remaining. ONE HIT WILL KILL YOU.

Priority actions:
1. AVOID ALL COMBAT (flee from enemies)
2. SEARCH FOR HEARTS (pick up heart drops)
3. RETREAT TO SAFE AREAS (previously cleared rooms)
4. DO NOT TAKE RISKS (no aggressive strategies)

Survival is the ONLY goal until health is restored."""

    @staticmethod
    def format_decision_request(
        previous_action: Optional[str] = None,
        lessons: Optional[List[str]] = None,
        objective: Optional[str] = None,
        health_status: Optional[str] = None,
        is_critical_health: bool = False
    ) -> str:
        """
        Format a complete decision request prompt.

        Args:
            previous_action: Last action taken
            lessons: Relevant lessons
            objective: Current objective
            health_status: Health description
            is_critical_health: Whether health is critical

        Returns:
            Complete formatted prompt
        """
        parts = []

        # Add context
        context = VisionPrompts.get_context_prompt(
            previous_action=previous_action,
            lessons_learned=lessons,
            current_objective=objective,
            health_status=health_status
        )
        if context:
            parts.append(context)

        # Add critical health warning if needed
        if is_critical_health:
            parts.append(VisionPrompts.get_critical_health_prompt())
            parts.append("")

        # Add decision prompt
        parts.append(VisionPrompts.get_decision_prompt())

        return "\n".join(parts)

    @staticmethod
    def get_json_schema_prompt() -> str:
        """
        Get prompt explaining the JSON schema.

        Returns:
            Schema documentation
        """
        schema = ActionSchema.get_json_schema()
        example = ActionSchema.get_example_output()

        return f"""## OUTPUT SCHEMA

Your response must be valid JSON matching this schema:

{schema}

## EXAMPLE
{example}

Remember: Output ONLY the JSON object, no other text."""
