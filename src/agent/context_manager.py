"""Context management for maintaining game history and state."""

from typing import List, Dict, Optional
from collections import deque
from dataclasses import dataclass, asdict
import json
from loguru import logger


@dataclass
class ContextEntry:
    """Represents a single context entry."""
    timestamp: float
    game_state: str
    action_taken: str
    result: str
    importance: int = 1  # 1-5, higher = more important


class ContextManager:
    """Manages context and history for the AI agent."""

    def __init__(self, max_history: int = 100, max_tokens: int = 100000, 
                 summarize_threshold: int = 80000):
        """
        Initialize the context manager.

        Args:
            max_history: Maximum number of entries to keep
            max_tokens: Maximum token count for context
            summarize_threshold: Token count that triggers summarization
        """
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.summarize_threshold = summarize_threshold
        self.history: deque[ContextEntry] = deque(maxlen=max_history)
        self.summary: str = ""
        self.current_tokens: int = 0

    def add_entry(self, timestamp: float, game_state: str, action_taken: str, 
                  result: str, importance: int = 1) -> None:
        """
        Add a new context entry.

        Args:
            timestamp: Time of entry
            game_state: Game state description
            action_taken: Action that was taken
            result: Result of the action
            importance: Importance level (1-5)
        """
        entry = ContextEntry(
            timestamp=timestamp,
            game_state=game_state,
            action_taken=action_taken,
            result=result,
            importance=importance
        )
        
        self.history.append(entry)
        self._update_token_count()
        
        logger.debug(f"Added context entry: {action_taken}")
        
        # Check if summarization needed
        if self.current_tokens > self.summarize_threshold:
            self._summarize_history()

    def get_context(self, num_recent: int = 10) -> str:
        """
        Get recent context for the AI.

        Args:
            num_recent: Number of recent entries to include

        Returns:
            Formatted context string
        """
        if not self.history:
            return "No previous actions."
        
        context_parts = []
        
        # Add summary if available
        if self.summary:
            context_parts.append(f"Summary of earlier actions:\n{self.summary}\n")
        
        # Add recent history
        recent_entries = list(self.history)[-num_recent:]
        context_parts.append("Recent actions:")
        
        for entry in recent_entries:
            context_parts.append(
                f"- {entry.action_taken}: {entry.result}"
            )
        
        return "\n".join(context_parts)

    def get_important_context(self, min_importance: int = 3) -> List[ContextEntry]:
        """
        Get important context entries.

        Args:
            min_importance: Minimum importance level

        Returns:
            List of important entries
        """
        return [entry for entry in self.history if entry.importance >= min_importance]

    def _update_token_count(self) -> None:
        """Update the estimated token count."""
        # Rough estimate: 1 token ≈ 4 characters
        total_chars = sum(
            len(entry.game_state) + len(entry.action_taken) + len(entry.result)
            for entry in self.history
        )
        self.current_tokens = total_chars // 4

    def _summarize_history(self) -> None:
        """Summarize older history to save tokens."""
        logger.info("Summarizing history to reduce context size")
        
        # Keep recent entries, summarize older ones
        keep_recent = 20
        to_summarize = list(self.history)[:-keep_recent]
        
        if not to_summarize:
            return
        
        # Create summary of key events
        important_events = [e for e in to_summarize if e.importance >= 3]
        
        summary_parts = []
        summary_parts.append(f"Summarized {len(to_summarize)} earlier actions.")
        
        if important_events:
            summary_parts.append("Key events:")
            for event in important_events[:10]:  # Top 10 important events
                summary_parts.append(f"- {event.action_taken}")
        
        self.summary = "\n".join(summary_parts)
        
        # Remove old entries (keep recent ones)
        recent_entries = list(self.history)[-keep_recent:]
        self.history.clear()
        self.history.extend(recent_entries)
        
        self._update_token_count()

    def mark_important(self, index: int = -1, importance: int = 5) -> None:
        """
        Mark a history entry as important.

        Args:
            index: Index of entry to mark (-1 for last)
            importance: Importance level to set
        """
        try:
            if -len(self.history) <= index < len(self.history):
                history_list = list(self.history)
                history_list[index].importance = importance
                self.history.clear()
                self.history.extend(history_list)
                logger.debug(f"Marked entry {index} as important (level {importance})")
        except Exception as e:
            logger.error(f"Failed to mark entry as important: {e}")

    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about the context.

        Returns:
            Dictionary with statistics
        """
        if not self.history:
            return {
                "total_entries": 0,
                "estimated_tokens": 0,
                "important_entries": 0,
            }
        
        return {
            "total_entries": len(self.history),
            "estimated_tokens": self.current_tokens,
            "important_entries": len([e for e in self.history if e.importance >= 3]),
            "has_summary": bool(self.summary),
        }

    def save_to_file(self, filename: str) -> bool:
        """
        Save context history to file.

        Args:
            filename: Output filename

        Returns:
            bool: True if saved successfully
        """
        try:
            data = {
                "summary": self.summary,
                "history": [asdict(entry) for entry in self.history],
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Context saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False

    def load_from_file(self, filename: str) -> bool:
        """
        Load context history from file.

        Args:
            filename: Input filename

        Returns:
            bool: True if loaded successfully
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.summary = data.get("summary", "")
            self.history.clear()
            
            for entry_dict in data.get("history", []):
                entry = ContextEntry(**entry_dict)
                self.history.append(entry)
            
            self._update_token_count()
            logger.info(f"Context loaded from {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            return False

    def clear(self) -> None:
        """Clear all context history."""
        self.history.clear()
        self.summary = ""
        self.current_tokens = 0
        logger.info("Context cleared")
