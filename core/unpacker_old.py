"""
Core unpacker module for BDSP-Batch-Editor.
Handles file operations with multi-file type support through handlers.
"""

import json
import os
import shutil
from typing import Dict, Any, Optional

from core.masterdata_handler import MasterdataHandler
from core.personal_masterdatas_handler import PersonalMasterdataHandler
from core.file_detector import FileDetector
from core.config import get_handler_class_name


class FileUnpacker:
    """Handles unpacking and packing of BDSP data files through specialized handlers."""

    def __init__(self):
        self.current_file_path: Optional[str] = None
        self.current_file_type: Optional[str] = None
        self.trainer_data: Optional[Dict[str, Any]] = None
        self.backup_created: bool = False
        self.handler: Optional[Any] = None  # Will be MasterdataHandler or PersonalMasterdataHandler

    def load_trainer_file(self, file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Load and parse a BDSP data file through the appropriate handler.

        Args:
            file_path: Path to the data file
            file_type: Optional file type hint, will be detected if not provided

        Returns:
            Dictionary containing the parsed data

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If file type is unsupported
            Exception: If unpacking fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect file type if not provided
        if not file_type:
            file_type = FileDetector.get_file_type(file_path)
            
        if not file_type:
            raise ValueError(f"Unsupported file type for: {file_path}")

        # Clean up any previous handler
        if self.handler:
            self.handler.cleanup()
            self.handler = None

        try:
            # Create appropriate handler
            self.handler = self._create_handler(file_type)
            
            # Load data through handler
            data = self.handler.unpack_masterdata(file_path)
            
            if not data:
                raise ValueError(f"No supported data found in file: {file_path}")

            self.current_file_path = file_path
            self.current_file_type = file_type
            self.trainer_data = data

            return data

        except Exception as e:
            if self.handler:
                self.handler.cleanup()
                self.handler = None
            raise Exception(f"Failed to load {file_type} file: {str(e)}")

    def _create_handler(self, file_type: str):
        """Create the appropriate handler for the given file type."""
        if file_type == 'masterdatas':
            return MasterdataHandler()
        elif file_type == 'personal_masterdatas':
            return PersonalMasterdataHandler()
        else:
            raise ValueError(f"No handler available for file type: {file_type}")

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
        Create a backup of the original file before modification.

        Returns:
            Path to the backup file

        Raises:
            RuntimeError: If no file is currently loaded
            Exception: If backup creation fails
        """
        if not self.current_file_path:
            raise RuntimeError("No file loaded to backup")

        if self.backup_created:
            return f"{self.current_file_path}.backup"

        try:
            backup_path = f"{self.current_file_path}.backup"
            shutil.copy2(self.current_file_path, backup_path)
            self.backup_created = True
            return backup_path

        except Exception as e:
            raise Exception(f"Failed to create backup: {str(e)}")

    def save_trainer_file(self, output_path: Optional[str] = None, create_backup: bool = True) -> str:
        """
        Save the modified trainer data back to file through the appropriate handler.

        Args:
            output_path: Optional output path, uses current file path if not specified
            create_backup: Whether to create a backup before saving

        Returns:
            Path to the saved file

        Raises:
            RuntimeError: If no data is loaded
            Exception: If saving fails
        """
        if not self.trainer_data or not self.current_file_path or not self.handler:
            raise RuntimeError("No trainer data loaded or no handler available")

        if create_backup and not self.backup_created:
            self.create_backup()

        save_path = output_path or self.current_file_path

        try:
            # For masterdatas files, use the handler's repack functionality
            if hasattr(self.handler, 'repack_masterdata'):
                self.handler.repack_masterdata(save_path)
            else:
                raise NotImplementedError(f"Saving not implemented for {self.current_file_type} files")

            return save_path

        except Exception as e:
            raise Exception(f"Failed to save {self.current_file_type} file: {str(e)}")

    def update_trainer_poke_data(self, modified_data: list) -> None:
        """
        Update the TrainerPoke data in the loaded trainer data.

        Args:
            modified_data: List of modified trainer Pokemon entries

        Raises:
            ValueError: If no data is loaded
        """
        if not self.trainer_data:
            raise ValueError("No trainer data loaded")

        self.trainer_data["TrainerPoke"] = modified_data

    def get_pokemon_counts(self) -> Dict[int, int]:
        """
        Get count of Pokemon for each trainer.

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
        """Clean up resources, especially for handler objects."""
        if self.handler:
            self.handler.cleanup()
            self.handler = None

        self.current_file_path = None
        self.current_file_type = None
        self.trainer_data = None
        self.backup_created = False

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup()
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
