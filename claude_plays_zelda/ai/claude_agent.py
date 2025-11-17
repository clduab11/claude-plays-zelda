"""Main Claude AI agent for playing Zelda."""

import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from loguru import logger

from claude_plays_zelda.ai.context_manager import ContextManager
from claude_plays_zelda.ai.action_planner import ActionPlanner
from claude_plays_zelda.ai.memory import AgentMemory


class ClaudeAgent:
    """Main AI agent that uses Claude API to make decisions."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ):
        """
        Initialize Claude agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens for responses
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

        self.context_manager = ContextManager()
        self.action_planner = ActionPlanner()
        self.memory = AgentMemory()

        self.conversation_history: List[Dict[str, str]] = []

        logger.info(f"ClaudeAgent initialized with model: {model}")

    def decide_action(
        self,
        game_state: Dict[str, Any],
        observations: Dict[str, Any],
        recent_actions: List[str],
    ) -> Dict[str, Any]:
        """
        Decide the next action based on game state.

        Args:
            game_state: Current game state (health, rupees, etc.)
            observations: Visual observations (enemies, items, etc.)
            recent_actions: List of recent actions taken

        Returns:
            Dictionary with 'action' and 'reasoning' keys
        """
        try:
            # Build context for Claude
            context = self.context_manager.build_context(
                game_state=game_state,
                observations=observations,
                recent_actions=recent_actions,
                memory=self.memory,
            )

            # Create system prompt
            system_prompt = self._get_system_prompt()

            # Create user message with current situation
            user_message = self._format_situation(context)

            logger.debug(f"Sending request to Claude API...")

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )

            # Parse response
            response_text = response.content[0].text
            logger.debug(f"Claude response: {response_text[:200]}...")

            # Extract action and reasoning
            decision = self._parse_decision(response_text)

            # Store in memory
            self.memory.add_decision(
                game_state=game_state,
                decision=decision,
                context=context,
            )

            logger.info(f"Decision: {decision['action']} - {decision['reasoning'][:100]}")
            return decision

        except Exception as e:
            logger.error(f"Error deciding action: {e}")
            # Fallback to safe action
            return {
                "action": "wait",
                "parameters": {"duration": 1.0},
                "reasoning": f"Error occurred: {str(e)}",
            }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for Claude."""
        return """You are an AI agent playing The Legend of Zelda: A Link to the Past on SNES.
Your goal is to progress through the game by:
1. Exploring the world of Hyrule
2. Defeating enemies and bosses
3. Solving puzzles in dungeons
4. Collecting items and upgrades
5. Talking to NPCs for information
6. Completing the main quest to save Princess Zelda

You will receive information about:
- Link's current health (hearts)
- Available items and rupees
- Visible enemies, items, and NPCs
- Current location and surroundings
- Recent actions taken

You must respond with a JSON object containing:
{
  "action": "<action_name>",
  "parameters": {<action_parameters>},
  "reasoning": "<explanation of why you chose this action>"
}

Available actions:
- move: Move in a direction (parameters: direction="up|down|left|right", duration=float, run=bool)
- attack: Attack with sword (parameters: charge=bool)
- use_item: Use selected item (parameters: none)
- open_menu: Open game menu (parameters: none)
- wait: Wait/observe (parameters: duration=float)
- talk: Talk to NPC (parameters: none)

Important gameplay knowledge:
- Hearts represent health; Link dies at 0 hearts
- Rupees are currency for buying items
- Dark areas often contain secrets or dungeons
- NPCs provide hints and quest information
- Some obstacles require specific items (e.g., bombs for cracked walls)
- Enemies have patterns; learn them to defeat them efficiently
- Save rupees for important purchases (shields, bottles, etc.)

