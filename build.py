#!/usr/bin/env python3
"""
Simple launcher for build tools from the root directory
"""

import os
import sys
import subprocess

def main():
    print("BDSP-Batch-Editor Build Launcher")
    print("=" * 35)
    print()
    print("Available options:")
    print("1. Build executable")
    print("2. Create release package")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\nLaunching build script...")
            try:
                subprocess.run([sys.executable, "build_tools/build_exe.py"], check=True)
            except subprocess.CalledProcessError:
                print("Build failed!")
                input("Press Enter to continue...")
            break
        elif choice == "2":
            print("\nLaunching release packager...")
            try:
                subprocess.run([sys.executable, "build_tools/create_release.py"], check=True)
            except subprocess.CalledProcessError:
                print("Release creation failed!")
                input("Press Enter to continue...")
            break
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
