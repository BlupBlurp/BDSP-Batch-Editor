# BDSP-Batch-Editor v2.0.0

## 🎉 Major Update: Direct Masterdatas Support!

**NEW in v2.0.0:**

- ⭐ **Direct masterdatas file editing** - No need to extract JSON files manually!
- ⭐ **Integrated BDSP-Repacker functionality** - Built-in unpack/edit/repack workflow
- ⭐ **Seamless file processing** - Open masterdatas files directly from the app
- ⭐ **Comprehensive verification system** - Ensure only Pokemon levels are modified
- ⭐ **Backward compatibility** - Still works with extracted JSON files

## Enhanced Features

- Bulk editing for BDSP trainer Pokemon levels with multiple modification types
- User-friendly GUI interface with trainer selection and filtering
- Original level tracking with visual change indicators
- Safe file operations (original files never modified)
- Real-time preview of modifications before applying
- Detailed statistics and modification reports

## Download Options

- **BDSP-Batch-Editor.exe** - Standalone executable
- **BDSP-Batch-Editor-v2.0.0-Windows.zip** - Complete package with documentation

## Requirements

- Windows 10/11 (64-bit)
- **NEW:** Works directly with masterdatas files from your BDSP game data
- **LEGACY:** Still supports TrainerTable.json files

## Quick Start

**Method 1: Direct Masterdatas Editing (Recommended)**

1. Download and extract the ZIP file
2. Run `BDSP-Batch-Editor.exe`
3. Click "Open Masterdatas/JSON" and select your masterdatas file
4. Make your level modifications using the intuitive interface
5. Save to a new masterdatas file - ready to use in your game!

**Method 2: Traditional JSON Workflow**

1. Extract TrainerTable.json using [BDSP-Repacker](https://github.com/Ai0796/BDSP-Repacker)
2. Load the JSON file in BDSP-Batch-Editor
3. Make modifications and save
4. Re-import using BDSP-Repacker

## Verification Tools

New comprehensive verification system to ensure data integrity:

- `python tests/verify_masterdatas.py original_file modified_file`
- Interactive verification with detailed reports
- Automatic detection of unintended changes

## Support

For help and community discussion, join our [Discord Server](https://discord.gg/5Qwz85EvC3)

## Installation from Source

```bash
git clone https://github.com/BlupBlurp/BDSP-Batch-Editor.git
cd BDSP-Batch-Editor
python main.py
```

## Building from Source

```bash
python build_tools/build_exe.py
```
