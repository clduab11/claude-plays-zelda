"""Unit tests for navigator."""

import pytest
from src.game.navigation import Navigator
from src.cv.map_recognizer import Location


class TestNavigator:
    """Tests for Navigator class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.navigator = Navigator()

    def test_find_path_simple(self):
        """Test finding a simple path."""
        start = Location(0, 0, "light_world")
        goal = Location(2, 2, "light_world")
        
        path = self.navigator.find_path(start, goal)
        assert len(path) > 0

    def test_estimate_distance(self):
        """Test distance estimation."""
        loc1 = Location(0, 0, "light_world")
        loc2 = Location(3, 4, "light_world")
        
        distance = self.navigator.estimate_distance(loc1, loc2)
        assert distance == 7  # Manhattan distance

    def test_record_visit(self):
        """Test recording a visit."""
        location = Location(1, 1, "light_world")
        self.navigator.record_visit(location)
        
        key = (1, 1, "light_world")
        assert key in self.navigator.visit_counts
        assert self.navigator.visit_counts[key] == 1

    def test_should_backtrack(self):
        """Test backtrack decision."""
        location = Location(1, 1, "light_world")
        
        # First visit - should not backtrack
        self.navigator.record_visit(location)
        assert not self.navigator.should_backtrack(location)
        
        # Multiple visits - should backtrack
        for _ in range(5):
            self.navigator.record_visit(location)
        assert self.navigator.should_backtrack(location)

    def test_get_backtrack_direction(self):
        """Test getting opposite direction."""
        location = Location(1, 1, "light_world")
        
        assert self.navigator.get_backtrack_direction(location, "up") == "down"
        assert self.navigator.get_backtrack_direction(location, "left") == "right"

    def test_statistics(self):
        """Test getting statistics."""
        loc1 = Location(0, 0, "light_world")
        loc2 = Location(1, 0, "light_world")
        
        self.navigator.record_visit(loc1)
        self.navigator.record_visit(loc2)
        self.navigator.add_room_connection(loc1, loc2, "right")
        
        stats = self.navigator.get_statistics()
        assert stats["unique_rooms_visited"] == 2
        assert stats["rooms_mapped"] == 1
