#!/usr/bin/env python3
"""
BDSP-Batch-Editor
A Python GUI application for bulk editing Pokémon Brilliant Diamond/Shining Pearl trainer data.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Entry point for the BDSP-Batch-Editor application."""
    try:
        # Create the main window
        root = tk.Tk()
        app = MainWindow(root)

        # Start the GUI event loop
        root.mainloop()

    except Exception as e:
        messagebox.showerror(
            "Application Error", f"Failed to start application:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
