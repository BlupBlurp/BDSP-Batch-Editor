"""
Personal masterdata handler module for BDSP-Batch-Editor.
Handles personal_masterdatas files following the MasterdataHandler pattern.
"""

import os
import shutil
import tempfile
import UnityPy
import rapidjson
from typing import Dict, Any, Optional, List
from pathlib import Path


class PersonalMasterdataHandler:
    """Handles unpacking and repacking of BDSP personal_masterdatas files."""

    def __init__(self):
        self.current_file_path: Optional[str] = None
        self.temp_dir: Optional[str] = None
        self.extracted_files: Dict[str, str] = {}  # content_name -> file_path mapping
        self.path_ids_file: Optional[str] = None

    def unpack_masterdata(self, masterdata_path: str) -> Optional[Dict[str, Any]]:
        """
        Unpack a personal_masterdatas file and extract available data.

        Args:
            masterdata_path: Path to the personal_masterdatas file

        Returns:
            Dictionary containing available data or None if not found

        Raises:
            FileNotFoundError: If the personal_masterdatas file doesn't exist
            Exception: If unpacking fails
        """
        if not os.path.exists(masterdata_path):
            raise FileNotFoundError(
                f"Personal masterdatas file not found: {masterdata_path}"
            )

        self.current_file_path = masterdata_path

        # Create temporary directory for extraction
        self.temp_dir = tempfile.mkdtemp(prefix="bdsp_personal_editor_")

        try:
            # Unpack the personal_masterdatas file
            self._unpack_assets(masterdata_path)

            # Find and catalog extracted files
            self._catalog_extracted_files()

            # Try to load PersonalTable data if available
            personal_table_data = self.load_content("PersonalTable")
            if personal_table_data:
                return {"PersonalTable": personal_table_data}

            # Return empty dict if no supported content found
            return {}

        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to unpack personal_masterdatas file: {str(e)}")

    def get_available_content(self) -> List[str]:
        """
        Get list of available content types in the extracted data.

        Returns:
            List of content type names found in the file
        """
        if not self.temp_dir:
            return []

        available_content = []
        extract_dir = os.path.join(self.temp_dir, "Export")

        if os.path.exists(extract_dir):
            for filename in os.listdir(extract_dir):
                if filename.endswith(".json"):
                    # Map common file names to content types
                    content_name = self._map_filename_to_content(filename)
                    if content_name and content_name not in available_content:
                        available_content.append(content_name)

        return available_content

    def load_content(self, content_name: str) -> Optional[Dict[str, Any]]:
        """
        Load specific content from the extracted data.

        Args:
            content_name: Name of the content to load (e.g., 'PersonalTable')

        Returns:
            Dictionary containing the content data or None if not found
        """
        if content_name in self.extracted_files:
            file_path = self.extracted_files[content_name]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return rapidjson.load(f)
            except Exception as e:
                print(f"Failed to load {content_name}: {str(e)}")
                return None

        return None

    def _unpack_assets(self, src_path: str) -> None:
        """Unpack assets from personal_masterdatas file using UnityPy."""
        if not self.temp_dir:
            raise RuntimeError("Temporary directory not initialized")

        extract_dir = os.path.join(self.temp_dir, "Export")
        path_dir = os.path.join(self.temp_dir, "pathIDs")

        os.makedirs(extract_dir, exist_ok=True)
        os.makedirs(path_dir, exist_ok=True)

        # Export types we're interested in
        export_types = ["MonoBehaviour"]
        existing_fps = []

        env = UnityPy.load(src_path)
        path_dic = {}

        for obj in env.objects:
            if obj.type.name in export_types:
                # Save decoded data
                tree = obj.read_typetree()

                # Get object name
                if "m_Name" in tree:
                    name = tree["m_Name"]
                else:
                    name = ""

                # Handle unnamed objects
                if name == "":
                    if obj.type.name == "MonoBehaviour":
                        script_path_id = tree["m_Script"]["m_PathID"]
                        for script in env.objects:
                            if script.path_id == script_path_id:
                                name = script.read().name

                name = os.path.basename(name)
                fp = os.path.join(extract_dir, f"{name}.json")

                # Handle duplicate names
                if fp.upper() in existing_fps:
                    fp = os.path.join(
                        extract_dir, f"{name}_{obj.type.name}_{obj.path_id}.json"
                    )
                    path_dic[str(obj.path_id)] = f"{name}_{obj.type.name}_{obj.path_id}"
                else:
                    path_dic[str(obj.path_id)] = name

                existing_fps.append(fp.upper())

                # Save JSON file
                with open(fp, "wb") as f:
                    rapidjson.dump(tree, f, ensure_ascii=False, indent=4)

        # Save path IDs mapping
        filename = os.path.basename(src_path)
        path_ids_path = os.path.join(path_dir, f"{filename}_pathIDs.json")
        with open(path_ids_path, "wb") as f:
            rapidjson.dump(path_dic, f, ensure_ascii=False, indent=4)

        self.path_ids_file = path_ids_path

    def _catalog_extracted_files(self) -> None:
        """Catalog all extracted files and map them to content types."""
        if not self.temp_dir:
            return

        extract_dir = os.path.join(self.temp_dir, "Export")

        if os.path.exists(extract_dir):
            for filename in os.listdir(extract_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(extract_dir, filename)
                    content_name = self._map_filename_to_content(filename)
                    if content_name:
                        self.extracted_files[content_name] = file_path

    def _map_filename_to_content(self, filename: str) -> Optional[str]:
        """
        Map extracted filenames to content type names.

        Args:
            filename: The extracted filename

        Returns:
            Content type name or None if not recognized
        """
        filename_lower = filename.lower()

        # Map common personal_masterdatas content
        if "personal" in filename_lower or "pokemon" in filename_lower:
            return "PersonalTable"
        elif "ability" in filename_lower:
            return "AbilityTable"
        elif "move" in filename_lower:
            return "MoveTable"
        elif "item" in filename_lower:
            return "ItemTable"
        elif "type" in filename_lower:
            return "TypeTable"

        return None

    def save_content(self, content_name: str, data: Dict[str, Any]) -> None:
        """
        Save modified content back to the extracted files.

        Args:
            content_name: Name of the content to save
            data: Modified data to save
        """
        if content_name in self.extracted_files:
            file_path = self.extracted_files[content_name]
            try:
                with open(file_path, "wb") as f:
                    rapidjson.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                raise Exception(f"Failed to save {content_name}: {str(e)}")
        else:
            raise ValueError(
                f"Content type {content_name} not found in extracted files"
            )

    def save_data(self, data: Dict[str, Any]) -> None:
        """
        Save data (generic method for unpacker compatibility).
        For personal_masterdatas, this saves PersonalTable data.

        Args:
            data: Dictionary containing the data to save
        """
        if "PersonalTable" in data:
            self.save_content("PersonalTable", data["PersonalTable"])
        else:
            # If data doesn't contain PersonalTable wrapper, assume it's direct PersonalTable data
            self.save_content("PersonalTable", data)

    def repack_masterdata(self, output_path: str) -> None:
        """
        Repack the modified data back into a personal_masterdatas file.

        Args:
            output_path: Path where the repacked file should be saved

        Raises:
            Exception: If repacking fails
        """
        if not self.current_file_path or not self.temp_dir:
            raise RuntimeError("No personal_masterdatas file currently loaded")

        try:
            self._repack_assets(output_path)
        except Exception as e:
            raise Exception(f"Failed to repack personal_masterdatas file: {str(e)}")

    def _repack_assets(self, output_path: str) -> None:
        """Repack assets back into personal_masterdatas file using UnityPy."""
        if not self.temp_dir or not self.path_ids_file:
            raise RuntimeError("Temporary directory or path IDs file not initialized")

        src_path = self.current_file_path
        extract_dir = os.path.join(self.temp_dir, "Export")

        # Load path IDs mapping
        with open(self.path_ids_file, "r") as f:
            path_dic = rapidjson.load(f)

        # Export types we handle
        export_types = ["MonoBehaviour"]

        env = UnityPy.load(src_path)

        for obj in env.objects:
            if obj.type.name in export_types:
                # Get object name from path mapping
                if str(obj.path_id) in path_dic:
                    name = path_dic[str(obj.path_id)]
                else:
                    # Fallback to reading tree for name
                    tree = obj.read_typetree()
                    name = self._get_object_name(env, obj, tree)

                # Check if modified JSON file exists
                json_path = os.path.join(extract_dir, f"{name}.json")
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf8") as f:
                        modified_data = rapidjson.load(f)
                        obj.save_typetree(modified_data)

        # Save repacked file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(env.file.save(packer=(64, 2)))

    def _get_object_name(self, env, obj, tree) -> str:
        """Get object name from tree data."""
        if "m_Name" in tree:
            name = tree["m_Name"]
        else:
            name = ""

        if name == "":
            if obj.type.name == "MonoBehaviour":
                script_path_id = tree["m_Script"]["m_PathID"]
                for script in env.objects:
                    if script.path_id == script_path_id:
                        name = script.read().name

        return os.path.basename(name) if name else f"unnamed_{obj.path_id}"

    def get_working_directory(self) -> Optional[str]:
        """Get the current working directory path for debugging."""
        return self.temp_dir

    def cleanup(self) -> None:
        """Clean up temporary files and directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Failed to clean up temporary directory: {str(e)}")

        self.temp_dir = None
        self.path_ids_file = None
        self.extracted_files.clear()
        self.current_file_path = None

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup()
