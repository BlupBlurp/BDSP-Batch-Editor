"""
Level editor module for BDSP-Batch-Editor.
Handles bulk editing logic for Pokemon levels.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


class LevelEditor:
    """Handles bulk editing operations for Pokemon levels."""

    def __init__(self):
        self.modification_history: List[Dict[str, Any]] = []

    def parse_level_modification(self, input_text: str) -> Tuple[str, float]:
        """
        Parse level modification input string.

        Args:
            input_text: User input string (e.g., "+10", "10%", "-5")

        Returns:
            Tuple of (operation_type, value)
            operation_type can be: 'absolute', 'percentage'

        Raises:
            ValueError: If input format is invalid
        """
        input_text = input_text.strip()

        if not input_text:
            raise ValueError("Empty input")

        # Check for percentage modification
        percentage_match = re.match(r"^([+-]?\d+(?:\.\d+)?)%$", input_text)
        if percentage_match:
            value = float(percentage_match.group(1))
            return ("percentage", value)

        # Check for absolute modification
        absolute_match = re.match(r"^([+-]?\d+(?:\.\d+)?)$", input_text)
        if absolute_match:
            value = float(absolute_match.group(1))
            return ("absolute", value)

        raise ValueError(f"Invalid input format: {input_text}")

    def apply_level_modification(
        self,
        trainer_poke_data: List[Dict[str, Any]],
        operation_type: str,
        value: float,
        min_level: int = 1,
        max_level: int = 100,
        selected_trainers: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Apply level modifications to trainer Pokemon data.

        Args:
            trainer_poke_data: List of trainer Pokemon data
            operation_type: 'absolute' or 'percentage'
            value: Modification value
            min_level: Minimum allowed level (default: 1)
            max_level: Maximum allowed level (default: 100)
            selected_trainers: List of trainer IDs to modify (None for all)

        Returns:
            Dictionary with modification results including statistics
        """
        modifications = []
        total_pokemon_modified = 0
        total_trainers_modified = 0

        for entry in trainer_poke_data:
            trainer_id = entry.get("ID", 0)

            # Skip if specific trainers selected and this isn't one of them
            if selected_trainers is not None and trainer_id not in selected_trainers:
                continue

            trainer_modified = False
            trainer_modifications = []

            # Process each Pokemon slot (P1-P6)
            for i in range(1, 7):
                level_key = f"P{i}Level"
                mons_no_key = f"P{i}MonsNo"

                # Only modify if Pokemon exists (MonsNo > 0 and Level > 0)
                if entry.get(mons_no_key, 0) > 0 and entry.get(level_key, 0) > 0:

                    old_level = entry[level_key]
                    new_level = self._calculate_new_level(
                        old_level, operation_type, value
                    )

                    # Apply level constraints
                    new_level = max(min_level, min(max_level, new_level))

                    if new_level != old_level:
                        entry[level_key] = new_level
                        trainer_modifications.append(
                            {
                                "pokemon_slot": i,
                                "old_level": old_level,
                                "new_level": new_level,
                                "mons_no": entry.get(mons_no_key, 0),
                            }
                        )
                        total_pokemon_modified += 1
                        trainer_modified = True

            if trainer_modified:
                modifications.append(
                    {"trainer_id": trainer_id, "pokemon_changes": trainer_modifications}
                )
                total_trainers_modified += 1

        # Store modification in history
        modification_record = {
            "operation_type": operation_type,
            "value": value,
            "min_level": min_level,
            "max_level": max_level,
            "selected_trainers": selected_trainers,
            "modifications": modifications,
            "total_pokemon_modified": total_pokemon_modified,
            "total_trainers_modified": total_trainers_modified,
        }

        self.modification_history.append(modification_record)

        return modification_record

    def _calculate_new_level(
        self, current_level: int, operation_type: str, value: float
    ) -> int:
        """
        Calculate new level based on operation type and value.

        Args:
            current_level: Current Pokemon level
            operation_type: 'absolute' or 'percentage'
            value: Modification value

        Returns:
            New level (as integer)
        """
        if operation_type == "absolute":
            return int(current_level + value)
        elif operation_type == "percentage":
            new_level = current_level * (1 + value / 100)
            return max(1, round(new_level))  # Round to nearest integer, minimum level 1
        else:
            raise ValueError(f"Unknown operation type: {operation_type}")

    def preview_modifications(
        self,
        trainer_poke_data: List[Dict[str, Any]],
        operation_type: str,
        value: float,
        min_level: int = 1,
        max_level: int = 100,
        selected_trainers: Optional[List[int]] = None,
        max_preview_entries: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Preview level modifications without applying them.

        Args:
            trainer_poke_data: List of trainer Pokemon data
            operation_type: 'absolute' or 'percentage'
            value: Modification value
            min_level: Minimum allowed level
            max_level: Maximum allowed level
            selected_trainers: List of trainer IDs to modify
            max_preview_entries: Maximum number of preview entries to return

        Returns:
            List of preview entries showing changes
        """
        preview_entries = []
        count = 0

        for entry in trainer_poke_data:
            if count >= max_preview_entries:
                break

            trainer_id = entry.get("ID", 0)

            # Skip if specific trainers selected and this isn't one of them
            if selected_trainers is not None and trainer_id not in selected_trainers:
                continue

            preview_entry = {"trainer_id": trainer_id, "pokemon_previews": []}

            has_changes = False

            # Process each Pokemon slot (P1-P6)
            for i in range(1, 7):
                level_key = f"P{i}Level"
                mons_no_key = f"P{i}MonsNo"

                # Only preview if Pokemon exists
                if entry.get(mons_no_key, 0) > 0 and entry.get(level_key, 0) > 0:

                    old_level = entry[level_key]
                    new_level = self._calculate_new_level(
                        old_level, operation_type, value
                    )
                    new_level = max(min_level, min(max_level, new_level))

                    preview_entry["pokemon_previews"].append(
                        {
                            "slot": i,
                            "mons_no": entry.get(mons_no_key, 0),
                            "old_level": old_level,
                            "new_level": new_level,
                            "changed": new_level != old_level,
                        }
                    )

                    if new_level != old_level:
                        has_changes = True

            if has_changes and preview_entry["pokemon_previews"]:
                preview_entries.append(preview_entry)
                count += 1

        return preview_entries

    def get_modification_statistics(
        self, trainer_poke_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about the trainer data.

        Args:
            trainer_poke_data: List of trainer Pokemon data

        Returns:
            Dictionary with statistics
        """
        total_trainers = len(trainer_poke_data)
        total_pokemon = 0
        level_distribution = {}
        trainers_with_pokemon = 0

        for entry in trainer_poke_data:
            trainer_has_pokemon = False

            for i in range(1, 7):
                level_key = f"P{i}Level"
                mons_no_key = f"P{i}MonsNo"

                if entry.get(mons_no_key, 0) > 0 and entry.get(level_key, 0) > 0:

                    level = entry[level_key]
                    total_pokemon += 1
                    trainer_has_pokemon = True

                    # Level distribution
                    level_range = f"{(level//10)*10}-{(level//10)*10+9}"
                    level_distribution[level_range] = (
                        level_distribution.get(level_range, 0) + 1
                    )

            if trainer_has_pokemon:
                trainers_with_pokemon += 1

        return {
            "total_trainers": total_trainers,
            "trainers_with_pokemon": trainers_with_pokemon,
            "total_pokemon": total_pokemon,
            "level_distribution": level_distribution,
            "average_pokemon_per_trainer": total_pokemon
            / max(trainers_with_pokemon, 1),
        }

    def clear_history(self):
        """Clear the modification history."""
        self.modification_history.clear()

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the modification history."""
        return self.modification_history.copy()

    def apply_level_modification_from_string(
        self,
        trainer_poke_data: List[Dict[str, Any]],
        modification_string: str,
        min_level: int = 1,
        max_level: int = 100,
        selected_trainers: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Apply level modifications using a string input like "+10" or "20%".
        Returns modified data instead of modifying in-place.

        Args:
            trainer_poke_data: List of trainer Pokemon data to modify
            modification_string: Modification string (e.g., "+10", "20%", "-5")
            min_level: Minimum allowed level (default: 1)
            max_level: Maximum allowed level (default: 100)
            selected_trainers: List of trainer IDs to modify (None for all)

        Returns:
            List of modified trainer Pokemon data (new copies)
        """
        import copy

        # Parse the modification string
        operation_type, value = self.parse_level_modification(modification_string)

        # Make copies of the data so we don't modify the original
        modified_data = copy.deepcopy(trainer_poke_data)

        # Apply modifications to the copies
        self.apply_level_modification(
            modified_data,
            operation_type,
            value,
            min_level,
            max_level,
            selected_trainers,
        )

        return modified_data
