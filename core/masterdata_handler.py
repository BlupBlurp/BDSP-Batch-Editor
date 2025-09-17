"""
Masterdata handler module for BDSP-Batch-Editor.
Integrates BDSP-Repacker functionality to handle masterdatas files directly.
"""

import os
import shutil
import tempfile
import UnityPy
import rapidjson
from typing import Dict, Any, Optional, List
import asyncio
from pathlib import Path


class MasterdataHandler:
    """Handles unpacking and repacking of BDSP masterdatas files."""

    def __init__(self):
        self.current_file_path: Optional[str] = None
        self.temp_dir: Optional[str] = None
        self.trainer_table_path: Optional[str] = None
        self.path_ids_file: Optional[str] = None

    def unpack_masterdata(self, masterdata_path: str) -> Optional[Dict[str, Any]]:
        """
        Unpack a masterdatas file and extract TrainerTable.json.

        Args:
            masterdata_path: Path to the masterdatas file

        Returns:
            Dictionary containing TrainerTable data or None if not found

        Raises:
            FileNotFoundError: If the masterdatas file doesn't exist
            Exception: If unpacking fails
        """
        if not os.path.exists(masterdata_path):
            raise FileNotFoundError(f"Masterdatas file not found: {masterdata_path}")

        self.current_file_path = masterdata_path

        # Create temporary directory for extraction
        self.temp_dir = tempfile.mkdtemp(prefix="bdsp_editor_")

        try:
            # Unpack the masterdatas file
            self._unpack_assets(masterdata_path)

            # Find and load TrainerTable.json
            trainer_table_data = self._find_and_load_trainer_table()

            return trainer_table_data

        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to unpack masterdatas file: {str(e)}")

    def _unpack_assets(self, src_path: str) -> None:
        """Unpack assets from masterdatas file using UnityPy."""
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

    def _find_and_load_trainer_table(self) -> Optional[Dict[str, Any]]:
        """Find and load TrainerTable.json from extracted files."""
        if not self.temp_dir:
            raise RuntimeError("Temporary directory not initialized")

        extract_dir = os.path.join(self.temp_dir, "Export")

        # Look for TrainerTable.json or similar files
        trainer_table_candidates = [
            "TrainerTable.json",
            "trainertable.json",
            "TrainerPoke.json",
            "trainerpoke.json",
        ]

        trainer_table_path = None

        # First try exact matches
        for candidate in trainer_table_candidates:
            full_path = os.path.join(extract_dir, candidate)
            if os.path.exists(full_path):
                trainer_table_path = full_path
                break

        # If not found, search for files containing trainer data
        if not trainer_table_path:
            for filename in os.listdir(extract_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(extract_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = rapidjson.load(f)
                            if isinstance(data, dict) and "TrainerPoke" in data:
                                trainer_table_path = file_path
                                break
                    except:
                        continue

        if not trainer_table_path:
            return None

        self.trainer_table_path = trainer_table_path

        # Load the trainer table data
        with open(trainer_table_path, "r", encoding="utf-8") as f:
            return rapidjson.load(f)

    def save_data(self, data: Dict[str, Any]) -> None:
        """
        Save modified data back to the extracted files.
        For masterdatas, this saves TrainerTable data.

        Args:
            data: Modified data dictionary
        """
        if not self.trainer_table_path:
            raise RuntimeError("No trainer table file loaded")

        with open(self.trainer_table_path, "wb") as f:
            rapidjson.dump(data, f, ensure_ascii=False, indent=4)

    def repack_masterdata(self, output_path: str) -> None:
        """
        Repack the modified data back into a masterdatas file.

        Args:
            output_path: Path where the repacked masterdatas file will be saved

        Raises:
            RuntimeError: If no masterdatas file is loaded
            Exception: If repacking fails
        """
        if not self.current_file_path or not self.temp_dir:
            raise RuntimeError("No masterdatas file loaded for repacking")

        try:
            self._repack_assets(output_path)
        except Exception as e:
            raise Exception(f"Failed to repack masterdatas file: {str(e)}")

    def _repack_assets(self, output_path: str) -> None:
        """Repack assets back into masterdatas file using UnityPy."""
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
        """Get the temporary working directory path."""
        return self.temp_dir

    def cleanup(self) -> None:
        """Clean up temporary files and directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None

        self.current_file_path = None
        self.trainer_table_path = None
        self.path_ids_file = None

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup()
