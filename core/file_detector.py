"""
File detection module for BDSP-Batch-Editor.
Handles detection of ROMFS structure and file type identification.
"""

import os
from pathlib import Path
from typing import Dict, Optional, List


class FileDetector:
    """Detects and categorizes BDSP file types within ROMFS structures."""

    # Supported file paths relative to ROMFS root
    SUPPORTED_PATHS = {
        "masterdatas": r"Data\StreamingAssets\AssetAssistant\Dpr\masterdatas",
        "personal_masterdatas": r"Data\StreamingAssets\AssetAssistant\Pml\personal_masterdatas",
    }

    # Alternative file names that might be encountered
    ALTERNATIVE_NAMES = {
        "masterdatas": ["masterdatas", "masterdatas.dat", "masterdatas.unity3d"],
        "personal_masterdatas": [
            "personal_masterdatas",
            "personal_masterdatas.dat",
            "personal_masterdatas.unity3d",
        ],
    }

    @staticmethod
    def detect_romfs_structure(folder_path: str) -> Dict[str, str]:
        """
        Detect BDSP file structure in a ROMFS directory.

        Args:
            folder_path: Path to the ROMFS directory or parent directory

        Returns:
            Dictionary mapping file types to their absolute paths
            Example: {'masterdatas': 'C:/path/to/masterdatas', 'personal_masterdatas': None}
        """
        detected_files = {}
        folder_path_obj = Path(folder_path)

        # Check if this is already a ROMFS directory or contains one
        romfs_candidates = []

        # Check current directory
        if FileDetector._is_romfs_directory(folder_path_obj):
            romfs_candidates.append(folder_path_obj)

        # Check for romfs subdirectory
        romfs_subdir = folder_path_obj / "romfs"
        if romfs_subdir.exists() and FileDetector._is_romfs_directory(romfs_subdir):
            romfs_candidates.append(romfs_subdir)

        # Check subdirectories for romfs-like structure
        for subdir in folder_path_obj.iterdir():
            if subdir.is_dir() and FileDetector._is_romfs_directory(subdir):
                romfs_candidates.append(subdir)

        # Process each candidate
        for romfs_root in romfs_candidates:
            for file_type, relative_path in FileDetector.SUPPORTED_PATHS.items():
                if file_type not in detected_files or detected_files[file_type] is None:
                    file_path = FileDetector._find_file_by_path(
                        romfs_root, relative_path, file_type
                    )
                    if file_path:
                        detected_files[file_type] = str(file_path)

        # Ensure all supported file types are represented
        for file_type in FileDetector.SUPPORTED_PATHS.keys():
            if file_type not in detected_files:
                detected_files[file_type] = None

        return detected_files

    @staticmethod
    def get_file_type(file_path: str) -> Optional[str]:
        """
        Determine the file type of a given file.

        Args:
            file_path: Absolute path to the file

        Returns:
            File type string or None if unsupported
        """
        file_path_obj = Path(file_path)
        filename = file_path_obj.name.lower()

        # Check against known file names
        for file_type, alt_names in FileDetector.ALTERNATIVE_NAMES.items():
            for alt_name in alt_names:
                if filename == alt_name.lower() or filename.startswith(
                    alt_name.lower()
                ):
                    return file_type

        # Check by parent directory structure
        parent_path = str(file_path_obj.parent)
        for file_type, supported_path in FileDetector.SUPPORTED_PATHS.items():
            # Convert to forward slashes for comparison
            normalized_supported = supported_path.replace("\\", "/")
            normalized_parent = parent_path.replace("\\", "/")

            if normalized_supported.lower() in normalized_parent.lower():
                return file_type

        return None

    @staticmethod
    def get_supported_content(file_type: str) -> List[str]:
        """
        Get list of supported content types for a given file type.

        Args:
            file_type: The file type (e.g., 'masterdatas', 'personal_masterdatas')

        Returns:
            List of supported content type names
        """
        # Import here to avoid circular dependencies
        from core.config import SUPPORTED_FILES

        if file_type in SUPPORTED_FILES:
            return SUPPORTED_FILES[file_type]["supported_content"]
        return []

    @staticmethod
    def _is_romfs_directory(path: Path) -> bool:
        """Check if a directory has ROMFS-like structure."""
        # Look for characteristic BDSP directory structure
        data_dir = path / "Data"
        streaming_assets = data_dir / "StreamingAssets" / "AssetAssistant"

        return (
            data_dir.exists()
            and streaming_assets.exists()
            and (streaming_assets / "Dpr").exists()
            or (streaming_assets / "Pml").exists()
        )

    @staticmethod
    def _find_file_by_path(
        romfs_root: Path, relative_path: str, file_type: str
    ) -> Optional[Path]:
        """Find a file by its relative path, trying alternative names."""
        # Convert relative path to use forward slashes
        relative_path = relative_path.replace("\\", "/")
        expected_path = romfs_root / Path(relative_path)

        # Try exact path first
        if expected_path.exists():
            return expected_path

        # Try alternative names in the same directory
        parent_dir = expected_path.parent
        if parent_dir.exists():
            for alt_name in FileDetector.ALTERNATIVE_NAMES.get(file_type, []):
                alt_path = parent_dir / alt_name
                if alt_path.exists():
                    return alt_path

        return None

    @staticmethod
    def validate_romfs_structure(folder_path: str) -> bool:
        """
        Validate that a folder contains a proper ROMFS structure.

        Args:
            folder_path: Path to validate

        Returns:
            True if valid ROMFS structure is found
        """
        detected = FileDetector.detect_romfs_structure(folder_path)
        return any(path is not None for path in detected.values())
