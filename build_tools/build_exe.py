#!/usr/bin/env python3
"""
Build script for creating BDSP-Batch-Editor executable
Uses PyInstaller to create a standalone .exe file
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
        return True
    except ImportError:
        print("Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install PyInstaller")
            return False


def main():
    """Main build process"""
    print("BDSP-Batch-Editor Executable Builder")
    print("=" * 40)

    # Ensure we're in the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print(f"Working in: {project_root}")

    # Step 1: Install PyInstaller
    if not install_pyinstaller():
        input("Press Enter to exit...")
        return False

    # Step 2: Clean previous builds
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned {dir_name} directory")

    # Step 3: Build executable
    print("\nBuilding executable...")
    
    # PyInstaller command with optimized settings
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=BDSP-Batch-Editor",
        "--distpath=build_tools/release",  # Output directly to build_tools/release
        "--add-data=README.md;.",
        "--optimize=2",
        "--clean",
        "main.py"
    ]

    # Add optional files if they exist
    optional_files = [
        ("USAGE.md", "--add-data=USAGE.md;."),
        ("TrainerTable_example.json", "--add-data=TrainerTable_example.json;."),
        ("icon.ico", "--icon=icon.ico"),
    ]

    for file_path, flag in optional_files:
        if os.path.exists(file_path):
            cmd.insert(-1, flag)
        elif "icon.ico" in flag:
            print("Note: No icon.ico found, building without custom icon")

    try:
        subprocess.check_call(cmd)
        print("✓ Executable built successfully!")
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        input("Press Enter to exit...")
        return False

    # Step 4: Add documentation to release package
    print("\nAdding documentation to release package...")
    
    release_dir = "build_tools/release"
    if not os.path.exists(f"{release_dir}/BDSP-Batch-Editor.exe"):
        print("✗ Executable not found in release folder")
        input("Press Enter to exit...")
        return False

    # Copy documentation to release folder
    docs_to_copy = ["README.md", "USAGE.md", "TrainerTable_example.json"]
    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy2(doc, f"{release_dir}/{doc}")

    print(f"✓ Release package created in '{release_dir}' folder")
    exe_size = os.path.getsize(f"{release_dir}/BDSP-Batch-Editor.exe") // 1024 // 1024
    print(f"   - BDSP-Batch-Editor.exe ({exe_size} MB)")
    print("   - README.md")
    print("   - Documentation files")

    print("\n" + "=" * 40)
    print("✓ Build completed successfully!")
    print("\nYour executable is ready for distribution:")
    print(f"- Release package: {release_dir}/ folder")
    print("\nYou can now upload the release/ folder contents to GitHub Releases")

    return True


if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
