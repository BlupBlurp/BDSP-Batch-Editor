"""
Configuration constants for BDSP-Batch-Editor.
Defines supported file types, handlers, and content mappings.
"""

from typing import Dict, Any, List


# Supported file types and their configurations
SUPPORTED_FILES: Dict[str, Dict[str, Any]] = {
    "masterdatas": {
        "path": r"Data\StreamingAssets\AssetAssistant\Dpr\masterdatas",
        "handler": "MasterdataHandler",
        "supported_content": ["TrainerTable"],
        "display_name": "Trainer Data (masterdatas)",
        "description": "Main trainer data including levels, Pokemon, and movesets",
    },
    "personal_masterdatas": {
        "path": r"Data\StreamingAssets\AssetAssistant\Pml\personal_masterdatas",
        "handler": "PersonalMasterdataHandler",
        "supported_content": ["PersonalTable"],  # Added PersonalTable support
        "display_name": "Pokemon Data (personal_masterdatas)",
        "description": "Pokemon base stats, abilities, and species data",
    },
}

# Content types and their display information
CONTENT_TYPES: Dict[str, Dict[str, str]] = {
    "TrainerTable": {
        "display_name": "Trainer Pokemon",
        "description": "Trainer team compositions, levels, and movesets",
        "editor_class": "TrainerTableEditor",
    },
    "PersonalTable": {
        "display_name": "Pokemon Stats",
        "description": "Base stats, types, abilities for all Pokemon",
        "editor_class": "PersonalTableEditor",
    },
}

# Export configuration
EXPORT_CONFIG = {
    "single_file_mode": {
        "output_subfolder": "ModifiedFiles",
        "preserve_structure": False,
    },
    "romfs_mode": {
        "output_folder": "Output",
        "romfs_path": "romfs/Data/StreamingAssets/AssetAssistant",
        "preserve_structure": True,
    },
}

# File detection patterns
FILE_PATTERNS = {
    "masterdatas": ["masterdatas", "masterdatas.dat", "masterdatas.unity3d"],
    "personal_masterdatas": [
        "personal_masterdatas",
        "personal_masterdatas.dat",
        "personal_masterdatas.unity3d",
    ],
}

# UI Configuration
UI_CONFIG = {
    "main_window": {
        "title": "BDSP Batch Editor - Multi-File Support",
        "min_width": 1400,  # Increased from 1000
        "min_height": 900,  # Increased from 700
        "left_panel_width": 350,  # Increased from 300
        "default_width": 1500,  # Adjusted to fit better on 1920x1080
        "default_height": 950,  # Adjusted to fit better on 1920x1080
    },
    "file_tree": {"show_unsupported": True, "unsupported_style": "disabled"},
    "personal_table_editor": {
        "multi_column_layout": True,
        "columns_per_row": 3,  # Display stats in 3 columns
        "field_width": 12,  # Reduced field width to fit more
        "category_spacing": 15,  # Space between categories
    },
}


def get_handler_class_name(file_type: str) -> str:
    """Get the handler class name for a given file type."""
    return SUPPORTED_FILES.get(file_type, {}).get("handler", "")


def get_supported_content_list(file_type: str) -> List[str]:
    """Get list of supported content types for a file type."""
    return SUPPORTED_FILES.get(file_type, {}).get("supported_content", [])


def is_content_supported(file_type: str, content_name: str) -> bool:
    """Check if a content type is supported for a given file type."""
    return content_name in get_supported_content_list(file_type)


def get_display_name(file_type: str) -> str:
    """Get user-friendly display name for a file type."""
    return SUPPORTED_FILES.get(file_type, {}).get("display_name", file_type)


def get_content_display_name(content_name: str) -> str:
    """Get user-friendly display name for a content type."""
    return CONTENT_TYPES.get(content_name, {}).get("display_name", content_name)
