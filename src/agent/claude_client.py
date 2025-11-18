"""Claude API client for AI decision making."""

from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from loguru import logger


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", 
                 max_tokens: int = 4096, temperature: float = 0.7):
        """
        Initialize the Claude client.

        Args:
            api_key: Anthropic API key
            model: Model identifier
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = Anthropic(api_key=api_key)

    def get_action(self, game_state: str, context: Optional[str] = None) -> str:
        """
        Get the next action from Claude based on game state.

        Args:
            game_state: Current game state description
            context: Optional additional context

        Returns:
            Action string from Claude
        """
        try:
            system_prompt = self._build_system_prompt()
            user_message = self._build_user_message(game_state, context)
            
            logger.debug(f"Requesting action from Claude")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            action = response.content[0].text
            logger.info(f"Claude suggested action: {action[:100]}...")
            return action
        except Exception as e:
            logger.error(f"Failed to get action from Claude: {e}")
            return "wait"

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for Claude.

        Returns:
            System prompt string
        """
        return """You are an AI playing The Legend of Zelda: A Link to the Past. Your goal is to progress through the game by:
1. Exploring the world and discovering new areas
2. Collecting items and hearts
3. Fighting enemies strategically
4. Solving puzzles
5. Completing dungeons
6. Advancing the story

When given a game state, respond with ONE of these actions:
- move_up / move_down / move_left / move_right
- attack
- use_item
- open_menu
- talk (when near NPCs)
- search (when looking for secrets)
- wait

Keep responses concise. Format: ACTION: <action> REASON: <brief reason>"""

    def _build_user_message(self, game_state: str, context: Optional[str] = None) -> str:
        """
        Build the user message with game state.

        Args:
            game_state: Game state description
            context: Optional context

        Returns:
            User message string
        """
        message = f"Current game state:\n{game_state}\n"
        
        if context:
            message += f"\nContext:\n{context}\n"
        
        message += "\nWhat action should I take next?"
        return message

    def analyze_situation(self, game_state: str, question: str) -> str:
        """
        Ask Claude to analyze a specific situation.

        Args:
            game_state: Current game state
            question: Specific question to ask

        Returns:
            Claude's analysis
        """
        try:
            system_prompt = "You are an expert at The Legend of Zelda: A Link to the Past. Provide strategic advice."
            
            user_message = f"Game state: {game_state}\n\nQuestion: {question}"
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to analyze situation: {e}")
            return ""

    def generate_strategy(self, objective: str, current_state: str) -> str:
        """
        Generate a high-level strategy for an objective.

        Args:
            objective: Goal to achieve
            current_state: Current game state

        Returns:
            Strategy description
        """
        try:
            system_prompt = "You are a strategic planner for Zelda gameplay. Create detailed plans."
            
            user_message = f"Objective: {objective}\nCurrent state: {current_state}\n\nProvide a step-by-step strategy."
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.5,  # Lower temperature for more focused planning
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Failed to generate strategy: {e}")
            return ""

    def parse_action_response(self, response: str) -> Dict[str, str]:
        """
        Parse Claude's action response.

        Args:
            response: Raw response from Claude

        Returns:
            Dictionary with action and reason
        """
        result = {"action": "wait", "reason": ""}
        
        try:
            # Parse "ACTION: <action> REASON: <reason>" format
            if "ACTION:" in response:
                parts = response.split("ACTION:")[1].split("REASON:")
                result["action"] = parts[0].strip().lower()
                if len(parts) > 1:
                    result["reason"] = parts[1].strip()
            else:
                # Fallback: treat entire response as action
                result["action"] = response.strip().lower()
            
            return result
        except Exception as e:
            logger.error(f"Failed to parse action response: {e}")
            return result
