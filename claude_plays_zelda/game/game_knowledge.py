"""Game-specific knowledge base for Legend of Zelda: A Link to the Past."""

from typing import Dict, Any, List
from loguru import logger


class ZeldaKnowledge:
    """Knowledge base for Zelda ALTTP game mechanics and information."""

    def __init__(self):
        """Initialize knowledge base."""
        # Item information
        self.items = {
            "sword": {
                "name": "Fighter's Sword",
                "description": "Basic sword, upgradeable",
                "usage": "Press Y to swing",
            },
            "shield": {
                "name": "Shield",
                "description": "Blocks projectiles",
                "usage": "Equipped automatically",
            },
            "bow": {
                "name": "Bow and Arrows",
                "description": "Ranged weapon, requires arrows",
                "usage": "Press item button",
            },
            "boomerang": {
                "name": "Boomerang",
                "description": "Stuns enemies and retrieves items",
                "usage": "Press item button",
            },
            "hookshot": {
                "name": "Hookshot",
                "description": "Grapples to distant objects",
                "usage": "Press item button",
            },
            "bombs": {
                "name": "Bombs",
                "description": "Destroys cracked walls",
                "usage": "Press item button to place",
            },
            "lantern": {
                "name": "Lantern",
                "description": "Lights torches and dark rooms",
                "usage": "Press item button",
            },
            "bottles": {
                "name": "Bottles",
                "description": "Store potions, fairies, etc.",
                "usage": "Press item button to use contents",
            },
        }

        # Dungeon information
        self.dungeons = {
            "eastern_palace": {
                "name": "Eastern Palace",
                "location": "East of Hyrule Castle",
                "boss": "Armos Knights",
                "reward": "Pendant of Courage",
                "required_items": [],
            },
            "desert_palace": {
                "name": "Desert Palace",
                "location": "Desert of Mystery",
                "boss": "Lanmolas",
                "reward": "Pendant of Power",
                "required_items": ["book_of_mudora"],
            },
            "tower_of_hera": {
                "name": "Tower of Hera",
                "location": "Death Mountain",
                "boss": "Moldorm",
                "reward": "Pendant of Wisdom",
                "required_items": [],
            },
        }

        # Enemy information
        self.enemies = {
            "octorok": {
                "name": "Octorok",
                "health": 1,
                "damage": 0.5,
                "behavior": "Shoots rocks at Link",
                "weakness": "Shield deflects rocks",
            },
            "moblin": {
                "name": "Moblin",
                "health": 2,
                "damage": 1,
                "behavior": "Charges at Link with spear",
                "weakness": "Arrows",
            },
            "soldier": {
                "name": "Soldier",
                "health": 2,
                "damage": 1,
                "behavior": "Patrols and attacks with sword",
                "weakness": "Sword attacks",
            },
        }

        # NPC dialogue and quests
        self.npcs = {
            "old_man": {
                "name": "Old Man",
                "locations": ["Various caves"],
                "hints": ["Take this lamp, it will light your way"],
            },
            "sahasrahla": {
                "name": "Sahasrahla",
                "location": "East of Kakariko",
                "hints": ["Collect the three pendants to get the Master Sword"],
            },
        }

        # Game progression milestones
        self.progression = [
            {"milestone": "Escape from castle", "requirements": []},
            {"milestone": "Get Master Sword", "requirements": ["3 pendants"]},
            {"milestone": "Enter Dark World", "requirements": ["Master Sword"]},
            {"milestone": "Collect 7 crystals", "requirements": ["Dark World access"]},
            {"milestone": "Defeat Ganon", "requirements": ["7 crystals", "Silver Arrows"]},
        ]

        logger.info("ZeldaKnowledge initialized")

    def get_item_info(self, item_name: str) -> Dict[str, Any]:
        """Get information about an item."""
        return self.items.get(item_name.lower(), {})

    def get_dungeon_info(self, dungeon_name: str) -> Dict[str, Any]:
        """Get information about a dungeon."""
        return self.dungeons.get(dungeon_name.lower(), {})

    def get_enemy_info(self, enemy_name: str) -> Dict[str, Any]:
        """Get information about an enemy."""
        return self.enemies.get(enemy_name.lower(), {})

    def get_npc_hints(self, npc_name: str) -> List[str]:
        """Get hints from an NPC."""
        npc = self.npcs.get(npc_name.lower(), {})
        return npc.get("hints", [])

    def get_next_objective(self, current_progress: Dict[str, Any]) -> str:
        """
        Get the next objective based on current progress.

        Args:
            current_progress: Dictionary with progress information

        Returns:
            Next objective description
        """
        # Simplified progression logic
        if not current_progress.get("escaped_castle"):
            return "Escape from Hyrule Castle"
        elif current_progress.get("pendants_collected", 0) < 3:
            return "Collect the three pendants from dungeons"
        elif not current_progress.get("has_master_sword"):
            return "Obtain the Master Sword from the Lost Woods"
        elif current_progress.get("crystals_collected", 0) < 7:
            return "Collect the seven crystals from Dark World dungeons"
        else:
            return "Defeat Ganon in Ganon's Tower"

    def get_item_locations(self) -> Dict[str, str]:
        """Get known item locations."""
        return {
            "lantern": "Link's House (chest)",
            "boomerang": "Hyrule Castle (room with pits)",
            "bow": "Eastern Palace",
            "hookshot": "Swamp Palace",
            "ice_rod": "Lake Hylia shop",
            "bombs": "Various shops and enemies",
        }

    def get_heart_piece_locations(self) -> List[str]:
        """Get locations of heart pieces."""
        return [
            "Under a rock near Link's House",
            "In a chest in Kakariko Village",
            "In the Desert of Mystery",
            "In the Lost Woods",
            "In the Graveyard (dig spot)",
            # ... many more
        ]

    def get_game_tips(self) -> List[str]:
        """Get general gameplay tips."""
        return [
            "Cut grass and break pots for hearts and rupees",
            "Talk to everyone to get hints and information",
            "Save your game frequently at bird statues",
            "Explore everywhere - secrets are hidden throughout Hyrule",
            "Dark World requires special items to navigate",
            "Boss keys are always required for the boss room",
            "Some items are required to progress (Flippers, Hookshot, etc.)",
            "Fairies in bottles will automatically revive you if you die",
            "The Fortune Teller can give you hints for rupees",
            "Upgrade your sword, shield, and armor at shops and through quests",
        ]

    def get_combat_tips(self) -> List[str]:
        """Get combat tips."""
        return [
            "Charge your sword by holding Y for a spin attack",
            "Use the shield to block projectiles",
            "Different enemies have different weaknesses",
            "Arrows do more damage than sword but cost rupees",
            "Learn enemy patterns to avoid damage",
            "Some enemies can only be defeated with specific items",
            "Defensive play is often better than aggressive",
        ]

    def get_dungeon_tips(self) -> List[str]:
        """Get dungeon exploration tips."""
        return [
            "Get the map and compass in each dungeon",
            "Small keys open locked doors",
            "Big keys are needed for the boss room",
            "Explore thoroughly to find all treasure chests",
            "Some dungeons require specific items to complete",
            "Boss patterns can be learned and exploited",
            "Save your game before entering a dungeon",
        ]

    def is_item_required(self, item: str, location: str) -> bool:
        """
        Check if an item is required for a location.

        Args:
            item: Item name
            location: Location name

        Returns:
            True if item is required
        """
        # Simplified - would have full requirement mapping
        requirements = {
            "desert_palace": ["book_of_mudora"],
            "dark_world": ["master_sword"],
            "swamp_palace": ["flippers"],
            "skull_woods": ["moon_pearl"],
        }

        location_items = requirements.get(location.lower(), [])
        return item.lower() in location_items
