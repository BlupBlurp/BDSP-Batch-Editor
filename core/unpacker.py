"""
Core unpacker module for BDSP-Batch-Editor.
Handles file operations and JSON processing, now with masterdatas support.
"""

import json
import os
import shutil
from typing import Dict, Any, Optional

from core.masterdata_handler import MasterdataHandler


class FileUnpacker:
    """Handles unpacking and packing of BDSP trainer data files."""

    def __init__(self):
        self.current_file_path: Optional[str] = None
        self.trainer_data: Optional[Dict[str, Any]] = None
        self.backup_created: bool = False
        self.masterdata_handler: Optional[MasterdataHandler] = None
        self.is_masterdata_file: bool = False

    def load_trainer_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse either a TrainerTable JSON file or a masterdatas file.

        Args:
            file_path: Path to the JSON or masterdatas file

        Returns:
            Dictionary containing the parsed trainer data

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
            Exception: If masterdatas unpacking fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type by extension and content
        _, file_ext = os.path.splitext(file_path)

        if file_ext.lower() == ".json":
            # Handle JSON file directly
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                self.current_file_path = file_path
                self.trainer_data = data
                self.is_masterdata_file = False

                return data

            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Invalid JSON file: {str(e)}", e.doc, e.pos)

        else:
            # Handle masterdatas file
            try:
                self.masterdata_handler = MasterdataHandler()
                data = self.masterdata_handler.unpack_masterdata(file_path)

                if not data:
                    raise ValueError("No TrainerTable data found in masterdatas file")

                self.current_file_path = file_path
                self.trainer_data = data
                self.is_masterdata_file = True

                return data

            except Exception as e:
                if self.masterdata_handler:
                    self.masterdata_handler.cleanup()
                    self.masterdata_handler = None
                raise Exception(f"Failed to load masterdatas file: {str(e)}")

    def extract_trainer_poke_data(self) -> list:
        """
        Extract TrainerPoke data from the loaded trainer data.

        Returns:
            List of trainer Pokemon data entries

        Raises:
            ValueError: If no data is loaded or TrainerPoke section not found
        """
        if not self.trainer_data:
            raise ValueError("No trainer data loaded")

        if "TrainerPoke" not in self.trainer_data:
            raise ValueError("TrainerPoke section not found in data")

        return self.trainer_data["TrainerPoke"]

    def create_backup(self) -> str:
        """
        Create a backup of the current file.

        Returns:
            Path to the backup file

        Raises:
            ValueError: If no file is currently loaded
        """
        if not self.current_file_path:
            raise ValueError("No file currently loaded")

        backup_path = f"{self.current_file_path}.backup"
        shutil.copy2(self.current_file_path, backup_path)
        self.backup_created = True

        return backup_path

    def save_trainer_file(self, output_path: Optional[str] = None) -> None:
        """
        Save the modified trainer data to file.

        Args:
            output_path: Path to save the file. If None, overwrites the original file.

        Raises:
            ValueError: If no data is loaded
        """
        if not self.trainer_data:
            raise ValueError("No trainer data to save")

        save_path = output_path or self.current_file_path

        if not save_path:
            raise ValueError("No save path specified")

        if self.is_masterdata_file and self.masterdata_handler:
            # Save for masterdatas file - need to save to temp first, then repack
            self.masterdata_handler.save_trainer_data(self.trainer_data)
            self.masterdata_handler.repack_masterdata(save_path)
        else:
            # Save for JSON file
            with open(save_path, "w", encoding="utf-8") as file:
                json.dump(self.trainer_data, file, indent=4, ensure_ascii=False)

    def get_pokemon_count_by_trainer(self) -> Dict[int, int]:
        """
        Get the count of Pokemon for each trainer.

        Returns:
            Dictionary mapping trainer ID to Pokemon count
        """
        if not self.trainer_data:
            return {}

        trainer_poke_data = self.extract_trainer_poke_data()
        pokemon_counts = {}

        for entry in trainer_poke_data:
            trainer_id = entry.get("ID", 0)
            count = 0

            # Count non-zero Pokemon entries (P1-P6)
            for i in range(1, 7):
                mons_no_key = f"P{i}MonsNo"
                level_key = f"P{i}Level"

                if entry.get(mons_no_key, 0) > 0 and entry.get(level_key, 0) > 0:
                    count += 1

            pokemon_counts[trainer_id] = count

        return pokemon_counts

    def validate_trainer_data(self) -> bool:
        """
        Validate the structure of the loaded trainer data.

        Returns:
            True if data is valid, False otherwise
        """
        if not self.trainer_data:
            return False

        # Check for required sections
        if "TrainerPoke" not in self.trainer_data:
            return False

        trainer_poke = self.trainer_data["TrainerPoke"]

        if not isinstance(trainer_poke, list):
            return False

        # Check if at least one entry exists and has expected structure
        if len(trainer_poke) > 0:
            first_entry = trainer_poke[0]
            required_keys = ["ID", "P1Level", "P1MonsNo"]

            for key in required_keys:
                if key not in first_entry:
                    return False

        return True

    def cleanup(self) -> None:
        """Clean up resources, especially for masterdatas files."""
        if self.masterdata_handler:
            self.masterdata_handler.cleanup()
            self.masterdata_handler = None

        self.current_file_path = None
        self.trainer_data = None
        self.backup_created = False
        self.is_masterdata_file = False

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup()
