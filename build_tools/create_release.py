#!/usr/bin/env python3
"""
Release preparation script for BDSP-Batch-Editor
Creates a production-ready release package
"""

import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime


def main():
    """Main release process"""
    print("BDSP-Batch-Editor Release Packager")
    print("=" * 40)

    # Work from the build_tools directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"Working in: {script_dir}")

    if not os.path.exists("release"):
        print("✗ Release folder not found. Run build_exe.py first.")
        input("Press Enter to exit...")
        return False

    # Create release ZIP
    version = input("Enter version (e.g., v1.0.0): ").strip()
    if not version:
        version = f"v{datetime.now().strftime('%Y.%m.%d')}"

    zip_name = f"BDSP-Batch-Editor-{version}-Windows.zip"

    print(f"Creating {zip_name}...")

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("release"):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, "release")
                zipf.write(file_path, arc_name)
                print(f"  Added: {arc_name}")

    file_size = os.path.getsize(zip_name) / (1024 * 1024)
    print(f"✓ Created {zip_name} ({file_size:.1f} MB)")

    # Create release notes template
    notes_file = f"release-notes-{version}.md"
    with open(notes_file, "w") as f:
        f.write(f"""# BDSP-Batch-Editor {version}

## What's New
- Bulk editing for BDSP trainer Pokemon levels
- User-friendly GUI interface with trainer selection
- Original level tracking with visual indicators
- Safe file operations (original files never modified)

## Download Options
- **BDSP-Batch-Editor.exe** - Standalone executable
- **{zip_name}** - Complete package with documentation

## Requirements
- Windows 10/11 (64-bit)
- TrainerTable.json extracted from BDSP using [BDSP-Repacker](https://github.com/Ai0796/BDSP-Repacker)

## Quick Start
1. Download and extract the ZIP file
2. Run `BDSP-Batch-Editor.exe`
3. Load your TrainerTable.json file
4. Make your modifications and save to a new file
5. Re-import the modified file using BDSP-Repacker

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
""")

    print(f"✓ Created release notes template: {notes_file}")
    print("\nRelease package is ready!")
    print(f"Upload these files to GitHub Releases:")
    print(f"  - {zip_name}")
    print(f"  - release/BDSP-Batch-Editor.exe (optional, for direct download)")
    print(f"\nUse the content from {notes_file} for your release description.")

    return True


if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
