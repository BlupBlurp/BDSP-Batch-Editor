"""
Export manager module for BDSP-Batch-Editor.
Handles single file and ROMFS structure export modes.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional, List
from core.config import EXPORT_CONFIG, SUPPORTED_FILES


class ExportManager:
    """Manages export operations for single files and ROMFS structures."""

    def __init__(self):
        self.export_config = EXPORT_CONFIG

    def export_single_file(self, unpacker, output_path: str) -> bool:
        """
        Export a single modified file.

        Args:
            unpacker: FileUnpacker instance with loaded data
            output_path: Path where the file should be saved

        Returns:
            True if successful, False otherwise
        """
        try:
            unpacker.save_trainer_file(output_path, create_backup=False)
            return True
        except Exception as e:
            raise Exception(f"Failed to export single file: {str(e)}")

    def export_romfs_structure(
        self,
        detected_files: Dict[str, Optional[str]],
        modified_files: Dict[str, str],  # file_type -> temp_modified_path
        output_directory: str,
    ) -> bool:
        """
        Export complete ROMFS structure with modifications.

        Args:
            detected_files: Original detected files mapping
            modified_files: Modified files that need to be exported
            output_directory: Directory where ROMFS structure should be created

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create base ROMFS structure
            romfs_base = os.path.join(output_directory, "romfs")
            asset_base = os.path.join(
                romfs_base, "Data", "StreamingAssets", "AssetAssistant"
            )

            # Create directory structure
            for file_type, config in SUPPORTED_FILES.items():
                if file_type in detected_files and detected_files[file_type]:
                    # Determine target directory
                    if file_type == "masterdatas":
                        target_dir = os.path.join(asset_base, "Dpr")
                    elif file_type == "personal_masterdatas":
                        target_dir = os.path.join(asset_base, "Pml")
                    else:
                        continue

                    # Create directory
                    os.makedirs(target_dir, exist_ok=True)

                    # Copy file (modified if available, otherwise original)
                    source_path = modified_files.get(
                        file_type, detected_files[file_type]
                    )
                    original_path = detected_files[file_type]
                    if source_path and original_path and os.path.exists(source_path):
                        filename = os.path.basename(original_path)
                        target_path = os.path.join(target_dir, filename)
                        shutil.copy2(source_path, target_path)

            return True

        except Exception as e:
            raise Exception(f"Failed to export ROMFS structure: {str(e)}")

    def create_output_directory(self, base_path: str, mode: str = "single") -> str:
        """
        Create appropriate output directory structure.

        Args:
            base_path: Base directory for output
            mode: Export mode ("single" or "romfs")

        Returns:
            Path to the created output directory
        """
        config = self.export_config[
            f"{mode}_file_mode" if mode == "single" else f"{mode}_mode"
        ]

        if mode == "single":
            output_dir = os.path.join(base_path, config["output_subfolder"])
        else:
            output_dir = os.path.join(base_path, config["output_folder"])

        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def validate_export_requirements(
        self,
        detected_files: Dict[str, Optional[str]],
        selected_file_type: Optional[str],
        mode: str,
    ) -> bool:
        """
        Validate that export requirements are met.

        Args:
            detected_files: Detected files mapping
            selected_file_type: Currently selected file type
            mode: Export mode

        Returns:
            True if requirements are met
        """
        if mode == "single":
            return (
                selected_file_type is not None
                and selected_file_type in detected_files
                and detected_files[selected_file_type] is not None
            )
        else:
            # ROMFS mode - at least one file should be detected
            return any(path is not None for path in detected_files.values())

    def get_export_summary(
        self,
        detected_files: Dict[str, Optional[str]],
        modified_files: List[str],
        mode: str,
    ) -> str:
        """
        Get a summary of what will be exported.

        Args:
            detected_files: Detected files mapping
            modified_files: List of modified file types
            mode: Export mode

        Returns:
            Summary string
        """
        if mode == "single":
            if modified_files:
                return f"Export single modified {modified_files[0]} file"
            else:
                return "Export single file (no modifications)"
        else:
            total_files = sum(1 for path in detected_files.values() if path is not None)
            modified_count = len(modified_files)
            return f"Export ROMFS structure with {total_files} files ({modified_count} modified)"
