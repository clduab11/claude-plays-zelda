"""Statistics tracking for gameplay metrics."""

from typing import Dict, Any, List
from dataclasses import dataclass, field
import time
import json
from loguru import logger


@dataclass
class SessionStats:
    """Statistics for a gameplay session."""
    session_id: str
    start_time: float
    end_time: float = 0.0
    actions_taken: int = 0
    rooms_visited: int = 0
    enemies_defeated: int = 0
    items_collected: int = 0
    damage_taken: int = 0
    deaths: int = 0
    puzzles_solved: int = 0
    distance_traveled: float = 0.0


class StatsTracker:
    """Tracks and aggregates gameplay statistics."""

    def __init__(self, update_interval: int = 5):
        """
        Initialize the stats tracker.

        Args:
            update_interval: Interval for stats updates (seconds)
        """
        self.update_interval = update_interval
        self.current_session: Optional[SessionStats] = None
        self.all_sessions: List[SessionStats] = []
        self.last_update_time: float = 0
        
        # Real-time counters
        self.actions_count = 0
        self.rooms_count = 0
        self.enemies_count = 0
        self.items_count = 0
        self.damage_count = 0
        self.deaths_count = 0
        self.puzzles_count = 0
        
        # Performance metrics
        self.decision_times: List[float] = []
        self.action_success_rate: float = 1.0

    def start_session(self, session_id: str = None) -> None:
        """
        Start a new tracking session.

        Args:
            session_id: Optional session identifier
        """
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        self.current_session = SessionStats(
            session_id=session_id,
            start_time=time.time()
        )
        
        logger.info(f"Started stats tracking session: {session_id}")

    def end_session(self) -> SessionStats:
        """
        End the current session.

        Returns:
            Session statistics
        """
        if not self.current_session:
            logger.warning("No active session to end")
            return None
        
        self.current_session.end_time = time.time()
        self.current_session.actions_taken = self.actions_count
        self.current_session.rooms_visited = self.rooms_count
        self.current_session.enemies_defeated = self.enemies_count
        self.current_session.items_collected = self.items_count
        self.current_session.damage_taken = self.damage_count
        self.current_session.deaths = self.deaths_count
        self.current_session.puzzles_solved = self.puzzles_count
        
        self.all_sessions.append(self.current_session)
        session = self.current_session
        self.current_session = None
        
        logger.info(f"Ended stats tracking session: {session.session_id}")
        return session

    def record_action(self, success: bool = True) -> None:
        """
        Record an action taken.

        Args:
            success: Whether the action was successful
        """
        self.actions_count += 1
        
        # Update success rate
        total_actions = self.actions_count
        if success:
            self.action_success_rate = (
                (self.action_success_rate * (total_actions - 1) + 1.0) / total_actions
            )
        else:
            self.action_success_rate = (
                (self.action_success_rate * (total_actions - 1)) / total_actions
            )

    def record_room_visit(self) -> None:
        """Record visiting a new room."""
        self.rooms_count += 1

    def record_enemy_defeat(self) -> None:
        """Record defeating an enemy."""
        self.enemies_count += 1

    def record_item_collection(self) -> None:
        """Record collecting an item."""
        self.items_count += 1

    def record_damage(self, amount: int = 1) -> None:
        """
        Record taking damage.

        Args:
            amount: Amount of damage taken
        """
        self.damage_count += amount

    def record_death(self) -> None:
        """Record a death."""
        self.deaths_count += 1
        logger.warning(f"Death recorded. Total: {self.deaths_count}")

    def record_puzzle_solved(self) -> None:
        """Record solving a puzzle."""
        self.puzzles_count += 1

    def record_decision_time(self, duration: float) -> None:
        """
        Record time taken for a decision.

        Args:
            duration: Decision time in seconds
        """
        self.decision_times.append(duration)
        
        # Keep only recent decision times (last 100)
        if len(self.decision_times) > 100:
            self.decision_times = self.decision_times[-100:]

    def get_current_stats(self) -> Dict[str, Any]:
        """
        Get current session statistics.

        Returns:
            Dictionary with current stats
        """
        session_duration = 0
        if self.current_session:
            session_duration = time.time() - self.current_session.start_time
        
        avg_decision_time = 0
        if self.decision_times:
            avg_decision_time = sum(self.decision_times) / len(self.decision_times)
        
        return {
            "play_time": session_duration,
            "actions_taken": self.actions_count,
            "rooms_visited": self.rooms_count,
            "enemies_defeated": self.enemies_count,
            "items_collected": self.items_count,
            "damage_taken": self.damage_count,
            "deaths": self.deaths_count,
            "puzzles_solved": self.puzzles_count,
            "action_success_rate": self.action_success_rate,
            "avg_decision_time": avg_decision_time,
        }

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics across all sessions.

        Returns:
            Dictionary with aggregate stats
        """
        if not self.all_sessions:
            return self.get_current_stats()
        
        total_time = sum(s.end_time - s.start_time for s in self.all_sessions)
        total_actions = sum(s.actions_taken for s in self.all_sessions)
        total_rooms = sum(s.rooms_visited for s in self.all_sessions)
        total_enemies = sum(s.enemies_defeated for s in self.all_sessions)
        total_items = sum(s.items_collected for s in self.all_sessions)
        total_damage = sum(s.damage_taken for s in self.all_sessions)
        total_deaths = sum(s.deaths for s in self.all_sessions)
        total_puzzles = sum(s.puzzles_solved for s in self.all_sessions)
        
        return {
            "total_sessions": len(self.all_sessions),
            "total_play_time": total_time,
            "total_actions": total_actions,
            "total_rooms": total_rooms,
            "total_enemies": total_enemies,
            "total_items": total_items,
            "total_damage": total_damage,
            "total_deaths": total_deaths,
            "total_puzzles": total_puzzles,
            "actions_per_hour": (total_actions / total_time * 3600) if total_time > 0 else 0,
            "deaths_per_hour": (total_deaths / total_time * 3600) if total_time > 0 else 0,
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        avg_decision_time = 0
        if self.decision_times:
            avg_decision_time = sum(self.decision_times) / len(self.decision_times)
        
        min_decision_time = min(self.decision_times) if self.decision_times else 0
        max_decision_time = max(self.decision_times) if self.decision_times else 0
        
        return {
            "action_success_rate": self.action_success_rate,
            "avg_decision_time": avg_decision_time,
            "min_decision_time": min_decision_time,
            "max_decision_time": max_decision_time,
            "decisions_tracked": len(self.decision_times),
        }

    def should_update(self) -> bool:
        """
        Check if it's time to send a stats update.

        Returns:
            bool: True if should update
        """
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            return True
        return False

    def save_to_file(self, filename: str) -> bool:
        """
        Save statistics to file.

        Args:
            filename: Output filename

        Returns:
            bool: True if saved successfully
        """
        try:
            data = {
                "current_stats": self.get_current_stats(),
                "aggregate_stats": self.get_aggregate_stats(),
                "performance_metrics": self.get_performance_metrics(),
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Statistics saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")
            return False

    def reset_session_stats(self) -> None:
        """Reset current session statistics."""
        self.actions_count = 0
        self.rooms_count = 0
        self.enemies_count = 0
        self.items_count = 0
        self.damage_count = 0
        self.deaths_count = 0
        self.puzzles_count = 0
        self.decision_times.clear()
        logger.info("Session statistics reset")

    def get_summary(self) -> str:
        """
        Get a text summary of statistics.

        Returns:
            Summary string
        """
        stats = self.get_current_stats()
        
        hours = int(stats["play_time"] // 3600)
        minutes = int((stats["play_time"] % 3600) // 60)
        seconds = int(stats["play_time"] % 60)
        
        summary = [
            "Session Statistics:",
            f"- Play Time: {hours}h {minutes}m {seconds}s",
            f"- Actions Taken: {stats['actions_taken']}",
            f"- Rooms Visited: {stats['rooms_visited']}",
            f"- Enemies Defeated: {stats['enemies_defeated']}",
            f"- Items Collected: {stats['items_collected']}",
            f"- Deaths: {stats['deaths']}",
            f"- Success Rate: {stats['action_success_rate']*100:.1f}%",
        ]
        
        return "\n".join(summary)