Strategy guidelines:
- Prioritize survival (avoid damage when low on hearts)
- Explore thoroughly to find items and secrets
- Talk to all NPCs to gather information
- Be cautious in new areas
- Learn enemy patterns before engaging
- Collect rupees and hearts when safe
- Use items strategically (don't waste limited items)

Think step by step and make smart decisions to progress through the game!"""

    def _format_situation(self, context: Dict[str, Any]) -> str:
        """Format the current situation for Claude."""
        situation_parts = []

        # Game state
        game_state = context.get("game_state", {})
        hearts = game_state.get("hearts", {})
        situation_parts.append(
            f"**Current Status:**\n"
            f"- Health: {hearts.get('current_hearts', 0)}/{hearts.get('max_hearts', 0)} hearts\n"
            f"- Rupees: {game_state.get('rupees', 0)}\n"
            f"- Current item: {game_state.get('current_item', 'None')}"
        )

        # Observations
        observations = context.get("observations", {})

        enemies = observations.get("enemies", [])
        if enemies:
            situation_parts.append(f"\n**Enemies Detected:** {len(enemies)} enemy(ies) nearby")

        items = observations.get("items", [])
        if items:
            item_types = [item.get("type", "unknown") for item in items]
            situation_parts.append(f"\n**Items Nearby:** {', '.join(set(item_types))}")

        doors = observations.get("doors", [])
        if doors:
            situation_parts.append(f"\n**Exits:** {len(doors)} door(s) detected")

        npcs = observations.get("npcs", [])
        if npcs:
            situation_parts.append(f"\n**NPCs:** {len(npcs)} NPC(s) nearby")

        # Recent actions
        recent_actions = context.get("recent_actions", [])
        if recent_actions:
            situation_parts.append(
                f"\n**Recent Actions:** {', '.join(recent_actions[-5:])}"
            )

        # Memory/objectives
        objectives = context.get("objectives", [])
        if objectives:
            situation_parts.append(
                f"\n**Current Objectives:**\n" + "\n".join(f"- {obj}" for obj in objectives)
            )

        # Strategy notes
        notes = context.get("strategy_notes", [])
        if notes:
            situation_parts.append(
                f"\n**Strategy Notes:**\n" + "\n".join(f"- {note}" for note in notes[-3:])
            )

        situation = "\n".join(situation_parts)
        situation += "\n\n**What should Link do next?** (Respond with JSON only)"

        return situation

    def _parse_decision(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response into a structured decision."""
        try:
            # Try to extract JSON from response
            # Sometimes Claude includes text before/after JSON
            import re

            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                json_str = json_match.group(0)
                decision = json.loads(json_str)

                # Validate required fields
                if "action" not in decision:
                    raise ValueError("No 'action' field in decision")

                if "parameters" not in decision:
                    decision["parameters"] = {}

                if "reasoning" not in decision:
                    decision["reasoning"] = "No reasoning provided"

                return decision
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.error(f"Error parsing decision: {e}")
            logger.debug(f"Response was: {response_text}")

            # Return safe fallback
            return {
                "action": "wait",
                "parameters": {"duration": 1.0},
                "reasoning": f"Could not parse response: {str(e)}",
            }

    def update_from_outcome(
        self, success: bool, result: Dict[str, Any], feedback: Optional[str] = None
    ):
        """
        Update agent's memory based on action outcome.

        Args:
            success: Whether the action was successful
            result: Result information (e.g., damage taken, item collected)
            feedback: Optional feedback about the outcome
        """
        try:
            self.memory.add_outcome(
                success=success,
                result=result,
                feedback=feedback,
            )

            # Learn from failures
            if not success:
                logger.warning(f"Action failed: {feedback}")
                self.memory.add_strategy_note(f"Failed: {feedback}")

        except Exception as e:
            logger.error(f"Error updating from outcome: {e}")

    def set_objective(self, objective: str):
        """
        Set a new objective for the agent.

        Args:
            objective: Description of the objective
        """
        self.memory.add_objective(objective)
        logger.info(f"New objective set: {objective}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "model": self.model,
            "total_decisions": self.memory.get_decision_count(),
            "success_rate": self.memory.get_success_rate(),
            "current_objectives": self.memory.get_objectives(),
        }

    def reset(self):
        """Reset the agent's state (but keep learned knowledge)."""
        self.conversation_history.clear()
        logger.info("Agent state reset")
