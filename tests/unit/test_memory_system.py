"""Unit tests for memory system."""

import pytest
import tempfile
import os
from src.agent.memory_system import MemorySystem


class TestMemorySystem:
    """Tests for MemorySystem class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.memory = MemorySystem(persistence_file=self.temp_file.name)

    def teardown_method(self):
        """Cleanup test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_store_and_retrieve(self):
        """Test storing and retrieving a memory."""
        self.memory.store("test_key", "test_value")
        value = self.memory.retrieve("test_key")
        assert value == "test_value"

    def test_retrieve_nonexistent(self):
        """Test retrieving a nonexistent memory."""
        value = self.memory.retrieve("nonexistent")
        assert value is None

    def test_mark_visited(self):
        """Test marking a location as visited."""
        self.memory.mark_visited("hyrule_castle")
        assert self.memory.has_visited("hyrule_castle")
        assert not self.memory.has_visited("death_mountain")

    def test_add_item(self):
        """Test adding an item."""
        self.memory.add_item("master_sword")
        assert self.memory.has_item("master_sword")
        assert not self.memory.has_item("boomerang")

    def test_defeat_enemy(self):
        """Test recording enemy defeats."""
        self.memory.defeat_enemy("moblin")
        self.memory.defeat_enemy("moblin")
        assert self.memory.get_enemy_defeats("moblin") == 2
        assert self.memory.get_enemy_defeats("octorok") == 0

    def test_solve_puzzle(self):
        """Test recording puzzle solutions."""
        self.memory.solve_puzzle("puzzle_1")
        assert self.memory.is_puzzle_solved("puzzle_1")
        assert not self.memory.is_puzzle_solved("puzzle_2")

    def test_save_and_load(self):
        """Test saving and loading memory."""
        self.memory.store("key1", "value1")
        self.memory.mark_visited("location1")
        self.memory.add_item("item1")
        
        assert self.memory.save()
        
        new_memory = MemorySystem(persistence_file=self.temp_file.name)
        assert new_memory.load()
        
        assert new_memory.retrieve("key1") == "value1"
        assert new_memory.has_visited("location1")
        assert new_memory.has_item("item1")

    def test_statistics(self):
        """Test getting statistics."""
        self.memory.mark_visited("loc1")
        self.memory.add_item("item1")
        self.memory.defeat_enemy("enemy1")
        self.memory.record_death()
        
        stats = self.memory.get_statistics()
        assert stats["locations_visited"] == 1
        assert stats["items_collected"] == 1
        assert stats["total_enemy_defeats"] == 1
        assert stats["deaths"] == 1
