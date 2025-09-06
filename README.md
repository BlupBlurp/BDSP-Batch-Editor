# BDSP-Batch-Editor

A Python GUI application for bulk editing Pokémon Brilliant Diamond/Shining Pearl trainer data.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## Community & Support

For help or questions, join my modding Discord server:

[Join Discord Server](https://discord.gg/5Qwz85EvC3)

## Current Functionality

This application currently focuses on **bulk editing trainer Pokemon levels**. Future updates are planned to expand functionality to include:

- Editing other trainer attributes (Pokemon species, moves, items, etc.)
- Support for additional game data files
- More advanced editing features and batch operations

## Getting TrainerTable.json

To use this application, you need to extract the TrainerTable.json file from your BDSP game data.
You can obtain this file using the **BDSP-Repacker** tool:

**Repository:** https://github.com/Ai0796/BDSP-Repacker

Follow the BDSP-Repacker documentation to export the TrainerTable.json file from your game files.
Once exported, you can use this application to edit the trainer data and then re-import it using the same tool.

## Basic Usage

1. **Extract TrainerTable.json** from your BDSP game files using BDSP-Repacker
2. **Open the TrainerTable JSON file** using the "Open TrainerTable JSON" button
3. **Enter level modifications** in the input field:
   - `+10` - Add 10 levels to all Pokémon
   - `-5` - Subtract 5 levels from all Pokémon
   - `20%` - Increase levels by 20%
   - `-15%` - Decrease levels by 15%
4. **Preview changes** to see what will be modified
5. **Apply changes** to execute the modifications
6. **Save your work** to a new file (original file remains unchanged)
7. **Re-import the modified file** back to your game using BDSP-Repacker

### Data File Format

The application works with BDSP TrainerTable.json files extracted from the `masterdatas` file, containing trainer data:

```json
{
  "TrainerPoke": [
    {
      "ID": 0,
      "P1Level": 25,
      "P1MonsNo": 387,
      "P2Level": 27,
      "P2MonsNo": 390,
      ...
    }
  ]
}
```

## Development

### Core Modules

- **`core/unpacker.py`**: Handles JSON file loading, validation, and saving
- **`core/level_editor.py`**: Implements level modification logic and statistics
- **`gui/main_window.py`**: Main application interface
- **`gui/dialogs.py`**: File selection and confirmation dialogs

## Building Executable

Create a standalone executable (.exe) file:

### Quick Build

1. **Run the build script:**

   ```bash
   python build_tools/build_exe.py
   ```

2. **Find your executable:**
   - Release package: `build_tools/release/` folder with executable and documentation

### Manual Build (Advanced)

If you prefer manual control:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name=BDSP-Batch-Editor --optimize=2 main.py

# Or use the spec file for advanced configuration
pyinstaller build_tools/BDSP-Batch-Editor.spec
```
